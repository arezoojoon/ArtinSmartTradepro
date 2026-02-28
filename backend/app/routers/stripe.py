"""
Stripe Integration Router.
CRITICAL RULE: Plan activation ONLY happens via webhook, never from frontend redirect.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Header, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.subscription import Subscription, Plan
from app.models.billing_ext import BillingCheckoutSession, StripeEvent, CheckoutSessionStatus
from app.middleware.auth import get_current_active_user
from app.middleware.plan_gate import invalidate_plan_cache
from app.config import get_settings
from app.services.provisioning import trigger_provisioning
from pydantic import BaseModel
from typing import Optional
import stripe
import json

settings = get_settings()
router = APIRouter()

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY if hasattr(settings, 'STRIPE_SECRET_KEY') else ""

# Dynamic frontend origin for return URLs
_FRONTEND_ORIGIN = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')

class CreateCheckoutRequest(BaseModel):
    plan_name: str  # "professional" or "enterprise"
    billing_cycle: str = "monthly"  # "monthly" or "yearly"

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str

@router.post("/create-checkout", response_model=CheckoutResponse)
def create_checkout_session(
    body: CreateCheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe Checkout Session for subscription payment.
    Does NOT activate the plan — that happens ONLY via webhook.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="No organization associated")
    
    # Look up plan from DB
    plan = db.execute(
        select(Plan).where(Plan.name == body.plan_name).where(Plan.is_active == True)
    ).scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan '{body.plan_name}' not found")
    
    # Get Stripe Price ID
    price_id = plan.stripe_price_id_monthly if body.billing_cycle == "monthly" else plan.stripe_price_id_yearly
    if not price_id:
        raise HTTPException(status_code=400, detail=f"Stripe pricing not configured for {body.plan_name} ({body.billing_cycle})")
    
    # Check existing subscription
    existing = db.execute(
        select(Subscription).where(Subscription.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()
    
    try:
        # Create or reuse Stripe customer
        customer_id = existing.stripe_customer_id if existing else None
        if not customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"tenant_id": str(current_user.tenant_id)}
            )
            customer_id = customer.id
        
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{_FRONTEND_ORIGIN}/settings/billing?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{_FRONTEND_ORIGIN}/settings/billing?canceled=true",
            metadata={
                "tenant_id": str(current_user.tenant_id),
                "plan_id": str(plan.id),
                "plan_name": plan.name,
            },
        )
        
        # [NEW] Secure Session Binding
        checkout_session = BillingCheckoutSession(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            stripe_session_id=session.id,
            stripe_customer_id=customer_id,
            plan_code=plan.name,
            status=CheckoutSessionStatus.OPEN
        )
        db.add(checkout_session)
        db.commit()
        
        return CheckoutResponse(checkout_url=session.url, session_id=session.id)
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Stripe Webhook Handler.
    THIS is the ONLY place where plan activation happens.
    
    Handles:
    - checkout.session.completed → activate plan
    - customer.subscription.updated → sync status
    - customer.subscription.deleted → deactivate plan
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET if hasattr(settings, 'STRIPE_WEBHOOK_SECRET') else ""
    
    # Verify signature — ALWAYS required, no dev-mode bypass
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    
    event_type = event.get("type", "") if isinstance(event, dict) else event.type
    data = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event.data.object
    
    # [NEW] Idempotency Check
    existing_event = db.execute(
        select(StripeEvent).where(StripeEvent.event_id == event.id)
    ).scalar_one_or_none()
    if existing_event:
        return {"status": "ignored", "reason": "already processed"}
    
    # Register event
    db.add(StripeEvent(event_id=event.id, event_type=event_type))
    db.commit()
    
    # --- checkout.session.completed ---
    if event_type == "checkout.session.completed":
        metadata = data.get("metadata", {})
        tenant_id = metadata.get("tenant_id")
        plan_id = metadata.get("plan_id")
        stripe_sub_id = data.get("subscription")
        stripe_customer_id = data.get("customer")
        
        if not tenant_id or not plan_id:
            return {"status": "ignored", "reason": "missing metadata"}
        
        # 1. Update tenant.plan_id (source of truth for features)
        tenant = db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        ).scalar_one_or_none()
        
        if tenant:
            tenant.plan_id = plan_id  # Upgrade/set plan
        
        # 2. Upsert subscription (billing status tracking)
        existing = db.execute(
            select(Subscription).where(Subscription.tenant_id == tenant_id)
        ).scalar_one_or_none()
        
        if existing:
            existing.plan_id = plan_id
            existing.stripe_subscription_id = stripe_sub_id
            existing.stripe_customer_id = stripe_customer_id
            existing.status = "active"
        else:
            sub = Subscription(
                tenant_id=tenant_id,
                plan_id=plan_id,
                stripe_subscription_id=stripe_sub_id,
                stripe_customer_id=stripe_customer_id,
                status="active"
            )
            db.add(sub)
        
        db.commit()
        
        # 3. Update internal binding status
        bound_session = db.execute(
            select(BillingCheckoutSession).where(BillingCheckoutSession.stripe_session_id == data.id)
        ).scalar_one_or_none()
        if bound_session:
            bound_session.status = CheckoutSessionStatus.COMPLETED
            db.commit()

        invalidate_plan_cache(tenant_id)
        
        # [NEW] Trigger Provisioning Async
        from uuid import UUID
        background_tasks.add_task(trigger_provisioning, UUID(tenant_id))
        
        print(f"[STRIPE] ✅ Plan activated and provisioning triggered for tenant {tenant_id}")
    
    # --- customer.subscription.updated ---
    elif event_type == "customer.subscription.updated":
        stripe_sub_id = data.get("id")
        status = data.get("status")  # active, past_due, canceled, etc.
        cancel_at_period_end = data.get("cancel_at_period_end", False)
        
        sub = db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        ).scalar_one_or_none()
        
        if sub:
            sub.status = status
            sub.cancel_at_period_end = cancel_at_period_end
            
            # If plan changed via Stripe (upgrade/downgrade), sync tenant.plan_id
            stripe_plan_items = data.get("items", {}).get("data", [])
            if stripe_plan_items:
                new_stripe_price = stripe_plan_items[0].get("price", {}).get("id")
                if new_stripe_price:
                    # Find matching plan by Stripe price ID
                    new_plan = db.execute(
                        select(Plan).where(
                            (Plan.stripe_price_id_monthly == new_stripe_price) |
                            (Plan.stripe_price_id_yearly == new_stripe_price)
                        )
                    ).scalar_one_or_none()
                    if new_plan and str(sub.plan_id) != str(new_plan.id):
                        sub.plan_id = new_plan.id
                        # Sync tenant.plan_id
                        tenant = db.execute(
                            select(Tenant).where(Tenant.id == sub.tenant_id)
                        ).scalar_one_or_none()
                        if tenant:
                            tenant.plan_id = new_plan.id
            
            # Sync period dates
            if data.get("current_period_start"):
                from datetime import datetime
                sub.current_period_start = datetime.fromtimestamp(data["current_period_start"])
            if data.get("current_period_end"):
                from datetime import datetime
                sub.current_period_end = datetime.fromtimestamp(data["current_period_end"])
            
            db.commit()
            invalidate_plan_cache(sub.tenant_id)
            print(f"[STRIPE] 🔄 Subscription updated: {stripe_sub_id} → {status}")
    
    # --- customer.subscription.deleted ---
    elif event_type == "customer.subscription.deleted":
        stripe_sub_id = data.get("id")
        
        sub = db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        ).scalar_one_or_none()
        
        if sub:
            sub.status = "canceled"
            # NOTE: We do NOT reset tenant.plan_id here.
            # Canceled subscriptions keep features until period_end.
            # Downgrade to Professional should happen via a separate cron/webhook.
            db.commit()
            invalidate_plan_cache(sub.tenant_id)
            print(f"[STRIPE] ❌ Subscription canceled: {stripe_sub_id}")
    
    return {"status": "processed"}

@router.get("/billing-portal")
def billing_portal(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Redirect to Stripe Customer Portal for subscription management.
    """
    sub = db.execute(
        select(Subscription).where(Subscription.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()
    
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    try:
        session = stripe.billing_portal.Session.create(
            customer=sub.stripe_customer_id,
            return_url="http://localhost:3000/billing"
        )
        return {"portal_url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")


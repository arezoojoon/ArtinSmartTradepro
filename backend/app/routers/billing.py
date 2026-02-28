"""
Billing Router — Wallet balance, transactions, and credit management.
This endpoint serves the frontend wallet/dashboard pages.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.billing import Wallet, WalletTransaction, Invoice, BillingCustomer
from app.models.subscription import Subscription, Plan
from app.models.billing_ext import BillingCheckoutSession, ProvisioningStatus, CheckoutSessionStatus, ProvisioningState
from app.middleware.auth import get_current_active_user
from app.services.audit import log_audit_event
from pydantic import BaseModel
from typing import Optional, List
from app.config import get_settings
import datetime
import uuid

_settings = get_settings()
_FRONTEND_URL = getattr(_settings, 'FRONTEND_URL', 'http://localhost:3000')

router = APIRouter()

class CheckoutSessionRequest(BaseModel):
    plan_name: str # professional, enterprise, white_label
    interval: str = "monthly" # monthly, yearly

@router.post("/checkout-session")
async def create_checkout_session(
    data: CheckoutSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe Checkout Session (or Stub).
    """
    # 1. Get Tenant
    tenant_id = current_user.tenant_id
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No active tenant context")
    
    # 2. Get Plan
    plan = db.query(Plan).filter(Plan.name == data.plan_name).first()
    if not plan:
        # Fallback stub plan if not seeded
        plan = Plan(name=data.plan_name, display_name=data.plan_name.title()) 
        # In real app, this should error if plan doesn't exist.
    
    # 3. Create/Get Billing Customer
    customer = db.query(BillingCustomer).filter(BillingCustomer.tenant_id == tenant_id).first()
    if not customer:
        customer = BillingCustomer(
            tenant_id=tenant_id,
            provider="stripe",
            provider_customer_id=f"cus_stub_{uuid.uuid4()}" # Stub
        )
        db.add(customer)
        db.commit()
    
    # 4. Create Session Stub
    session_id = f"cs_stub_{uuid.uuid4()}"
    checkout_url = f"{_FRONTEND_URL}/settings/billing?session_id={session_id}"
    
    log_audit_event(db, "billing.checkout_session_created", user_id=current_user.id, tenant_id=tenant_id, details={"plan": data.plan_name})
    
    return {"url": checkout_url, "session_id": session_id}

@router.get("/checkout-session")
async def verify_checkout_session(
    session_id: str = Query(..., description="Stripe Checkout Session ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    [SECURE] Verify a checkout session and return its provisioning status.
    Strictly checks tenant_id binding.
    """
    # 1. Fetch the bound session
    bound_session = db.execute(
        select(BillingCheckoutSession).where(
            BillingCheckoutSession.stripe_session_id == session_id,
            BillingCheckoutSession.tenant_id == current_user.tenant_id
        )
    ).scalar_one_or_none()
    
    if not bound_session:
        # Cross-tenant check or invalid ID
        raise HTTPException(status_code=403, detail="Unauthorized access to this session or invalid ID")

    # 2. Fetch Subscription Status
    sub = db.execute(
        select(Subscription).where(Subscription.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()
    
    subscription_status = sub.status if sub else "pending"
    
    # 3. Fetch Provisioning Status
    prov = db.execute(
        select(ProvisioningStatus).where(ProvisioningStatus.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()
    
    prov_data = {
        "overall": "pending",
        "waha": "pending",
        "crm": "pending",
        "resources": {}
    }
    
    if prov:
        prov_data = {
            "overall": prov.overall_status,
            "waha": prov.waha_status,
            "crm": prov.crm_status,
            "resources": {
                "waha_session_name": prov.waha_session_name,
                "qr_ref": prov.qr_ref,
                "telegram_deeplink": prov.telegram_deeplink
            },
            "last_error": prov.last_error
        }

    return {
        "session_id": session_id,
        "subscription_status": subscription_status,
        "plan_code": bound_session.plan_code,
        "provisioning": prov_data
    }

@router.get("/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current subscription status.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="No active tenant")
        
    sub = db.query(Subscription).filter(Subscription.tenant_id == current_user.tenant_id).first()
    
    if not sub:
        return {"status": "free", "plan": "Trial", "current_period_end": None}
        
    plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
    
    return {
        "status": sub.status,
        "plan": plan.display_name if plan else "Unknown",
        "current_period_end": sub.current_period_end,
        "cancel_at_period_end": sub.cancel_at_period_end
    }

@router.get("/invoices")
async def get_invoices(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if not current_user.tenant_id:
         raise HTTPException(status_code=400, detail="No active tenant")
         
    invoices = db.query(Invoice).filter(Invoice.tenant_id == current_user.tenant_id).order_by(desc(Invoice.created_at)).all()
    return invoices

@router.post("/webhook")
async def billing_webhook(request: Request):
    """
    Handle Stripe Webhooks (Stub).
    """
    # body = await request.body()
    # In real implementation: verify signature
    return {"status": "success"}





@router.get("/wallet")
async def get_wallet(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get wallet balance and recent transactions.
    Used by: /dashboard (stats), /wallet (full page).
    """
    wallet = db.execute(
        select(Wallet).where(Wallet.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()

    if not wallet:
        return {"balance": 0.0, "currency": "AED", "transactions": []}

    transactions = db.execute(
        select(WalletTransaction)
        .where(WalletTransaction.wallet_id == wallet.id)
        .order_by(desc(WalletTransaction.created_at))
        .limit(50)
    ).scalars().all()

    return {
        "balance": float(wallet.balance),
        "currency": getattr(wallet, "currency", "AED"),
        "transactions": [
            {
                "id": str(tx.id),
                "amount": float(tx.amount),
                "type": tx.type,
                "description": tx.description,
                "status": getattr(tx, "status", "completed"),
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            }
            for tx in transactions
        ],
    }


@router.get("/transactions")
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    tx_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List wallet transactions with pagination and optional type filter.
    Types: credit, debit
    """
    wallet = db.execute(
        select(Wallet).where(Wallet.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()

    if not wallet:
        return {"total": 0, "transactions": []}

    query = select(WalletTransaction).where(
        WalletTransaction.wallet_id == wallet.id
    )
    if tx_type:
        query = query.where(WalletTransaction.type == tx_type)

    # Count
    from sqlalchemy import func
    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total = db.execute(count_query).scalar() or 0

    # Fetch
    transactions = db.execute(
        query.order_by(desc(WalletTransaction.created_at))
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    return {
        "total": total,
        "transactions": [
            {
                "id": str(tx.id),
                "amount": float(tx.amount),
                "type": tx.type,
                "description": tx.description,
                "status": getattr(tx, "status", "completed"),
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            }
            for tx in transactions
        ],
    }

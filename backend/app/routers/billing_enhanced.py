"""
Enhanced Billing Router with Real Stripe Integration
Phase 6 Enhancement - Complete billing with subscription management and usage tracking
"""
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.phase6 import SysPlan, TenantSubscription, UsageCounter
from app.models.billing import Wallet, Invoice, BillingCustomer, WalletTransaction
from app.middleware.auth import get_current_active_user
import stripe

router = APIRouter()


# Pydantic Models
class WalletResponse(BaseModel):
    id: str
    balance: float
    currency: str
    credit_limit: Optional[float]
    available_credit: float
    last_transaction_at: Optional[str]
    created_at: str
    updated_at: str


class SubscriptionResponse(BaseModel):
    id: str
    plan_id: str
    plan_name: str
    plan_code: str
    status: str
    current_period_start: str
    current_period_end: Optional[str]
    monthly_price: float
    features: Dict[str, Any]
    limits: Dict[str, Any]
    usage: Dict[str, Any]
    created_at: str
    updated_at: str


class UsageResponse(BaseModel):
    metric: str
    current_value: int
    limit_value: Optional[int]
    percentage_used: float
    period_key: str
    reset_date: Optional[str]


class TransactionResponse(BaseModel):
    id: str
    type: str
    amount: float
    currency: str
    description: str
    status: str
    stripe_transaction_id: Optional[str]
    created_at: str


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    amount: float
    currency: str
    status: str
    due_date: str
    paid_at: Optional[str]
    stripe_invoice_id: Optional[str]
    created_at: str


@router.get("/wallet", response_model=WalletResponse, summary="Get Wallet Information")
def get_wallet(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WalletResponse:
    """
    Get current wallet information
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get or create wallet
    wallet = db.query(Wallet).filter(Wallet.tenant_id == tenant_id).first()
    
    if not wallet:
        # Create wallet with default balance
        wallet = Wallet(
            tenant_id=tenant_id,
            balance=0.0,
            currency="USD",
            credit_limit=10000.0,  # Default credit limit
            created_by=current_user.id
        )
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    # Get last transaction
    last_transaction = db.query(WalletTransaction).filter(
        WalletTransaction.tenant_id == tenant_id
    ).order_by(WalletTransaction.created_at.desc()).first()
    
    return WalletResponse(
        id=str(wallet.id),
        balance=float(wallet.balance),
        currency=wallet.currency,
        credit_limit=float(wallet.credit_limit) if wallet.credit_limit else None,
        available_credit=float(wallet.credit_limit - wallet.balance) if wallet.credit_limit else 0,
        last_transaction_at=last_transaction.created_at.isoformat() if last_transaction else None,
        created_at=wallet.created_at.isoformat(),
        updated_at=wallet.updated_at.isoformat()
    )


@router.get("/subscription", response_model=SubscriptionResponse, summary="Get Current Subscription")
def get_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SubscriptionResponse:
    """
    Get current subscription information
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get tenant's subscription
    subscription = db.query(TenantSubscription).filter(
        TenantSubscription.tenant_id == tenant_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    # Get plan details
    plan = db.query(SysPlan).filter(SysPlan.id == subscription.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Get current usage
    current_period = datetime.utcnow().strftime("%Y-%m")
    usage_counters = db.query(UsageCounter).filter(
        UsageCounter.tenant_id == tenant_id,
        UsageCounter.period_key == current_period
    ).all()
    
    usage = {}
    for counter in usage_counters:
        usage[counter.metric] = {
            "current": counter.value,
            "limit": plan.limits.get(counter.metric, 0) if plan.limits else 0
        }
    
    return SubscriptionResponse(
        id=str(subscription.id),
        plan_id=str(subscription.plan_id),
        plan_name=plan.name,
        plan_code=plan.code,
        status=subscription.status,
        current_period_start=subscription.current_period_start.isoformat(),
        current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        monthly_price=float(plan.monthly_price_usd) if plan.monthly_price_usd else 0,
        features=plan.features or {},
        limits=plan.limits or {},
        usage=usage,
        created_at=subscription.created_at.isoformat(),
        updated_at=subscription.updated_at.isoformat()
    )


@router.get("/usage", response_model=List[UsageResponse], summary="Get Current Usage")
def get_usage(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[UsageResponse]:
    """
    Get current usage metrics
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get subscription for limits
    subscription = db.query(TenantSubscription).filter(
        TenantSubscription.tenant_id == tenant_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    plan = db.query(SysPlan).filter(SysPlan.id == subscription.plan_id).first()
    limits = plan.limits or {}
    
    # Get current usage
    current_period = datetime.utcnow().strftime("%Y-%m")
    usage_counters = db.query(UsageCounter).filter(
        UsageCounter.tenant_id == tenant_id,
        UsageCounter.period_key == current_period
    ).all()
    
    usage_responses = []
    for counter in usage_counters:
        limit_value = limits.get(counter.metric, 0)
        percentage_used = (counter.value / limit_value * 100) if limit_value > 0 else 0
        
        # Calculate reset date (next month)
        next_month = datetime.utcnow().replace(day=1) + timedelta(days=32)
        next_month = next_month.replace(day=1)
        reset_date = next_month.strftime("%Y-%m-%d")
        
        usage_responses.append(UsageResponse(
            metric=counter.metric,
            current_value=counter.value,
            limit_value=limit_value,
            percentage_used=percentage_used,
            period_key=counter.period_key,
            reset_date=reset_date
        ))
    
    return usage_responses


@router.post("/wallet/top-up", summary="Top Up Wallet")
def top_up_wallet(
    amount: float,
    payment_method_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Top up wallet balance
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    # Get wallet
    wallet = db.query(Wallet).filter(Wallet.tenant_id == tenant_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    # Create payment intent with Stripe
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency="usd",
            payment_method=payment_method_id,
            metadata={
                "tenant_id": str(tenant_id),
                "user_id": str(current_user.id)
            }
        )
        
        # Create transaction record
        transaction = WalletTransaction(
            tenant_id=tenant_id,
            type="top_up",
            amount=amount,
            currency="USD",
            description=f"Wallet top-up of ${amount}",
            status="pending",
            stripe_transaction_id=intent.id,
            created_by=current_user.id
        )
        
        db.add(transaction)
        db.commit()
        
        return {
            "client_secret": intent.client_secret,
            "transaction_id": str(transaction.id),
            "amount": amount,
            "currency": "USD"
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")


@router.post("/wallet/withdraw", summary="Withdraw from Wallet")
def withdraw_wallet(
    amount: float,
    bank_account_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Withdraw from wallet balance
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    # Get wallet
    wallet = db.query(Wallet).filter(Wallet.tenant_id == tenant_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    if wallet.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Create transaction record
    transaction = WalletTransaction(
        tenant_id=tenant_id,
        type="withdraw",
        amount=amount,
        currency="USD",
        description=f"Wallet withdrawal of ${amount}",
        status="completed",
        created_by=current_user.id
    )
    
    # Update wallet balance
    wallet.balance -= amount
    wallet.updated_at = datetime.utcnow()
    
    db.add(transaction)
    db.commit()
    
    return {
        "transaction_id": str(transaction.id),
        "amount": amount,
        "currency": "USD",
        "new_balance": float(wallet.balance)
    }


@router.get("/transactions", response_model=List[TransactionResponse], summary="Get Transaction History")
def get_transactions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    transaction_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[TransactionResponse]:
    """
    Get transaction history
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    query = db.query(WalletTransaction).filter(WalletTransaction.tenant_id == tenant_id)
    
    if transaction_type:
        query = query.filter(WalletTransaction.type == transaction_type)
    
    transactions = query.order_by(WalletTransaction.created_at.desc()).offset(offset).limit(limit).all()
    
    transaction_responses = []
    for transaction in transactions:
        transaction_responses.append(TransactionResponse(
            id=str(transaction.id),
            type=transaction.type,
            amount=float(transaction.amount),
            currency=transaction.currency,
            description=transaction.description,
            status=transaction.status,
            stripe_transaction_id=transaction.stripe_transaction_id,
            created_at=transaction.created_at.isoformat()
        ))
    
    return transaction_responses


@router.get("/invoices", response_model=List[InvoiceResponse], summary="Get Invoice History")
def get_invoices(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[InvoiceResponse]:
    """
    Get invoice history
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    query = db.query(Invoice).filter(Invoice.tenant_id == tenant_id)
    
    if status:
        query = query.filter(Invoice.status == status)
    
    invoices = query.order_by(Invoice.created_at.desc()).offset(offset).limit(limit).all()
    
    invoice_responses = []
    for invoice in invoices:
        invoice_responses.append(InvoiceResponse(
            id=str(invoice.id),
            invoice_number=invoice.invoice_number,
            amount=float(invoice.amount),
            currency=invoice.currency,
            status=invoice.status,
            due_date=invoice.due_date.isoformat() if invoice.due_date else None,
            paid_at=invoice.paid_at.isoformat() if invoice.paid_at else None,
            stripe_invoice_id=invoice.stripe_invoice_id,
            created_at=invoice.created_at.isoformat()
        ))
    
    return invoice_responses


@router.post("/subscription/upgrade", summary="Upgrade Subscription")
def upgrade_subscription(
    plan_code: str,
    payment_method_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Upgrade subscription to a higher plan
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get target plan
    target_plan = db.query(SysPlan).filter(
        SysPlan.code == plan_code,
        SysPlan.is_active == True
    ).first()
    
    if not target_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Get current subscription
    current_subscription = db.query(TenantSubscription).filter(
        TenantSubscription.tenant_id == tenant_id
    ).first()
    
    if not current_subscription:
        raise HTTPException(status_code=404, detail="No current subscription")
    
    # Create Stripe subscription
    try:
        stripe_subscription = stripe.Subscription.create(
            customer=current_subscription.stripe_customer_id,
            items=[{
                "price": target_plan.stripe_price_id,
                "quantity": 1,
            }],
            metadata={
                "tenant_id": str(tenant_id),
                "plan_code": plan_code
            }
        )
        
        # Update subscription
        current_subscription.plan_id = target_plan.id
        current_subscription.status = "active"
        current_subscription.stripe_subscription_id = stripe_subscription.id
        current_subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
        current_subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
        current_subscription.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "subscription_id": str(current_subscription.id),
            "plan_code": plan_code,
            "plan_name": target_plan.name,
            "monthly_price": float(target_plan.monthly_price_usd) if target_plan.monthly_price_usd else 0,
            "stripe_subscription_id": stripe_subscription.id
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")


@router.post("/subscription/cancel", summary="Cancel Subscription")
def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Cancel subscription
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get current subscription
    subscription = db.query(TenantSubscription).filter(
        TenantSubscription.tenant_id == tenant_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription")
    
    # Cancel Stripe subscription
    if subscription.stripe_subscription_id:
        try:
            stripe.Subscription.delete(subscription.stripe_subscription_id)
        except stripe.error.StripeError as e:
            # Log error but continue with local cancellation
            print(f"Stripe cancellation error: {e}")
    
    # Update subscription status
    subscription.status = "canceled"
    subscription.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "subscription_id": str(subscription.id),
        "status": "canceled",
        "canceled_at": datetime.utcnow().isoformat()
    }


@router.get("/billing-overview", summary="Get Billing Overview")
def get_billing_overview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get comprehensive billing overview
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get wallet
    wallet = db.query(Wallet).filter(Wallet.tenant_id == tenant_id).first()
    
    # Get subscription
    subscription = db.query(TenantSubscription).filter(
        TenantSubscription.tenant_id == tenant_id
    ).first()
    
    # Get plan
    plan = None
    if subscription:
        plan = db.query(SysPlan).filter(SysPlan.id == subscription.plan_id).first()
    
    # Get current month usage
    current_period = datetime.utcnow().strftime("%Y-%m")
    usage_counters = db.query(UsageCounter).filter(
        UsageCounter.tenant_id == tenant_id,
        UsageCounter.period_key == current_period
    ).all()
    
    # Get recent transactions
    recent_transactions = db.query(WalletTransaction).filter(
        WalletTransaction.tenant_id == tenant_id
    ).order_by(WalletTransaction.created_at.desc()).limit(5).all()
    
    # Get unpaid invoices
    unpaid_invoices = db.query(Invoice).filter(
        Invoice.tenant_id == tenant_id,
        Invoice.status == "unpaid"
    ).order_by(Invoice.due_date.asc()).all()
    
    return {
        "wallet": {
            "balance": float(wallet.balance) if wallet else 0,
            "currency": wallet.currency if wallet else "USD",
            "credit_limit": float(wallet.credit_limit) if wallet and wallet.credit_limit else 0
        },
        "subscription": {
            "plan_name": plan.name if plan else None,
            "plan_code": plan.code if plan else None,
            "status": subscription.status if subscription else None,
            "monthly_price": float(plan.monthly_price_usd) if plan and plan.monthly_price_usd else 0,
            "features": plan.features if plan else {},
            "limits": plan.limits if plan else {}
        } if subscription else None,
        "usage": {
            counter.metric: counter.value
            for counter in usage_counters
        },
        "recent_transactions": [
            {
                "id": str(t.id),
                "type": t.type,
                "amount": float(t.amount),
                "description": t.description,
                "status": t.status,
                "created_at": t.created_at.isoformat()
            }
            for t in recent_transactions
        ],
        "unpaid_invoices": [
            {
                "id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "amount": float(inv.amount),
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
                "created_at": inv.created_at.isoformat()
            }
            for inv in unpaid_invoices
        ]
    }

"""
Super Admin Router — Platform-level management.
Only accessible by users with is_superuser=True.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant, TenantMembership
from app.models.billing import Wallet
from app.models.subscription import Subscription, Plan, PlanFeature
from app.middleware.auth import get_current_superuser
from app.middleware.plan_gate import invalidate_plan_cache
from app.constants import DEFAULT_PLAN_FEATURES
from pydantic import BaseModel
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────

class TenantInfo(BaseModel):
    id: UUID
    name: str
    slug: str
    plan: str
    mode: str
    is_active: bool
    balance: Optional[float] = None
    user_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TenantToggleRequest(BaseModel):
    tenant_id: UUID
    is_active: bool

class TenantPlanChangeRequest(BaseModel):
    tenant_id: UUID
    plan: str  # "professional", "enterprise", "whitelabel"

class UserInfo(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    is_superuser: bool = False
    tenant_name: Optional[str] = None
    membership_role: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PlanInfo(BaseModel):
    id: UUID
    name: str
    display_name: str
    price_monthly: Optional[float] = None
    currency: str = "USD"
    is_active: bool = True
    feature_count: int = 0
    features: List[str] = []

class PlatformStats(BaseModel):
    total_tenants: int
    active_tenants: int
    total_users: int
    active_users: int
    total_revenue: float
    plans_breakdown: dict


# ─── Platform Stats ──────────────────────────────────

@router.get("/stats", response_model=PlatformStats)
def admin_stats(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Global platform statistics for super admin dashboard."""
    total_tenants = db.query(Tenant).count()
    active_tenants = db.query(Tenant).filter(Tenant.is_active == True).count()
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # Calculate total wallet balance across all tenants
    total_balance = db.query(func.coalesce(func.sum(Wallet.balance), 0)).scalar()

    # Plans breakdown
    plans_breakdown = {}
    for plan_name in ["professional", "enterprise", "whitelabel"]:
        count = db.query(Tenant).filter(Tenant.plan == plan_name).count()
        plans_breakdown[plan_name] = count
    
    return PlatformStats(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        total_users=total_users,
        active_users=active_users,
        total_revenue=float(total_balance),
        plans_breakdown=plans_breakdown
    )


# ─── Tenant Management ──────────────────────────────

@router.get("/tenants", response_model=List[TenantInfo])
def list_tenants(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """List all tenants with wallet balance and member count."""
    tenants = db.query(Tenant).order_by(Tenant.created_at.desc()).all()
    result = []
    for t in tenants:
        wallet = db.query(Wallet).filter(Wallet.tenant_id == t.id).first()
        user_count = db.query(TenantMembership).filter(TenantMembership.tenant_id == t.id).count()
        result.append(TenantInfo(
            id=t.id,
            name=t.name,
            slug=t.slug,
            plan=t.plan or "professional",
            mode=t.mode or "hybrid",
            is_active=t.is_active,
            balance=float(wallet.balance) if wallet else 0.0,
            user_count=user_count,
            created_at=t.created_at
        ))
    return result


@router.post("/tenants/toggle")
def toggle_tenant(
    body: TenantToggleRequest,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """KILL SWITCH: Enable/disable a tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == body.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    tenant.is_active = body.is_active
    db.commit()
    
    action = "enabled" if body.is_active else "DISABLED"
    return {"detail": f"Tenant '{tenant.name}' has been {action}"}


@router.post("/tenants/change-plan")
def change_tenant_plan(
    body: TenantPlanChangeRequest,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Change a tenant's plan and update their features."""
    valid_plans = ["professional", "enterprise", "whitelabel"]
    if body.plan not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Must be one of: {valid_plans}")
    
    tenant = db.query(Tenant).filter(Tenant.id == body.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    old_plan = tenant.plan
    tenant.plan = body.plan
    
    # Update subscription plan_id if exists
    plan_record = db.query(Plan).filter(Plan.name == body.plan).first()
    if plan_record:
        sub = db.query(Subscription).filter(Subscription.tenant_id == tenant.id).first()
        if sub:
            sub.plan_id = plan_record.id
            sub.status = "active"
    
    # Invalidate feature cache
    invalidate_plan_cache(tenant.id)
    
    db.commit()
    return {
        "detail": f"Tenant '{tenant.name}' plan changed from '{old_plan}' to '{body.plan}'",
        "tenant_id": str(tenant.id)
    }


# ─── User Management ────────────────────────────────

@router.get("/users", response_model=List[UserInfo])
def list_users(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """List all users with their tenant membership info."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        # Get primary membership
        membership = db.query(TenantMembership).filter(
            TenantMembership.user_id == u.id
        ).first()
        
        tenant_name = None
        membership_role = None
        if membership:
            tenant = db.query(Tenant).filter(Tenant.id == membership.tenant_id).first()
            tenant_name = tenant.name if tenant else None
            membership_role = membership.role
        
        result.append(UserInfo(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role or "user",
            is_active=u.is_active,
            is_superuser=u.is_superuser,
            tenant_name=tenant_name,
            membership_role=membership_role,
            created_at=u.created_at
        ))
    return result


@router.post("/users/{user_id}/toggle")
def toggle_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Enable/disable a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    db.commit()
    
    action = "enabled" if user.is_active else "disabled"
    return {"detail": f"User '{user.email}' has been {action}"}


# ─── Plan Management ────────────────────────────────

@router.get("/plans", response_model=List[PlanInfo])
def list_plans(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """List all plans with their features."""
    plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.price_monthly).all()
    result = []
    for p in plans:
        features = db.query(PlanFeature.feature_key).filter(
            PlanFeature.plan_id == p.id
        ).all()
        feature_list = [f[0] for f in features]
        
        # Fallback to constants if no DB features
        if not feature_list:
            feature_list = DEFAULT_PLAN_FEATURES.get(p.name, [])
        
        result.append(PlanInfo(
            id=p.id,
            name=p.name,
            display_name=p.display_name or p.name.capitalize(),
            price_monthly=float(p.price_monthly) if p.price_monthly else None,
            currency=p.currency or "USD",
            is_active=p.is_active,
            feature_count=len(feature_list),
            features=feature_list
        ))
    return result


@router.post("/plans/seed-features")
def seed_plan_features(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Seed PlanFeature records from DEFAULT_PLAN_FEATURES for all plans."""
    results = {}
    for plan_name, features in DEFAULT_PLAN_FEATURES.items():
        plan = db.query(Plan).filter(Plan.name == plan_name).first()
        if not plan:
            # Create the plan record
            plan_prices = {"professional": 299, "enterprise": 999, "white_label": 2999}
            plan = Plan(
                name=plan_name,
                display_name=plan_name.replace("_", " ").title(),
                price_monthly=plan_prices.get(plan_name, 0),
                currency="USD",
                is_active=True
            )
            db.add(plan)
            db.flush()
        
        # Clear existing features and re-seed
        db.query(PlanFeature).filter(PlanFeature.plan_id == plan.id).delete()
        for fk in features:
            db.add(PlanFeature(plan_id=plan.id, feature_key=fk))
        
        results[plan_name] = len(features)
    
    # Invalidate all caches
    from app.middleware.plan_gate import _plan_cache
    _plan_cache.clear()
    
    db.commit()
    return {"detail": "Plan features seeded successfully", "plans": results}

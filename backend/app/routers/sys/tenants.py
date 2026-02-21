"""
/sys/tenants — CRUD, suspend/restore, impersonation, users, subscription, usage.
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.phase6 import SystemAdmin, SysPlan, TenantSubscription, UsageCounter, WhitelabelConfig
from app.models.tenant import Tenant, TenantMembership
from app.models.user import User
from app.services.sys_admin_auth import get_current_sys_admin, create_impersonation_token, write_sys_audit

router = APIRouter()


def _tenant_snapshot(t: Tenant) -> dict:
    return {"id": str(t.id), "name": t.name, "is_active": t.is_active, "slug": getattr(t, "slug", None)}


@router.get("", summary="List Tenants")
def list_tenants(
    q: Optional[str] = Query(None, description="Search by name"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Tenant)
    if q:
        query = query.filter(Tenant.name.ilike(f"%{q}%"))
    total = query.count()
    tenants = query.order_by(Tenant.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": str(t.id),
                "name": t.name,
                "is_active": t.is_active,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tenants
        ],
    }


@router.get("/{tenant_id}", summary="Get Tenant Detail")
def get_tenant(
    tenant_id: UUID,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    sub = db.query(TenantSubscription).filter(TenantSubscription.tenant_id == tenant_id).first()
    plan = None
    if sub:
        p = db.query(SysPlan).filter(SysPlan.id == sub.plan_id).first()
        plan = {"code": p.code, "name": p.name} if p else None

    wl = db.query(WhitelabelConfig).filter(WhitelabelConfig.tenant_id == tenant_id).first()

    # Usage summary
    usage_rows = db.query(UsageCounter).filter(UsageCounter.tenant_id == tenant_id).all()
    usage = {f"{r.period_key}:{r.metric}": r.value for r in usage_rows}

    user_count = db.query(TenantMembership).filter(TenantMembership.tenant_id == tenant_id).count()

    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "is_active": tenant.is_active,
        "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
        "subscription": {
            "status": sub.status if sub else None,
            "plan": plan,
            "period_start": sub.current_period_start.isoformat() if sub and sub.current_period_start else None,
        } if sub else None,
        "whitelabel": {"is_enabled": wl.is_enabled, "brand_name": wl.brand_name} if wl else None,
        "usage_summary": usage,
        "user_count": user_count,
    }


@router.post("/{tenant_id}/suspend", summary="Suspend Tenant")
def suspend_tenant(
    tenant_id: UUID,
    request: Request,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    before = _tenant_snapshot(tenant)
    tenant.is_active = False
    db.commit()

    write_sys_audit(db, action="tenant_suspend", resource_type="tenant",
                    actor_sys_admin_id=admin.id, tenant_id=tenant_id,
                    resource_id=str(tenant_id), before_state=before,
                    after_state=_tenant_snapshot(tenant),
                    ip_address=request.client.host if request.client else None)
    return {"status": "suspended", "tenant_id": str(tenant_id)}


@router.post("/{tenant_id}/restore", summary="Restore Tenant")
def restore_tenant(
    tenant_id: UUID,
    request: Request,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    before = _tenant_snapshot(tenant)
    tenant.is_active = True
    db.commit()

    write_sys_audit(db, action="tenant_restore", resource_type="tenant",
                    actor_sys_admin_id=admin.id, tenant_id=tenant_id,
                    resource_id=str(tenant_id), before_state=before,
                    after_state=_tenant_snapshot(tenant),
                    ip_address=request.client.host if request.client else None)
    return {"status": "restored", "tenant_id": str(tenant_id)}


@router.get("/{tenant_id}/users", summary="List Tenant Users")
def list_tenant_users(
    tenant_id: UUID,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(TenantMembership, User)
        .join(User, TenantMembership.user_id == User.id)
        .filter(TenantMembership.tenant_id == tenant_id)
        .all()
    )
    return [
        {
            "user_id": str(u.id),
            "email": u.email,
            "name": getattr(u, "full_name", None) or getattr(u, "name", None),
            "role": m.role,
            "is_active": u.is_active,
        }
        for m, u in rows
    ]


@router.post("/{tenant_id}/impersonate", summary="Impersonate Tenant (Support Mode)")
def impersonate_tenant(
    tenant_id: UUID,
    request: Request,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    token = create_impersonation_token(admin.id, tenant_id)

    write_sys_audit(
        db, action="tenant_impersonate", resource_type="tenant",
        actor_sys_admin_id=admin.id, tenant_id=tenant_id,
        resource_id=str(tenant_id),
        metadata={"sys_admin_id": str(admin.id), "operation": "impersonate",
                   "expires_in_minutes": 15},
        ip_address=request.client.host if request.client else None,
    )
    return {
        "impersonation_token": token,
        "token_type": "bearer",
        "expires_in_minutes": 15,
        "tenant_id": str(tenant_id),
        "warning": "This token is audited and expires in 15 minutes.",
    }


class SetSubscriptionRequest(BaseModel):
    plan_code: str
    status: str = "active"


@router.post("/{tenant_id}/subscription", summary="Set Tenant Subscription")
def set_subscription(
    tenant_id: UUID,
    body: SetSubscriptionRequest,
    request: Request,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
):
    from datetime import datetime
    plan = db.query(SysPlan).filter(SysPlan.code == body.plan_code).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan '{body.plan_code}' not found")

    sub = db.query(TenantSubscription).filter(TenantSubscription.tenant_id == tenant_id).first()
    before = {"plan": None, "status": None}
    if sub:
        before = {"plan": str(sub.plan_id), "status": sub.status}
        sub.plan_id = plan.id
        sub.status = body.status
        sub.current_period_start = datetime.utcnow()
    else:
        sub = TenantSubscription(
            tenant_id=tenant_id,
            plan_id=plan.id,
            status=body.status,
        )
        db.add(sub)

    db.commit()
    write_sys_audit(db, action="subscription_update", resource_type="subscription",
                    actor_sys_admin_id=admin.id, tenant_id=tenant_id,
                    resource_id=str(sub.id),
                    before_state=before,
                    after_state={"plan": plan.code, "status": body.status})
    return {"tenant_id": str(tenant_id), "plan": plan.code, "status": body.status}


@router.get("/{tenant_id}/usage", summary="Get Tenant Usage Counters")
def get_tenant_usage(
    tenant_id: UUID,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
):
    rows = db.query(UsageCounter).filter(UsageCounter.tenant_id == tenant_id).all()
    return {
        "tenant_id": str(tenant_id),
        "counters": [
            {"period": r.period_key, "metric": r.metric, "value": r.value}
            for r in rows
        ],
    }

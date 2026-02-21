"""
Tenant billing — plan and usage info for the current tenant.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.services.entitlement import get_tenant_plan, get_current_usage

router = APIRouter()


def _require_tenant(current_user: User) -> UUID:
    tenant_id = getattr(current_user, "current_tenant_id", None) or getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")
    return tenant_id


@router.get("/plan", summary="Get Current Plan")
def get_plan(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    tenant_id = _require_tenant(current_user)
    plan = get_tenant_plan(db, tenant_id)
    if not plan:
        return {"plan": None, "message": "No active subscription"}
    return plan


@router.get("/usage", summary="Get Current Usage")
def get_usage(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    tenant_id = _require_tenant(current_user)
    plan = get_tenant_plan(db, tenant_id)
    limits = plan.get("limits", {}) if plan else {}

    from app.models.phase6 import UsageCounter
    rows = db.query(UsageCounter).filter(UsageCounter.tenant_id == tenant_id).all()

    counters = []
    for r in rows:
        metric = r.metric
        period = r.period_key
        limit_key = f"{metric}_daily" if "-" in period and len(period) == 10 else f"{metric}_monthly"
        limit_val = limits.get(limit_key, -1)
        counters.append({
            "metric": metric,
            "period": period,
            "value": r.value,
            "limit": limit_val,
            "pct_used": round(r.value / limit_val * 100, 1) if limit_val and limit_val > 0 else None,
        })

    return {
        "tenant_id": str(tenant_id),
        "plan": plan.get("name") if plan else None,
        "counters": counters,
    }

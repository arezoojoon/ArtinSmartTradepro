"""
Phase 6 — Entitlement Service
Deterministic quota enforcement for plans and usage counters.
"""
from datetime import datetime, date
from typing import Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.phase6 import SysPlan, TenantSubscription, UsageCounter


# ─── Period helpers ───────────────────────────────────────────────────────────

def _monthly_key() -> str:
    """Returns 'YYYY-MM' for today."""
    return datetime.utcnow().strftime("%Y-%m")


def _daily_key() -> str:
    """Returns 'YYYY-MM-DD' for today."""
    return datetime.utcnow().strftime("%Y-%m-%d")


# Metrics that reset daily vs monthly
_DAILY_METRICS = {"messages_sent", "brain_runs", "data_refresh"}
_MONTHLY_METRICS = {"leads_created", "enrich_jobs", "seats"}


def _period_key(metric: str) -> str:
    if metric in _DAILY_METRICS:
        return _daily_key()
    return _monthly_key()


# ─── Core service ─────────────────────────────────────────────────────────────

def get_tenant_plan(db: Session, tenant_id: UUID) -> Optional[dict]:
    """
    Returns the current plan dict {'limits': {...}, 'features': {...}} for a tenant,
    or None if no subscription exists (no limits enforced for unsubscribed tenants IN DEV).
    """
    sub = (
        db.query(TenantSubscription)
        .filter(
            TenantSubscription.tenant_id == tenant_id,
            TenantSubscription.status == "active",
        )
        .first()
    )
    if not sub:
        return None

    plan = db.query(SysPlan).filter(SysPlan.id == sub.plan_id).first()
    if not plan:
        return None

    return {
        "id": str(plan.id),
        "code": plan.code,
        "name": plan.name,
        "features": plan.features or {},
        "limits": plan.limits or {},
    }


def get_current_usage(db: Session, tenant_id: UUID, metric: str) -> int:
    """Returns current usage value for (tenant, metric, current period)."""
    period = _period_key(metric)
    row = (
        db.query(UsageCounter)
        .filter(
            UsageCounter.tenant_id == tenant_id,
            UsageCounter.period_key == period,
            UsageCounter.metric == metric,
        )
        .first()
    )
    return row.value if row else 0


def check_limit(db: Session, tenant_id: UUID, metric: str, increment: int = 1) -> None:
    """
    Raises HTTP 429 if the tenant has exhausted their plan quota for `metric`.
    This is deterministic: no "best effort" — if over limit, request is denied.
    """
    plan = get_tenant_plan(db, tenant_id)
    if plan is None:
        # No subscription / no plan → allow in development, block in production
        import os
        if os.getenv("ENVIRONMENT", "development") == "production":
            raise HTTPException(
                status_code=402,
                detail="No active subscription. Please contact support.",
            )
        return  # Dev: allow everything

    limits = plan.get("limits", {})

    # Determine the limit key based on metric
    # Limit keys: "messages_sent_daily", "leads_created_monthly", etc.
    period_type = "daily" if metric in _DAILY_METRICS else "monthly"
    limit_key = f"{metric}_{period_type}"

    if limit_key not in limits:
        return  # This metric has no limit configured → allow

    limit_value = limits[limit_key]
    if limit_value == -1:
        return  # -1 means unlimited

    current = get_current_usage(db, tenant_id, metric)
    if current + increment > limit_value:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "QUOTA_EXCEEDED",
                "metric": metric,
                "current": current,
                "limit": limit_value,
                "period": _period_key(metric),
                "message": f"Plan limit reached: {metric} ({current}/{limit_value}). Upgrade your plan to continue.",
            },
        )


def increment_usage(db: Session, tenant_id: UUID, metric: str, n: int = 1) -> int:
    """
    Atomically increments usage counter for (tenant, metric, current period).
    Returns the new value.
    Uses PostgreSQL upsert for race-condition safety.
    """
    period = _period_key(metric)

    stmt = pg_insert(UsageCounter.__table__).values(
        id=__import__("uuid").uuid4(),
        tenant_id=tenant_id,
        period_key=period,
        metric=metric,
        value=n,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ).on_conflict_do_update(
        constraint="uq_usage_counters_period",
        set_={
            "value": UsageCounter.__table__.c.value + n,
            "updated_at": datetime.utcnow(),
        },
    ).returning(UsageCounter.__table__.c.value)

    result = db.execute(stmt)
    db.commit()
    row = result.fetchone()
    return row[0] if row else n


def check_and_increment(db: Session, tenant_id: UUID, metric: str, n: int = 1) -> None:
    """
    Convenience: check limit then increment atomically.
    Call this before performing the metered action.
    """
    check_limit(db, tenant_id, metric, n)
    increment_usage(db, tenant_id, metric, n)


def has_feature(db: Session, tenant_id: UUID, feature: str) -> bool:
    """Returns True if tenant's plan has the given feature flag set to True."""
    plan = get_tenant_plan(db, tenant_id)
    if not plan:
        return False
    return bool(plan.get("features", {}).get(feature, False))


def require_feature(db: Session, tenant_id: UUID, feature: str) -> None:
    """Raises 403 if tenant's plan does not include the feature."""
    if not has_feature(db, tenant_id, feature):
        raise HTTPException(
            status_code=403,
            detail=f"This feature ('{feature}') is not included in your current plan. Please upgrade.",
        )

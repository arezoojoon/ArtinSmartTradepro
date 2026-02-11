"""
Plan Gate Middleware — Backend Feature Enforcement.

Architecture:
  - Plan (tenant.plan_id) → controls which features are available
  - Subscription → controls billing status (active, past_due, etc.)
  - These are SEPARATE concepts

Every paid feature endpoint MUST use @require_feature(Feature.X).
Features are loaded from DB via tenant.plan_id, cached per tenant.
"""
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.subscription import PlanFeature
from app.middleware.auth import get_current_active_user
from uuid import UUID
import functools
from typing import Set, Dict
import time

# In-memory cache: tenant_id -> (features_set, expiry_timestamp)
_plan_cache: Dict[str, tuple] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

def _get_tenant_features(db: Session, tenant_id: UUID) -> Set[str]:
    """
    Load features from DB using tenant.plan_id (NOT subscription).
    Plan = features. Subscription = billing. They are separate.
    """
    cache_key = str(tenant_id)
    now = time.time()
    
    # Check cache first
    if cache_key in _plan_cache:
        features, expiry = _plan_cache[cache_key]
        if now < expiry:
            return features
    
    # Cache miss — get plan_id from tenant
    tenant = db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    ).scalar_one_or_none()
    
    if not tenant or not tenant.plan_id:
        features = set()  # No plan = no features
    else:
        plan_features = db.execute(
            select(PlanFeature.feature_key)
            .where(PlanFeature.plan_id == tenant.plan_id)
        ).scalars().all()
        features = set(plan_features)
    
    # Write to cache
    _plan_cache[cache_key] = (features, now + CACHE_TTL_SECONDS)
    return features

def invalidate_plan_cache(tenant_id):
    """Call this when a plan changes (webhook, admin action, upgrade)."""
    cache_key = str(tenant_id)
    _plan_cache.pop(cache_key, None)

def require_feature(feature: str):
    """
    Decorator: Rejects request with 403 if tenant's plan lacks the feature.
    
    Reads from tenant.plan_id → plan_features table.
    Does NOT depend on subscription status.
    
    Usage:
        @router.post("/analyze")
        @require_feature(Feature.TRADE_INTELLIGENCE)
        async def analyze(...):
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            db: Session = kwargs.get("db")
            current_user: User = kwargs.get("current_user")
            
            if not db or not current_user:
                raise HTTPException(status_code=500, detail="Plan gate configuration error")
            
            if not current_user.tenant_id:
                raise HTTPException(status_code=403, detail="No organization associated")
            
            features = _get_tenant_features(db, current_user.tenant_id)
            
            # Wildcard = White Label (all features)
            if "*" in features:
                return await func(*args, **kwargs)
            
            if feature not in features:
                raise HTTPException(
                    status_code=403,
                    detail=f"This feature requires a plan upgrade. Missing: {feature}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

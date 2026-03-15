"""
Plan Gate Middleware — Backend Feature Enforcement.

Architecture:
  - Tenant.plan (string: "professional", "enterprise", "whitelabel")
  - Plan (DB model) → PlanFeature (feature_key strings)
  - If DB features exist → use them. Otherwise → fallback to DEFAULT_PLAN_FEATURES.

Every paid feature endpoint MUST use @require_feature(Feature.X).
"""
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.middleware.auth import get_current_active_user
from uuid import UUID
import functools
from typing import Set, Dict
import time
import logging

logger = logging.getLogger(__name__)

# In-memory cache: tenant_id -> (features_set, expiry_timestamp)
_plan_cache: Dict[str, tuple] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

def _get_tenant_features(db: Session, tenant_id: UUID) -> Set[str]:
    """
    Load features for a tenant. Strategy:
    1. Read tenant.plan (string)
    2. Try to find matching Plan record in DB → PlanFeature entries
    3. If no DB features → fallback to DEFAULT_PLAN_FEATURES from constants.py
    """
    cache_key = str(tenant_id)
    now = time.time()
    
    # Check cache first
    if cache_key in _plan_cache:
        features, expiry = _plan_cache[cache_key]
        if now < expiry:
            return features
    
    # Cache miss — get plan string from tenant
    tenant = db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    ).scalar_one_or_none()
    
    if not tenant or not tenant.plan:
        features = set()  # No plan = no features
        _plan_cache[cache_key] = (features, now + CACHE_TTL_SECONDS)
        return features
    
    plan_name = tenant.plan  # e.g. "professional", "enterprise", "whitelabel"
    
    # Try DB lookup: find Plan record by name, then get PlanFeatures
    features = set()
    try:
        from app.models.subscription import Plan, PlanFeature
        plan_record = db.execute(
            select(Plan).where(Plan.name == plan_name)
        ).scalar_one_or_none()
        
        if plan_record:
            plan_features = db.execute(
                select(PlanFeature.feature_key)
                .where(PlanFeature.plan_id == plan_record.id)
            ).scalars().all()
            features = set(plan_features)
    except Exception as e:
        logger.warning(f"DB plan feature lookup failed: {e}")
    
    # Fallback to constants if DB has no features
    if not features:
        from app.constants import DEFAULT_PLAN_FEATURES
        default_features = DEFAULT_PLAN_FEATURES.get(plan_name, [])
        features = set(default_features)
        logger.info(f"Using fallback features for plan '{plan_name}': {features}")
    
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
    
    Reads from tenant.plan → Plan.name → PlanFeatures.
    Falls back to DEFAULT_PLAN_FEATURES from constants.py.
    
    Usage:
        @router.post("/analyze")
        @require_feature(Feature.TRADE_INTELLIGENCE)
        async def analyze(...):
    """
    def decorator(func):
        import asyncio

        _is_async = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            db: Session = kwargs.get("db")
            current_user: User = kwargs.get("current_user")
            
            if not db or not current_user:
                raise HTTPException(status_code=500, detail="Plan gate configuration error")
            
            # Super Admins bypass all feature gates
            if getattr(current_user, 'is_superuser', False) or getattr(current_user, 'role', '') == "super_admin":
                result = func(*args, **kwargs)
                return await result if _is_async else result
            
            tenant_id = getattr(current_user, 'tenant_id', None) or getattr(current_user, 'current_tenant_id', None)
            
            if not tenant_id:
                raise HTTPException(status_code=403, detail="No organization associated")

            features = _get_tenant_features(db, tenant_id)
            
            # Wildcard = White Label (all features)
            if "*" in features:
                result = func(*args, **kwargs)
                return await result if _is_async else result
            
            if feature not in features:
                raise HTTPException(
                    status_code=403,
                    detail=f"This feature requires a plan upgrade. Missing: {feature}"
                )
            
            result = func(*args, **kwargs)
            return await result if _is_async else result
        return wrapper
    return decorator


def require_role(*allowed_roles: str):
    """
    Decorator: Rejects request with 403 if user's tenant membership role
    is not in the allowed roles.
    
    Usage:
        @router.post("/manage-team")
        @require_role("owner", "trade_manager")
        async def manage_team(...):
    """
    def decorator(func):
        import asyncio
        _is_async = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            db: Session = kwargs.get("db")
            current_user: User = kwargs.get("current_user")
            
            if not db or not current_user:
                raise HTTPException(status_code=500, detail="Role gate configuration error")
            
            # Super Admins bypass all role checks
            if getattr(current_user, 'is_superuser', False) or getattr(current_user, 'role', '') == "super_admin":
                result = func(*args, **kwargs)
                return await result if _is_async else result
            
            tenant_id = getattr(current_user, 'tenant_id', None) or getattr(current_user, 'current_tenant_id', None)
            if not tenant_id:
                raise HTTPException(status_code=403, detail="No organization associated")
            
            # Look up membership role
            from app.models.tenant import TenantMembership
            membership = db.execute(
                select(TenantMembership).where(
                    TenantMembership.user_id == current_user.id,
                    TenantMembership.tenant_id == tenant_id
                )
            ).scalar_one_or_none()
            
            if not membership or membership.role not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"This action requires one of: {', '.join(allowed_roles)}. Your role: {membership.role if membership else 'none'}"
                )
            
            result = func(*args, **kwargs)
            return await result if _is_async else result
        return wrapper
    return decorator

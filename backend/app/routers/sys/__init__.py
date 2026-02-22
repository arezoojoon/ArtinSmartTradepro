"""
System Admin Router Package
Phase 6 - Complete Super Admin Panel
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .tenants import router as tenants_router
from .plans import router as plans_router
from .whitelabel import router as whitelabel_router
from .audit import router as audit_router
from .queues import router as queues_router
from .prompt_ops import router as prompt_ops_router
from .revenue import router as revenue_router
from .health import router as health_router
from .security import router as security_router
from .support import router as support_router
from .costs import router as costs_router

# Create main system router
sys_router = APIRouter(prefix="/sys", tags=["sys-admin"])

# Register all sub-routers
sys_router.include_router(auth_router, prefix="/auth", tags=["System Admin Auth"])
sys_router.include_router(tenants_router, prefix="/tenants", tags=["Tenant Management"])
sys_router.include_router(plans_router, prefix="/plans", tags=["Plans & Pricing"])
sys_router.include_router(whitelabel_router, prefix="/whitelabel", tags=["White-Label Control"])
sys_router.include_router(audit_router, prefix="/audit", tags=["Audit Logs"])
sys_router.include_router(queues_router, prefix="/queues", tags=["DLQ & Queues"])
sys_router.include_router(prompt_ops_router, prefix="/prompts", tags=["Prompt Operations"])
sys_router.include_router(revenue_router, prefix="/revenue", tags=["Revenue & Analytics"])
sys_router.include_router(health_router, prefix="/health", tags=["Health Monitoring"])
sys_router.include_router(security_router, prefix="/security", tags=["Security & Compliance"])
sys_router.include_router(support_router, prefix="/support", tags=["Support Ticketing"])
sys_router.include_router(costs_router, prefix="/costs", tags=["Cost Dashboard"])

# Export the main router
router = sys_router

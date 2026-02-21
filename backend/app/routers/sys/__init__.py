"""
/sys/* route package — Phase 6 Super Admin endpoints.
All routes in this package require sys admin JWT (get_current_sys_admin).
Tenant JWTs are explicitly rejected.
"""
from fastapi import APIRouter
from .auth import router as auth_router
from .tenants import router as tenants_router
from .plans import router as plans_router
from .whitelabel import router as whitelabel_router
from .audit import router as audit_router
from .queues import router as queues_router
from .prompt_ops import router as prompt_ops_router

sys_router = APIRouter(prefix="/sys", tags=["sys-admin"])

sys_router.include_router(auth_router,        prefix="/auth")
sys_router.include_router(tenants_router,     prefix="/tenants")
sys_router.include_router(plans_router,       prefix="/plans")
sys_router.include_router(whitelabel_router,  prefix="/whitelabel")
sys_router.include_router(audit_router,       prefix="/audit")
sys_router.include_router(queues_router,      prefix="/queues")
sys_router.include_router(prompt_ops_router,  prefix="/prompts")

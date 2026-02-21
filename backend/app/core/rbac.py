"""
RBAC Guard — Phase 1 Architecture.
FastAPI dependency that checks if the current user has required permissions.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.rbac import UserRole, Role, RolePermission, Permission
from typing import List, Callable
import uuid


def require_permissions(required: List[str]) -> Callable:
    """
    FastAPI dependency factory.
    Usage: @router.get("/admin/ping", dependencies=[Depends(require_permissions(["roles.read"]))])
    
    The decorated endpoint will reject requests from users who lack
    ANY of the listed permissions.
    """
    async def _guard(
        request=None,
        db: AsyncSession = Depends(get_db),
    ):
        # Extract user from request state (set by auth middleware)
        from fastapi import Request
        if request is None:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user = getattr(request.state, "user", None)
        if user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_id = getattr(user, "id", None) or getattr(user, "user_id", None)
        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Super admin bypasses all permission checks
        if getattr(user, "is_superuser", False):
            return True

        # Load user's roles + permissions for current tenant
        tenant_id = getattr(user, "current_tenant_id", None) or getattr(user, "tenant_id", None)
        if not tenant_id:
            raise HTTPException(status_code=403, detail="No tenant context")

        result = await db.execute(
            select(Permission.name)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user_id,
                Role.tenant_id == tenant_id
            )
        )
        user_permissions = {row[0] for row in result.all()}

        missing = set(required) - user_permissions
        if missing:
            raise HTTPException(
                status_code=403,
                detail=f"Missing permissions: {', '.join(missing)}"
            )
        return True

    return _guard


# Seed permissions list — used by the seed migration/script
SEED_PERMISSIONS = [
    # CRM
    "crm.read", "crm.write", "crm.admin",
    # Users & Roles
    "users.read", "users.write", "users.manage",
    "roles.read", "roles.write",
    # Hunter
    "hunter.read", "hunter.write",
    # Brain / AI
    "brain.read", "brain.write",
    # Toolbox
    "toolbox.read", "toolbox.write",
    # WhatsApp / Campaigns
    "whatsapp.read", "whatsapp.write",
    "campaigns.read", "campaigns.write",
    # Finance
    "finance.read", "finance.write",
    # Billing / Wallet
    "billing.read", "billing.manage",
    # Settings
    "settings.read", "settings.write",
    # Admin
    "admin.access",
]


# Default role templates — used when creating a new tenant
DEFAULT_ROLES = {
    "Owner": SEED_PERMISSIONS,  # Full access
    "Trade Manager": [
        "crm.read", "crm.write", "hunter.read", "hunter.write",
        "brain.read", "brain.write", "toolbox.read", "toolbox.write",
        "finance.read", "whatsapp.read",
    ],
    "Sales Agent": [
        "crm.read", "crm.write", "whatsapp.read", "whatsapp.write",
        "campaigns.read", "campaigns.write",
    ],
    "Sourcing Agent": [
        "crm.read", "toolbox.read", "toolbox.write",
    ],
    "Finance": [
        "finance.read", "finance.write", "billing.read",
    ],
    "Viewer": [
        "crm.read", "hunter.read", "brain.read", "toolbox.read",
        "finance.read", "whatsapp.read",
    ],
}

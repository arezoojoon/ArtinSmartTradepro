from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db.session import get_db
from ..models.user import User
from app.models.tenant import Tenant, TenantMembership
from .security import verify_token


security = HTTPBearer()


class TenantContext:
    """Tenant context for multi-tenant isolation."""
    
    def __init__(
        self, 
        tenant_id: str, 
        user_id: str,
        user_role: str
    ):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.user_role = user_role


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    token = credentials.credentials
    user_id = verify_token(token, "access")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_tenant_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TenantContext:
    """
    Get tenant context for the current user.
    Uses user.current_tenant_id if set, otherwise validates tenant membership.
    """
    if not current_user.current_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active tenant selected",
        )
    
    # Verify user has access to this tenant
    user_role = None
    
    # Check for Super Admin (Defensive check for attributes)
    is_super = getattr(current_user, "is_superuser", False)
    role_str = getattr(current_user, "role", "")
    
    if is_super or role_str == "super_admin":
        user_role = "owner"
    else:
        result = await db.execute(
            select(TenantMembership)
            .where(
                TenantMembership.tenant_id == current_user.current_tenant_id,
                TenantMembership.user_id == current_user.id
            )
        )
        membership = result.scalar_one_or_none()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant",
            )
        user_role = membership.role
    
    # Verify tenant exists
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.current_tenant_id)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    
    return TenantContext(
        tenant_id=tenant.id,
        user_id=current_user.id,
        user_role=user_role
    )



from typing import Callable
from fastapi import Depends, HTTPException, status

# Role-specific dependencies - create proper callable dependencies
def require_tenant_role(*allowed_roles: str) -> Callable:
    """Factory function to create role-based dependencies."""
    async def _checker(tenant_context = Depends(get_tenant_context)):
        role = getattr(tenant_context, "user_role", None)
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Insufficient tenant role",
                        "details": {"required": list(allowed_roles), "actual": role},
                    }
                },
            )
        return tenant_context
    return _checker

# Export as dependencies
require_tenant_owner = require_tenant_role("owner")
require_tenant_admin = require_tenant_role("owner", "admin")
require_tenant_member = require_tenant_role("owner", "admin", "member")


class BaseTenantModel:
    """Base class for tenant-scoped models."""
    
    @classmethod
    def get_tenant_scoped_query(cls, tenant_id: str):
        """Get a query scoped to the specified tenant."""
        # This will be implemented in model classes
        pass

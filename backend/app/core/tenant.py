from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db.session import get_db
from ..models.user import User
from ..models.tenant import Tenant, TenantMembership
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
        user_role=membership.role
    )


async def require_tenant_role(
    required_roles: list[str],
    tenant_context: TenantContext = Depends(get_tenant_context)
) -> TenantContext:
    """Require specific tenant role(s) to access a resource."""
    if tenant_context.user_role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required role: {', '.join(required_roles)}",
        )
    return tenant_context


# Role-specific dependencies
require_tenant_owner = Depends(require_tenant_role(["owner"]))
require_tenant_admin = Depends(require_tenant_role(["owner", "admin"]))
require_tenant_member = Depends(require_tenant_role(["owner", "admin", "member"]))


class BaseTenantModel:
    """Base class for tenant-scoped models."""
    
    @classmethod
    def get_tenant_scoped_query(cls, tenant_id: str):
        """Get a query scoped to the specified tenant."""
        # This will be implemented in model classes
        pass

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_db
from ..models.user import User
from ..core.security import verify_token
from ..core.tenant import get_tenant_context, TenantContext

security = HTTPBearer()


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
    
    from sqlalchemy import select
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


async def get_current_tenant_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TenantContext:
    """Get tenant context for the current user."""
    return await get_tenant_context(current_user, db)


async def get_optional_tenant_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Optional[TenantContext]:
    """Get tenant context if user has one, otherwise None."""
    try:
        return await get_tenant_context(current_user, db)
    except HTTPException:
        return None


from ..services.email.base import EmailService
from ..services.email.local_stub import LocalStubEmailService
from ..core.config import settings

def get_email_service() -> EmailService:
    """Get the configured email service."""
    if settings.EMAIL_PROVIDER == "local_stub":
        return LocalStubEmailService()
    # Add other providers here as needed
    return LocalStubEmailService()

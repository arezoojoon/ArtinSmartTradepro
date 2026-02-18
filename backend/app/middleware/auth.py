from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.security import is_token_blacklisted

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

from app.models.tenant import TenantMembership

def _check_tenant_active(db: Session, user: User, tenant_id_str: str = None):
    """
    Check if the context tenant is active.
    If tenant_id is in token claim, validate it and membership.
    """
    if not tenant_id_str:
        return # No tenant context (global user scope)

    tenant_id = uuid.UUID(tenant_id_str)
    
    # Check membership + tenant active
    # This query verifies user IS a member AND gets tenant status
    result = db.query(TenantMembership, Tenant).join(Tenant).filter(
        TenantMembership.user_id == user.id,
        TenantMembership.tenant_id == tenant_id
    ).first()
    
    if not result:
        # Not a member or tenant deleted
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this organization."
        )
        
    membership, tenant = result
    
    if not tenant.is_active:
        raise HTTPException(
            status_code=403,
            detail="Your organization has been suspended. Contact support."
        )

    # Attach to request state if needed?
    # For now, just validation.

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check blacklist (logout enforcement)
    if is_token_blacklisted(token): # Assume this function exists and works
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        tenant_id_str: str = payload.get("tenant_id") # Extract tenant context
        
        if email is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Validate tenant context if present
    if tenant_id_str:
        try:
            _check_tenant_active(db, user, tenant_id_str)
            # Maybe store current_tenant_id on user object for convenience?
            user.current_tenant_id = uuid.UUID(tenant_id_str)
        except ValueError:
             raise credentials_exception

    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user

def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Insufficient privileges"
        )
    return current_user

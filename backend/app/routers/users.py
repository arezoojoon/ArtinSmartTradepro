from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas import user as user_schema
from app.middleware.auth import get_current_active_user

router = APIRouter()

@router.get("/me", response_model=user_schema.User)
def read_user_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get current user profile.
    For superadmins: returns user with role=super_admin, tenant may be None.
    For normal users: hydrates tenant info from current_tenant_id.
    """
    # Ensure superadmin role is correctly set
    if current_user.is_superuser and current_user.role != "super_admin":
        current_user.role = "super_admin"
        db.commit()
    
    # Hydrate tenant info for users with active tenant context
    if hasattr(current_user, "current_tenant_id") and current_user.current_tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == current_user.current_tenant_id).first()
        current_user.tenant = tenant
        current_user.tenant_id = current_user.current_tenant_id
    
    return current_user

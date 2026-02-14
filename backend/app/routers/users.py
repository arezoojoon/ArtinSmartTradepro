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
    Get current user.
    If 'current_tenant_id' is set on the user object (via middleware), 
    we could theoretically return tenant info here too, 
    but Pydantic schema likely only has tenant_id/tenant fields.
    
    Since we removed user.tenant_id, we should update the schema or populate it dynamically.
    """
    
    # If the user object has a transient 'current_tenant_id', we can hydrate the tenant field
    # But schema might expect 'tenant' object.
    
    if hasattr(current_user, "current_tenant_id") and current_user.current_tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == current_user.current_tenant_id).first()
        current_user.tenant = tenant
        current_user.tenant_id = current_user.current_tenant_id
    
    return current_user

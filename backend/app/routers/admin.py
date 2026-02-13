from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.billing import Wallet
from app.middleware.auth import get_current_superuser
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

router = APIRouter()

class TenantInfo(BaseModel):
    id: UUID
    name: str
    slug: str
    is_active: bool
    balance: Optional[float] = None

    class Config:
        from_attributes = True

class TenantToggleRequest(BaseModel):
    tenant_id: UUID
    is_active: bool

@router.get("/tenants", response_model=List[TenantInfo])
def list_tenants(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """List all tenants with wallet balance."""
    tenants = db.query(Tenant).all()
    result = []
    for t in tenants:
        wallet = db.query(Wallet).filter(Wallet.tenant_id == t.id).first()
        result.append(TenantInfo(
            id=t.id,
            name=t.name,
            slug=t.slug,
            is_active=t.is_active,
            balance=float(wallet.balance) if wallet else 0.0
        ))
    return result

@router.post("/tenants/toggle")
def toggle_tenant(
    body: TenantToggleRequest,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    KILL SWITCH: Instantly enable/disable a tenant.
    When disabled:
    - Login is blocked (checked in auth router)
    - All API calls for that tenant's users will fail
    """
    tenant = db.query(Tenant).filter(Tenant.id == body.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    tenant.is_active = body.is_active
    db.commit()
    
    action = "enabled" if body.is_active else "DISABLED"
    return {"detail": f"Tenant '{tenant.name}' has been {action}"}

@router.get("/stats")
def admin_stats(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Global platform stats for super admin."""
    total_tenants = db.query(Tenant).count()
    active_tenants = db.query(Tenant).filter(Tenant.is_active == True).count()
    total_users = db.query(User).count()
    
    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "total_users": total_users
    }

class UserInfo(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    tenant_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True

@router.get("/users", response_model=List[UserInfo])
def list_users(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """List all users across the platform."""
    users = db.query(User).all()
    return users

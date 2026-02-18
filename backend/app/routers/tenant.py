from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.tenant import Tenant, TenantMembership, TenantInvitation, TenantRole
from app.schemas import tenant as tenant_schema
from app.security import create_access_token
from app.services.audit import log_audit_event
from app.middleware.auth import get_current_active_user
from app.config import get_settings
from slugify import slugify
import uuid
import datetime

router = APIRouter()
settings = get_settings()

@router.get("/", response_model=List[tenant_schema.TenantRead])
def get_user_tenants(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List all tenants the current user is a member of.
    """
    memberships = db.query(TenantMembership).filter(
        TenantMembership.user_id == current_user.id
    ).all()
    
    tenants = []
    for m in memberships:
        # Assuming Tenant is eager loaded or lazy loaded
        t = db.query(Tenant).filter(Tenant.id == m.tenant_id).first()
        if t:
            tenants.append(t)
    return tenants

@router.post("/", response_model=tenant_schema.TenantRead)
def create_new_tenant(
    tenant_in: tenant_schema.TenantCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new tenant and make the current user the OWNER.
    """
    # 1. Check existing name uniqueness? Slug logic handles duplications?
    slug = slugify(tenant_in.name) + "-" + str(uuid.uuid4())[:4]
    
    # 2. Get Plan (default professional for now/stub)
    # real logic uses tenant_in.plan_id or default
    
    tenant = Tenant(
        name=tenant_in.name,
        slug=slug,
        is_active=True,
        mode=tenant_in.mode,
        # plan_id handled via default migration logic or separate lookup
    )
    db.add(tenant)
    db.flush()
    
    # 3. Create Membership (Owner)
    membership = TenantMembership(
        tenant_id=tenant.id,
        user_id=current_user.id,
        role=TenantRole.OWNER
    )
    db.add(membership)
    db.commit()
    db.refresh(tenant)
    
    log_audit_event(db, "tenant.create", user_id=current_user.id, tenant_id=tenant.id, details={"name": tenant.name})
    
    return tenant

@router.post("/{tenant_id}/switch")
def switch_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Verify membership and return a new access token scoped to this tenant.
    """
    # Verify membership
    membership = db.query(TenantMembership).filter(
        TenantMembership.user_id == current_user.id,
        TenantMembership.tenant_id == tenant_id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this tenant")
    
    # Generate new token
    claims = {
        "tenant_id": str(tenant_id),
        "role": membership.role
    }
    
    access_token = create_access_token(
        subject=current_user.email,
        additional_claims=claims
    )
    
    log_audit_event(db, "tenant.switch", user_id=current_user.id, tenant_id=tenant_id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "tenant_id": tenant_id
    }

@router.post("/{tenant_id}/invite")
def invite_member(
    tenant_id: str,
    email: str,
    role: str = "member",
    current_user: User = Depends(get_current_active_user),
    # current_tenant: Tenant = Depends(get_current_tenant), # Requires middleware
    db: Session = Depends(get_db)
) -> Any:
    """
    Invite a user to the tenant via email.
    """
    # Validate role permissions (Only Owner/Admin can invite)
    membership = db.query(TenantMembership).filter(
        TenantMembership.user_id == current_user.id,
        TenantMembership.tenant_id == tenant_id
    ).first()
    
    if not membership or membership.role not in [TenantRole.OWNER, TenantRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Check if already a member
    # ... logic here ...
    
    # Create Invitation
    token = str(uuid.uuid4())
    invitation = TenantInvitation(
        tenant_id=tenant_id,
        email=email,
        role=role,
        token_hash=token, # In real app, hash this
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=7)
    )
    db.add(invitation)
    db.commit()
    
    # STUB: Send email
    print(f"[EMAIL STUB] Invitation to {email} for tenant {tenant_id}: Token={token}")
    
    log_audit_event(db, "tenant.invite", user_id=current_user.id, tenant_id=tenant_id, details={"email": email, "role": role})
    
    return {"detail": "Invitation sent"}

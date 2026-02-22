from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta

from ...db.session import get_db
from ...models.user import User
from ...models.tenant import Tenant, TenantMembership, TenantInvitation
from ...models.audit import AuditLog
from ...schemas.tenant import (
    TenantCreateRequest,
    TenantUpdateRequest,
    TenantSwitchRequest,
    TenantInviteRequest,
    TenantInviteAcceptRequest,
    TenantResponse,
    TenantListResponse,
    TenantMembershipResponse,
    TenantInvitationResponse
)
from ..deps import get_current_user, get_current_tenant_context
from ...core.tenant import require_tenant_role

router = APIRouter(tags=["tenants"])


@router.get("", response_model=TenantListResponse)
async def get_user_tenants(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get all tenants for the current user."""
    """Get all tenants for the current user."""
    
    # Check for Super Admin (Defensive)
    is_super = getattr(current_user, "is_superuser", False)
    role_str = getattr(current_user, "role", "")
    
    if is_super or role_str == "super_admin":
        # Super admin gets all tenants
        result = await db.execute(
            select(Tenant).order_by(Tenant.created_at.desc())
        )
        tenants = result.scalars().all()
        
        tenant_memberships = []
        for tenant in tenants:
            tenant_memberships.append(TenantMembershipResponse(
                tenant_id=tenant.id,
                tenant_name=tenant.name,
                role="owner", # Grant owner view to super admin
                created_at=tenant.created_at
            ))
            
        return TenantListResponse(
            tenants=tenant_memberships,
            current_tenant_id=current_user.current_tenant_id
        )
    
    # Normal user
    memberships = result.all()
    
    tenant_memberships = []
    for membership, tenant in memberships:
        tenant_memberships.append(TenantMembershipResponse(
            tenant_id=tenant.id,
            tenant_name=tenant.name,
            role=membership.role,
            created_at=membership.created_at
        ))
    
    return TenantListResponse(
        tenants=tenant_memberships,
        current_tenant_id=current_user.current_tenant_id
    )


@router.post("", response_model=TenantResponse)
async def create_tenant(
    tenant_data: TenantCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a new tenant."""
    # Generate slug if not provided
    slug = tenant_data.slug or tenant_data.name.lower().replace(" ", "-")
    
    # Ensure slug is unique
    existing_slug = await db.execute(
        select(Tenant).where(Tenant.slug == slug)
    )
    if existing_slug.scalar_one_or_none():
        counter = 1
        while True:
            new_slug = f"{slug}-{counter}"
            existing = await db.execute(
                select(Tenant).where(Tenant.slug == new_slug)
            )
            if not existing.scalar_one_or_none():
                slug = new_slug
                break
            counter += 1
    
    # Create tenant
    tenant = Tenant(
        name=tenant_data.name,
        slug=slug,
        plan=tenant_data.plan.value,
        is_active=True
    )
    
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)  # Ensure created_at/updated_at are populated
    
    # Create owner membership
    membership = TenantMembership(
        tenant_id=tenant.id,
        user_id=current_user.id,
        role="owner"
    )
    
    db.add(membership)
    await db.commit()
    await db.refresh(membership)  # Ensure created_at/updated_at are populated
    
    # Set as current tenant for user
    current_user.current_tenant_id = tenant.id
    
    # Log tenant creation
    audit_log = AuditLog(
        tenant_id=tenant.id,
        user_id=current_user.id,
        action="tenant_create",
        resource_type="tenant",
        resource_id=str(tenant.id),
        metadata_json={"name": tenant.name, "plan": tenant.plan},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit_log)
    await db.commit()

    # Seed Default Roles, Permissions, and Pipelines
    from ...services.tenant_seeder import seed_new_tenant
    await seed_new_tenant(db, tenant.id, current_user.id)
    
    return TenantResponse.model_validate(tenant)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: uuid.UUID,
    tenant_context = Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get tenant details."""
    if str(tenant_context.tenant_id) != str(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant"
        )
    
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return TenantResponse.from_orm(tenant)


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: uuid.UUID,
    tenant_data: TenantUpdateRequest,
    request: Request,
    tenant_context = Depends(require_tenant_role("owner", "admin")),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update tenant details."""
    if str(tenant_context.tenant_id) != str(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant"
        )
    
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Update fields
    if tenant_data.name is not None:
        tenant.name = tenant_data.name
    
    if tenant_data.settings is not None:
        tenant.settings = tenant_data.settings
    
    # Log tenant update
    audit_log = AuditLog(
        tenant_id=tenant.id,
        actor_user_id=tenant_context.user_id,
        action="tenant_update",
        resource_type="tenant",
        resource_id=str(tenant.id),
        details={"updated_fields": tenant_data.dict(exclude_unset=True)},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(tenant)
    
    return TenantResponse.from_orm(tenant)


@router.post("/{tenant_id}/switch")
async def switch_tenant(
    tenant_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Switch to a different tenant."""
    # Verify user has access to this tenant
    # Verify user has access to this tenant
    
    # Check for Super Admin
    is_super = getattr(current_user, "is_superuser", False)
    role_str = getattr(current_user, "role", "")
    
    if is_super or role_str == "super_admin":
        pass # Allow access
    else:
        result = await db.execute(
            select(TenantMembership).where(
                and_(
                    TenantMembership.tenant_id == tenant_id,
                    TenantMembership.user_id == current_user.id
                )
            )
        )
        membership = result.scalar_one_or_none()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )
    
    # Update user's current tenant
    old_tenant_id = current_user.current_tenant_id
    current_user.current_tenant_id = tenant_id
    
    # Log tenant switch
    audit_log = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=current_user.id,
        action="tenant_switch",
        resource_type="user",
        resource_id=str(current_user.id),
        details={
            "from_tenant_id": str(old_tenant_id) if old_tenant_id else None,
            "to_tenant_id": str(tenant_id)
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit_log)
    
    await db.commit()
    
    return {"message": "Successfully switched tenant", "tenant_id": str(tenant_id)}


@router.post("/{tenant_id}/invite")
async def invite_user(
    tenant_id: uuid.UUID,
    invite_data: TenantInviteRequest,
    request: Request,
    tenant_context = Depends(require_tenant_role("owner", "admin")),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Invite a user to join the tenant."""
    if str(tenant_context.tenant_id) != str(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant"
        )
    
    # Check if user already has membership
    result = await db.execute(
        select(User).where(User.email == invite_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        # Check if already a member
        result = await db.execute(
            select(TenantMembership).where(
                and_(
                    TenantMembership.tenant_id == tenant_id,
                    TenantMembership.user_id == existing_user.id
                )
            )
        )
        existing_membership = result.scalar_one_or_none()
        
        if existing_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this tenant"
            )
    
    # Generate invitation token
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Create invitation
    invitation = TenantInvitation(
        tenant_id=tenant_id,
        email=invite_data.email,
        role=invite_data.role.value,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(days=7),
        invited_by_user_id=tenant_context.user_id
    )
    
    db.add(invitation)
    
    # Get tenant for email
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    
    # Log invitation
    audit_log = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=tenant_context.user_id,
        action="tenant_invite",
        resource_type="invitation",
        resource_id=str(invitation.id),
        details={
            "email": invite_data.email,
            "role": invite_data.role.value
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit_log)
    
    await db.commit()
    
    # TODO: Send invitation email (stubbed for now)
    print(f"Invitation token for {invite_data.email}: {token}")
    
    return {"message": "Invitation sent successfully"}


@router.get("/{tenant_id}/invitations", response_model=List[TenantInvitationResponse])
async def get_tenant_invitations(
    tenant_id: uuid.UUID,
    tenant_context = Depends(require_tenant_role("owner", "admin")),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get all pending invitations for the tenant."""
    if str(tenant_context.tenant_id) != str(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant"
        )
    
    result = await db.execute(
        select(TenantInvitation)
        .where(
            and_(
                TenantInvitation.tenant_id == tenant_id,
                TenantInvitation.accepted_at.is_(None),
                TenantInvitation.expires_at > datetime.utcnow()
            )
        )
        .order_by(TenantInvitation.created_at.desc())
    )
    invitations = result.scalars().all()
    
    # Get tenant name for each invitation
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = tenant_result.scalar_one_or_none()
    
    return [
        TenantInvitationResponse(
            id=invitation.id,
            tenant_id=invitation.tenant_id,
            tenant_name=tenant.name if tenant else "",
            email=invitation.email,
            role=invitation.role,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at
        )
        for invitation in invitations
    ]


@router.post("/invitations/accept")
async def accept_invitation(
    accept_data: TenantInviteAcceptRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Accept a tenant invitation."""
    token_hash = hashlib.sha256(accept_data.token.encode()).hexdigest()
    
    # Find valid invitation
    result = await db.execute(
        select(TenantInvitation)
        .where(
            and_(
                TenantInvitation.token_hash == token_hash,
                TenantInvitation.expires_at > datetime.utcnow(),
                TenantInvitation.accepted_at.is_(None)
            )
        )
    )
    invitation = result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation"
        )
    
    # Verify email matches
    if invitation.email.lower() != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation was sent to a different email address"
        )
    
    # Check if already a member
    result = await db.execute(
        select(TenantMembership).where(
            and_(
                TenantMembership.tenant_id == invitation.tenant_id,
                TenantMembership.user_id == current_user.id
            )
        )
    )
    existing_membership = result.scalar_one_or_none()
    
    if existing_membership:
        # Mark invitation as accepted anyway
        invitation.accepted_at = datetime.utcnow()
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of this tenant"
        )
    
    # Create membership
    membership = TenantMembership(
        tenant_id=invitation.tenant_id,
        user_id=current_user.id,
        role=invitation.role
    )
    
    db.add(membership)
    
    # Mark invitation as accepted
    invitation.accepted_at = datetime.utcnow()
    
    # Set as current tenant if user doesn't have one
    if not current_user.current_tenant_id:
        current_user.current_tenant_id = invitation.tenant_id
    
    # Log acceptance
    audit_log = AuditLog(
        tenant_id=invitation.tenant_id,
        actor_user_id=current_user.id,
        action="invitation_accept",
        resource_type="membership",
        resource_id=str(membership.id),
        details={
            "invitation_id": str(invitation.id),
            "role": invitation.role
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit_log)
    
    await db.commit()
    
    return {"message": "Invitation accepted successfully"}

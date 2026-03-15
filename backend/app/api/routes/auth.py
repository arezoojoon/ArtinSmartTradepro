from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ...db.session import get_db
from ...models.user import User
from ...models.auth import Session, PasswordResetToken, EmailVerificationToken
from ...models.tenant import Tenant, TenantMembership
from ...models.audit import AuditLog
from ...core.security import (
    get_password_hash, 
    verify_password, 
    validate_password,
    create_access_token,
    create_refresh_token,
    generate_password_reset_token,
    generate_email_verification_token
)
from ...core.config import settings
from ...schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    MeResponse
)
from ..deps import get_current_user, get_optional_tenant_context, get_email_service
from app.services.email.base import EmailService
import bcrypt
import hashlib
import uuid

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service)
) -> Any:
    """Register a new user."""
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password
    is_valid, message = validate_password(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Create user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role or "user",
        persona=user_data.persona or "trader",
        email_verified=False
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Determine selected plan (from checkout flow)
    selected_plan = user_data.plan or "professional"
    if selected_plan not in ("professional", "enterprise", "whitelabel"):
        selected_plan = "professional"
    
    # Create tenant if company name is provided
    if user_data.company_name:
        slug = user_data.company_name.lower().replace(" ", "-")
        # Ensure slug is unique
        existing_slug = await db.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        if existing_slug.scalar_one_or_none():
            slug = f"{slug}-{uuid.uuid4().hex[:4]}"
            
        tenant = Tenant(
            name=user_data.company_name,
            slug=slug,
            mode=user_data.tenant_mode or "hybrid",
            plan=selected_plan,
            is_active=True
        )
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        
        # Create owner membership
        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role="owner"
        )
        db.add(membership)
        
        # Set as current tenant
        user.current_tenant_id = tenant.id
        
        # Create wallet for tenant
        try:
            from ...models.billing import Wallet
            wallet = Wallet(
                tenant_id=tenant.id,
                balance=0.0
            )
            db.add(wallet)
        except Exception as e:
            print(f"Failed to create wallet: {e}")
        
        # Create subscription with 3-day free trial
        try:
            from ...models.subscription import Subscription, Plan, PlanFeature
            from ...constants import DEFAULT_PLAN_FEATURES
            trial_end = datetime.utcnow() + timedelta(days=3)
            # Find or create the plan record
            plan_result = await db.execute(
                select(Plan).where(Plan.name == selected_plan)
            )
            plan_record = plan_result.scalar_one_or_none()
            if not plan_record:
                # Create plan record if it doesn't exist
                plan_prices = {"professional": 299, "enterprise": 999, "whitelabel": 2999}
                plan_record = Plan(
                    name=selected_plan,
                    display_name=selected_plan.capitalize(),
                    price_monthly=plan_prices.get(selected_plan, 299),
                    currency="USD",
                    is_active=True
                )
                db.add(plan_record)
                await db.commit()
                await db.refresh(plan_record)
                
                # Seed PlanFeature records for this plan
                feature_keys = DEFAULT_PLAN_FEATURES.get(selected_plan, [])
                for fk in feature_keys:
                    db.add(PlanFeature(plan_id=plan_record.id, feature_key=fk))
            
            subscription = Subscription(
                tenant_id=tenant.id,
                plan_id=plan_record.id,
                status="trialing",
                current_period_start=datetime.utcnow(),
                current_period_end=trial_end,
            )
            db.add(subscription)
        except Exception as e:
            print(f"Failed to create trial subscription: {e}")
        
        # Seed default tenant data (roles, permissions)
        from ...services.tenant_seeder import seed_new_tenant
        try:
            await seed_new_tenant(db, tenant.id, user.id)
        except Exception as e:
            # Don't fail registration if seeder fails, but log it
            print(f"Failed to seed tenant: {e}")
            
        await db.commit()
    
    # Create email verification token
    token = generate_email_verification_token()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    verification_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    
    db.add(verification_token)
    await db.commit()
    
    # Send verification email
    try:
        await email_service.send_email(
            to_email=user.email,
            subject="Verify your email - Artin Smart Trade",
            content=f"Please verify your email by clicking: {getattr(settings, 'FRONTEND_URL', getattr(settings, 'APP_URL', 'http://localhost:3000'))}/verify-email?token={token}"
        )
    except Exception as e:
        # Don't fail registration if email fails, but log it
        print(f"Failed to send verification email: {e}")
    
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Authenticate user and return tokens."""
    # Handle both JSON and form data
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
    else:
        data = await request.form()
    
    user_data = UserLoginRequest(email=data["email"], password=data["password"])
    # Find user
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is disabled"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Get user roles and tenant context
    extra_claims = {}
    if user.is_superuser:
        extra_claims["roles"] = ["super_admin"]
    elif user.current_tenant_id:
        from ...models.rbac import UserRole, Role
        roles_query = await db.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user.id,
                Role.tenant_id == user.current_tenant_id
            )
        )
        extra_claims["tenant_id"] = str(user.current_tenant_id)
        extra_claims["roles"] = [r[0] for r in roles_query.all()]

    access_token = create_access_token(
        subject=str(user.id), 
        expires_delta=access_token_expires,
        extra_claims=extra_claims
    )
    refresh_token = create_refresh_token(
        subject=str(user.id), 
        expires_delta=refresh_token_expires
    )
    
    # Store refresh token in database
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    
    # Enforce single-session policy: delete existing sessions for this user
    await db.execute(
        delete(Session).where(Session.user_id == user.id)
    )
    
    # Create new session
    session = Session(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + refresh_token_expires
    )
    
    db.add(session)
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    
    # Log login
    if user.current_tenant_id:
        audit_log = AuditLog(
            user_id=user.id,
            tenant_id=user.current_tenant_id,
            action="user_login",
            resource_type="user",
            resource_id=user.id,
            metadata_json={"email": user.email},
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        db.add(audit_log)
    
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Refresh access token using refresh token."""
    token_hash = hashlib.sha256(token_data.refresh_token.encode()).hexdigest()
    
    # Find valid session
    result = await db.execute(
        select(Session).where(
            Session.token_hash == token_hash,
            Session.expires_at > datetime.utcnow(),
            Session.revoked_at.is_(None)
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == session.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Get user roles and tenant context
    extra_claims = {}
    if user.is_superuser:
        extra_claims["roles"] = ["super_admin"]
    elif user.current_tenant_id:
        from ...models.rbac import UserRole, Role
        roles_query = await db.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user.id,
                Role.tenant_id == user.current_tenant_id
            )
        )
        extra_claims["tenant_id"] = str(user.current_tenant_id)
        extra_claims["roles"] = [r[0] for r in roles_query.all()]

    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), 
        expires_delta=access_token_expires,
        extra_claims=extra_claims
    )
    
    # Token rotation: create new refresh token
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = create_refresh_token(
        subject=str(user.id), 
        expires_delta=refresh_token_expires
    )
    new_token_hash = hashlib.sha256(new_refresh_token.encode()).hexdigest()

    # Revoke old session and create new one
    await db.execute(delete(Session).where(Session.id == session.id))
    new_session = Session(
        user_id=user.id,
        token_hash=new_token_hash,
        expires_at=datetime.utcnow() + refresh_token_expires
    )
    db.add(new_session)
    
    # Log token refresh
    audit_log = AuditLog(
        actor_user_id=user.id,
        action="token_refresh_rotation",
        resource_type="session",
        resource_id=str(new_session.id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit_log)
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Logout user by revoking refresh token."""
    # Note: In a real implementation, we'd need to identify which session to revoke
    # For now, we'll just log the logout
    audit_log = AuditLog(
        actor_user_id=current_user.id,
        action="user_logout",
        resource_type="user",
        resource_id=str(current_user.id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit_log)
    await db.commit()
    
    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
async def forgot_password(
    forgot_data: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service)
) -> Any:
    """Send password reset email."""
    # Find user
    result = await db.execute(
        select(User).where(User.email == forgot_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If email exists, password reset instructions have been sent"}
    
    # Create reset token
    token = generate_password_reset_token()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Invalidate any existing tokens
    await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None)
        ).update({"used_at": datetime.utcnow()})
    )
    
    # Create new token
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    
    db.add(reset_token)
    
    # Log password reset request
    audit_log = AuditLog(
        actor_user_id=user.id,
        action="password_reset_request",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit_log)
    
    await db.commit()
    
    # Send password reset email
    await email_service.send_email(
        to_email=user.email,
        subject="Reset your password - Artin Smart Trade",
        content=f"Reset your password by clicking: {settings.APP_URL if hasattr(settings, 'APP_URL') else 'http://localhost:3000'}/reset-password?token={token}"
    )
    
    return {"message": "If email exists, password reset instructions have been sent"}


@router.post("/reset-password")
async def reset_password(
    reset_data: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Reset password using token."""
    token_hash = hashlib.sha256(reset_data.token.encode()).hexdigest()
    
    # Find valid token
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.expires_at > datetime.utcnow(),
            PasswordResetToken.used_at.is_(None)
        )
    )
    reset_token = result.scalar_one_or_none()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Validate new password
    is_valid, message = validate_password(reset_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == reset_token.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.password)
    
    # Mark token as used
    reset_token.used_at = datetime.utcnow()
    
    # Revoke all sessions for this user (single-session policy)
    await db.execute(
        delete(Session).where(Session.user_id == user.id)
    )
    
    # Log password reset
    audit_log = AuditLog(
        actor_user_id=user.id,
        action="password_reset",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit_log)
    
    await db.commit()
    
    return {"message": "Password reset successfully"}


@router.post("/verify-email")
async def verify_email(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Verify email using token."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Find valid token
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.expires_at > datetime.utcnow(),
            EmailVerificationToken.verified_at.is_(None)
        )
    )
    verification_token = result.scalar_one_or_none()
    
    if not verification_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == verification_token.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mark email as verified
    user.email_verified = True
    verification_token.verified_at = datetime.utcnow()
    
    # Log email verification
    audit_log = AuditLog(
        actor_user_id=user.id,
        action="email_verify",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit_log)
    
    await db.commit()
    
    return {"message": "Email verified successfully"}


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get current user info with tenant memberships."""
    from sqlalchemy import select
    from ...models.tenant import Tenant, TenantMembership
    
    # Get user's tenant memberships
    tenants = []
    
    # Check for Super Admin
    is_super = getattr(current_user, "is_superuser", False)
    role_str = getattr(current_user, "role", "")
    
    if is_super or role_str == "super_admin":
        # Super admin gets all tenants
        result = await db.execute(
            select(Tenant).order_by(Tenant.created_at.desc())
        )
        all_tenants = result.scalars().all()
        
        for tenant in all_tenants:
            tenants.append({
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "plan": tenant.plan,
                "role": "owner",
                "created_at": tenant.created_at.isoformat() if tenant.created_at else None
            })
    else:
        # Normal user
        result = await db.execute(
            select(TenantMembership, Tenant)
            .join(Tenant, TenantMembership.tenant_id == Tenant.id)
            .where(TenantMembership.user_id == current_user.id)
        )
        memberships = result.all()
        
        for membership, tenant in memberships:
            tenants.append({
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "plan": tenant.plan,
                "role": membership.role,
                "created_at": membership.created_at.isoformat() if membership.created_at else None
            })
    
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        email_verified=current_user.email_verified,
        is_active=current_user.is_active,
        current_tenant_id=current_user.current_tenant_id,
        created_at=current_user.created_at.isoformat(),
        last_login_at=current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        tenants=tenants
    )

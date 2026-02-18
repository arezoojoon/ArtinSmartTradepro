from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.models.billing import Wallet
from app.schemas import token, user
from app.security import (
    create_access_token, create_refresh_token, create_password_reset_token,
    verify_password_reset_token, verify_password, get_password_hash,
    blacklist_token
)
from app.middleware.auth import oauth2_scheme, get_current_active_user
from app.config import get_settings
from app.services.audit import log_audit_event
from jose import jwt, JWTError
from slugify import slugify
from pydantic import BaseModel, EmailStr
import uuid

settings = get_settings()
router = APIRouter()

# --- Schemas for new endpoints ---
class RefreshRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# --- Endpoints ---

from app.models.tenant import TenantMembership, TenantRole

# ... imports ...

@router.post("/login", response_model=token.Token)
def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login.
    Returns access_token + refresh_token.
    """
    db_user = db.query(User).filter(User.email == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    if not db_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # NEW Multi-Tenant Logic:
    # 1. Fetch memberships
    memberships = db.query(TenantMembership).filter(
        TenantMembership.user_id == db_user.id
    ).all()
    
    default_tenant_id = None
    default_role = None
    
    if memberships:
        # Defaults to first tenant
        # MVP: Could store 'last_tenant_id' in user model
        default_tenant_id = str(memberships[0].tenant_id)
        default_role = memberships[0].role
        
        # Check if default tenant is active
        # (Middleware handles this, but good to check before issuing token)
        t = db.query(Tenant).filter(Tenant.id == default_tenant_id).first()
        if t and not t.is_active:
             # Try next membership? Or just fail?
             pass 

    claims = {
        "tenant_id": default_tenant_id,
        "role": default_role or db_user.role # Fallback to user role if no tenant
    }
    
    access_token = create_access_token(subject=db_user.email, additional_claims=claims)
    refresh_token = create_refresh_token(subject=db_user.email, additional_claims=claims)
    
    log_audit_event(db, "auth.login", user_id=db_user.id, tenant_id=default_tenant_id, ip_address="unknown")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/refresh", response_model=token.Token)
def refresh_access_token(body: RefreshRequest, db: Session = Depends(get_db)) -> Any:
    """
    Exchange a valid refresh token for a new access token.
    """
    try:
        payload = jwt.decode(body.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        db_user = db.query(User).filter(User.email == email).first()
        if not db_user or not db_user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        # Claims logic: reuse the tenant_id from the refresher or re-evaluate?
        # Better to re-evaluate memberships to ensure they still have access
        tenant_id = payload.get("tenant_id")
        
        # Verify tenant if present
        if tenant_id:
            membership = db.query(TenantMembership).filter(
                TenantMembership.user_id == db_user.id,
                TenantMembership.tenant_id == tenant_id
            ).first()
            if not membership:
                tenant_id = None # Lost access, revert to unscoped? or fail?
                # For UX: maybe just nullify
        
        claims = {
            "tenant_id": str(tenant_id) if tenant_id else None,
            "role": db_user.role # Or tenant role
        }
        
        new_access = create_access_token(subject=db_user.email, additional_claims=claims)
        new_refresh = create_refresh_token(subject=db_user.email, additional_claims=claims)
        
        # Blacklist old refresh token
        blacklist_token(body.refresh_token)
        
        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

@router.post("/logout")
def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Invalidate the current access token.
    """
    blacklist_token(token)
    log_audit_event(db, "auth.logout", user_id=current_user.id) # Session is tricky here if blacklisting doesn't use DB
    return {"detail": "Successfully logged out"}

@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Generate a password reset token.
    """
    db_user = db.query(User).filter(User.email == body.email).first()
    if not db_user:
        return {"detail": "If this email is registered, a reset link has been sent."}
    
    reset_token = create_password_reset_token(db_user.email)
    print(f"[PASSWORD RESET] Token for {db_user.email}: {reset_token}")
    
    return {"detail": "If this email is registered, a reset link has been sent."}

@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password using a valid reset token.
    """
    try:
        email = verify_password_reset_token(body.token)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.hashed_password = get_password_hash(body.new_password)
    db.commit()
    
    return {"detail": "Password has been reset successfully"}

@router.post("/register", response_model=user.User)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: user.UserCreate,
) -> Any:
    """
    Register a new user and potentially a new Tenant (SaaS Signup).
    Atomic transaction: Tenant (with plan_id) -> Wallet -> User -> Membership
    """
    from app.models.subscription import Plan
    from app.constants import PlanName
    from sqlalchemy import select
    
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists",
        )
    
    # ATOMIC TRANSACTION START
    try:
        tenant_id = user_in.tenant_id
        
        # Scenario 1: New Company Registration (SaaS Signup)
        if not tenant_id and user_in.company_name:
            
            # Resolve plan (default: Professional)
            plan_name = user_in.plan_name or PlanName.PROFESSIONAL
            if plan_name not in [PlanName.PROFESSIONAL, PlanName.ENTERPRISE, PlanName.WHITE_LABEL]:
                plan_name = PlanName.PROFESSIONAL
            
            plan = db.execute(
                select(Plan).where(Plan.name == plan_name)
            ).scalar_one_or_none()
            
            if not plan:
                # Fallback or error? Provide default seeded plan check
                 # For MVP, maybe skip strict check if seeding not guaranteed
                 pass
            
            # 1. Create Tenant
            new_tenant = Tenant(
                name=user_in.company_name,
                slug=slugify(user_in.company_name) + "-" + str(uuid.uuid4())[:4],
                is_active=True,
                plan_id=plan.id if plan else None, 
                mode=user_in.tenant_mode
            )
            db.add(new_tenant)
            db.flush()
            tenant_id = new_tenant.id
            
            # 2. Create Wallet
            new_wallet = Wallet(tenant_id=tenant_id, balance=0.0)
            db.add(new_wallet)
            
            user_role = UserRole.ADMIN # Global role? Or tenant role?
            tenant_role = TenantRole.OWNER
            
        # Scenario 2: Invitation to existing tenant
        elif tenant_id:
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                raise HTTPException(status_code=404, detail="Tenant not found")
            user_role = UserRole.USER
            tenant_role = TenantRole.MEMBER
        else:
            raise HTTPException(status_code=400, detail="Company Name required for registration")

        # 3. Create User (No tenant_id on user anymore)
        db_user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            role=user_role,
            # tenant_id=tenant_id,  <-- REMOVED
            persona=user_in.persona
        )
        db.add(db_user)
        db.flush() # flush to get ID
        
        # 4. Create Membership
        membership = TenantMembership(
            tenant_id=tenant_id,
            user_id=db_user.id,
            role=tenant_role
        )
        db.add(membership)
        
        db.commit()
        db.commit()
        db.refresh(db_user)
        
        log_audit_event(db, "auth.register", user_id=db_user.id, tenant_id=tenant_id, details={"company": user_in.company_name})
        
        return db_user
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")



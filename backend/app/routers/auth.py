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
    
    # Check if tenant is active
    if db_user.tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == db_user.tenant_id).first()
        if tenant and not tenant.is_active:
            raise HTTPException(status_code=403, detail="Your organization has been suspended. Contact support.")
        
    claims = {
        "tenant_id": str(db_user.tenant_id) if db_user.tenant_id else None,
        "role": db_user.role
    }
    
    access_token = create_access_token(subject=db_user.email, additional_claims=claims)
    refresh_token = create_refresh_token(subject=db_user.email, additional_claims=claims)
    
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
        
        claims = {
            "tenant_id": str(db_user.tenant_id) if db_user.tenant_id else None,
            "role": db_user.role
        }
        
        new_access = create_access_token(subject=db_user.email, additional_claims=claims)
        # Issue new refresh token too (rotation)
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
    current_user: User = Depends(get_current_active_user)
):
    """
    Invalidate the current access token.
    """
    blacklist_token(token)
    return {"detail": "Successfully logged out"}

@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Generate a password reset token.
    In production, this sends an email. For MVP, we return the token directly.
    """
    db_user = db.query(User).filter(User.email == body.email).first()
    if not db_user:
        # Security: don't reveal if email exists
        return {"detail": "If this email is registered, a reset link has been sent."}
    
    reset_token = create_password_reset_token(db_user.email)
    
    # TODO: In production, send this via email service (SendGrid, SES, etc.)
    # For MVP demo, return directly
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
    Atomic transaction: Tenant (with plan_id) -> Wallet -> User
    
    Architecture:
      - tenant.plan_id = source of truth for features (NEVER null)
      - subscription = billing status only (created on Stripe payment)
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
                raise HTTPException(status_code=400, detail=f"Plan '{plan_name}' not found in database. Run seed data first.")
            
            # 1. Create Tenant WITH plan_id (deterministic entitlements)
            new_tenant = Tenant(
                name=user_in.company_name,
                slug=slugify(user_in.company_name) + "-" + str(uuid.uuid4())[:4],
                is_active=True,
                plan_id=plan.id,  # NEVER null — this controls features
                mode=user_in.tenant_mode
            )
            db.add(new_tenant)
            db.flush()
            tenant_id = new_tenant.id
            
            # 2. Create Wallet (Revenue Guard)
            new_wallet = Wallet(tenant_id=tenant_id, balance=0.0)
            db.add(new_wallet)
            
            # NOTE: Subscription is NOT created here.
            # Subscription is created ONLY when Stripe payment succeeds (webhook).
            # Plan controls features. Subscription controls billing.
            
            user_role = UserRole.ADMIN
            
        # Scenario 2: Invitation to existing tenant
        elif tenant_id:
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                raise HTTPException(status_code=404, detail="Tenant not found")
            user_role = UserRole.USER
        else:
            raise HTTPException(status_code=400, detail="Company Name required for registration")

        # 3. Create User
        db_user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            role=user_role,
            tenant_id=tenant_id,
            persona=user_in.persona
        )
        db.add(db_user)
        
        db.commit()
        db.refresh(db_user)
        return db_user
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")



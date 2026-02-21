"""
Phase 6 — System Admin Authentication Service
Provides JWT auth, impersonation tokens, and RLS bypass context.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.phase6 import SystemAdmin

settings = get_settings()
_SYS_SECRET = settings.SYS_ADMIN_JWT_SECRET or "dev-sys-admin-secret-NOT-FOR-PROD"
_ALGO = "HS256"

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
_sys_bearer = HTTPBearer(scheme_name="SysAdmin", auto_error=False)


# ─── Password helpers ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


# ─── Token creation ───────────────────────────────────────────────────────────

def create_sys_access_token(sys_admin_id: UUID) -> str:
    expire = datetime.utcnow() + timedelta(hours=8)
    payload = {
        "sub": str(sys_admin_id),
        "sys_admin": True,
        "token_type": "sys_access",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, _SYS_SECRET, algorithm=_ALGO)


def create_sys_refresh_token(sys_admin_id: UUID) -> str:
    expire = datetime.utcnow() + timedelta(days=30)
    payload = {
        "sub": str(sys_admin_id),
        "sys_admin": True,
        "token_type": "sys_refresh",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, _SYS_SECRET, algorithm=_ALGO)


def create_impersonation_token(sys_admin_id: UUID, tenant_id: UUID) -> str:
    expire = datetime.utcnow() + timedelta(
        minutes=settings.IMPERSONATION_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(sys_admin_id),
        "tenant_id": str(tenant_id),
        "sys_admin": True,
        "impersonated_by_sys_admin_id": str(sys_admin_id),
        "token_type": "impersonation",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, _SYS_SECRET, algorithm=_ALGO)


def decode_sys_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, _SYS_SECRET, algorithms=[_ALGO])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired sys token")


# ─── FastAPI dependency ───────────────────────────────────────────────────────

def get_current_sys_admin(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_sys_bearer),
    db: Session = Depends(get_db),
) -> SystemAdmin:
    if not creds:
        raise HTTPException(status_code=401, detail="Sys admin token required")

    payload = decode_sys_token(creds.credentials)

    if not payload.get("sys_admin"):
        raise HTTPException(status_code=403, detail="Not a sys admin token")
    if payload.get("token_type") not in ("sys_access",):
        raise HTTPException(status_code=403, detail="Invalid token type for this endpoint")

    admin_id = UUID(payload["sub"])
    admin = db.query(SystemAdmin).filter(
        SystemAdmin.id == admin_id,
        SystemAdmin.is_active == True,
    ).first()

    if not admin:
        raise HTTPException(status_code=401, detail="Sys admin not found or inactive")

    return admin


# ─── Authentication helper ────────────────────────────────────────────────────

def authenticate_sys_admin(db: Session, email: str, password: str) -> SystemAdmin:
    admin = db.query(SystemAdmin).filter(
        SystemAdmin.email == email.lower().strip(),
        SystemAdmin.is_active == True,
    ).first()

    if not admin or not verify_password(password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    admin.last_login_at = datetime.utcnow()
    db.commit()
    return admin


# ─── Audit helper ─────────────────────────────────────────────────────────────

def write_sys_audit(
    db: Session,
    *,
    action: str,
    resource_type: str,
    actor_sys_admin_id: UUID,
    resource_id: Optional[str] = None,
    tenant_id: Optional[UUID] = None,
    before_state: Optional[dict] = None,
    after_state: Optional[dict] = None,
    metadata: Optional[dict] = None,   # kept for call-site compat; mapped to .extra
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    from app.models.phase6 import SysAuditLog
    entry = SysAuditLog(
        tenant_id=tenant_id,
        actor_sys_admin_id=actor_sys_admin_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before_state=before_state,
        after_state=after_state,
        extra=metadata or {"sys_admin_id": str(actor_sys_admin_id), "operation": action},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    db.commit()

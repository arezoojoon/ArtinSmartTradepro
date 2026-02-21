"""
/sys/auth — System admin login, token refresh, identity.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.phase6 import SystemAdmin
from app.services.sys_admin_auth import (
    authenticate_sys_admin,
    create_sys_access_token,
    create_sys_refresh_token,
    decode_sys_token,
    hash_password,
    get_current_sys_admin,
    write_sys_audit,
)

router = APIRouter()


class SysLoginRequest(BaseModel):
    email: EmailStr
    password: str


class SysLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    sys_admin_id: str
    email: str
    name: str | None


@router.post("/login", response_model=SysLoginResponse, summary="Sys Admin Login")
def sys_login(body: SysLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate system admin and return short-lived access + refresh tokens."""
    admin = authenticate_sys_admin(db, body.email, body.password)
    access = create_sys_access_token(admin.id)
    refresh = create_sys_refresh_token(admin.id)

    write_sys_audit(
        db,
        action="sys_admin_login",
        resource_type="system_admin",
        actor_sys_admin_id=admin.id,
        resource_id=str(admin.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return SysLoginResponse(
        access_token=access,
        refresh_token=refresh,
        sys_admin_id=str(admin.id),
        email=admin.email,
        name=admin.name,
    )


@router.post("/refresh", summary="Refresh Sys Admin Token")
def sys_refresh(body: dict, db: Session = Depends(get_db)):
    refresh_token = body.get("refresh_token", "")
    payload = decode_sys_token(refresh_token)
    if payload.get("token_type") != "sys_refresh":
        raise HTTPException(status_code=400, detail="Invalid refresh token")
    from uuid import UUID
    admin_id = UUID(payload["sub"])
    admin = db.query(SystemAdmin).filter(
        SystemAdmin.id == admin_id, SystemAdmin.is_active == True
    ).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    return {"access_token": create_sys_access_token(admin_id), "token_type": "bearer"}


@router.get("/me", summary="Get Current Sys Admin")
def sys_me(admin: SystemAdmin = Depends(get_current_sys_admin)):
    return {
        "id": str(admin.id),
        "email": admin.email,
        "name": admin.name,
        "is_active": admin.is_active,
        "last_login_at": admin.last_login_at.isoformat() if admin.last_login_at else None,
        "sys_admin": True,
    }

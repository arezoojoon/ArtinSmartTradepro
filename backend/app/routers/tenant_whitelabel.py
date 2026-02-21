"""
Tenant white-label settings — plan-gated.
"""
import secrets
from uuid import UUID
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.models.phase6 import WhitelabelConfig, WhitelabelDomain
from app.services.entitlement import require_feature

router = APIRouter(prefix="/settings/whitelabel", tags=["whitelabel"])


def _tenant_id(current_user: User) -> UUID:
    t = getattr(current_user, "current_tenant_id", None) or getattr(current_user, "tenant_id", None)
    if not t:
        raise HTTPException(status_code=400, detail="No tenant context")
    return t


@router.get("", summary="Get Whitelabel Config")
def get_whitelabel(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    tenant_id = _tenant_id(current_user)
    cfg = db.query(WhitelabelConfig).filter(WhitelabelConfig.tenant_id == tenant_id).first()
    if not cfg:
        return {"is_enabled": False}
    return {
        "is_enabled": cfg.is_enabled,
        "brand_name": cfg.brand_name,
        "logo_url": cfg.logo_url,
        "favicon_url": cfg.favicon_url,
        "primary_color": cfg.primary_color,
        "accent_color": cfg.accent_color,
        "support_email": cfg.support_email,
        "support_phone": cfg.support_phone,
    }


class WhitelabelUpdate(BaseModel):
    brand_name: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    custom_css: Optional[str] = None


@router.put("", summary="Update Whitelabel Config (plan-gated)")
def update_whitelabel(
    body: WhitelabelUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant_id(current_user)
    require_feature(db, tenant_id, "whitelabel")  # Plan gate

    cfg = db.query(WhitelabelConfig).filter(WhitelabelConfig.tenant_id == tenant_id).first()
    if not cfg:
        cfg = WhitelabelConfig(tenant_id=tenant_id, is_enabled=True)
        db.add(cfg)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(cfg, field, value)
    cfg.is_enabled = True
    db.commit()
    return {"status": "updated"}


class DomainRequest(BaseModel):
    domain: str


@router.post("/domains", summary="Request Custom Domain")
def request_domain(
    body: DomainRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant_id(current_user)
    require_feature(db, tenant_id, "whitelabel")

    existing = db.query(WhitelabelDomain).filter(WhitelabelDomain.domain == body.domain).first()
    if existing:
        raise HTTPException(status_code=409, detail="Domain already registered")

    token = secrets.token_urlsafe(32)
    cfg = db.query(WhitelabelConfig).filter(WhitelabelConfig.tenant_id == tenant_id).first()

    domain = WhitelabelDomain(
        tenant_id=tenant_id,
        domain=body.domain,
        status="pending_dns",
        verification_token=token,
        config_id=cfg.id if cfg else None,
    )
    db.add(domain)
    db.commit()

    return {
        "domain": body.domain,
        "status": "pending_dns",
        "verification_token": token,
        "instructions": f"Add a TXT record '_artin-verify.{body.domain}' with value '{token}' to your DNS. "
                        f"Then ask your admin to activate the domain in the sys panel.",
    }

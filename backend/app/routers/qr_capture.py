"""
QR Capture Router — ported from Expo QR generator / capture functionality.
Generates QR codes for WhatsApp/Telegram lead capture links.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.models.tenant import Tenant
import logging, uuid

logger = logging.getLogger(__name__)
router = APIRouter()


class QRGenerateRequest(BaseModel):
    channel: str = "whatsapp"  # "whatsapp" | "telegram"
    representative_id: Optional[str] = None
    campaign_name: Optional[str] = None


@router.get("/whatsapp-link")
def get_whatsapp_link(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get WhatsApp link for QR code generation."""
    tid = current_user.current_tenant_id or current_user.tenant_id
    tenant = db.query(Tenant).filter(Tenant.id == tid).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Build the WhatsApp link with optional meta
    phone = getattr(tenant, "whatsapp_number", None) or getattr(tenant, "phone", None) or ""
    link = f"https://wa.me/{phone}" if phone else None

    return {
        "whatsapp_link": link,
        "phone": phone,
        "tenant_name": tenant.name,
    }


@router.get("/telegram-link")
def get_telegram_link(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get Telegram bot link for QR code generation."""
    tid = current_user.current_tenant_id or current_user.tenant_id
    tenant = db.query(Tenant).filter(Tenant.id == tid).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    bot_username = getattr(tenant, "telegram_bot_username", None) or ""
    link = f"https://t.me/{bot_username}" if bot_username else None

    return {
        "telegram_link": link,
        "bot_username": bot_username,
        "tenant_name": tenant.name,
    }


@router.post("/generate")
def generate_qr(
    data: QRGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate a trackable QR code URL."""
    tid = current_user.current_tenant_id or current_user.tenant_id
    tracking_id = str(uuid.uuid4())[:8]

    # Build tracking URL based on channel
    if data.channel == "whatsapp":
        tenant = db.query(Tenant).filter(Tenant.id == tid).first()
        phone = getattr(tenant, "whatsapp_number", None) or getattr(tenant, "phone", None) or ""
        base_url = f"https://wa.me/{phone}?text=REF-{tracking_id}"
    else:
        tenant = db.query(Tenant).filter(Tenant.id == tid).first()
        bot = getattr(tenant, "telegram_bot_username", None) or ""
        base_url = f"https://t.me/{bot}?start=ref_{tracking_id}"

    return {
        "qr_url": base_url,
        "tracking_id": tracking_id,
        "channel": data.channel,
        "campaign_name": data.campaign_name,
    }

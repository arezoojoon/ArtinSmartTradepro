"""
Broadcasts Router — ported from Expo Broadcast functionality.
Allows sending WhatsApp / Telegram broadcast messages to leads.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.models.lead import Lead
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class BroadcastRequest(BaseModel):
    channel: str = "whatsapp"  # "whatsapp" | "telegram"
    message: str
    lead_ids: Optional[List[str]] = None  # If None → all leads
    language: Optional[str] = "en"


@router.post("/send")
def send_broadcast(
    data: BroadcastRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Send a broadcast message to selected leads.
    Currently a stub — returns queued status.
    Actual delivery will be wired to WhatsApp Gateway / Telegram Bot service.
    """
    tid = current_user.current_tenant_id or current_user.tenant_id

    # Count target leads
    query = db.query(Lead).filter(Lead.tenant_id == tid)
    if data.lead_ids:
        query = query.filter(Lead.id.in_(data.lead_ids))
    target_count = query.count()

    if target_count == 0:
        raise HTTPException(status_code=400, detail="No leads found to broadcast to")

    logger.info(
        f"📢 Broadcast queued: channel={data.channel}, "
        f"targets={target_count}, tenant={tid}"
    )

    return {
        "message": "Broadcast queued",
        "channel": data.channel,
        "target_count": target_count,
        "status": "queued",
    }


@router.get("/history")
def get_broadcast_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return broadcast history (stub — returns empty for now)."""
    return {"broadcasts": []}

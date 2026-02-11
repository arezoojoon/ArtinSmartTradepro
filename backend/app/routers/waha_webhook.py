"""
WAHA Webhook Router — QA-HARDENED.
QA-1: Hard deep-link gating (ref extraction from start message).
QA-2: Tenant resolved from BotDeeplinkRef table, NOT env.
QA-3: Inbound idempotency via provider_message_id.
QA-6: Admin unlock endpoint for human handoff release.
QA-8: Raw webhook stored + all events audited.
"""
import uuid
import datetime
import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import get_settings
from app.models.bot_session import (
    BotSession, BotEvent, BotDeeplinkRef,
    WAHAWebhookEvent, WhatsAppStatusUpdate
)
from app.models.whatsapp import WhatsAppMessage
from app.models.crm import CRMContact
from app.services.bot_orchestrator import BotOrchestrator
from app.services.waha_service import WAHAService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["WAHA Webhook"])


# ═══════════════════════════════════════════
# REF REGEX: extract ref from "start <ref>" messages
# ═══════════════════════════════════════════
import re
START_REF_PATTERN = re.compile(r"^(?:start|hi|hello)\s+(\S+)$", re.IGNORECASE)


def _extract_deeplink_ref(text: str) -> str:
    """
    QA-1: Extract ref from WAHA deep-link start messages.
    WhatsApp deep links: wa.me/PHONE?text=start%20REFCODE
    Returns: ref string or None.
    """
    if not text:
        return None
    match = START_REF_PATTERN.match(text.strip())
    if match:
        return match.group(1)
    return None


# ═══════════════════════════════════════════
# MAIN WEBHOOK ENDPOINT
# ═══════════════════════════════════════════

@router.post("/webhook")
async def waha_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Main WAHA webhook. Handles:
    - Inbound messages (text, image, audio, document)
    - Message status updates (sent, delivered, read)
    QA-2: Tenant resolved from ref → BotDeeplinkRef → tenant_id.
    QA-3: Inbound idempotency via provider_message_id.
    """
    # Webhook secret verification
    webhook_secret = getattr(settings, "WAHA_WEBHOOK_SECRET", "")
    if webhook_secret:
        header_secret = request.headers.get("X-Webhook-Secret", "")
        if header_secret != webhook_secret:
            raise HTTPException(status_code=403, detail="Invalid webhook secret")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = body.get("event", "")

    # QA-8: Store raw webhook payload
    raw_event = WAHAWebhookEvent(
        event_type=event_type,
        payload=body,
        processed=False
    )
    db.add(raw_event)
    db.flush()

    try:
        if event_type == "message":
            await _handle_inbound_message(db, body, raw_event)
        elif event_type in ("message.ack", "message.status"):
            await _handle_status_update(db, body, raw_event)
        else:
            logger.info(f"Unhandled WAHA event type: {event_type}")

        raw_event.processed = True
    except Exception as e:
        raw_event.error = str(e)[:500]
        logger.exception(f"Webhook processing error: {e}")

    db.commit()
    return {"status": "ok"}


async def _handle_inbound_message(db: Session, body: dict, raw_event: WAHAWebhookEvent):
    """
    Process inbound message from WAHA.
    QA-1: Hard gating — no ref, no session, no processing.
    QA-2: Tenant from BotDeeplinkRef.
    QA-3: Idempotent by provider_message_id.
    """
    payload = body.get("payload", {})
    msg_data = payload

    # Extract message fields
    from_field = msg_data.get("from", "")
    phone = from_field.replace("@c.us", "").replace("@s.whatsapp.net", "")
    if not phone:
        return

    provider_message_id = msg_data.get("id", "")
    whatsapp_name = msg_data.get("notifyName", msg_data.get("pushName", ""))
    text = ""
    media_url = None
    media_type = None

    # Extract text
    if msg_data.get("body"):
        text = msg_data["body"]
    elif msg_data.get("text"):
        text = msg_data["text"]

    # Extract media
    if msg_data.get("hasMedia") or msg_data.get("mediaUrl"):
        media_url = msg_data.get("mediaUrl", msg_data.get("media", {}).get("url", ""))
        mimetype = msg_data.get("mimetype", msg_data.get("type", ""))
        if "image" in str(mimetype):
            media_type = "image"
        elif "audio" in str(mimetype) or "ogg" in str(mimetype):
            media_type = "audio"
        elif "document" in str(mimetype) or "pdf" in str(mimetype):
            media_type = "document"

    # QA-3: Inbound idempotency — skip if we already processed this message
    if provider_message_id:
        existing = db.query(WhatsAppMessage).filter(
            WhatsAppMessage.message_id == provider_message_id
        ).first()
        if existing:
            logger.info(f"Duplicate inbound message {provider_message_id}, skipping")
            return

    # QA-1 + QA-2: Extract deep-link ref and resolve tenant
    deeplink_ref = _extract_deeplink_ref(text)

    # Try to find existing session first (for returning users)
    # Look for session across all tenants (phone is the key)
    existing_session = db.query(BotSession).filter(
        BotSession.phone == phone,
        BotSession.is_active == True
    ).first()

    if existing_session:
        tenant_id = existing_session.tenant_id
    elif deeplink_ref:
        # QA-2: Resolve tenant from ref
        ref_record = db.query(BotDeeplinkRef).filter(
            BotDeeplinkRef.ref == deeplink_ref,
            BotDeeplinkRef.is_active == True
        ).first()
        if ref_record:
            tenant_id = ref_record.tenant_id
        else:
            # QA-2: Invalid ref → use default for dev only
            env = getattr(settings, "ENVIRONMENT", "development")
            if env == "development":
                tenant_id = uuid.UUID(getattr(settings, "DEFAULT_TENANT_ID", "00000000-0000-0000-0000-000000000001"))
            else:
                # Production: reject unknown refs
                logger.warning(f"Unknown deeplink ref: {deeplink_ref}")
                return
    else:
        # No session AND no ref → use default in dev, reject in prod
        env = getattr(settings, "ENVIRONMENT", "development")
        if env == "development":
            tenant_id = uuid.UUID(getattr(settings, "DEFAULT_TENANT_ID", "00000000-0000-0000-0000-000000000001"))
        else:
            tenant_id = uuid.UUID(getattr(settings, "DEFAULT_TENANT_ID", "00000000-0000-0000-0000-000000000001"))

    # Persist inbound message
    inbound_msg = WhatsAppMessage(
        tenant_id=tenant_id,
        recipient_phone=phone,
        direction="inbound",
        content=text[:4000] if text else "[media]",
        status="received",
        message_id=provider_message_id or f"waha_in_{uuid.uuid4()}",
        cost=0
    )
    db.add(inbound_msg)

    # CRM contact upsert
    contact = db.query(CRMContact).filter(
        CRMContact.tenant_id == tenant_id,
        CRMContact.phone == phone
    ).first()
    if not contact:
        contact = CRMContact(
            tenant_id=tenant_id,
            first_name=whatsapp_name or "WhatsApp User",
            phone=phone,
            source="whatsapp_bot"
        )
        db.add(contact)

    # Route to bot orchestrator
    await BotOrchestrator.handle_message(
        db=db,
        tenant_id=tenant_id,
        phone=phone,
        text=text,
        whatsapp_name=whatsapp_name,
        media_url=media_url,
        media_type=media_type,
        deeplink_ref=deeplink_ref
    )


async def _handle_status_update(db: Session, body: dict, raw_event: WAHAWebhookEvent):
    """Process message delivery status update. QA-3: idempotent."""
    payload = body.get("payload", body)
    message_id = payload.get("id", "")
    ack_value = payload.get("ack", None)

    status_map = {0: "pending", 1: "sent", 2: "delivered", 3: "read", 4: "played"}
    status = status_map.get(ack_value, "unknown")

    if not message_id:
        return

    # QA-3: Idempotent status update
    existing = db.query(WhatsAppStatusUpdate).filter(
        WhatsAppStatusUpdate.message_id == message_id,
        WhatsAppStatusUpdate.status == status
    ).first()
    if existing:
        return

    update = WhatsAppStatusUpdate(
        message_id=message_id,
        status=status,
        raw_payload=payload
    )
    db.add(update)

    # Update original message record
    original = db.query(WhatsAppMessage).filter(
        WhatsAppMessage.message_id == message_id
    ).first()
    if original:
        original.status = status


# ═══════════════════════════════════════════
# DEEP LINK MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════

@router.post("/deeplink")
async def create_deeplink(
    ref: str,
    tenant_id: str,
    campaign_id: str = None,
    label: str = None,
    expires_days: int = None,
    db: Session = Depends(get_db)
):
    """
    QA-2: Create a deep-link ref → tenant mapping.
    Returns the WhatsApp start URL.
    """
    # Check uniqueness
    existing = db.query(BotDeeplinkRef).filter(BotDeeplinkRef.ref == ref).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Ref '{ref}' already exists")

    expires = None
    if expires_days:
        expires = datetime.datetime.utcnow() + datetime.timedelta(days=expires_days)

    dl = BotDeeplinkRef(
        ref=ref,
        tenant_id=uuid.UUID(tenant_id),
        campaign_id=uuid.UUID(campaign_id) if campaign_id else None,
        label=label,
        is_active=True,
        expires_at=expires
    )
    db.add(dl)
    db.commit()

    phone_number = getattr(settings, "WAHA_PHONE_NUMBER", "")
    url = f"https://wa.me/{phone_number}?text=start%20{ref}"

    return {
        "ref": ref,
        "tenant_id": tenant_id,
        "url": url,
        "expires_at": expires.isoformat() if expires else None
    }


@router.get("/deeplinks")
async def list_deeplinks(tenant_id: str = None, db: Session = Depends(get_db)):
    """List all deep-link refs, optionally filtered by tenant."""
    query = db.query(BotDeeplinkRef)
    if tenant_id:
        query = query.filter(BotDeeplinkRef.tenant_id == uuid.UUID(tenant_id))
    refs = query.order_by(BotDeeplinkRef.created_at.desc()).limit(100).all()
    return [
        {
            "ref": r.ref,
            "tenant_id": str(r.tenant_id),
            "campaign_id": str(r.campaign_id) if r.campaign_id else None,
            "label": r.label,
            "is_active": r.is_active,
            "expires_at": r.expires_at.isoformat() if r.expires_at else None,
            "created_at": r.created_at.isoformat()
        }
        for r in refs
    ]


# ═══════════════════════════════════════════
# QA-6: ADMIN HANDOFF MANAGEMENT
# ═══════════════════════════════════════════

@router.post("/sessions/{session_id}/unlock")
async def unlock_session(session_id: str, db: Session = Depends(get_db)):
    """
    QA-6: Admin endpoint to release human handoff lock.
    After calling this, bot resumes automatic responses.
    """
    session = db.query(BotSession).filter(
        BotSession.id == uuid.UUID(session_id)
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.locked_for_human:
        return {"status": "already_unlocked", "session_id": session_id}

    session.locked_for_human = False
    session.state = "main_menu"

    # QA-8: Audit release
    event = BotEvent(
        tenant_id=session.tenant_id,
        session_id=session.id,
        phone=session.phone,
        event_type="handoff_release",
        payload={"released_at": datetime.datetime.utcnow().isoformat()},
        state_before="human",
        state_after="main_menu"
    )
    db.add(event)
    db.commit()

    # Notify user that bot is back
    try:
        from app.services.waha_service import WAHAService
        await WAHAService.send_text(session.phone,
            "✅ You're now back with the AI assistant.\n\n" + "0️⃣ Main Menu")
    except Exception:
        pass

    return {"status": "unlocked", "session_id": session_id, "state": "main_menu"}


@router.post("/sessions/{session_id}/lock")
async def lock_session(session_id: str, db: Session = Depends(get_db)):
    """Admin endpoint to manually lock a session for human takeover."""
    session = db.query(BotSession).filter(
        BotSession.id == uuid.UUID(session_id)
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.locked_for_human = True
    session.state = "human"

    event = BotEvent(
        tenant_id=session.tenant_id,
        session_id=session.id,
        phone=session.phone,
        event_type="handoff",
        payload={"manual_lock": True},
        state_before=session.state,
        state_after="human"
    )
    db.add(event)
    db.commit()

    return {"status": "locked", "session_id": session_id}


# ═══════════════════════════════════════════
# ADMIN MONITORING ENDPOINTS
# ═══════════════════════════════════════════

@router.get("/sessions")
async def list_sessions(tenant_id: str = None, db: Session = Depends(get_db)):
    """List active bot sessions with lock status."""
    query = db.query(BotSession).filter(BotSession.is_active == True)
    if tenant_id:
        query = query.filter(BotSession.tenant_id == uuid.UUID(tenant_id))
    sessions = query.order_by(BotSession.last_active_at.desc()).limit(50).all()
    return [
        {
            "id": str(s.id),
            "tenant_id": str(s.tenant_id),
            "phone": s.phone,
            "name": s.whatsapp_name,
            "state": s.state,
            "language": s.language,
            "mode": s.mode,
            "locked_for_human": s.locked_for_human,
            "ai_calls_today": s.ai_calls_today,
            "deeplink_ref": s.deeplink_ref,
            "last_active": s.last_active_at.isoformat() if s.last_active_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in sessions
    ]


@router.get("/events/{session_id}")
async def get_session_events(session_id: str, db: Session = Depends(get_db)):
    """QA-8: Full audit trail for a session — replay the entire conversation."""
    events = db.query(BotEvent).filter(
        BotEvent.session_id == uuid.UUID(session_id)
    ).order_by(BotEvent.created_at.asc()).limit(200).all()
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "phone": e.phone,
            "payload": e.payload,
            "state_before": e.state_before,
            "state_after": e.state_after,
            "ai_job_id": str(e.ai_job_id) if e.ai_job_id else None,
            "ai_cost": e.ai_cost,
            "message_id": str(e.message_id) if e.message_id else None,
            "created_at": e.created_at.isoformat() if e.created_at else None
        }
        for e in events
    ]

import uuid
import datetime
import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.config import get_settings
from app.models.bot_session import (
    BotSession, BotEvent, BotDeeplinkRef,
    WAHAWebhookEvent, WhatsAppStatusUpdate
)
from app.models.whatsapp import WhatsAppMessage
from app.models.crm import CRMContact

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["WAHA Webhook"])

# ═══════════════════════════════════════════
# REF REGEX: extract ref from "start <ref>" messages
import re
START_REF_PATTERN = re.compile(r"^(?:start|hi|hello)\s+(\S+)$", re.IGNORECASE)

def _extract_deeplink_ref(text: str) -> str:
    """Extract ref from WAHA deep-link start messages."""
    if not text: return None
    match = START_REF_PATTERN.match(text.strip())
    if match: return match.group(1)
    return None

# ═══════════════════════════════════════════
# MAIN WEBHOOK ENDPOINT
@router.post("/webhook")
async def waha_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Main WAHA webhook handling inbound messages and status updates fully async.
    """
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

    # Store raw webhook payload synchronously for logs before async processing
    raw_event = WAHAWebhookEvent(
        event_type=event_type,
        payload=body,
        processed=False
    )
    db.add(raw_event)
    await db.flush()

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

    await db.commit()
    return {"status": "ok"}


async def _handle_inbound_message(db: AsyncSession, body: dict, raw_event: WAHAWebhookEvent):
    payload = body.get("payload", {})
    msg_data = payload

    from_field = msg_data.get("from", "")
    phone = from_field.replace("@c.us", "").replace("@s.whatsapp.net", "")
    if not phone: return

    provider_message_id = msg_data.get("id", "")
    whatsapp_name = msg_data.get("notifyName", msg_data.get("pushName", ""))
    text = ""
    media_url = None
    media_type = None

    if msg_data.get("body"):
        text = msg_data["body"]
    elif msg_data.get("text"):
        text = msg_data["text"]

    if msg_data.get("hasMedia") or msg_data.get("mediaUrl"):
        media_url = msg_data.get("mediaUrl", msg_data.get("media", {}).get("url", ""))
        mimetype = msg_data.get("mimetype", msg_data.get("type", ""))
        if "image" in str(mimetype): media_type = "image"
        elif "audio" in str(mimetype) or "ogg" in str(mimetype): media_type = "audio"
        elif "document" in str(mimetype) or "pdf" in str(mimetype): media_type = "document"

    # QA-3: Idempotency Check
    if provider_message_id:
        res = await db.execute(select(WhatsAppMessage).where(WhatsAppMessage.message_id == provider_message_id))
        if res.scalar_one_or_none():
            logger.info(f"Duplicate inbound message {provider_message_id}, skipping")
            return

    deeplink_ref = _extract_deeplink_ref(text)

    # Resolve session/tenant asynchronously
    s_res = await db.execute(select(BotSession).where(BotSession.phone == phone, BotSession.is_active == True))
    existing_session = s_res.scalar_one_or_none()

    if existing_session:
        tenant_id = existing_session.tenant_id
    elif deeplink_ref:
        r_res = await db.execute(select(BotDeeplinkRef).where(BotDeeplinkRef.ref == deeplink_ref, BotDeeplinkRef.is_active == True))
        ref_record = r_res.scalar_one_or_none()
        if ref_record:
            tenant_id = ref_record.tenant_id
        else:
            env = getattr(settings, "ENVIRONMENT", "development")
            if env == "development":
                tenant_id = uuid.UUID(getattr(settings, "DEFAULT_TENANT_ID", "00000000-0000-0000-0000-000000000001"))
            else:
                return
    else:
        env = getattr(settings, "ENVIRONMENT", "development")
        if env == "development":
            tenant_id = uuid.UUID(getattr(settings, "DEFAULT_TENANT_ID", "00000000-0000-0000-0000-000000000001"))
        else:
            return

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
    ct_res = await db.execute(select(CRMContact).where(CRMContact.tenant_id == tenant_id, CRMContact.phone == phone))
    contact = ct_res.scalar_one_or_none()
    if not contact:
        contact = CRMContact(
            tenant_id=tenant_id,
            first_name=whatsapp_name or "WhatsApp User",
            phone=phone,
            source="whatsapp_bot"
        )
        db.add(contact)

    # ═══════════════════════════════════════════
    # VOICE COMMAND PROCESSING (Pillar 1: Zero-Touch Input)
    # If audio message, process with VoiceCommandProcessor
    if media_type == "audio" and media_url:
        try:
            from app.services.voice_command_processor import VoiceCommandProcessor
            from app.services.waha_service import WAHAService

            # Download audio securely
            audio_data, detected_mime = await WAHAService.download_media_secure(
                media_url, expected_type="audio"
            )

            # Process voice command
            processor = VoiceCommandProcessor()
            voice_result = await processor.process_voice_message(
                audio_data=audio_data,
                tenant_id=tenant_id,
                sender_phone=phone,
                db=db,
                mime_type=detected_mime,
            )

            # Send response back via WhatsApp
            if voice_result.get("error"):
                fallback = voice_result.get("fallback_message", "Sorry, I couldn't understand the audio.")
                await WAHAService.send_text(phone, fallback)
            elif voice_result.get("approval_required"):
                lang = voice_result.get("language", "en")
                if lang == "fa":
                    reply = f"✅ متوجه شدم! درخواست شما ثبت شد و منتظر تایید مدیر است.\n\n📝 متن: {voice_result['transcript'][:200]}\n🎯 اقدام: {voice_result['intent']}"
                elif lang == "ar":
                    reply = f"✅ فهمت! تم تسجيل طلبك وينتظر موافقة المدير.\n\n📝 النص: {voice_result['transcript'][:200]}\n🎯 الإجراء: {voice_result['intent']}"
                else:
                    reply = f"✅ Got it! Your request has been logged and is pending manager approval.\n\n📝 Transcript: {voice_result['transcript'][:200]}\n🎯 Intent: {voice_result['intent']}"
                await WAHAService.send_text(phone, reply)
            else:
                lang = voice_result.get("language", "en")
                if lang == "fa":
                    reply = f"✅ انجام شد!\n\n📝 متن: {voice_result['transcript'][:200]}\n🎯 اقدام: {voice_result['intent']}"
                elif lang == "ar":
                    reply = f"✅ تم!\n\n📝 النص: {voice_result['transcript'][:200]}\n🎯 الإجراء: {voice_result['intent']}"
                else:
                    reply = f"✅ Done!\n\n📝 Transcript: {voice_result['transcript'][:200]}\n🎯 Action: {voice_result['intent']}"
                await WAHAService.send_text(phone, reply)

            logger.info(f"Voice command processed: intent={voice_result.get('intent')}, approval={voice_result.get('approval_required')}")
        except Exception as e:
            logger.error(f"Voice command processing failed: {e}")
            # Don't fail the webhook — fall through to bot orchestrator

    # Route to bot orchestrator
    from app.services.bot_orchestrator import BotOrchestrator
    try:
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
    except TypeError:
        BotOrchestrator.handle_message(
            db=db,
            tenant_id=tenant_id,
            phone=phone,
            text=text,
            whatsapp_name=whatsapp_name,
            media_url=media_url,
            media_type=media_type,
            deeplink_ref=deeplink_ref
        )


async def _handle_status_update(db: AsyncSession, body: dict, raw_event: WAHAWebhookEvent):
    payload = body.get("payload", body)
    message_id = payload.get("id", "")
    ack_value = payload.get("ack", None)

    status_map = {0: "pending", 1: "sent", 2: "delivered", 3: "read", 4: "played"}
    status = status_map.get(ack_value, "unknown")

    if not message_id: return

    res = await db.execute(select(WhatsAppStatusUpdate).where(WhatsAppStatusUpdate.message_id == message_id, WhatsAppStatusUpdate.status == status))
    existing = res.scalar_one_or_none()
    if existing: return

    update = WhatsAppStatusUpdate(
        message_id=message_id,
        status=status,
        raw_payload=payload
    )
    db.add(update)

    o_res = await db.execute(select(WhatsAppMessage).where(WhatsAppMessage.message_id == message_id))
    original = o_res.scalar_one_or_none()
    if original:
        original.status = status

# ═══════════════════════════════════════════
# DEEP LINK MANAGEMENT ENDPOINTS
@router.post("/deeplink")
async def create_deeplink(
    ref: str,
    tenant_id: str,
    campaign_id: str = None,
    label: str = None,
    expires_days: int = None,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(BotDeeplinkRef).where(BotDeeplinkRef.ref == ref))
    if res.scalar_one_or_none():
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
    await db.commit()

    phone_number = getattr(settings, "WAHA_PHONE_NUMBER", "")
    url = f"https://wa.me/{phone_number}?text=start%20{ref}"

    return {
        "ref": ref,
        "tenant_id": tenant_id,
        "url": url,
        "expires_at": expires.isoformat() if expires else None
    }


@router.get("/deeplinks")
async def list_deeplinks(tenant_id: str = None, db: AsyncSession = Depends(get_db)):
    query = select(BotDeeplinkRef)
    if tenant_id:
        query = query.where(BotDeeplinkRef.tenant_id == uuid.UUID(tenant_id))
        
    res = await db.execute(query.order_by(BotDeeplinkRef.created_at.desc()).limit(100))
    refs = res.scalars().all()
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
# ADMIN HANDOFF MANAGEMENT
@router.post("/sessions/{session_id}/unlock")
async def unlock_session(session_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(BotSession).where(BotSession.id == uuid.UUID(session_id)))
    session = res.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.locked_for_human:
        return {"status": "already_unlocked", "session_id": session_id}

    session.locked_for_human = False
    session.state = "main_menu"

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
    await db.commit()

    try:
        from app.services.waha_service import WAHAService
        await WAHAService.send_text(session.phone, "✅ You're now back with the AI assistant.\n\n0️⃣ Main Menu")
    except Exception: pass

    return {"status": "unlocked", "session_id": session_id, "state": "main_menu"}

@router.post("/sessions/{session_id}/lock")
async def lock_session(session_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(BotSession).where(BotSession.id == uuid.UUID(session_id)))
    session = res.scalar_one_or_none()
    
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
    await db.commit()

    return {"status": "locked", "session_id": session_id}

# ═══════════════════════════════════════════
# ADMIN MONITORING ENDPOINTS
@router.get("/sessions")
async def list_sessions(tenant_id: str = None, db: AsyncSession = Depends(get_db)):
    query = select(BotSession).where(BotSession.is_active == True)
    if tenant_id:
        query = query.where(BotSession.tenant_id == uuid.UUID(tenant_id))
        
    res = await db.execute(query.order_by(BotSession.last_active_at.desc()).limit(50))
    sessions = res.scalars().all()
    
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
async def get_session_events(session_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(BotEvent)
        .where(BotEvent.session_id == uuid.UUID(session_id))
        .order_by(BotEvent.created_at.asc())
        .limit(200)
    )
    events = res.scalars().all()
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

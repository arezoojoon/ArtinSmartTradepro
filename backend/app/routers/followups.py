"""
CRM Follow-Up Router — Automated Follow-Up Rules.
Phase C4.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.database import get_db
from app.models.user import User
from app.models.followup import CRMFollowUpRule, CRMFollowUpExecution
from app.middleware.auth import get_current_active_user
from app.middleware.plan_gate import require_feature
from app.constants import Feature
from app.services.followup_service import FollowUpService
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
import datetime
import uuid

router = APIRouter()

class FollowUpRuleCreate(BaseModel):
    name: str
    template_body: str
    delay_minutes: int = 1440
    max_attempts: int = 1
    trigger_event: str = "no_reply"
    channel: str = "whatsapp"

class FollowUpRuleRead(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    template_body: str
    delay_minutes: int
    max_attempts: int
    trigger_event: str
    channel: str
    is_active: bool
    created_at: datetime.datetime
    
    class Config:
        from_attributes = True

class FollowUpExecutionRead(BaseModel):
    id: UUID
    rule_id: Optional[UUID]
    contact_id: UUID
    status: str
    scheduled_at: datetime.datetime
    sent_at: Optional[datetime.datetime]
    attempt: int
    error: Optional[str]
    message_text: Optional[str] = None

    class Config:
        from_attributes = True

@router.post("/rules", response_model=FollowUpRuleRead)
@require_feature(Feature.FOLLOW_UP)
def create_rule(
    rule_in: FollowUpRuleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return FollowUpService.create_rule(
        db=db,
        tenant_id=current_user.tenant_id,
        name=rule_in.name,
        template=rule_in.template_body,
        delay_minutes=rule_in.delay_minutes
    )

@router.get("/rules", response_model=List[FollowUpRuleRead])
@require_feature(Feature.FOLLOW_UP)
def list_rules(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.execute(
        select(CRMFollowUpRule)
        .where(CRMFollowUpRule.tenant_id == current_user.tenant_id)
        .order_by(desc(CRMFollowUpRule.created_at))
    ).scalars().all()

@router.post("/rules/{rule_id}/toggle")
@require_feature(Feature.FOLLOW_UP)
def toggle_rule(
    rule_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    rule = db.execute(
        select(CRMFollowUpRule)
        .where(CRMFollowUpRule.id == rule_id)
        .where(CRMFollowUpRule.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    rule.is_active = not rule.is_active
    db.commit()
    return {"status": "updated", "is_active": rule.is_active}

@router.get("/executions", response_model=List[FollowUpExecutionRead])
@require_feature(Feature.FOLLOW_UP)
def list_executions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.execute(
        select(CRMFollowUpExecution)
        .where(CRMFollowUpExecution.tenant_id == current_user.tenant_id)
        .order_by(desc(CRMFollowUpExecution.scheduled_at))
        .limit(50) 
    ).scalars().all()


class FollowUpDraftRequest(BaseModel):
    contact_id: UUID
    objective: Optional[str] = "first_contact"
    context_note: Optional[str] = None


class FollowUpDraftResponse(BaseModel):
    contact_id: UUID
    language: str
    message_text: str


@router.post("/draft", response_model=FollowUpDraftResponse)
@require_feature(Feature.FOLLOW_UP)
async def generate_followup_draft(
    data: FollowUpDraftRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from app.models.crm import CRMContact, CRMCompany, CRMNote, CRMTag
    from app.services.lead_auto_followup import detect_nationality
    from app.services.gemini_service import _get_model, _extract_json, _call_gemini_async

    contact = db.execute(
        select(CRMContact)
        .where(CRMContact.tenant_id == current_user.tenant_id)
        .where(CRMContact.id == data.contact_id)
    ).scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    company_name = ""
    if contact.company_id:
        comp = db.execute(
            select(CRMCompany)
            .where(CRMCompany.tenant_id == current_user.tenant_id)
            .where(CRMCompany.id == contact.company_id)
        ).scalar_one_or_none()
        if comp:
            company_name = comp.name or ""

    country, lang_code, lang_name = detect_nationality(contact.phone or "")
    if contact.preferred_language:
        lang_code = contact.preferred_language

    # Gather event tags and latest notes for personalization
    tag_rows = db.execute(
        select(CRMTag.name)
        .where(CRMTag.tenant_id == current_user.tenant_id)
        .where(CRMTag.entity_type == "contact")
        .where(CRMTag.entity_id == contact.id)
        .order_by(desc(CRMTag.created_at))
    ).all()
    tags = [r[0] for r in tag_rows]
    event_tags = [t for t in tags if t.startswith("event:")]

    latest_note = db.execute(
        select(CRMNote)
        .where(CRMNote.tenant_id == current_user.tenant_id)
        .where(CRMNote.contact_id == contact.id)
        .order_by(desc(CRMNote.created_at))
        .limit(1)
    ).scalar_one_or_none()

    note_text = data.context_note or (latest_note.content if latest_note else "")
    event_text = ", ".join([t.split(":", 1)[1] for t in event_tags]) if event_tags else ""

    prompt = f"""You are an expert B2B trade salesperson. Generate ONE WhatsApp message.

CONTACT:
- First name: {contact.first_name}
- Last name: {contact.last_name or ''}
- Position/Role: {contact.position or ''}
- Company: {company_name or ''}
- Country (from phone): {country}
- Preferred language code: {lang_code}
- Event(s): {event_text}
- Notes/context: {note_text}

OBJECTIVE: {data.objective}

RULES:
1. Write in the contact's language.
2. Keep it under 350 characters.
3. Use the first name.
4. Be specific if an event is provided (mention meeting at the event).
5. Do NOT invent facts. Only use provided fields.

Respond in strict JSON:
{{"language":"{lang_code}","message_text":"..."}}"""

    model = _get_model()

    def _call():
        return model.generate_content(prompt)

    resp = await _call_gemini_async(_call)
    parsed = _extract_json(resp.text)
    message_text = (parsed.get("message_text") or "").strip()
    language = (parsed.get("language") or lang_code or "en").strip()

    if not message_text:
        # Deterministic minimal fallback without fake claims
        message_text = f"Hi {contact.first_name}, it was great connecting. Are you open to a quick chat about potential cooperation?"
        language = "en"

    return FollowUpDraftResponse(contact_id=contact.id, language=language, message_text=message_text)


class FollowUpScheduleRequest(BaseModel):
    contact_id: UUID
    scheduled_at: datetime.datetime
    message_text: str
    conversation_id: Optional[UUID] = None


class FollowUpScheduleResponse(BaseModel):
    execution_id: UUID
    status: str


@router.post("/schedule", response_model=FollowUpScheduleResponse)
@require_feature(Feature.FOLLOW_UP)
def schedule_manual_followup(
    data: FollowUpScheduleRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from app.models.crm import CRMContact
    if not data.message_text or not data.message_text.strip():
        raise HTTPException(status_code=400, detail="message_text is required")

    contact = db.execute(
        select(CRMContact)
        .where(CRMContact.tenant_id == current_user.tenant_id)
        .where(CRMContact.id == data.contact_id)
    ).scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    exe = CRMFollowUpExecution(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        rule_id=None,
        contact_id=contact.id,
        conversation_id=data.conversation_id,
        status="scheduled",
        scheduled_at=data.scheduled_at,
        attempt=1,
        message_text=data.message_text.strip(),
    )
    db.add(exe)
    db.commit()
    return FollowUpScheduleResponse(execution_id=exe.id, status=exe.status)


class DispatchDueRequest(BaseModel):
    limit: int = 50


class DispatchDueResponse(BaseModel):
    processed: int
    sent: int
    failed: int


@router.post("/dispatch-due", response_model=DispatchDueResponse)
@require_feature(Feature.FOLLOW_UP)
async def dispatch_due_followups(
    data: DispatchDueRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Cron target: call every minute. Sends due scheduled follow-ups for this tenant."""
    from app.models.crm import CRMContact
    from app.services.waha_service import WAHAService
    from app.db.session import AsyncSessionLocal

    now = datetime.datetime.now(datetime.timezone.utc)
    limit = max(1, min(int(data.limit), 200))

    processed = 0
    sent = 0
    failed = 0

    async with AsyncSessionLocal() as adb:
        res = await adb.execute(
            select(CRMFollowUpExecution)
            .where(CRMFollowUpExecution.tenant_id == current_user.tenant_id)
            .where(CRMFollowUpExecution.status == "scheduled")
            .where(CRMFollowUpExecution.scheduled_at <= now)
            .order_by(CRMFollowUpExecution.scheduled_at.asc())
            .limit(limit)
        )
        due = res.scalars().all()
        processed = len(due)

        for exe in due:
            try:
                c_res = await adb.execute(
                    select(CRMContact)
                    .where(CRMContact.tenant_id == current_user.tenant_id)
                    .where(CRMContact.id == exe.contact_id)
                )
                contact = c_res.scalar_one_or_none()
                if not contact or not contact.phone:
                    exe.status = "failed"
                    exe.error = "Missing contact or phone"
                    failed += 1
                    await adb.commit()
                    continue

                body = (exe.message_text or "").strip()
                if not body:
                    exe.status = "failed"
                    exe.error = "Missing message_text"
                    failed += 1
                    await adb.commit()
                    continue

                wa_msg = await WAHAService.send_and_persist(
                    db=adb,
                    tenant_id=current_user.tenant_id,
                    phone=contact.phone,
                    text=body,
                    session_id=None,
                    event_type="followup_outbound",
                )

                if wa_msg.status == "sent":
                    exe.status = "sent"
                    exe.sent_at = datetime.datetime.utcnow()
                    sent += 1
                else:
                    exe.status = "failed"
                    exe.error = "Send failed"
                    failed += 1

                await adb.commit()

            except Exception as e:
                exe.status = "failed"
                exe.error = str(e)
                failed += 1
                try:
                    await adb.commit()
                except Exception:
                    pass

    return DispatchDueResponse(processed=processed, sent=sent, failed=failed)

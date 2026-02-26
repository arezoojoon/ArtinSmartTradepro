"""
CRM Vision Intelligence Router — Phase D2.
Business Card Scan → Per-field Confidence → User Confirms → CRM Contact.
Uses unified AIWorkerService (same as Voice).
Enterprise+ only.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.database import get_db
from app.models.user import User
from app.models.vision import ScannedCard
from app.models.crm import CRMContact, CRMCompany
from app.models.ai_job import AIJob
from app.middleware.auth import get_current_active_user
from app.middleware.plan_gate import require_feature
from app.constants import Feature
from app.services.gemini_service import GeminiService
from app.services.billing import BillingService
from app.services.ai_worker import AIWorkerService, RATE_LIMITS
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict
import datetime
import uuid
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Constants ---
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
JOB_TYPE = "vision_scan"
CREDIT_COST = RATE_LIMITS[JOB_TYPE]["credits"]
ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"]
UPLOAD_DIR = "uploads/vision"


# --- Response Schemas ---
class VisionScanResponse(BaseModel):
    job_id: str
    card_id: str
    status: str
    message: str
    credit_cost: float


class VisionStatusResponse(BaseModel):
    job_id: str
    status: str
    error_message: Optional[str] = None
    card_id: Optional[str] = None
    extracted_name: Optional[str] = None
    extracted_company: Optional[str] = None
    extracted_position: Optional[str] = None
    extracted_phone: Optional[str] = None
    extracted_email: Optional[str] = None
    extracted_website: Optional[str] = None
    extracted_linkedin: Optional[str] = None
    extracted_address: Optional[str] = None
    confidence_name: Optional[float] = None
    confidence_company: Optional[float] = None
    confidence_phone: Optional[float] = None
    confidence_email: Optional[float] = None
    confidence_overall: Optional[float] = None


class ConfirmContactRequest(BaseModel):
    """User can edit any field before confirming."""
    first_name: str
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    event_name: Optional[str] = None
    note: Optional[str] = None


class ScannedCardRead(BaseModel):
    id: UUID
    file_name: Optional[str]
    extracted_name: Optional[str]
    extracted_company: Optional[str]
    extracted_email: Optional[str]
    extracted_phone: Optional[str]
    confidence_overall: Optional[float]
    contact_created_id: Optional[UUID]
    is_ai_suggested: Optional[bool]
    created_at: datetime.datetime

    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=()
    )


# --- Background Worker ---
def process_vision_job(job_id: UUID, card_id: UUID, tenant_id: UUID, file_path: str):
    """
    Background worker: Gemini Vision analysis with per-field confidence.
    """
    from app.database import SessionLocal
    import time

    AIWorkerService.mark_processing(job_id)

    db = SessionLocal()
    try:
        start_time = time.time()

        with open(file_path, "rb") as f:
            image_bytes = f.read()

        # Use enhanced prompt for per-field confidence
        result = GeminiService.scan_business_card_enhanced(image_bytes)
        processing_time = time.time() - start_time

        # Update scanned card with extracted data
        card = db.execute(select(ScannedCard).where(ScannedCard.id == card_id)).scalar_one()

        card.extracted_name = result.get("name", "")
        card.extracted_company = result.get("company", "")
        card.extracted_position = result.get("position", "")
        card.extracted_phone = result.get("phone", "")
        card.extracted_email = result.get("email", "")
        card.extracted_website = result.get("website", "")
        card.extracted_linkedin = result.get("linkedin", "")
        card.extracted_address = result.get("address", "")

        # Per-field confidence
        conf = result.get("field_confidence", {})
        card.confidence_name = conf.get("name", 0.0)
        card.confidence_company = conf.get("company", 0.0)
        card.confidence_phone = conf.get("phone", 0.0)
        card.confidence_email = conf.get("email", 0.0)
        card.confidence_overall = result.get("confidence", 0.0)

        card.processing_time_seconds = round(processing_time, 2)

        # Mark job completed
        AIWorkerService.mark_completed(db, job_id, result_reference=card_id)
        db.commit()
        logger.info(f"Vision job {job_id} completed in {processing_time:.1f}s")

    except Exception as e:
        logger.error(f"Vision job {job_id} failed: {e}")
        db.rollback()

        try:
            AIWorkerService.mark_failed(db, job_id, str(e))
            BillingService.refund(db, tenant_id, CREDIT_COST, f"Vision scan refund (failed): {job_id}")
            db.commit()
        except Exception as refund_err:
            logger.error(f"Refund failed for vision job {job_id}: {refund_err}")
            db.rollback()
    finally:
        db.close()


# --- API Endpoints ---

@router.post("/scan", response_model=VisionScanResponse)
@require_feature(Feature.AI_VISION)
async def scan_business_card(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload business card image → async Gemini Vision analysis.
    Returns job_id. Frontend polls /status/{job_id}.
    """
    # 1. Kill switch
    AIWorkerService.check_kill_switch(db)

    # 2. Validate type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {file.content_type}. Use JPEG/PNG/WebP.")

    # 3. Read & validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Image too large. Maximum: 5MB")

    # 4. SHA256 dedup
    file_hash = AIWorkerService.compute_file_hash(content)
    existing = db.execute(
        select(ScannedCard)
        .where(ScannedCard.tenant_id == current_user.tenant_id)
        .where(ScannedCard.file_hash == file_hash)
    ).scalar_one_or_none()

    if existing:
        existing_job = db.execute(
            select(AIJob)
            .where(AIJob.input_reference == existing.id)
            .where(AIJob.tenant_id == current_user.tenant_id)
            .order_by(desc(AIJob.created_at))
            .limit(1)
        ).scalar_one_or_none()

        return VisionScanResponse(
            job_id=str(existing_job.id) if existing_job else "",
            card_id=str(existing.id),
            status="duplicate",
            message="This image has already been scanned. Check existing results.",
            credit_cost=0
        )

    # 5. Rate limit (FOR UPDATE)
    usage, today, hour_start = AIWorkerService.check_rate_limit(db, current_user.tenant_id, JOB_TYPE)

    # 6. Deduct credits
    BillingService.deduct_balance(db, current_user.tenant_id, CREDIT_COST, f"Business card scan: {file.filename or 'image'}")

    # 7. Save file
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    card_id = uuid.uuid4()
    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    saved_path = os.path.join(UPLOAD_DIR, f"{card_id}{ext}")
    with open(saved_path, "wb") as f:
        f.write(content)

    # 8. Create card entry
    card = ScannedCard(
        id=card_id,
        tenant_id=current_user.tenant_id,
        file_path=saved_path,
        file_name=file.filename,
        file_hash=file_hash,
        file_size_bytes=len(content),
        mime_type=file.content_type,
    )
    db.add(card)

    # 9. Create job
    job = AIWorkerService.create_job(db, current_user.tenant_id, JOB_TYPE, card_id, CREDIT_COST)

    # 10. Increment usage
    AIWorkerService.increment_usage(db, current_user.tenant_id, JOB_TYPE, usage, today, hour_start)

    db.commit()

    # 11. Background worker
    background_tasks.add_task(process_vision_job, job.id, card_id, current_user.tenant_id, saved_path)

    return VisionScanResponse(
        job_id=str(job.id),
        card_id=str(card_id),
        status="processing",
        message="Image uploaded. Scanning in background. Poll /status/{job_id}.",
        credit_cost=CREDIT_COST
    )


@router.get("/status/{job_id}", response_model=VisionStatusResponse)
@require_feature(Feature.AI_VISION)
def get_scan_status(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Poll for scan status. Returns per-field data and confidence when complete."""
    job = AIWorkerService.get_job_status(db, job_id, current_user.tenant_id)

    if job.status in ("pending", "processing"):
        return VisionStatusResponse(job_id=str(job_id), status=job.status)

    if job.status == "failed":
        return VisionStatusResponse(job_id=str(job_id), status="failed", error_message=job.error_message)

    # Completed — fetch card data
    card = None
    if job.result_reference:
        card = db.execute(select(ScannedCard).where(ScannedCard.id == job.result_reference)).scalar_one_or_none()

    if not card:
        return VisionStatusResponse(job_id=str(job_id), status="completed")

    return VisionStatusResponse(
        job_id=str(job_id),
        status="completed",
        card_id=str(card.id),
        extracted_name=card.extracted_name,
        extracted_company=card.extracted_company,
        extracted_position=card.extracted_position,
        extracted_phone=card.extracted_phone,
        extracted_email=card.extracted_email,
        extracted_website=card.extracted_website,
        extracted_linkedin=card.extracted_linkedin,
        extracted_address=card.extracted_address,
        confidence_name=float(card.confidence_name) if card.confidence_name else 0.0,
        confidence_company=float(card.confidence_company) if card.confidence_company else 0.0,
        confidence_phone=float(card.confidence_phone) if card.confidence_phone else 0.0,
        confidence_email=float(card.confidence_email) if card.confidence_email else 0.0,
        confidence_overall=float(card.confidence_overall) if card.confidence_overall else 0.0,
    )


@router.post("/confirm/{card_id}")
@require_feature(Feature.AI_VISION)
def confirm_as_contact(
    card_id: UUID,
    data: ConfirmContactRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    User-confirmed contact creation from scanned card.
    User can edit any field before confirming.
    NEVER auto-creates — explicit user action required.
    """
    card = db.execute(
        select(ScannedCard)
        .where(ScannedCard.id == card_id)
        .where(ScannedCard.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()

    if not card:
        raise HTTPException(status_code=404, detail="Scanned card not found")

    if card.contact_created_id:
        raise HTTPException(status_code=409, detail="Contact already created from this card")

    # Create or find company
    company_id = None
    if data.company_name:
        existing_company = db.execute(
            select(CRMCompany)
            .where(CRMCompany.tenant_id == current_user.tenant_id)
            .where(CRMCompany.name == data.company_name)
        ).scalar_one_or_none()

        if existing_company:
            company_id = existing_company.id
        else:
            new_company = CRMCompany(
                tenant_id=current_user.tenant_id,
                name=data.company_name,
            )
            db.add(new_company)
            db.flush()
            company_id = new_company.id

    # Split name if only first_name provided
    first_name = data.first_name
    last_name = data.last_name

    # Create CRM Contact
    contact = CRMContact(
        tenant_id=current_user.tenant_id,
        company_id=company_id,
        first_name=first_name,
        last_name=last_name,
        email=data.email,
        phone=data.phone,
        position=data.position,
        linkedin_url=data.linkedin_url,
    )
    db.add(contact)
    db.flush()

    # Optional: attach event as a tag and store user note
    try:
        from app.models.crm import CRMNote, CRMTag

        if data.event_name:
            tag_name = f"event:{data.event_name.strip()}"
            existing_tag = db.execute(
                select(CRMTag)
                .where(CRMTag.tenant_id == current_user.tenant_id)
                .where(CRMTag.entity_type == "contact")
                .where(CRMTag.entity_id == contact.id)
                .where(CRMTag.name == tag_name)
            ).scalar_one_or_none()

            if not existing_tag:
                db.add(
                    CRMTag(
                        tenant_id=current_user.tenant_id,
                        name=tag_name,
                        color="#10B981",
                        entity_type="contact",
                        entity_id=contact.id,
                    )
                )

        if data.note or data.event_name:
            note_parts = []
            if data.event_name:
                note_parts.append(f"Event: {data.event_name.strip()}")
            if data.note:
                note_parts.append(data.note.strip())

            content = "\n".join([p for p in note_parts if p])
            if content:
                db.add(
                    CRMNote(
                        tenant_id=current_user.tenant_id,
                        author_id=getattr(current_user, "id", None),
                        contact_id=contact.id,
                        content=content,
                    )
                )
    except Exception as _e:
        # Do not fail contact creation if note/tag creation fails
        pass

    # Audit: link card to created contact
    card.contact_created_id = contact.id
    card.is_ai_suggested = False  # User confirmed

    db.commit()

    return {
        "contact_id": str(contact.id),
        "company_id": str(company_id) if company_id else None,
        "message": "Contact created successfully from scanned card.",
        "card_id": str(card_id)
    }


@router.get("/cards", response_model=List[ScannedCardRead])
@require_feature(Feature.AI_VISION)
def list_scanned_cards(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all scanned cards for this tenant."""
    return db.execute(
        select(ScannedCard)
        .where(ScannedCard.tenant_id == current_user.tenant_id)
        .order_by(desc(ScannedCard.created_at))
        .limit(50)
    ).scalars().all()

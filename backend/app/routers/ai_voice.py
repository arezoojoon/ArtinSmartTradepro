"""
CRM Voice Intelligence Router — Phase D1 (Production-Hardened).
Uses unified AIWorkerService for async jobs, rate limiting, billing, and recovery.
Enterprise+ only.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.database import get_db
from app.models.user import User
from app.models.voice import CRMVoiceRecording, CRMVoiceInsight
from app.models.ai_job import AIJob
from app.middleware.auth import get_current_active_user
from app.middleware.plan_gate import require_feature
from app.constants import Feature
from app.services.gemini_service import GeminiService
from app.services.billing import BillingService
from app.services.ai_worker import AIWorkerService, RATE_LIMITS
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
import datetime
import uuid
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Constants ---
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
JOB_TYPE = "voice_analysis"
CREDIT_COST = RATE_LIMITS[JOB_TYPE]["credits"]
ALLOWED_TYPES = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/m4a", "audio/ogg", "audio/webm", "audio/x-wav"]
UPLOAD_DIR = "uploads/voice"


# --- Response Schemas ---
class VoiceAnalysisResponse(BaseModel):
    job_id: str
    recording_id: str
    status: str
    message: str
    credit_cost: float


class VoiceStatusResponse(BaseModel):
    job_id: str
    status: str
    error_message: Optional[str] = None
    transcript: Optional[str] = None
    sentiment: Optional[str] = None
    intent: Optional[str] = None
    action_items: Optional[list] = []
    key_topics: Optional[list] = []
    urgency: Optional[str] = None
    confidence: Optional[float] = None
    processing_time: Optional[float] = None
    suggested_actions: Optional[list] = []
    disclaimer: Optional[str] = None


class VoiceInsightRead(BaseModel):
    id: UUID
    recording_id: UUID
    transcript: Optional[str]
    sentiment: Optional[str]
    intent: Optional[str]
    action_items: Optional[list] = []
    key_topics: Optional[list] = []
    urgency: Optional[str]
    confidence_score: Optional[float]
    model_used: Optional[str]
    model_version: Optional[str]
    processing_time_seconds: Optional[float]
    contains_sensitive_data: Optional[bool]
    retention_days: Optional[int]
    disclaimer: Optional[str]
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class VoiceRecordingRead(BaseModel):
    id: UUID
    contact_id: Optional[UUID]
    file_name: Optional[str]
    file_hash: Optional[str]
    duration_seconds: Optional[int]
    file_size_bytes: Optional[int]
    mime_type: Optional[str]
    credit_cost: Optional[float]
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# --- Background Worker ---
def process_voice_job(job_id: UUID, recording_id: UUID, tenant_id: UUID, file_path: str):
    """
    Background worker: Gemini analysis with full lifecycle management.
    Uses AIWorkerService for status tracking and BillingService for refunds.
    """
    from app.database import SessionLocal
    import time

    AIWorkerService.mark_processing(job_id)

    db = SessionLocal()
    try:
        start_time = time.time()

        class AudioFile:
            """Wrapper to match GeminiService.analyze_audio interface."""
            def __init__(self, path):
                self.filename = os.path.basename(path)
                self.file = open(path, "rb")
            def close(self):
                self.file.close()

        audio = AudioFile(file_path)
        try:
            result = GeminiService.analyze_audio(audio)
        finally:
            audio.close()

        processing_time = time.time() - start_time

        # Store insight (IMMUTABLE)
        insight_id = uuid.uuid4()
        insight = CRMVoiceInsight(
            id=insight_id,
            tenant_id=tenant_id,
            recording_id=recording_id,
            transcript=result.get("transcript", ""),
            sentiment=result.get("sentiment", "NEUTRAL"),
            intent=result.get("intent", ""),
            action_items=result.get("action_items", []),
            key_topics=result.get("key_topics", []),
            urgency=result.get("urgency", "medium"),
            confidence_score=result.get("confidence", 0.0),
            model_used="gemini-2.0-pro",
            model_version="v1",
            processing_time_seconds=round(processing_time, 2),
            contains_sensitive_data=False,
            retention_days=365,
            disclaimer=result.get("disclaimer", "AI-generated analysis.")
        )
        db.add(insight)

        # Mark job completed
        AIWorkerService.mark_completed(db, job_id, result_reference=insight_id)
        db.commit()
        logger.info(f"Voice job {job_id} completed in {processing_time:.1f}s")

    except Exception as e:
        logger.error(f"Voice job {job_id} failed: {e}")
        db.rollback()

        try:
            AIWorkerService.mark_failed(db, job_id, str(e))
            BillingService.refund(db, tenant_id, CREDIT_COST, f"Voice analysis refund (failed): {job_id}")
            db.commit()
            logger.info(f"Credits refunded for failed job {job_id}")
        except Exception as refund_err:
            logger.error(f"Refund failed for job {job_id}: {refund_err}")
            db.rollback()
    finally:
        db.close()


# --- API Endpoints ---

@router.post("/analyze", response_model=VoiceAnalysisResponse)
@require_feature(Feature.AI_VOICE)
async def analyze_voice(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    contact_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload audio → returns immediately with job_id + recording_id.
    Background task processes with Gemini 2.0 Pro.
    Frontend polls GET /status/{job_id}.
    Credits deducted upfront, refunded on failure.
    """
    # 1. Kill switch check
    AIWorkerService.check_kill_switch(db)

    # 2. Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {file.content_type}")

    # 3. Read & validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum: 10MB")

    # 4. Idempotency: check file hash
    file_hash = AIWorkerService.compute_file_hash(content)
    existing = db.execute(
        select(CRMVoiceRecording)
        .where(CRMVoiceRecording.tenant_id == current_user.tenant_id)
        .where(CRMVoiceRecording.file_hash == file_hash)
    ).scalar_one_or_none()

    if existing:
        # Find existing job for this recording
        existing_job = db.execute(
            select(AIJob)
            .where(AIJob.input_reference == existing.id)
            .where(AIJob.tenant_id == current_user.tenant_id)
            .order_by(desc(AIJob.created_at))
            .limit(1)
        ).scalar_one_or_none()

        return VoiceAnalysisResponse(
            job_id=str(existing_job.id) if existing_job else "",
            recording_id=str(existing.id),
            status="duplicate",
            message="This audio has already been analyzed. Check existing results.",
            credit_cost=0
        )

    # 5. Rate limit check (ROW LOCKED)
    usage, today, hour_start = AIWorkerService.check_rate_limit(db, current_user.tenant_id, JOB_TYPE)

    # 6. Deduct credits (ATOMIC)
    BillingService.deduct_balance(db, current_user.tenant_id, CREDIT_COST, f"Voice analysis: {file.filename or 'audio'}")

    # 7. Save file
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_id = uuid.uuid4()
    ext = os.path.splitext(file.filename)[1] if file.filename else ".wav"
    saved_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    with open(saved_path, "wb") as f:
        f.write(content)

    # 8. Create recording
    recording = CRMVoiceRecording(
        id=file_id,
        tenant_id=current_user.tenant_id,
        contact_id=uuid.UUID(contact_id) if contact_id else None,
        file_path=saved_path,
        file_name=file.filename,
        file_hash=file_hash,
        file_size_bytes=len(content),
        mime_type=file.content_type,
        credit_cost=CREDIT_COST
    )
    db.add(recording)

    # 9. Create job (unified tracking)
    job = AIWorkerService.create_job(db, current_user.tenant_id, JOB_TYPE, file_id, CREDIT_COST)

    # 10. Increment usage (row still locked from step 5)
    AIWorkerService.increment_usage(db, current_user.tenant_id, JOB_TYPE, usage, today, hour_start)

    # 11. Commit entire transaction atomically
    db.commit()

    # 12. Launch background worker
    background_tasks.add_task(process_voice_job, job.id, file_id, current_user.tenant_id, saved_path)

    return VoiceAnalysisResponse(
        job_id=str(job.id),
        recording_id=str(file_id),
        status="processing",
        message="Audio uploaded. Analysis running in background. Poll /status/{job_id}.",
        credit_cost=CREDIT_COST
    )


@router.get("/status/{job_id}", response_model=VoiceStatusResponse)
@require_feature(Feature.AI_VOICE)
def get_analysis_status(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Poll for analysis status. Returns full results when complete."""
    job = AIWorkerService.get_job_status(db, job_id, current_user.tenant_id)

    if job.status in ("pending", "processing"):
        return VoiceStatusResponse(job_id=str(job_id), status=job.status)

    if job.status == "failed":
        return VoiceStatusResponse(
            job_id=str(job_id),
            status="failed",
            error_message=job.error_message
        )

    # Completed — fetch insight by result_reference
    insight = None
    if job.result_reference:
        insight = db.execute(
            select(CRMVoiceInsight).where(CRMVoiceInsight.id == job.result_reference)
        ).scalar_one_or_none()

    if not insight:
        return VoiceStatusResponse(job_id=str(job_id), status="completed")

    # Build suggested actions from action items
    suggested_actions = []
    for item in (insight.action_items or []):
        if isinstance(item, str):
            if any(kw in item.lower() for kw in ["follow up", "follow-up", "call back", "schedule"]):
                suggested_actions.append({"type": "followup", "label": item, "action": "schedule_followup"})
            elif any(kw in item.lower() for kw in ["send", "email", "catalog", "document", "proposal"]):
                suggested_actions.append({"type": "task", "label": item, "action": "create_task"})
            else:
                suggested_actions.append({"type": "note", "label": item, "action": "add_note"})

    return VoiceStatusResponse(
        job_id=str(job_id),
        status="completed",
        transcript=insight.transcript,
        sentiment=insight.sentiment,
        intent=insight.intent,
        action_items=insight.action_items or [],
        key_topics=insight.key_topics or [],
        urgency=insight.urgency,
        confidence=float(insight.confidence_score) if insight.confidence_score else 0.0,
        processing_time=float(insight.processing_time_seconds) if insight.processing_time_seconds else 0.0,
        suggested_actions=suggested_actions,
        disclaimer=insight.disclaimer
    )


@router.get("/recordings", response_model=List[VoiceRecordingRead])
@require_feature(Feature.AI_VOICE)
def list_recordings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all voice recordings for this tenant."""
    return db.execute(
        select(CRMVoiceRecording)
        .where(CRMVoiceRecording.tenant_id == current_user.tenant_id)
        .order_by(desc(CRMVoiceRecording.created_at))
        .limit(50)
    ).scalars().all()


@router.get("/recordings/{recording_id}/insights", response_model=List[VoiceInsightRead])
@require_feature(Feature.AI_VOICE)
def get_insights(
    recording_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all insights for a specific recording (immutable log)."""
    return db.execute(
        select(CRMVoiceInsight)
        .where(CRMVoiceInsight.recording_id == recording_id)
        .where(CRMVoiceInsight.tenant_id == current_user.tenant_id)
        .order_by(desc(CRMVoiceInsight.created_at))
    ).scalars().all()

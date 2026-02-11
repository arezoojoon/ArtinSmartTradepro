"""
Unified AI Worker Service — Shared infrastructure for Voice, Vision, Brain.
Handles: rate limiting (row-locked), job management, watchdog recovery, kill switch, idempotency.
Concurrency: Semaphore limits max parallel AI calls to prevent thread pool exhaustion.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_
from fastapi import HTTPException
from app.models.ai_job import AIJob, AIUsage
from app.services.billing import BillingService
from uuid import UUID
import datetime
import uuid
import hashlib
import logging
import asyncio

logger = logging.getLogger(__name__)

# Concurrency guard: max 3 parallel AI calls to prevent thread pool exhaustion
_ai_semaphore = asyncio.Semaphore(3)

# --- Rate Limits ---
RATE_LIMITS = {
    "voice_analysis": {"daily": 20, "hourly": 5, "credits": 5.0},
    "vision_scan":    {"daily": 30, "hourly": 10, "credits": 2.0},
    "brain_insight":  {"daily": 10, "hourly": 3, "credits": 8.0},
}


class AIWorkerService:
    """Unified AI job lifecycle management with enterprise guardrails."""

    @staticmethod
    def check_kill_switch(db: Session):
        """
        Global AI kill switch. If enabled, all AI operations are blocked.
        Checks system_settings for ai_disabled flag.
        """
        try:
            from app.models.user import SystemSetting
            setting = db.execute(
                select(SystemSetting).where(SystemSetting.key == "ai_disabled")
            ).scalar_one_or_none()
            if setting and setting.value in ("true", "1", "yes"):
                raise HTTPException(status_code=503, detail="AI services are temporarily disabled. Contact admin.")
        except ImportError:
            # SystemSetting model may not exist yet — graceful fallback
            pass

    @staticmethod
    def compute_file_hash(content: bytes) -> str:
        """SHA256 hash for idempotency checking."""
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def check_rate_limit(db: Session, tenant_id: UUID, job_type: str):
        """
        Row-locked rate limit check.
        Uses SELECT FOR UPDATE to prevent race conditions on concurrent uploads.
        Returns the usage row (locked) for subsequent increment.
        """
        limits = RATE_LIMITS.get(job_type, {"daily": 10, "hourly": 3})
        today = datetime.date.today()
        now = datetime.datetime.utcnow()
        hour_start = now.replace(minute=0, second=0, microsecond=0)

        # Row-lock with FOR UPDATE — blocks concurrent requests for same tenant
        usage = db.execute(
            select(AIUsage)
            .where(AIUsage.tenant_id == tenant_id)
            .where(AIUsage.usage_date == today)
            .with_for_update()
        ).scalar_one_or_none()

        # Determine column names based on job type
        prefix = job_type.split("_")[0]  # voice, vision, brain
        daily_col = f"{prefix}_daily"
        hourly_col = f"{prefix}_hourly"

        if usage:
            daily_count = getattr(usage, daily_col, 0) or 0
            hourly_count = getattr(usage, hourly_col, 0) or 0

            # Check daily limit
            if daily_count >= limits["daily"]:
                raise HTTPException(
                    status_code=429,
                    detail=f"Daily {job_type} limit reached ({limits['daily']}/day). Resets at midnight UTC."
                )

            # Check hourly limit (reset if different hour)
            if usage.hour_window and usage.hour_window >= hour_start:
                if hourly_count >= limits["hourly"]:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Hourly {job_type} limit reached ({limits['hourly']}/hour). Try again later."
                    )

        return usage, today, hour_start

    @staticmethod
    def increment_usage(db: Session, tenant_id: UUID, job_type: str, usage, today, hour_start):
        """
        Atomically increment usage counters.
        MUST be called within the same transaction as check_rate_limit.
        """
        prefix = job_type.split("_")[0]
        daily_col = f"{prefix}_daily"
        hourly_col = f"{prefix}_hourly"

        if usage:
            setattr(usage, daily_col, (getattr(usage, daily_col, 0) or 0) + 1)
            if not usage.hour_window or usage.hour_window < hour_start:
                setattr(usage, hourly_col, 1)
                usage.hour_window = hour_start
            else:
                setattr(usage, hourly_col, (getattr(usage, hourly_col, 0) or 0) + 1)
        else:
            new_usage = AIUsage(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                usage_date=today,
                hour_window=hour_start,
            )
            setattr(new_usage, daily_col, 1)
            setattr(new_usage, hourly_col, 1)
            db.add(new_usage)

    @staticmethod
    def create_job(db: Session, tenant_id: UUID, job_type: str, input_reference: UUID, credit_cost: float) -> AIJob:
        """Create a new AI job entry (status=pending)."""
        job = AIJob(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            job_type=job_type,
            status="pending",
            input_reference=input_reference,
            credit_cost=credit_cost,
        )
        db.add(job)
        return job

    @staticmethod
    def mark_processing(job_id: UUID):
        """Mark job as processing (called by background worker)."""
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            db.execute(
                update(AIJob)
                .where(AIJob.id == job_id)
                .values(status="processing", started_at=datetime.datetime.utcnow())
            )
            db.commit()
        finally:
            db.close()

    @staticmethod
    def mark_completed(db: Session, job_id: UUID, result_reference: UUID = None):
        """Mark job as completed."""
        db.execute(
            update(AIJob)
            .where(AIJob.id == job_id)
            .values(
                status="completed",
                result_reference=result_reference,
                completed_at=datetime.datetime.utcnow()
            )
        )

    @staticmethod
    def mark_failed(db: Session, job_id: UUID, error_message: str):
        """Mark job as failed."""
        db.execute(
            update(AIJob)
            .where(AIJob.id == job_id)
            .values(
                status="failed",
                error_message=error_message,
                completed_at=datetime.datetime.utcnow()
            )
        )

    @staticmethod
    def get_job_status(db: Session, job_id: UUID, tenant_id: UUID) -> AIJob:
        """Get job by ID with tenant check."""
        job = db.execute(
            select(AIJob)
            .where(AIJob.id == job_id)
            .where(AIJob.tenant_id == tenant_id)
        ).scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    @staticmethod
    def recover_stuck_jobs():
        """
        Watchdog: Find jobs stuck in 'processing' for > 10 minutes.
        Marks them failed and refunds credits.
        Should be called periodically (startup + every 5 minutes).
        """
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)

            stuck_jobs = db.execute(
                select(AIJob).where(
                    and_(
                        AIJob.status == "processing",
                        AIJob.started_at < cutoff
                    )
                )
            ).scalars().all()

            for job in stuck_jobs:
                logger.warning(f"Recovering stuck job {job.id} (type={job.job_type}, started={job.started_at})")

                # Mark failed
                job.status = "failed"
                job.error_message = "Processing timeout (>10 min). Credits refunded."
                job.completed_at = datetime.datetime.utcnow()

                # Refund credits
                if job.credit_cost and float(job.credit_cost) > 0:
                    try:
                        BillingService.refund(
                            db, job.tenant_id, float(job.credit_cost),
                            f"AI job timeout refund: {job.job_type} ({job.id})"
                        )
                    except Exception as e:
                        logger.error(f"Refund failed for stuck job {job.id}: {e}")

            if stuck_jobs:
                db.commit()
                logger.info(f"Recovered {len(stuck_jobs)} stuck AI jobs")

        except Exception as e:
            logger.error(f"Watchdog error: {e}")
            db.rollback()
        finally:
            db.close()

    @staticmethod
    async def run_with_concurrency_limit(coro):
        """
        Run an AI coroutine with semaphore-limited concurrency.
        Prevents thread pool exhaustion when many tenants submit jobs simultaneously.
        Usage: result = await AIWorkerService.run_with_concurrency_limit(some_async_fn())
        """
        async with _ai_semaphore:
            return await coro

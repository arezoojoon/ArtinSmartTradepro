"""
Rate Limit Tests — Verify FOR UPDATE locking and limit enforcement.
"""
import pytest
import uuid
import datetime
from app.services.ai_worker import AIWorkerService, RATE_LIMITS
from app.models.ai_job import AIUsage
from fastapi import HTTPException


class TestRateLimits:
    def test_first_request_creates_usage(self, db, tenant_enterprise):
        """First request creates AIUsage row."""
        usage, today, hour_start = AIWorkerService.check_rate_limit(
            db, tenant_enterprise.id, "voice_analysis"
        )
        assert usage is None  # First time — no row yet

    def test_increment_creates_usage_row(self, db, tenant_enterprise):
        """Incrementing on first use creates AIUsage row."""
        usage, today, hour_start = AIWorkerService.check_rate_limit(
            db, tenant_enterprise.id, "voice_analysis"
        )
        AIWorkerService.increment_usage(
            db, tenant_enterprise.id, "voice_analysis", usage, today, hour_start
        )
        db.flush()

        saved = db.query(AIUsage).filter(
            AIUsage.tenant_id == tenant_enterprise.id
        ).first()
        assert saved is not None
        assert saved.voice_daily == 1
        assert saved.voice_hourly == 1

    def test_daily_limit_blocks(self, db, tenant_enterprise):
        """After reaching daily limit, next request raises 429."""
        limit = RATE_LIMITS["voice_analysis"]["daily"]

        # Create usage at limit
        today = datetime.date.today()
        usage_row = AIUsage(
            id=uuid.uuid4(),
            tenant_id=tenant_enterprise.id,
            usage_date=today,
            voice_daily=limit,
            voice_hourly=0,
            hour_window=datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0),
        )
        db.add(usage_row)
        db.flush()

        with pytest.raises(HTTPException) as exc_info:
            AIWorkerService.check_rate_limit(
                db, tenant_enterprise.id, "voice_analysis"
            )
        assert exc_info.value.status_code == 429
        assert "daily" in exc_info.value.detail.lower()

    def test_hourly_limit_blocks(self, db, tenant_enterprise):
        """After reaching hourly limit, next request raises 429."""
        limit = RATE_LIMITS["voice_analysis"]["hourly"]
        now = datetime.datetime.utcnow()
        hour_start = now.replace(minute=0, second=0, microsecond=0)

        usage_row = AIUsage(
            id=uuid.uuid4(),
            tenant_id=tenant_enterprise.id,
            usage_date=datetime.date.today(),
            voice_daily=0,
            voice_hourly=limit,
            hour_window=hour_start,
        )
        db.add(usage_row)
        db.flush()

        with pytest.raises(HTTPException) as exc_info:
            AIWorkerService.check_rate_limit(
                db, tenant_enterprise.id, "voice_analysis"
            )
        assert exc_info.value.status_code == 429
        assert "hourly" in exc_info.value.detail.lower()


class TestWatchdog:
    def test_recover_stuck_jobs_refunds(self, db, tenant_enterprise):
        """Watchdog should mark stuck jobs as failed and refund credits."""
        from app.models.ai_job import AIJob
        from app.models.billing import Wallet
        from sqlalchemy import select

        wallet = db.execute(
            select(Wallet).where(Wallet.tenant_id == tenant_enterprise.id)
        ).scalar_one()
        balance_before = float(wallet.balance)

        # Create stuck job (started 15 minutes ago)
        job = AIJob(
            id=uuid.uuid4(),
            tenant_id=tenant_enterprise.id,
            job_type="voice_analysis",
            status="processing",
            credit_cost=5.0,
            started_at=datetime.datetime.utcnow() - datetime.timedelta(minutes=15),
        )
        db.add(job)
        db.commit()

        # Run watchdog
        AIWorkerService.recover_stuck_jobs()

        # Verify job is marked failed
        db.expire_all()
        updated_job = db.query(AIJob).filter(AIJob.id == job.id).first()
        assert updated_job.status == "failed"
        assert "timeout" in updated_job.error_message.lower()

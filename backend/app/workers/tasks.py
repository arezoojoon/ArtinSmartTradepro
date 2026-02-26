"""
Celery Task Definitions for Hunter & AI Jobs
Replaces asyncio.create_task with durable, Redis-backed task queue.
"""
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.workers.celery_app import celery_app
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


def _get_sync_db() -> Session:
    """Create a synchronous DB session for Celery workers."""
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


@celery_app.task(bind=True, name="app.workers.tasks.run_hunter_job", max_retries=2)
def run_hunter_job(
    self,
    job_id: str,
    tenant_id: str,
    keyword: str,
    location: str,
    sources: list,
    hs_code: str = None,
    min_volume_usd: float = None,
    min_growth_pct: float = None,
):
    """
    Execute a Hunter scraping + lead generation job.
    Runs in Celery worker process — survives server restarts.
    """
    db = _get_sync_db()
    try:
        from app.models.ai_job import AIJob
        from app.models.hunter import HunterRun, HunterResult
        import uuid

        logger.info(f"[Hunter] Starting job {job_id} for tenant {tenant_id}")

        # Mark job as running
        job = db.query(AIJob).get(job_id)
        if not job:
            logger.error(f"[Hunter] Job {job_id} not found")
            return
        job.status = "running"
        db.commit()

        # Create hunter run
        run = HunterRun(
            job_id=uuid.UUID(job_id),
            tenant_id=uuid.UUID(tenant_id),
            keyword=keyword,
            location=location,
            sources=sources,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # Execute scraping via service (sync wrapper)
        import asyncio
        from app.services.hunter_service import HunterService

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                HunterService.run_hunter_job(
                    job_id=uuid.UUID(job_id),
                    tenant_id=uuid.UUID(tenant_id),
                    keyword=keyword,
                    location=location,
                    sources=sources,
                    hs_code=hs_code,
                    min_volume_usd=min_volume_usd,
                    min_growth_pct=min_growth_pct,
                )
            )
        finally:
            loop.close()

        logger.info(f"[Hunter] Job {job_id} completed successfully")

    except Exception as exc:
        logger.error(f"[Hunter] Job {job_id} failed: {exc}")
        try:
            job = db.query(AIJob).get(job_id)
            if job:
                job.status = "failed"
                job.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


@celery_app.task(bind=True, name="app.workers.tasks.track_competitor_job", max_retries=2)
def track_competitor_job(self, competitor_id: str, tenant_id: str):
    """
    Execute competitor tracking job in Celery worker.
    """
    db = _get_sync_db()
    try:
        import asyncio
        import uuid
        from app.services.competitor_service import CompetitorService

        logger.info(f"[Competitor] Tracking competitor {competitor_id}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                CompetitorService.track_competitor_job(
                    competitor_id=uuid.UUID(competitor_id),
                    tenant_id=uuid.UUID(tenant_id),
                )
            )
        finally:
            loop.close()

        logger.info(f"[Competitor] Tracking {competitor_id} completed")

    except Exception as exc:
        logger.error(f"[Competitor] Tracking {competitor_id} failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@celery_app.task(bind=True, name="app.workers.tasks.run_enrichment_job", max_retries=2)
def run_enrichment_job(self, job_id: str, tenant_id: str, lead_id: str, provider: str):
    """
    Execute a Hunter enrichment job in Celery worker.
    """
    db = _get_sync_db()
    try:
        import asyncio
        import uuid
        from app.services.hunter_repository import HunterRepository
        from app.services.hunter_enrichment import WebBasicProvider

        logger.info(f"[Enrichment] Processing job {job_id} for lead {lead_id}")

        repo = HunterRepository(db)
        repo.update_job_status(uuid.UUID(tenant_id), uuid.UUID(job_id), "running")

        providers = {
            "web_basic": WebBasicProvider({
                "timeout": 10,
                "max_size": 5 * 1024 * 1024,
                "user_agent": "ArtinHunter/1.0",
                "rate_limit_delay": 5,
            })
        }

        prov = providers.get(provider)
        if not prov:
            raise ValueError(f"Provider '{provider}' not found")

        lead = repo.get_lead_with_details(uuid.UUID(tenant_id), uuid.UUID(lead_id))
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(prov.enrich(lead, repo))
        finally:
            loop.close()

        # Apply results
        for identity in result.identities:
            repo.attach_identity(
                tenant_id=uuid.UUID(tenant_id),
                lead_id=uuid.UUID(lead_id),
                type=identity["type"],
                value=identity["value"],
            )
        for evidence_item in result.evidence:
            repo.attach_evidence(
                tenant_id=uuid.UUID(tenant_id),
                lead_id=uuid.UUID(lead_id),
                field_name=evidence_item["field_name"],
                source_name=evidence_item["source_name"],
                source_url=evidence_item.get("source_url"),
                confidence=evidence_item["confidence"],
                snippet=evidence_item.get("snippet"),
                collected_at=evidence_item["collected_at"],
                raw=evidence_item.get("raw"),
            )

        repo.update_job_status(uuid.UUID(tenant_id), uuid.UUID(job_id), "done")
        logger.info(f"[Enrichment] Job {job_id} completed")

    except Exception as exc:
        logger.error(f"[Enrichment] Job {job_id} failed: {exc}")
        try:
            from app.services.hunter_repository import HunterRepository
            import uuid
            repo = HunterRepository(db)
            repo.update_job_status(
                uuid.UUID(tenant_id), uuid.UUID(job_id), "failed",
                error={"message": str(exc), "type": type(exc).__name__},
            )
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()

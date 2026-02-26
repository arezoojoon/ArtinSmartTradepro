"""
Celery Application Configuration
Uses Redis as both broker and result backend.
"""
from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "artin_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,   # 5 min soft limit
    task_time_limit=600,        # 10 min hard limit
    result_expires=3600,        # Results expire after 1 hour
    task_default_queue="default",
    task_routes={
        "app.workers.tasks.run_hunter_job": {"queue": "hunter"},
        "app.workers.tasks.track_competitor_job": {"queue": "hunter"},
        "app.workers.tasks.run_enrichment_job": {"queue": "enrichment"},
    },
)

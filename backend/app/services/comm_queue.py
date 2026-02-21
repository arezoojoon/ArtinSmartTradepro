"""
Redis queue utility for outbound message dispatch.
Queues: comm:outbound (main), comm:outbound:dlq (dead letter)
Each job is a JSON-encoded dict with keys:
  tenant_id, message_id, to_e164, body_text, attempt
"""
import json
import logging
from typing import Optional
import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

REDIS_URL        = getattr(settings, "REDIS_URL", "redis://redis:6379/0")
QUEUE_OUTBOUND   = "comm:outbound"
QUEUE_DLQ        = "comm:outbound:dlq"
MAX_ATTEMPTS     = 5

_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _pool


async def enqueue_outbound(job: dict) -> None:
    """Push a job onto the main outbound queue."""
    r = await get_redis()
    await r.rpush(QUEUE_OUTBOUND, json.dumps(job))
    logger.debug("Enqueued outbound job: %s", job.get("message_id"))


async def enqueue_dlq(job: dict, error_detail: str) -> None:
    """Push a failed job onto the dead-letter queue."""
    job["dlq_error"] = error_detail
    r = await get_redis()
    await r.rpush(QUEUE_DLQ, json.dumps(job))
    logger.warning("Sent to DLQ: message_id=%s error=%s", job.get("message_id"), error_detail)


async def dequeue_outbound(timeout: int = 5) -> Optional[dict]:
    """Blocking left-pop from the outbound queue. Returns job dict or None."""
    r = await get_redis()
    result = await r.blpop(QUEUE_OUTBOUND, timeout=timeout)
    if result:
        _, raw = result
        return json.loads(raw)
    return None


async def list_dlq(limit: int = 50) -> list:
    """Inspect DLQ items without removing them (LRANGE)."""
    r = await get_redis()
    items = await r.lrange(QUEUE_DLQ, 0, limit - 1)
    return [json.loads(i) for i in items]


async def requeue_from_dlq(message_id: str) -> bool:
    """
    Scan DLQ for a specific message_id, remove it, reset attempts, push to main queue.
    Returns True if found and requeued.
    """
    r = await get_redis()
    items = await r.lrange(QUEUE_DLQ, 0, -1)
    for raw in items:
        job = json.loads(raw)
        if job.get("message_id") == message_id:
            await r.lrem(QUEUE_DLQ, 1, raw)
            job["attempt"] = 0
            job.pop("dlq_error", None)
            await r.rpush(QUEUE_OUTBOUND, json.dumps(job))
            logger.info("Requeued from DLQ: message_id=%s", message_id)
            return True
    return False

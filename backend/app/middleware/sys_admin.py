"""
Phase 6 — Sys Admin Middleware
Provides IP allowlist enforcement + Redis rate limiting for /sys/* routes.
Mount BEFORE the sys router in main.py.
"""
from datetime import datetime
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

settings = get_settings()


def _get_redis():
    """Lazy Redis client; returns None if unconfigured."""
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.ping()
        return r
    except Exception:
        return None


_redis = None


class SysAdminMiddleware(BaseHTTPMiddleware):
    """
    Applied only to requests starting with /sys.
    1. IP Allowlist — if SYS_ADMIN_IP_ALLOWLIST is non-empty, blocks unlisted IPs.
    2. Rate Limiting — if Redis is available, enforces SYS_ADMIN_RATE_LIMIT_PER_MIN
       per source IP using a sliding 60-second window.

    Paths NOT protected: /sys/auth/login (so login still works from any IP
    before the token is obtained — control this via firewall instead).
    """

    def __init__(self, app, debug: bool = False):
        super().__init__(app)
        self.debug = debug
        global _redis
        _redis = _get_redis()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Only apply to /sys routes
        if not path.startswith("/sys"):
            return await call_next(request)

        client_ip = _get_client_ip(request)

        # ── 1. IP Allowlist ───────────────────────────────────────────────────
        allowlist_raw = settings.SYS_ADMIN_IP_ALLOWLIST.strip()
        if allowlist_raw:
            allowed_ips = {ip.strip() for ip in allowlist_raw.split(",") if ip.strip()}
            if client_ip not in allowed_ips:
                return JSONResponse(
                    status_code=403,
                    content={
                        "code": "IP_NOT_ALLOWED",
                        "detail": "Access denied: your IP is not in the sys admin allowlist.",
                    },
                )

        # ── 2. Rate Limiting (Redis) ──────────────────────────────────────────
        if _redis is not None:
            try:
                rate_key = f"sys:ratelimit:{client_ip}"
                limit = settings.SYS_ADMIN_RATE_LIMIT_PER_MIN
                count = _redis.incr(rate_key)
                if count == 1:
                    _redis.expire(rate_key, 60)
                if count > limit:
                    retry_after = _redis.ttl(rate_key)
                    return JSONResponse(
                        status_code=429,
                        headers={
                            "Retry-After": str(max(retry_after, 1)),
                            "X-RateLimit-Limit": str(limit),
                            "X-RateLimit-Remaining": "0",
                        },
                        content={
                            "code": "RATE_LIMITED",
                            "detail": f"Too many requests to sys panel. Limit: {limit}/min.",
                        },
                    )
            except Exception:
                # Redis error → fail open (don't block legitimate admins)
                pass

        return await call_next(request)


def _get_client_ip(request: Request) -> str:
    """Respects X-Forwarded-For when behind a proxy."""
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"

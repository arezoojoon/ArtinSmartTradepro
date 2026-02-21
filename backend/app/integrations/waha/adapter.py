"""
WAHA HTTP Adapter
==================
Minimal assumptions. Only send_text is implemented.
send_media stubs are marked NOT IMPLEMENTED.

Config is read from app settings (environment variables):
  WAHA_BASE_URL        http://waha:3000
  WAHA_API_KEY         optional
  WAHA_SESSION_NAME    default
  WAHA_WEBHOOK_SECRET  optional — used in webhook router
"""
import logging
from typing import Optional
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

WAHA_BASE_URL    = getattr(settings, "WAHA_BASE_URL",     "http://waha:3000")
WAHA_API_KEY     = getattr(settings, "WAHA_API_KEY",      "")
WAHA_SESSION     = getattr(settings, "WAHA_SESSION_NAME", "default")


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if WAHA_API_KEY:
        h["X-Api-Key"] = WAHA_API_KEY
    return h


class WAHAAdapter:
    """Async adapter. All methods raise on non-2xx responses."""

    @staticmethod
    async def health() -> dict:
        """
        Returns basic health info.
        Checks GET /api/sessions/{session} to verify the session is active.
        """
        url = f"{WAHA_BASE_URL}/api/sessions/{WAHA_SESSION}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=_headers())
                resp.raise_for_status()
                data = resp.json()
                return {
                    "reachable": True,
                    "session": WAHA_SESSION,
                    "status": data.get("status", "UNKNOWN"),
                    "raw": data,
                }
        except httpx.ConnectError:
            return {"reachable": False, "session": WAHA_SESSION, "status": "UNREACHABLE"}
        except Exception as e:
            return {"reachable": False, "session": WAHA_SESSION, "status": "ERROR", "error": str(e)}

    @staticmethod
    async def send_text(to_e164: str, text: str) -> Optional[str]:
        """
        Sends a plain text message.
        Returns provider_message_id (WAHA 'id' field) or raises on error.
        """
        chat_id = _e164_to_chat_id(to_e164)
        url = f"{WAHA_BASE_URL}/api/sendText"
        payload = {
            "chatId":  chat_id,
            "text":    text,
            "session": WAHA_SESSION,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, json=payload, headers=_headers())
            resp.raise_for_status()
            data = resp.json()
            return data.get("id") or data.get("key", {}).get("id")

    @staticmethod
    async def send_media(to_e164: str, media_url: str, caption: str = "") -> Optional[str]:
        """NOT IMPLEMENTED — stub for future media sending via WAHA."""
        raise NotImplementedError(
            "send_media is not implemented. "
            "Configure your WAHA instance and implement file upload or URL-based sending."
        )


def _e164_to_chat_id(phone: str) -> str:
    """Convert +971501234567 -> 971501234567@c.us"""
    digits = phone.lstrip("+").strip()
    return f"{digits}@c.us"

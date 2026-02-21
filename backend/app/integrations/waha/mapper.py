"""
WAHA Payload Mapper
=====================
Decouples raw webhook payload parsing from business logic.
All functions return None on parse failure so callers can
still persist the raw payload as UNKNOWN format.

WAHA payload format (community best-effort, may change):
{
  "event": "message",
  "session": "default",
  "payload": {
    "id": "true_...",
    "timestamp": 1234567890,
    "from": "971501234567@c.us",
    "to": "...",
    "body": "Hello",
    ...
  }
}

Status update format:
{
  "event": "message.ack",
  "payload": { "id": "...", "ack": 3 }
}

ACK codes (WAHA): 1=sent, 2=delivered, 3=read, -1=error
"""
from typing import Optional


# WAHA ACK code → our status
_ACK_MAP = {
    1: "sent",
    2: "delivered",
    3: "read",
    -1: "failed",
}


def extract_event_type(payload: dict) -> str:
    """
    Returns one of: 'inbound_message', 'status_update', 'unknown'.
    """
    event = payload.get("event", "")
    if event in ("message", "message.any"):
        # Could be inbound or outbound depending on fromMe
        inner = payload.get("payload", {})
        if inner.get("fromMe") is True:
            return "outbound_echo"
        return "inbound_message"
    if event in ("message.ack",):
        return "status_update"
    return "unknown"


def extract_sender(payload: dict) -> Optional[str]:
    """
    Returns E.164 phone number of the sender.
    WAHA delivers 'from' as '971501234567@c.us'.
    Returns None if extraction fails.
    """
    try:
        inner = payload.get("payload", payload)
        raw = inner.get("from", "")
        phone = raw.split("@")[0].strip()
        if phone and phone.isdigit():
            return f"+{phone}"
        return None
    except Exception:
        return None


def extract_text(payload: dict) -> Optional[str]:
    """Returns message body text, or None."""
    try:
        inner = payload.get("payload", payload)
        body = inner.get("body") or inner.get("text") or inner.get("caption")
        return str(body) if body else None
    except Exception:
        return None


def extract_provider_message_id(payload: dict) -> Optional[str]:
    """Returns WAHA message id string, or None."""
    try:
        inner = payload.get("payload", payload)
        return inner.get("id") or None
    except Exception:
        return None


def extract_media(payload: dict) -> Optional[dict]:
    """
    Returns media metadata dict if present, else None.
    We store metadata only, never raw bytes.
    """
    try:
        inner = payload.get("payload", payload)
        media = inner.get("media") or inner.get("document") or inner.get("image") or inner.get("audio")
        if not media:
            return None
        # Strip any binary/base64 fields
        safe = {k: v for k, v in media.items() if k not in ("data", "base64", "file")}
        return safe if safe else None
    except Exception:
        return None


def extract_ack_status(payload: dict) -> Optional[str]:
    """Returns our status string from a status_update event, or None."""
    try:
        inner = payload.get("payload", payload)
        ack = inner.get("ack")
        return _ACK_MAP.get(ack)
    except Exception:
        return None


def extract_recipient(payload: dict) -> Optional[str]:
    """Returns E.164 recipient for outbound echo events."""
    try:
        inner = payload.get("payload", payload)
        raw = inner.get("to", "")
        phone = raw.split("@")[0].strip()
        return f"+{phone}" if phone and phone.isdigit() else None
    except Exception:
        return None

"""
WAHA Service — QA-HARDENED HTTP adapter for WAHA WhatsApp API.
QA-3: Outbound idempotency via client_message_id hash.
QA-4: SSRF-safe media download (allowlist, max size, MIME sniffing).
QA-8: Every outbound creates BotEvent audit record.
"""
import httpx
import uuid
import hashlib
import datetime
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models.whatsapp import WhatsAppMessage
from app.models.bot_session import BotEvent
from app.services.whatsapp import WhatsAppService

settings = get_settings()

# WAHA Config
WAHA_API_URL = getattr(settings, "WAHA_API_URL", "http://localhost:3000")
WAHA_SESSION = getattr(settings, "WAHA_SESSION", "default")
WAHA_API_KEY = getattr(settings, "WAHA_API_KEY", "")

# ═══════════════════════════════════════════
# QA-4: SSRF PROTECTION CONFIG
# ═══════════════════════════════════════════
_waha_parsed = urlparse(WAHA_API_URL)
ALLOWED_MEDIA_HOSTS = {_waha_parsed.hostname, "localhost", "127.0.0.1"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024    # 5 MB
MAX_AUDIO_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_DOC_SIZE = 15 * 1024 * 1024     # 15 MB

# Magic byte signatures for MIME sniffing
SAFE_MIME_MAGIC = {
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG': 'image/png',
    b'GIF8': 'image/gif',
    b'RIFF': 'audio/wav',       # WAV
    b'OggS': 'audio/ogg',       # OGG (voice notes)
    b'\x1a\x45\xdf\xa3': 'video/webm',  # WEBM
    b'%PDF': 'application/pdf',
    b'ID3': 'audio/mpeg',       # MP3
    b'\xff\xfb': 'audio/mpeg',  # MP3 without ID3
}

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.ogg', '.wav', '.mp3', '.webm', '.opus'}


def _compute_outbound_hash(tenant_id: uuid.UUID, phone: str, body: str) -> str:
    """QA-3: Deterministic hash for outbound dedup within same minute."""
    minute = datetime.datetime.utcnow().strftime("%Y%m%d%H%M")
    raw = f"{tenant_id}:{phone}:{body[:200]}:{minute}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _sniff_mime(data: bytes) -> str:
    """QA-4: MIME sniffing via magic bytes (not trusting Content-Type header)."""
    for magic, mime in SAFE_MIME_MAGIC.items():
        if data[:len(magic)] == magic:
            return mime
    return "application/octet-stream"


def _validate_media_url(url: str) -> None:
    """QA-4: SSRF protection — only allow downloads from WAHA host."""
    parsed = urlparse(url)
    host = parsed.hostname
    if host not in ALLOWED_MEDIA_HOSTS:
        raise ValueError(f"SSRF BLOCKED: media host '{host}' not in allowlist {ALLOWED_MEDIA_HOSTS}")
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"SSRF BLOCKED: unsupported scheme '{parsed.scheme}'")
    # Path traversal check
    if ".." in parsed.path:
        raise ValueError("SSRF BLOCKED: path traversal detected")


class WAHAService:
    """
    Production WAHA adapter — QA-hardened.
    """

    @staticmethod
    async def send_text(phone: str, text: str) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{WAHA_API_URL}/api/sendText",
                json={
                    "chatId": f"{phone}@c.us",
                    "text": text,
                    "session": WAHA_SESSION
                },
                headers={"X-Api-Key": WAHA_API_KEY} if WAHA_API_KEY else {}
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def send_image(phone: str, image_url: str, caption: str = "") -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{WAHA_API_URL}/api/sendImage",
                json={
                    "chatId": f"{phone}@c.us",
                    "file": {"url": image_url},
                    "caption": caption,
                    "session": WAHA_SESSION
                },
                headers={"X-Api-Key": WAHA_API_KEY} if WAHA_API_KEY else {}
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def send_file(phone: str, file_url: str, filename: str = "document.pdf") -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{WAHA_API_URL}/api/sendFile",
                json={
                    "chatId": f"{phone}@c.us",
                    "file": {"url": file_url},
                    "fileName": filename,
                    "session": WAHA_SESSION
                },
                headers={"X-Api-Key": WAHA_API_KEY} if WAHA_API_KEY else {}
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def send_and_persist(
        db: Session,
        tenant_id: uuid.UUID,
        phone: str,
        text: str,
        media_url: str = None,
        media_type: str = None,  # image, file
        session_id: uuid.UUID = None,
        event_type: str = "outbound"
    ) -> WhatsAppMessage:
        """
        QA-3: Outbound idempotency via hash.
        QA-8: Creates BotEvent for every outbound message.
        """
        # QA-3: Check outbound dedup
        client_hash = _compute_outbound_hash(tenant_id, phone, text)
        existing = db.query(WhatsAppMessage).filter(
            WhatsAppMessage.tenant_id == tenant_id,
            WhatsAppMessage.recipient_phone == phone,
            WhatsAppMessage.direction == "outbound",
            WhatsAppMessage.template_name == client_hash  # Reuse template_name field for dedup hash
        ).first()
        if existing:
            return existing  # Already sent this minute, skip

        msg = WhatsAppMessage(
            tenant_id=tenant_id,
            recipient_phone=phone,
            direction="outbound",
            content=text[:4000],
            status="pending",
            cost=0,
            template_name=client_hash  # QA-3: Store hash for dedup
        )
        db.add(msg)
        db.flush()

        try:
            if media_url and media_type == "image":
                result = await WAHAService.send_image(phone, media_url, text)
            elif media_url and media_type == "file":
                result = await WAHAService.send_file(phone, media_url)
            else:
                result = await WAHAService.send_text(phone, text)

            msg.message_id = result.get("id", f"waha_{uuid.uuid4()}")
            msg.status = "sent"

        except Exception as e:
            msg.status = "failed"
            msg.content = f"{text[:3800]} [SEND_ERROR: {str(e)[:200]}]"

        # QA-8: Audit outbound
        event = BotEvent(
            tenant_id=tenant_id,
            session_id=session_id,
            phone=phone,
            event_type=event_type,
            payload={"text": text[:500], "status": msg.status},
            message_id=msg.id
        )
        db.add(event)

        # Sync to CRM conversation
        WhatsAppService.sync_conversation(db, tenant_id, phone, msg)
        return msg

    @staticmethod
    async def download_media_secure(
        media_url: str,
        expected_type: str = "image"  # image, audio, document
    ) -> tuple:
        """
        QA-4: SSRF-safe media download.
        Returns: (bytes, detected_mime)
        Raises: ValueError on SSRF / size / bad MIME.
        """
        # Step 1: SSRF allowlist check
        _validate_media_url(media_url)

        # Step 2: Set max size based on type
        max_size = {
            "image": MAX_IMAGE_SIZE,
            "audio": MAX_AUDIO_SIZE,
            "document": MAX_DOC_SIZE,
        }.get(expected_type, MAX_IMAGE_SIZE)

        # Step 3: Stream download with size limit
        data = b""
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"X-Api-Key": WAHA_API_KEY} if WAHA_API_KEY else {}
            async with client.stream("GET", media_url, headers=headers) as response:
                response.raise_for_status()

                # Check Content-Length header before downloading
                content_length = int(response.headers.get("content-length", 0))
                if content_length > max_size:
                    raise ValueError(f"File too large: {content_length} bytes > {max_size} limit")

                async for chunk in response.aiter_bytes(chunk_size=65536):
                    data += chunk
                    if len(data) > max_size:
                        raise ValueError(
                            f"FILE_TOO_LARGE: {len(data)} bytes exceeds {max_size // (1024*1024)}MB limit for {expected_type}"
                        )

        if not data:
            raise ValueError("Empty media file")

        # Step 4: MIME sniffing (magic bytes)
        detected_mime = _sniff_mime(data)
        allowed_mimes_by_type = {
            "image": {"image/jpeg", "image/png", "image/gif"},
            "audio": {"audio/ogg", "audio/wav", "audio/mpeg", "audio/webm", "video/webm"},
            "document": {"application/pdf"},
        }
        allowed = allowed_mimes_by_type.get(expected_type, set())
        if detected_mime not in allowed and detected_mime != "application/octet-stream":
            raise ValueError(f"BAD_MIME: detected '{detected_mime}', expected one of {allowed}")

        return data, detected_mime

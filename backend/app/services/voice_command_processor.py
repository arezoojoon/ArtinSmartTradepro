"""
Voice Command Processor — Pillar 1: Zero-Touch Input
WhatsApp voice message → Gemini transcription → Intent extraction → CRM action

Flow:
1. User sends voice note to WhatsApp bot
2. WAHA downloads audio → sends to this service
3. Gemini transcribes audio (multi-language: FA, AR, EN, RU, TR)
4. Gemini extracts intent + entities from transcript
5. System creates AI Approval item OR auto-executes low-risk actions
"""
import logging
import json
import uuid
import httpx
import base64
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.ai_approval import AIApprovalQueue, ApprovalStatus, ApprovalPriority, ApprovalCategory

logger = logging.getLogger(__name__)

# Intent definitions with risk levels
INTENT_DEFINITIONS = {
    "update_lead": {
        "description": "Update a CRM lead/contact with new information",
        "risk": "low",
        "auto_approve": True,
        "category": ApprovalCategory.CRM_UPDATE.value,
        "examples_fa": ["جلسه با شرکت ایکس عالی بود", "لید جدید از نمایشگاه"],
        "examples_en": ["meeting with company X went great", "new lead from exhibition"],
    },
    "send_proforma": {
        "description": "Generate and send a proforma invoice",
        "risk": "high",
        "auto_approve": False,
        "category": ApprovalCategory.PROFORMA_INVOICE.value,
        "examples_fa": ["پروفرما بفرست", "پیش‌فاکتور آماده کن"],
        "examples_en": ["send proforma", "prepare invoice"],
    },
    "send_message": {
        "description": "Send a message to a contact via WhatsApp",
        "risk": "medium",
        "auto_approve": False,
        "category": ApprovalCategory.OUTBOUND_MESSAGE.value,
        "examples_fa": ["پیام بده به", "بهش بگو"],
        "examples_en": ["message to", "tell them"],
    },
    "update_shipment": {
        "description": "Update shipment status or details",
        "risk": "low",
        "auto_approve": True,
        "category": ApprovalCategory.SHIPMENT_UPDATE.value,
        "examples_fa": ["محموله رسید", "بارگیری انجام شد"],
        "examples_en": ["shipment arrived", "loading completed"],
    },
    "create_deal": {
        "description": "Create a new deal in the pipeline",
        "risk": "medium",
        "auto_approve": False,
        "category": ApprovalCategory.CRM_UPDATE.value,
        "examples_fa": ["معامله جدید", "توافق کردیم"],
        "examples_en": ["new deal", "we agreed on"],
    },
    "schedule_followup": {
        "description": "Schedule a follow-up task",
        "risk": "low",
        "auto_approve": True,
        "category": ApprovalCategory.CRM_UPDATE.value,
        "examples_fa": ["یادآوری بذار", "فردا زنگ بزنم"],
        "examples_en": ["set reminder", "call tomorrow"],
    },
    "price_inquiry": {
        "description": "Check or update pricing information",
        "risk": "low",
        "auto_approve": True,
        "category": ApprovalCategory.PRICE_QUOTE.value,
        "examples_fa": ["قیمت چنده", "نرخ امروز"],
        "examples_en": ["what's the price", "today's rate"],
    },
    "general_note": {
        "description": "Save a general note or observation",
        "risk": "low",
        "auto_approve": True,
        "category": ApprovalCategory.CRM_UPDATE.value,
        "examples_fa": ["یادداشت", "نکته مهم"],
        "examples_en": ["note", "important point"],
    },
}


class VoiceCommandProcessor:
    """
    Processes voice commands from WhatsApp using Gemini AI.
    Supports Farsi, Arabic, English, Russian, Turkish.
    """

    def __init__(self):
        self.gemini_api_key = getattr(settings, "GEMINI_API_KEY", "")
        self.gemini_model = "gemini-2.5-flash"

    async def process_voice_message(
        self,
        audio_data: bytes,
        tenant_id: uuid.UUID,
        sender_phone: str,
        db: AsyncSession,
        mime_type: str = "audio/ogg",
    ) -> Dict[str, Any]:
        """
        Main entry point: Process a WhatsApp voice message end-to-end.
        Returns the processing result with transcript, intent, and action taken.
        """
        result = {
            "transcript": "",
            "language": "unknown",
            "intent": None,
            "entities": {},
            "action": None,
            "approval_required": False,
            "approval_id": None,
            "error": None,
            "fallback_message": None,
        }

        # Step 1: Transcribe audio using Gemini
        transcript, language, confidence = await self._transcribe_with_gemini(audio_data, mime_type)

        if not transcript or confidence < 0.3:
            result["error"] = "low_confidence_transcription"
            result["fallback_message"] = self._get_fallback_message(language, "unclear_audio")
            return result

        result["transcript"] = transcript
        result["language"] = language

        # Step 2: Extract intent and entities
        intent_data = await self._extract_intent(transcript, language)
        result["intent"] = intent_data.get("intent", "general_note")
        result["entities"] = intent_data.get("entities", {})

        # Step 3: Determine action based on intent risk level
        intent_config = INTENT_DEFINITIONS.get(result["intent"], INTENT_DEFINITIONS["general_note"])

        action_payload = self._build_action_payload(
            intent=result["intent"],
            entities=result["entities"],
            transcript=transcript,
            language=language,
            sender_phone=sender_phone,
        )

        if intent_config["auto_approve"]:
            # Low-risk: auto-execute
            result["action"] = "auto_executed"
            result["approval_required"] = False
        else:
            # High/medium risk: create approval request
            approval = AIApprovalQueue(
                tenant_id=tenant_id,
                category=intent_config["category"],
                title=self._generate_approval_title(result["intent"], result["entities"], language),
                description=f"Voice command from {sender_phone}: {transcript[:500]}",
                ai_payload=action_payload,
                ai_confidence=intent_data.get("confidence", 0.5),
                ai_reasoning=intent_data.get("reasoning", ""),
                source_type="voice_command",
                source_preview=transcript[:200],
                status=ApprovalStatus.PENDING.value,
                priority=ApprovalPriority.HIGH.value if intent_config["risk"] == "high" else ApprovalPriority.MEDIUM.value,
                expires_at=datetime.utcnow() + timedelta(hours=24),
            )
            db.add(approval)
            await db.flush()

            result["action"] = "pending_approval"
            result["approval_required"] = True
            result["approval_id"] = str(approval.id)

        return result

    async def _transcribe_with_gemini(
        self, audio_data: bytes, mime_type: str
    ) -> Tuple[str, str, float]:
        """
        Transcribe audio using Gemini multimodal API.
        Returns (transcript, detected_language, confidence).
        """
        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY not set, cannot transcribe")
            return ("", "unknown", 0.0)

        audio_b64 = base64.b64encode(audio_data).decode("utf-8")

        prompt = """You are a multilingual transcription assistant for a trade/business platform.
Transcribe this audio message EXACTLY as spoken. The speaker may use Farsi (Persian), Arabic, English, Russian, or Turkish.

Return a JSON object with:
{
  "transcript": "exact transcription of what was said",
  "language": "fa|ar|en|ru|tr",
  "confidence": 0.0 to 1.0
}

Rules:
- Keep the original language, do NOT translate
- If multiple languages are mixed, use the dominant one for "language"
- If audio is unclear, set confidence low and transcribe what you can
- Business/trade terminology should be preserved accurately"""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
            payload = {
                "contents": [{
                    "parts": [
                        {"inline_data": {"mime_type": mime_type, "data": audio_b64}},
                        {"text": prompt}
                    ]
                }],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2000}
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()

            text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = self._extract_json(text)

            return (
                parsed.get("transcript", ""),
                parsed.get("language", "unknown"),
                parsed.get("confidence", 0.5),
            )

        except Exception as e:
            logger.error(f"Gemini transcription failed: {e}")
            return ("", "unknown", 0.0)

    async def _extract_intent(self, transcript: str, language: str) -> Dict[str, Any]:
        """
        Extract business intent and entities from transcript using Gemini.
        """
        if not self.gemini_api_key:
            return {"intent": "general_note", "entities": {}, "confidence": 0.3}

        intent_list = "\n".join([
            f"- {k}: {v['description']}" for k, v in INTENT_DEFINITIONS.items()
        ])

        prompt = f"""You are an AI assistant for a trade/business platform. Analyze this voice command and extract the business intent.

Transcript ({language}): "{transcript}"

Available intents:
{intent_list}

Return a JSON object:
{{
  "intent": "one of the intent names above",
  "confidence": 0.0 to 1.0,
  "reasoning": "brief explanation of why this intent was chosen",
  "entities": {{
    "company_name": "if mentioned",
    "contact_name": "if mentioned",
    "product": "if mentioned (e.g. pistachios, saffron, dates)",
    "price": "if mentioned",
    "currency": "if mentioned (USD, EUR, AED, IRR)",
    "quantity": "if mentioned",
    "deadline": "if mentioned (tomorrow, next week, etc.)",
    "phone": "if a phone number is mentioned",
    "action_detail": "specific action requested"
  }}
}}

Rules:
- Understand Farsi/Arabic/English/Russian/Turkish business context
- "پروفرما" = proforma invoice, "پیش‌فاکتور" = proforma
- "لید" = lead, "معامله" = deal, "محموله" = shipment
- Extract ALL mentioned entities even if partial
- If unsure about intent, use "general_note" with low confidence"""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1500}
            }

            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()

            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return self._extract_json(text)

        except Exception as e:
            logger.error(f"Gemini intent extraction failed: {e}")
            return {"intent": "general_note", "entities": {}, "confidence": 0.3}

    def _build_action_payload(
        self, intent: str, entities: Dict, transcript: str, language: str, sender_phone: str
    ) -> Dict[str, Any]:
        """Build the action payload that will be executed on approval."""
        return {
            "intent": intent,
            "entities": entities,
            "transcript": transcript,
            "language": language,
            "sender_phone": sender_phone,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _generate_approval_title(self, intent: str, entities: Dict, language: str) -> str:
        """Generate a human-readable title for the approval item."""
        company = entities.get("company_name", "")
        product = entities.get("product", "")
        contact = entities.get("contact_name", "")

        titles = {
            "send_proforma": f"Send proforma to {company or contact or 'contact'}",
            "send_message": f"Send WhatsApp to {contact or company or 'contact'}",
            "create_deal": f"Create deal: {product or 'new deal'} with {company or 'company'}",
            "update_lead": f"Update lead: {company or contact or 'lead'}",
        }
        return titles.get(intent, f"AI Action: {intent}")

    def _get_fallback_message(self, language: str, error_type: str) -> str:
        """Pillar 4: Friendly fallback messages in user's language."""
        messages = {
            "unclear_audio": {
                "fa": "متاسفانه صدای شما واضح نبود. لطفاً دوباره با صدای بلندتر ضبط کنید یا پیام متنی بفرستید. 🎤",
                "ar": "عذراً، لم أتمكن من فهم الرسالة الصوتية. يرجى إعادة التسجيل بصوت أوضح أو إرسال رسالة نصية. 🎤",
                "en": "Sorry, I couldn't understand the audio clearly. Please record again louder or send a text message. 🎤",
                "ru": "К сожалению, я не смог разобрать аудио. Пожалуйста, запишите снова громче или отправьте текст. 🎤",
                "tr": "Üzgünüm, sesi net anlayamadım. Lütfen daha yüksek sesle tekrar kaydedin veya metin mesajı gönderin. 🎤",
            },
            "processing_error": {
                "fa": "مشکلی در پردازش پیام شما پیش آمد. لطفاً دوباره تلاش کنید. 🔄",
                "ar": "حدث خطأ في معالجة رسالتك. يرجى المحاولة مرة أخرى. 🔄",
                "en": "There was an issue processing your message. Please try again. 🔄",
                "ru": "Произошла ошибка при обработке вашего сообщения. Попробуйте ещё раз. 🔄",
                "tr": "Mesajınızı işlerken bir sorun oluştu. Lütfen tekrar deneyin. 🔄",
            },
        }
        lang_messages = messages.get(error_type, messages["processing_error"])
        return lang_messages.get(language, lang_messages["en"])

    def _extract_json(self, text: str) -> Dict:
        """Robust JSON extraction from Gemini response."""
        import re
        # Try direct parse
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass
        # Try extracting from code block
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except (json.JSONDecodeError, TypeError):
                pass
        # Try finding JSON object
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except (json.JSONDecodeError, TypeError):
                pass
        return {}

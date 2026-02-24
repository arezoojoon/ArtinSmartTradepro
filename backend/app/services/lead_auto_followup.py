"""
Lead Auto Follow-Up Service
When a Hunter lead is imported to CRM:
1. Detect phone number nationality
2. Generate personalized WhatsApp message in the contact's language via Gemini
3. Send WhatsApp message automatically
4. Create CRM conversation and follow-up execution record
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.crm import CRMContact, CRMConversation
from app.models.whatsapp import WhatsAppMessage
from app.models.followup import CRMFollowUpExecution

logger = logging.getLogger(__name__)

# Phone prefix → (country, language code, language name)
PHONE_PREFIX_MAP = {
    "+971": ("UAE", "ar", "Arabic"),
    "+966": ("Saudi Arabia", "ar", "Arabic"),
    "+968": ("Oman", "ar", "Arabic"),
    "+973": ("Bahrain", "ar", "Arabic"),
    "+974": ("Qatar", "ar", "Arabic"),
    "+965": ("Kuwait", "ar", "Arabic"),
    "+98":  ("Iran", "fa", "Persian/Farsi"),
    "+90":  ("Turkey", "tr", "Turkish"),
    "+91":  ("India", "en", "English"),
    "+86":  ("China", "zh", "Chinese"),
    "+7":   ("Russia", "ru", "Russian"),
    "+49":  ("Germany", "de", "German"),
    "+33":  ("France", "fr", "French"),
    "+39":  ("Italy", "it", "Italian"),
    "+34":  ("Spain", "es", "Spanish"),
    "+55":  ("Brazil", "pt", "Portuguese"),
    "+234": ("Nigeria", "en", "English"),
    "+27":  ("South Africa", "en", "English"),
    "+254": ("Kenya", "en", "English"),
    "+62":  ("Indonesia", "id", "Indonesian"),
    "+60":  ("Malaysia", "ms", "Malay"),
    "+66":  ("Thailand", "th", "Thai"),
    "+84":  ("Vietnam", "vi", "Vietnamese"),
    "+81":  ("Japan", "ja", "Japanese"),
    "+82":  ("South Korea", "ko", "Korean"),
    "+1":   ("USA/Canada", "en", "English"),
    "+44":  ("UK", "en", "English"),
    "+61":  ("Australia", "en", "English"),
    "+20":  ("Egypt", "ar", "Arabic"),
    "+212": ("Morocco", "ar", "Arabic"),
    "+216": ("Tunisia", "ar", "Arabic"),
    "+213": ("Algeria", "ar", "Arabic"),
    "+92":  ("Pakistan", "ur", "Urdu"),
    "+880": ("Bangladesh", "bn", "Bengali"),
    "+94":  ("Sri Lanka", "si", "Sinhala"),
    "+63":  ("Philippines", "en", "English"),
}


def detect_nationality(phone: str) -> Tuple[str, str, str]:
    """
    Detect country, language code, and language name from phone number.
    Returns (country, lang_code, lang_name).
    """
    if not phone:
        return ("Unknown", "en", "English")

    cleaned = phone.strip().replace(" ", "").replace("-", "")
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned

    # Try longest prefix first (3-digit codes before 2-digit before 1-digit)
    for prefix_len in [4, 3, 2]:
        prefix = cleaned[:prefix_len]
        if prefix in PHONE_PREFIX_MAP:
            return PHONE_PREFIX_MAP[prefix]

    return ("Unknown", "en", "English")


async def generate_first_contact_message(
    contact_name: str,
    company_name: str,
    product_keyword: str,
    country: str,
    language: str,
    lang_code: str,
) -> str:
    """
    Use Gemini to generate a personalized first-contact WhatsApp message
    in the contact's native language.
    """
    try:
        from app.services.gemini_service import _get_model, _extract_json, _call_gemini_async

        prompt = f"""You are an expert international trade sales agent. Generate a professional, warm, and concise first-contact WhatsApp message for a potential trade partner.

CONTEXT:
- Contact Name: {contact_name}
- Company: {company_name or 'their company'}
- Product of Interest: {product_keyword or 'trade products'}
- Country: {country}
- Language: {language} ({lang_code})

INSTRUCTIONS:
1. Write the message in {language} ({lang_code}).
2. Keep it under 300 characters (WhatsApp friendly).
3. Be professional but friendly — this is a B2B trade inquiry.
4. Mention the product and express interest in cooperation.
5. Include a call to action (ask if they're open to discuss).
6. Do NOT include any greeting like "Dear Sir/Madam" — use their first name.

Respond in this exact JSON format:
{{
    "message": "the WhatsApp message text in {language}",
    "language_used": "{lang_code}",
    "english_translation": "English translation of the message for internal reference"
}}"""

        model = _get_model()

        def _call():
            return model.generate_content(prompt)

        response = await _call_gemini_async(_call)
        parsed = _extract_json(response.text)
        return parsed.get("message", f"Hi {contact_name}, we'd love to explore trade opportunities with you.")

    except Exception as e:
        logger.error(f"Gemini message generation failed: {e}")
        # Fallback to English template
        return f"Hi {contact_name}, I found your company while researching {product_keyword or 'trade'} opportunities. Would you be open to a brief conversation about potential cooperation?"


async def auto_followup_on_import(
    db: AsyncSession,
    contact: CRMContact,
    tenant_id,
    product_keyword: str = "",
) -> Optional[str]:
    """
    Main entry point: called after a Hunter lead is imported to CRM.
    Detects nationality, generates message, sends WhatsApp, creates conversation.
    Returns the WhatsApp message ID or None.
    """
    if not contact.phone:
        logger.info(f"No phone for contact {contact.id}, skipping auto-followup")
        return None

    try:
        # 1. Detect nationality
        country, lang_code, lang_name = detect_nationality(contact.phone)
        logger.info(f"Detected nationality for {contact.phone}: {country} ({lang_name})")

        # Update contact's preferred language if not set
        if not contact.preferred_language:
            contact.preferred_language = lang_code

        # 2. Generate personalized message via Gemini
        contact_name = contact.first_name or "there"
        company_name = ""
        if contact.company_id:
            from app.models.crm import CRMCompany
            c_res = await db.execute(select(CRMCompany).where(CRMCompany.id == contact.company_id))
            company = c_res.scalar_one_or_none()
            if company:
                company_name = company.name

        message_text = await generate_first_contact_message(
            contact_name=contact_name,
            company_name=company_name,
            product_keyword=product_keyword,
            country=country,
            language=lang_name,
            lang_code=lang_code,
        )

        # 3. Send WhatsApp message
        from app.services.whatsapp import WhatsAppService
        try:
            wamid = await WhatsAppService.send_template(
                phone=contact.phone,
                template="first_contact",
                variables={"text": message_text}
            )
        except Exception as send_err:
            logger.error(f"WhatsApp send failed for {contact.phone}: {send_err}")
            return None

        # 4. Create/update CRM conversation
        conv_res = await db.execute(
            select(CRMConversation)
            .where(CRMConversation.tenant_id == tenant_id)
            .where(CRMConversation.identifier == contact.phone)
            .where(CRMConversation.channel == "whatsapp")
        )
        conversation = conv_res.scalar_one_or_none()

        if not conversation:
            conversation = CRMConversation(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                contact_id=contact.id,
                channel="whatsapp",
                identifier=contact.phone,
                subject=f"{contact.first_name} {contact.last_name or ''}".strip(),
                status="open",
                unread_count=0,
                last_message_at=datetime.utcnow(),
            )
            db.add(conversation)
            await db.flush()

        # 5. Log the WhatsApp message
        wa_msg = WhatsAppMessage(
            tenant_id=tenant_id,
            recipient_phone=contact.phone,
            content=message_text,
            status="sent",
            message_id=wamid,
            cost=0.5,
            direction="outbound",
            conversation_id=conversation.id,
        )
        db.add(wa_msg)

        # 6. Create follow-up execution record
        followup_exec = CRMFollowUpExecution(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            contact_id=contact.id,
            conversation_id=conversation.id,
            status="sent",
            scheduled_at=datetime.utcnow(),
            sent_at=datetime.utcnow(),
            attempt=1,
        )
        db.add(followup_exec)

        await db.commit()
        logger.info(f"Auto follow-up sent to {contact.phone} ({country}/{lang_name}): {wamid}")
        return wamid

    except Exception as e:
        logger.error(f"Auto follow-up failed for contact {contact.id}: {e}")
        try:
            await db.rollback()
        except Exception:
            pass
        return None

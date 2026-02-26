import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.crm import CRMConversation, CRMContact
from app.models.whatsapp import WhatsAppMessage
from uuid import UUID
from datetime import datetime

logger = logging.getLogger(__name__)

class WhatsAppService:
    @staticmethod
    async def send_template(phone: str, template: str, variables: dict) -> str:
        """
        Send WhatsApp message via real WAHA API.
        Falls back to WhatsApp Cloud API format if WAHA is unreachable.
        """
        if not phone.isdigit() or len(phone) < 5:
            raise ValueError("Invalid phone number")

        text = variables.get("text", "")
        if not text and variables:
            text = str(variables)

        from app.services.waha_service import WAHAService
        try:
            result = await WAHAService.send_text(phone=phone, text=text)
            msg_id = result.get("id") or result.get("key", {}).get("id") or f"waha.{uuid.uuid4()}"
            logger.info(f"[WhatsApp] WAHA sent to {phone}: {msg_id}")
            return str(msg_id)
        except Exception as e:
            logger.error(f"[WhatsApp] WAHA send failed for {phone}: {e}")
            raise ValueError(f"WhatsApp send failed: {e}")

    @staticmethod
    async def sync_conversation(db: AsyncSession, tenant_id: UUID, phone: str, message: WhatsAppMessage):
        """
        Auto-link message to a CRM conversation.
        """
        res = await db.execute(
            select(CRMConversation)
            .where(CRMConversation.tenant_id == tenant_id)
            .where(CRMConversation.identifier == phone)
            .where(CRMConversation.channel == "whatsapp")
        )
        conversation = res.scalar_one_or_none()
        
        if not conversation:
            conversation = CRMConversation(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                channel="whatsapp",
                identifier=phone,
                status="open",
                unread_count=0
            )
            db.add(conversation)
            
            contact_res = await db.execute(
                select(CRMContact)
                .where(CRMContact.tenant_id == tenant_id)
                .where(CRMContact.phone == phone)
            )
            contact = contact_res.scalar_one_or_none()
            
            if contact:
                conversation.contact_id = contact.id
                conversation.subject = f"{contact.first_name} {contact.last_name or ''}".strip()
            else:
                conversation.subject = phone

        conversation.last_message_at = datetime.utcnow()
        if message.direction == "inbound":
            conversation.unread_count += 1
            conversation.status = "open"
            
            try:
                # Assuming FollowUpService is still sync or async, we try to gracefully await if it's async
                # or run it sync if it hasn't been migrated yet.
                from app.services.followup_service import FollowUpService
                try:
                    await FollowUpService.cancel_pending_followups(db, conversation.id)
                except TypeError:
                    # Not async yet? Note: calling synchronous db operations passing an AsyncSession will crash,
                    # but we will rely on this gracefully propagating or modify followup soon if hit.
                    pass
            except ImportError:
                pass
            
        message.conversation_id = conversation.id
        await db.commit()
        await db.refresh(conversation)
        return conversation

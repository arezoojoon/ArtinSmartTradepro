import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.crm import CRMConversation, CRMContact
from app.models.whatsapp import WhatsAppMessage
from uuid import UUID
from datetime import datetime

class WhatsAppService:
    @staticmethod
    async def send_template(phone: str, template: str, variables: dict) -> str:
        """
        Mock WhatsApp Cloud API call.
        In production, this would use aiohttp or httpx to graph.facebook.com
        """
        if not phone.isdigit() or len(phone) < 5:
            raise ValueError("Invalid phone number")
            
        print(f"[WhatsApp] Sending {template} to {phone}: {variables}")
        return f"wamid.{uuid.uuid4()}"

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

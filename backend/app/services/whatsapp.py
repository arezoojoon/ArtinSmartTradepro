import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.crm import CRMConversation, CRMContact
from app.models.whatsapp import WhatsAppMessage
from uuid import UUID
from datetime import datetime

class WhatsAppService:
    @staticmethod
    def send_template(phone: str, template: str, variables: dict) -> str:
        """
        Mock WhatsApp Cloud API call.
        In production, this would use requests to graph.facebook.com
        """
        if not phone.isdigit() or len(phone) < 5:
            raise ValueError("Invalid phone number")
            
        print(f"[WhatsApp] Sending {template} to {phone}: {variables}")
        return f"wamid.{uuid.uuid4()}"

    @staticmethod
    def sync_conversation(db: Session, tenant_id: UUID, phone: str, message: WhatsAppMessage):
        """
        Auto-link message to a CRM conversation.
        1. Find existing conversation for phone/tenant.
        2. If none, create new one.
        3. Try to link to CRM Contact by phone.
        4. Update last_message_at and unread_count.
        """
        # Find conversation
        conversation = db.execute(
            select(CRMConversation)
            .where(CRMConversation.tenant_id == tenant_id)
            .where(CRMConversation.identifier == phone)
            .where(CRMConversation.channel == "whatsapp")
        ).scalar_one_or_none()
        
        if not conversation:
            # Create new conversation
            conversation = CRMConversation(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                channel="whatsapp",
                identifier=phone,
                status="open",
                unread_count=0
            )
            db.add(conversation)
            
            # Try to link to contact
            contact = db.execute(
                select(CRMContact)
                .where(CRMContact.tenant_id == tenant_id)
                .where(CRMContact.phone == phone)
            ).scalar_one_or_none()
            
            if contact:
                conversation.contact_id = contact.id
                conversation.subject = f"{contact.first_name} {contact.last_name or ''}".strip()
            else:
                conversation.subject = phone

        # Update conversation stats
        conversation.last_message_at = datetime.utcnow()
        if message.direction == "inbound":
            conversation.unread_count += 1
            conversation.status = "open"  # Reopen if closed
            
            # Cancel pending follow-ups (User replied!)
            # Import inside function to avoid circular import (FollowUpService -> WhatsAppService -> FollowUpService)
            from app.services.followup_service import FollowUpService
            FollowUpService.cancel_pending_followups(db, conversation.id)
            
        # Link message
        message.conversation_id = conversation.id
        
        db.commit()
        db.refresh(conversation)
        return conversation

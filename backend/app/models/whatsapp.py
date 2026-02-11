from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class WhatsAppMessage(Base):
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("crm_conversations.id"), nullable=True) # Linked to CRM thread
    
    recipient_phone = Column(String, index=True, nullable=False)
    direction = Column(String, default="outbound") # inbound, outbound
    status = Column(String, default="queued") # queued, sent, delivered, read, failed
    content = Column(Text, nullable=True)
    template_name = Column(String, nullable=True)
    
    message_id = Column(String, index=True, nullable=True) # WhatsApp Message ID
    cost = Column(Numeric(12, 2), default=0.00)
    
    tenant = relationship("Tenant", back_populates="whatsapp_messages")
    conversation = relationship("CRMConversation", back_populates="messages")

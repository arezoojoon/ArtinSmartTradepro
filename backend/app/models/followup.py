from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import uuid

class CRMFollowUpRule(Base):
    """Rules for automating follow-ups."""
    __tablename__ = "crm_followup_rules"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    
    trigger_event = Column(String, default="no_reply") # no_reply, deal_stage, manual
    delay_minutes = Column(Integer, default=1440) # 24h
    max_attempts = Column(Integer, default=1)
    
    channel = Column(String, default="whatsapp")
    template_body = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant")
    executions = relationship("CRMFollowUpExecution", back_populates="rule")

class CRMFollowUpExecution(Base):
    """Scheduled follow-up execution."""
    __tablename__ = "crm_followup_executions"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("crm_followup_rules.id"), nullable=True)
    
    contact_id = Column(UUID(as_uuid=True), ForeignKey("crm_contacts.id"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("crm_campaigns.id"), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("crm_conversations.id"), nullable=True) # Linked conversation
    
    attempt = Column(Integer, default=1)
    status = Column(String, default="scheduled") # scheduled, sent, cancelled, failed

    message_text = Column(Text, nullable=True)
    
    scheduled_at = Column(DateTime, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    rule = relationship("CRMFollowUpRule", back_populates="executions")
    contact = relationship("CRMContact")
    campaign = relationship("CRMCampaign")
    conversation = relationship("CRMConversation")
    tenant = relationship("Tenant")

class CRMRevenueAttribution(Base):
    """Tracks revenue source."""
    __tablename__ = "crm_revenue_attributions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    deal_id = Column(UUID(as_uuid=True), ForeignKey("crm_deals.id"), nullable=False)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("crm_campaigns.id"), nullable=True)
    message_id = Column(String, index=True, nullable=True) # Link to exact message if possible
    
    attribution_type = Column(String, default="last_touch") # first_touch, last_touch
    amount = Column(Integer, default=0) # Attributed amount
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    deal = relationship("CRMDeal")
    campaign = relationship("CRMCampaign")
    tenant = relationship("Tenant")

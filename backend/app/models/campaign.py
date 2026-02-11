from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Float, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import enum

class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"

class CampaignChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"

class CampaignMessageStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    REPLIED = "replied"

class CRMCampaign(Base):
    """Outbound Campaign (Manual for now)."""
    __tablename__ = "crm_campaigns"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default=CampaignStatus.DRAFT, index=True) # draft, running, paused, completed
    channel = Column(String, default=CampaignChannel.WHATSAPP)
    
    # Template
    template_body = Column(Text, nullable=True) # "Hello {{first_name}}, ..."
    
    # Stats
    total_contacts = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    replied_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    tenant = relationship("Tenant")
    segments = relationship("CRMCampaignSegment", back_populates="campaign", cascade="all, delete-orphan")
    messages = relationship("CRMCampaignMessage", back_populates="campaign", cascade="all, delete-orphan")

class CRMCampaignSegment(Base):
    """Filter criteria for campaign targets."""
    __tablename__ = "crm_campaign_segments"
    
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("crm_campaigns.id"), nullable=False, index=True)
    filter_json = Column(JSON, default={}) # { "country": "UAE", "tags": ["vip"], "manual_ids": [...] }
    
    campaign = relationship("CRMCampaign", back_populates="segments")

class CRMCampaignMessage(Base):
    """Individual message in a campaign."""
    __tablename__ = "crm_campaign_messages"
    
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("crm_campaigns.id"), nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("crm_contacts.id"), nullable=False, index=True)
    
    status = Column(String, default=CampaignMessageStatus.PENDING, index=True)
    sent_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    
    # Link to actual WhatsApp message if sent
    whatsapp_message_id = Column(UUID(as_uuid=True), ForeignKey("whatsapp_messages.id"), nullable=True)
    
    campaign = relationship("CRMCampaign", back_populates="messages")
    contact = relationship("CRMContact")
    whatsapp_message = relationship("WhatsAppMessage")

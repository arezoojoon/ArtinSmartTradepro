from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Float, JSON, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import uuid

class CRMCompany(Base):
    """Business entities. Distinct from Leads."""
    __tablename__ = "crm_companies"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, index=True, nullable=False)
    domain = Column(String, index=True)
    industry = Column(String)
    size = Column(String)  # 1-10, 11-50, etc.
    country = Column(String)
    city = Column(String)
    address = Column(Text)
    linkedin_url = Column(String)
    website = Column(String)
    
    # Relationships
    contacts = relationship("CRMContact", back_populates="company")
    deals = relationship("CRMDeal", back_populates="company")
    notes = relationship("CRMNote", back_populates="company")
    tenant = relationship("Tenant")

class CRMContact(Base):
    """People. Distinct from Leads."""
    __tablename__ = "crm_contacts"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("crm_companies.id"), nullable=True)
    
    first_name = Column(String, nullable=False)
    last_name = Column(String)
    email = Column(String, index=True)
    phone = Column(String, index=True) # Added index for fast lookup by phone
    position = Column(String)
    linkedin_url = Column(String)
    
    # Relationships
    company = relationship("CRMCompany", back_populates="contacts")
    deals = relationship("CRMDeal", back_populates="contact")
    notes = relationship("CRMNote", back_populates="contact")
    conversations = relationship("CRMConversation", back_populates="contact")
    tenant = relationship("Tenant")

class CRMPipeline(Base):
    """Sales pipelines (e.g. 'Export Deals', 'Distributor Partnerships')."""
    __tablename__ = "crm_pipelines"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    stages = Column(JSON, default=[])  # check 'stages' schema below
    is_default = Column(Integer, default=0) # 1=True
    
    deals = relationship("CRMDeal", back_populates="pipeline")
    tenant = relationship("Tenant")

class CRMDeal(Base):
    """Sales opportunities."""
    __tablename__ = "crm_deals"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("crm_pipelines.id"), nullable=False)
    stage_id = Column(String, nullable=False) # ID from pipeline.stages JSON
    
    company_id = Column(UUID(as_uuid=True), ForeignKey("crm_companies.id"), nullable=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("crm_contacts.id"), nullable=True)
    
    name = Column(String, nullable=False)
    value = Column(Float, default=0.0)
    currency = Column(String, default="AED")
    probability = Column(Float, default=0.5)
    expected_close_date = Column(DateTime)
    closed_at = Column(DateTime)
    status = Column(String, default="open") # open, won, lost
    
    pipeline = relationship("CRMPipeline", back_populates="deals")
    company = relationship("CRMCompany", back_populates="deals")
    contact = relationship("CRMContact", back_populates="deals")
    notes = relationship("CRMNote", back_populates="deal")
    tenant = relationship("Tenant")

class CRMNote(Base):
    """Notes on any entity."""
    __tablename__ = "crm_notes"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    company_id = Column(UUID(as_uuid=True), ForeignKey("crm_companies.id"), nullable=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("crm_contacts.id"), nullable=True)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("crm_deals.id"), nullable=True)
    
    content = Column(Text, nullable=False)
    
    company = relationship("CRMCompany", back_populates="notes")
    contact = relationship("CRMContact", back_populates="notes")
    deal = relationship("CRMDeal", back_populates="notes")
    tenant = relationship("Tenant")

class CRMTag(Base):
    """Tags for filtering."""
    __tablename__ = "crm_tags"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    color = Column(String, default="#CCCCCC")
    
    entity_type = Column(String) # contact, company, deal
    entity_id = Column(UUID(as_uuid=True)) # Loose coupling for flexibility

class CRMConversation(Base):
    """Unified Conversation Thread (WhatsApp, maybe Email later)."""
    __tablename__ = "crm_conversations"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("crm_contacts.id"), nullable=True)
    
    channel = Column(String, default="whatsapp") # whatsapp, email
    identifier = Column(String, index=True, nullable=False) # e.g. Phone Number or Email
    
    subject = Column(String, nullable=True)
    last_message_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="open") # open, closed, archived
    unread_count = Column(Integer, default=0)
    
    contact = relationship("CRMContact", back_populates="conversations")
    tenant = relationship("Tenant")
    messages = relationship("WhatsAppMessage", back_populates="conversation")

class CRMInvoice(Base):
    """
    Invoices for DSO (Days Sales Outstanding) calculation.
    """
    __tablename__ = "crm_invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Linked to Company (Debtor)
    company_id = Column(UUID(as_uuid=True), ForeignKey("crm_companies.id"), nullable=False)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("crm_deals.id"), nullable=True)
    
    invoice_number = Column(String, nullable=False)
    
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="USD")
    
    issued_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    paid_date = Column(DateTime, nullable=True)
    
    status = Column(String, default="open") # open, paid, overdue, canceled
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    company = relationship("CRMCompany")


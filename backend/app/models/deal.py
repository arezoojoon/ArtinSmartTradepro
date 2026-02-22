"""
Deal Management for Phase 6 Enhancement
Complete deal lifecycle with parties, incoterms, documents, and margin tracking
"""
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Boolean, JSON, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime

from .base import Base


class DealStatus(str, Enum):
    IDENTIFIED = "identified"
    MATCHING = "matching"
    VALIDATING = "validating"
    NEGOTIATING = "negotiating"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    CANCELLED = "cancelled"


class DealPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Deal(Base):
    """Main deal record"""
    __tablename__ = "deals"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Basic deal information
    deal_number = Column(String(20), nullable=False, unique=True, index=True)  # Auto-generated
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Deal classification
    status = Column(String(20), nullable=False, default=DealStatus.IDENTIFIED.value, index=True)
    priority = Column(String(10), nullable=False, default=DealPriority.MEDIUM.value)
    
    # Parties
    buyer_company_id = Column(UUID(as_uuid=True), ForeignKey("crm_companies.id"), nullable=True)
    seller_company_id = Column(UUID(as_uuid=True), ForeignKey("crm_companies.id"), nullable=True)
    
    # Financial details
    currency = Column(String(3), nullable=False, default="USD")
    total_value = Column(Numeric(15, 2), nullable=True)  # Total deal value
    estimated_margin_pct = Column(Numeric(5, 2), nullable=True)  # Estimated margin percentage
    realized_margin_pct = Column(Numeric(5, 2), nullable=True)  # Realized margin after completion
    
    # Trade details
    product_category = Column(String(100), nullable=True)
    product_key = Column(String(100), nullable=True)
    incoterms = Column(String(20), nullable=True)  # FOB, CIF, EXW, etc.
    
    # Geographic details
    origin_country = Column(String(100), nullable=True)
    origin_port = Column(String(100), nullable=True)
    destination_country = Column(String(100), nullable=True)
    destination_port = Column(String(100), nullable=True)
    
    # Timeline
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True)
    actual_delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    # Team assignment
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Metadata
    tags = Column(JSON, nullable=True)  # Array of tags
    custom_fields = Column(JSON, nullable=True)  # Flexible custom fields
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="deals")
    buyer_company = relationship("CRMCompany", foreign_keys=[buyer_company_id], back_populates="buyer_deals")
    seller_company = relationship("CRMCompany", foreign_keys=[seller_company_id], back_populates="seller_deals")
    assigned_user = relationship("User", back_populates="assigned_deals")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_deals")
    
    # Deal components
    price_components = relationship("DealPriceComponent", back_populates="deal", cascade="all, delete-orphan")
    documents = relationship("DealDocument", back_populates="deal", cascade="all, delete-orphan")
    milestones = relationship("DealMilestone", back_populates="deal", cascade="all, delete-orphan")
    risk_assessments = relationship("DealRiskAssessment", back_populates="deal", cascade="all, delete-orphan")
    communications = relationship("DealCommunication", back_populates="deal", cascade="all, delete-orphan")


class DealPriceComponent(Base):
    """Price components for detailed margin calculation"""
    __tablename__ = "deal_price_components"

    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False, index=True)
    
    # Component details
    component_type = Column(String(50), nullable=False)  # buy_price, sell_price, freight, insurance, taxes, etc.
    component_name = Column(String(100), nullable=False)
    
    # Financial details
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Unit details (if applicable)
    quantity = Column(Numeric(15, 4), nullable=True)
    unit = Column(String(20), nullable=True)  # kg, tons, pieces, etc.
    unit_price = Column(Numeric(10, 4), nullable=True)
    
    # Provider information
    provider = Column(String(100), nullable=True)  # Supplier, shipping line, etc.
    
    # Metadata
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    deal = relationship("Deal", back_populates="price_components")


class DealDocument(Base):
    """Documents attached to deals"""
    __tablename__ = "deal_documents"

    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False, index=True)
    
    # Document details
    document_type = Column(String(50), nullable=False)  # contract, invoice, packing_list, bill_of_lading, etc.
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # File information
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # Status
    status = Column(String(20), nullable=False, default="draft")  # draft, uploaded, signed, verified
    signed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Upload information
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    deal = relationship("Deal", back_populates="documents")
    uploader = relationship("User", back_populates="uploaded_documents")
    signer = relationship("User", back_populates="signed_documents")


class DealMilestone(Base):
    """Milestones for deal tracking"""
    __tablename__ = "deal_milestones"

    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False, index=True)
    
    # Milestone details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    milestone_type = Column(String(50), nullable=False)  # contract_signed, payment_received, goods_shipped, etc.
    
    # Dates
    due_date = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="pending")  # pending, completed, overdue, cancelled
    
    # Responsibility
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Metadata
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    deal = relationship("Deal", back_populates="milestones")
    assignee = relationship("User", back_populates="assigned_milestones")


class DealRiskAssessment(Base):
    """Risk assessments for deals"""
    __tablename__ = "deal_risk_assessments"

    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False, index=True)
    
    # Risk details
    risk_category = Column(String(50), nullable=False)  # payment, shipping, quality, regulatory, etc.
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    risk_score = Column(Integer, nullable=False)  # 0-100
    
    # Assessment details
    description = Column(Text, nullable=False)
    mitigation_plan = Column(Text, nullable=True)
    
    # Assessment metadata
    assessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assessment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Status
    status = Column(String(20), nullable=False, default="active")  # active, mitigated, accepted
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    deal = relationship("Deal", back_populates="risk_assessments")
    assessor = relationship("User", back_populates="assessed_risks")


class DealCommunication(Base):
    """Communication records for deals"""
    __tablename__ = "deal_communications"

    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False, index=True)
    
    # Communication details
    communication_type = Column(String(50), nullable=False)  # email, phone, meeting, note
    subject = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    
    # Participants
    from_party = Column(String(100), nullable=False)  # buyer, seller, internal
    to_party = Column(String(100), nullable=False)
    
    # Contact information
    contact_person = Column(String(100), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    
    # Metadata
    direction = Column(String(20), nullable=False)  # inbound, outbound
    priority = Column(String(10), nullable=False, default="medium")
    
    # User information
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    communication_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    deal = relationship("Deal", back_populates="communications")
    creator = relationship("User", back_populates="created_communications")


class DealTemplate(Base):
    """Deal templates for quick deal creation"""
    __tablename__ = "deal_templates"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Template details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # import_export, domestic, services, etc.
    
    # Default deal structure
    default_incoterms = Column(String(20), nullable=True)
    default_currency = Column(String(3), nullable=True, default="USD")
    
    # Price component templates
    price_components = Column(JSON, nullable=True)  # Default price components structure
    
    # Milestone templates
    milestones = Column(JSON, nullable=True)  # Default milestones structure
    
    # Risk assessment templates
    risk_assessments = Column(JSON, nullable=True)  # Default risk categories to assess
    
    # Document requirements
    required_documents = Column(JSON, nullable=True)  # List of required document types
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="deal_templates")
    creator = relationship("User", back_populates="created_deal_templates")

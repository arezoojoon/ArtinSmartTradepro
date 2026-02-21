"""
Hunter Phase 4 SQLAlchemy Models
Leads + Evidence + Enrichment Jobs + RLS
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Numeric, JSON, text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import uuid

# Enums
hunter_lead_status_enum = ENUM('new', 'enriched', 'qualified', 'rejected', 'pushed_to_crm', name='hunter_lead_status')
hunter_identity_type_enum = ENUM('email', 'phone', 'domain', 'linkedin', 'address', 'other', name='hunter_identity_type')
hunter_enrichment_status_enum = ENUM('queued', 'running', 'done', 'failed', name='hunter_enrichment_status')

class HunterLead(Base):
    """
    Main lead entity with provenance tracking
    """
    __tablename__ = "hunter_leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    primary_name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    city = Column(String, nullable=True)
    website = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    source_hint = Column(String, nullable=True)  # e.g., "comtrade", "manual_import", "web"
    status = Column(hunter_lead_status_enum, nullable=False, default='new', index=True)
    score_total = Column(Integer, nullable=False, default=0)
    score_breakdown = Column(JSON, nullable=False, server_default='{}')
    created_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)

    # Relationships
    identities = relationship("HunterLeadIdentity", back_populates="lead", cascade="all, delete-orphan")
    evidence = relationship("HunterEvidence", back_populates="lead", cascade="all, delete-orphan")
    enrichment_jobs = relationship("HunterEnrichmentJob", back_populates="lead", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_hunter_leads_status', 'status'),
    )

class HunterLeadIdentity(Base):
    """
    Contact/identity information for leads with normalization
    """
    __tablename__ = "hunter_lead_identities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("hunter_leads.id"), nullable=False, index=True)
    type = Column(hunter_identity_type_enum, nullable=False)
    value = Column(String, nullable=False)
    normalized_value = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)

    # Relationships
    lead = relationship("HunterLead", back_populates="identities")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'type', 'normalized_value', name='uq_hunter_identities'),
    )

class HunterEvidence(Base):
    """
    Evidence/provenance for each lead attribute
    """
    __tablename__ = "hunter_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("hunter_leads.id"), nullable=False, index=True)
    field_name = Column(String, nullable=False, index=True)  # e.g., "website", "email", "import_volume"
    source_name = Column(String, nullable=False)  # e.g., "manual", "web_scrape", "csv_import"
    source_url = Column(String, nullable=True)
    collected_at = Column(DateTime(timezone=True), nullable=False)
    confidence = Column(Numeric(precision=3, scale=2), nullable=False)  # 0.00-1.00
    snippet = Column(String, nullable=True)  # <= 2KB evidence snippet
    raw = Column(JSON, nullable=True)  # Store raw extracted payload
    created_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)

    # Relationships
    lead = relationship("HunterLead", back_populates="evidence")

    __table_args__ = (
        Index('ix_hunter_evidence_field_name', 'field_name'),
        Index('ix_hunter_evidence_lead_field', 'tenant_id', 'lead_id', 'field_name'),
    )

class HunterEnrichmentJob(Base):
    """
    Asynchronous enrichment job tracking
    """
    __tablename__ = "hunter_enrichment_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("hunter_leads.id"), nullable=False, index=True)
    provider = Column(String, nullable=False)  # e.g., "web_basic", "clearbit", "importyeti"
    status = Column(hunter_enrichment_status_enum, nullable=False, default='queued', index=True)
    attempts = Column(Integer, nullable=False, default=0)
    scheduled_for = Column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)

    # Relationships
    lead = relationship("HunterLead", back_populates="enrichment_jobs")

    __table_args__ = (
        Index('ix_hunter_enrichment_jobs_scheduled', 'status', 'scheduled_for'),
    )

class HunterScoringProfile(Base):
    """
    Tenant-specific scoring profiles with explainable weights
    """
    __tablename__ = "hunter_scoring_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    weights = Column(JSON, nullable=False)  # Explainable weights configuration
    is_default = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)

    __table_args__ = (
        Index('ix_hunter_scoring_profiles_is_default', 'is_default'),
    )

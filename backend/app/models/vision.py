"""
CRM Vision Models — Phase D2.
Business card scan results with per-field confidence.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Numeric, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import uuid


class ScannedCard(Base):
    """
    AI-extracted business card data with per-field confidence.
    Links to AIJob for async tracking.
    Links to CRMContact when user confirms creation.
    """
    __tablename__ = "crm_scanned_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    file_path = Column(String, nullable=False)
    file_name = Column(String)
    file_hash = Column(String, nullable=True)
    file_size_bytes = Column(Integer)
    mime_type = Column(String, default="image/jpeg")

    # Extracted fields
    extracted_name = Column(String)
    extracted_company = Column(String)
    extracted_position = Column(String)
    extracted_phone = Column(String)
    extracted_email = Column(String)
    extracted_website = Column(String)
    extracted_linkedin = Column(String)
    extracted_address = Column(Text)

    # Per-field confidence
    confidence_name = Column(Numeric(3, 2), default=0.0)
    confidence_company = Column(Numeric(3, 2), default=0.0)
    confidence_phone = Column(Numeric(3, 2), default=0.0)
    confidence_email = Column(Numeric(3, 2), default=0.0)
    confidence_overall = Column(Numeric(3, 2), default=0.0)

    # Audit
    is_ai_suggested = Column(Boolean, default=True)
    contact_created_id = Column(UUID(as_uuid=True), ForeignKey("crm_contacts.id"), nullable=True)
    model_used = Column(String, default="gemini-2.5-flash")
    processing_time_seconds = Column(Numeric(6, 2))

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant")
    contact_created = relationship("CRMContact")

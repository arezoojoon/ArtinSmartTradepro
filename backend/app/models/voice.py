"""
CRM Voice Intelligence Models — Phase D1 (Clean).
Recording + Insight only. Job tracking moved to AIJob.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Numeric, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import uuid


class CRMVoiceRecording(Base):
    """Uploaded audio recordings linked to contacts."""
    __tablename__ = "crm_voice_recordings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("crm_contacts.id"), nullable=True)

    file_path = Column(String, nullable=False)
    file_name = Column(String)
    file_hash = Column(String, nullable=True)  # SHA256 for idempotency
    duration_seconds = Column(Integer)
    file_size_bytes = Column(Integer)
    mime_type = Column(String, default="audio/wav")
    credit_cost = Column(Numeric(6, 2), default=5.0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant")
    contact = relationship("CRMContact")
    insights = relationship("CRMVoiceInsight", back_populates="recording")


class CRMVoiceInsight(Base):
    """
    AI-generated insights — IMMUTABLE (append-only).
    Never update, only create new records.
    """
    __tablename__ = "crm_voice_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    recording_id = Column(UUID(as_uuid=True), ForeignKey("crm_voice_recordings.id"), nullable=False)

    transcript = Column(Text)
    sentiment = Column(String, default="NEUTRAL")
    intent = Column(String)
    action_items = Column(JSON, default=[])
    key_topics = Column(JSON, default=[])
    urgency = Column(String, default="medium")
    confidence_score = Column(Numeric(3, 2), default=0.0)

    model_used = Column(String, default="gemini-2.5-flash")
    model_version = Column(String, nullable=True)
    processing_time_seconds = Column(Numeric(6, 2))

    # Compliance
    contains_sensitive_data = Column(Boolean, default=False)
    retention_days = Column(Integer, default=365)
    disclaimer = Column(Text, default="AI-generated analysis. Verify before acting.")

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    recording = relationship("CRMVoiceRecording", back_populates="insights")
    tenant = relationship("Tenant")

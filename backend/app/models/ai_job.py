"""
Unified AI Job & Usage Models — Shared infrastructure for Voice, Vision, Brain.
Replaces per-feature job tracking with a single, scalable system.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Date, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import uuid


class AIJob(Base):
    """
    Unified async job tracker for all AI operations.
    Voice, Vision, Brain all create AIJob entries.
    Status: pending → processing → completed/failed.
    """
    __tablename__ = "ai_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    job_type = Column(String, nullable=False)  # voice_analysis, vision_scan, brain_insight
    status = Column(String, nullable=False, default="pending")  # pending, processing, completed, failed
    input_reference = Column(UUID(as_uuid=True), nullable=True)  # recording_id, image_id, etc.
    result_reference = Column(UUID(as_uuid=True), nullable=True)  # insight_id

    credit_cost = Column(Numeric(6, 2), default=0.0)
    error_message = Column(String, nullable=True)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AIUsage(Base):
    """
    Unified per-tenant rate limiting.
    Row-locked (SELECT FOR UPDATE) to prevent race conditions.
    Separate counters per AI feature type.
    """
    __tablename__ = "ai_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    usage_date = Column(Date, nullable=False, default=datetime.date.today)

    voice_daily = Column(Integer, default=0)
    voice_hourly = Column(Integer, default=0)
    vision_daily = Column(Integer, default=0)
    vision_hourly = Column(Integer, default=0)
    brain_daily = Column(Integer, default=0)
    brain_hourly = Column(Integer, default=0)

    hour_window = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'usage_date', name='uq_ai_usage_tenant_date'),
    )

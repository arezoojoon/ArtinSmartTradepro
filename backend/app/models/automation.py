"""
Automation Models — Rules engine for scheduling follow-ups and workflows.
All tables are RLS-enforced per tenant_id.
"""
import enum
from sqlalchemy import (
    Column, String, Text, Boolean, ForeignKey,
    DateTime, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PgEnum
from sqlalchemy.orm import relationship
from .base import Base


class TriggerType(str, enum.Enum):
    no_reply      = "no_reply"
    stage_changed = "stage_changed"
    new_lead      = "new_lead"

class AutomationRunStatus(str, enum.Enum):
    scheduled = "scheduled"
    executed  = "executed"
    skipped   = "skipped"
    failed    = "failed"


class Automation(Base):
    """A rule definition: trigger + conditions + actions."""
    __tablename__ = "automations"

    tenant_id    = Column(UUID(as_uuid=True), nullable=False, index=True)
    name         = Column(String(255), nullable=False)
    is_active    = Column(Boolean, default=True, nullable=False)
    trigger_type = Column(PgEnum(TriggerType, name="automation_trigger_type", create_type=True), nullable=False)
    conditions   = Column(JSONB, default=dict)   # e.g. {"minutes_no_reply": 30}
    actions      = Column(JSONB, default=dict)   # e.g. {"type": "send_template", "template_id": "..."}

    runs = relationship("AutomationRun", back_populates="automation", cascade="all, delete-orphan")


class AutomationRun(Base):
    """A scheduled execution of an automation for a specific entity."""
    __tablename__ = "automation_runs"

    tenant_id       = Column(UUID(as_uuid=True), nullable=False, index=True)
    automation_id   = Column(UUID(as_uuid=True), ForeignKey("automations.id", ondelete="CASCADE"), nullable=False)
    entity_type     = Column(String(50), nullable=False)  # 'conversation', 'deal', 'lead'
    entity_id       = Column(UUID(as_uuid=True), nullable=False)
    status          = Column(PgEnum(AutomationRunStatus, name="automation_run_status", create_type=True),
                             nullable=False, default="scheduled")
    scheduled_for   = Column(DateTime(timezone=True), nullable=False, index=True)
    executed_at     = Column(DateTime(timezone=True), nullable=True)
    idempotency_key = Column(String(255), nullable=False)
    error           = Column(JSONB, nullable=True)

    automation = relationship("Automation", back_populates="runs")

    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_automation_run_idem"),
    )


class MessageTemplate(Base):
    """Reusable message body templates with variable substitution."""
    __tablename__ = "message_templates"

    tenant_id    = Column(UUID(as_uuid=True), nullable=False, index=True)
    name         = Column(String(255), nullable=False)
    channel_type = Column(String(50),  nullable=False, default="whatsapp")
    language     = Column(String(10),  nullable=False, default="en")
    body         = Column(Text, nullable=False)
    variables    = Column(JSONB, default=list)   # e.g. ["company_name","contact_name"]

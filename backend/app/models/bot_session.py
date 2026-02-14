"""
Bot Session + Event Models — State machine for WhatsApp bot conversations.
QA-HARDENED: Deep-link gating, tenant routing, handoff lock, audit trail.
"""
import uuid
import datetime
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text, Boolean, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base


class BotDeeplinkRef(Base):
    """
    QA-2: Maps deep-link ref codes → tenant_id + optional campaign.
    Webhook resolves tenant from this table, NOT from env.
    Each tenant generates refs; visitors carry the ref in the start link.
    """
    __tablename__ = "bot_deeplink_refs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ref = Column(String, unique=True, nullable=False, index=True)   # e.g. "gulfood2026", "linkedin_ad_43"
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("crm_campaigns.id"), nullable=True)

    label = Column(String, nullable=True)         # Human-readable name
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)   # Optional expiry

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class BotSession(Base):
    """
    Active bot conversation state. One per phone per tenant.
    State machine: welcome → language → mode → collecting → done
    QA-1: HARD gating — only created via valid deep-link ref.
    QA-6: locked flag — bot goes silent after human handoff.
    """
    __tablename__ = "bot_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    phone = Column(String, nullable=False, index=True)
    whatsapp_name = Column(String, nullable=True)

    # Session config
    language = Column(String, default="en")
    mode = Column(String, nullable=True)
    state = Column(String, default="welcome")
    context = Column(JSON, default={})

    # Gating (QA-1)
    started_via_deeplink = Column(Boolean, default=False)
    deeplink_ref = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    # Handoff lock (QA-6)
    locked_for_human = Column(Boolean, default=False)

    # AI usage tracking (QA-5)
    ai_calls_today = Column(Integer, default=0)
    ai_calls_today_date = Column(String, nullable=True)   # "2026-02-11"

    # Timestamps
    last_active_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'phone', name='uq_bot_session_tenant_phone'),
    )


class BotEvent(Base):
    """
    QA-8: Complete audit trail. Every interaction logged immutably.
    event_type: inbound_text, inbound_image, inbound_audio, outbound, state_change,
                ai_vision, ai_audio, ai_market, rfq_created, booking_created,
                handoff, handoff_release, deeplink_reject, ai_limit_hit, error
    """
    __tablename__ = "bot_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("bot_sessions.id"), nullable=True, index=True)

    phone = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, default={})
    state_before = Column(String, nullable=True)
    state_after = Column(String, nullable=True)

    # QA-8: AI/billing references
    ai_job_id = Column(UUID(as_uuid=True), nullable=True)
    ai_cost = Column(Float, nullable=True)
    message_id = Column(UUID(as_uuid=True), nullable=True)   # WhatsAppMessage.id

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class WAHAWebhookEvent(Base):
    """Raw WAHA webhook payload storage for debugging and replay."""
    __tablename__ = "waha_webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    processed = Column(Boolean, default=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class WhatsAppStatusUpdate(Base):
    """Message delivery/read status updates from WAHA."""
    __tablename__ = "whatsapp_message_status_updates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    raw_payload = Column(JSON, nullable=True)

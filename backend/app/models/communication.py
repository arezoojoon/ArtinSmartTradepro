"""
Comm Models — Generic multi-channel messaging infrastructure.
Supports WhatsApp (WAHA), Email (SMTP/IMAP), Telegram etc.
All tables are RLS-enforced per tenant_id.
"""
import uuid
import enum
from sqlalchemy import (
    Column, String, Text, Boolean, ForeignKey,
    DateTime, Index, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PgEnum
from sqlalchemy.orm import relationship
from .base import Base


# ── Enum types ──────────────────────────────────────────────────────────────

class ChannelType(str, enum.Enum):
    whatsapp = "whatsapp"
    email    = "email"
    telegram = "telegram"

class ProviderType(str, enum.Enum):
    waha = "waha"
    smtp = "smtp"
    imap = "imap"

class IdentityType(str, enum.Enum):
    phone  = "phone"
    email  = "email"
    handle = "handle"

class ConversationStatus(str, enum.Enum):
    open    = "open"
    pending = "pending"
    closed  = "closed"

class MessageDirection(str, enum.Enum):
    inbound  = "inbound"
    outbound = "outbound"

class MessageStatus(str, enum.Enum):
    queued    = "queued"
    sent      = "sent"
    delivered = "delivered"
    read      = "read"
    failed    = "failed"

class MessageEventType(str, enum.Enum):
    status  = "status"
    webhook = "webhook"
    retry   = "retry"
    dlq     = "dlq"


# ── Tables ───────────────────────────────────────────────────────────────────

class CommChannel(Base):
    """A configured communication channel for a tenant (e.g. their WAHA instance)."""
    __tablename__ = "comm_channels"

    tenant_id    = Column(UUID(as_uuid=True), nullable=False, index=True)
    type         = Column(PgEnum(ChannelType,  name="comm_channel_type",  create_type=True), nullable=False)
    provider     = Column(PgEnum(ProviderType, name="comm_provider_type", create_type=True), nullable=False)
    display_name = Column(Text, nullable=False)
    config       = Column(JSONB, default=dict)   # e.g. {"session": "default"}
    is_active    = Column(Boolean, default=True, nullable=False)

    identities    = relationship("CommIdentity",    back_populates="channel", cascade="all, delete-orphan")
    conversations = relationship("CommConversation", back_populates="channel", cascade="all, delete-orphan")


class CommIdentity(Base):
    """An external party identity (phone number / email) optionally linked to a CRM entity."""
    __tablename__ = "comm_identities"

    tenant_id      = Column(UUID(as_uuid=True), nullable=False, index=True)
    channel_id     = Column(UUID(as_uuid=True), ForeignKey("comm_channels.id", ondelete="CASCADE"), nullable=False)
    identity_type  = Column(PgEnum(IdentityType, name="comm_identity_type", create_type=True), nullable=False)
    identity_value = Column(String(200), nullable=False)  # E.164 for phone
    company_id     = Column(UUID(as_uuid=True), ForeignKey("crm_companies.id", ondelete="SET NULL"), nullable=True)
    contact_id     = Column(UUID(as_uuid=True), ForeignKey("crm_contacts.id",  ondelete="SET NULL"), nullable=True)

    channel       = relationship("CommChannel",   back_populates="identities")
    company       = relationship("CRMCompany",    foreign_keys=[company_id])
    contact       = relationship("CRMContact",    foreign_keys=[contact_id])
    conversations = relationship("CommConversation", back_populates="identity")

    __table_args__ = (
        UniqueConstraint("tenant_id", "channel_id", "identity_type", "identity_value",
                         name="uq_comm_identity"),
    )


class CommConversation(Base):
    """A thread of messages between tenant and an identity on a channel."""
    __tablename__ = "comm_conversations"

    tenant_id       = Column(UUID(as_uuid=True), nullable=False, index=True)
    channel_id      = Column(UUID(as_uuid=True), ForeignKey("comm_channels.id", ondelete="CASCADE"), nullable=False)
    identity_id     = Column(UUID(as_uuid=True), ForeignKey("comm_identities.id", ondelete="CASCADE"), nullable=False)
    subject         = Column(Text, nullable=True)
    status          = Column(PgEnum(ConversationStatus, name="comm_conversation_status", create_type=True),
                             nullable=False, default="open")
    last_message_at = Column(DateTime(timezone=True), server_default=func.now())

    channel  = relationship("CommChannel",  back_populates="conversations")
    identity = relationship("CommIdentity", back_populates="conversations")
    messages = relationship("CommMessage",  back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "channel_id", "identity_id", name="uq_comm_conversation"),
    )


class CommMessage(Base):
    """A single message in a conversation (inbound or outbound)."""
    __tablename__ = "comm_messages"

    tenant_id                = Column(UUID(as_uuid=True), nullable=False, index=True)
    conversation_id          = Column(UUID(as_uuid=True), ForeignKey("comm_conversations.id", ondelete="CASCADE"), nullable=False)
    direction                = Column(PgEnum(MessageDirection, name="comm_message_direction", create_type=True), nullable=False)
    status                   = Column(PgEnum(MessageStatus, name="comm_message_status", create_type=True),
                                      nullable=False, default="queued")
    provider_message_id      = Column(String(255), nullable=True)
    sender_identity_value    = Column(String(200), nullable=True)
    recipient_identity_value = Column(String(200), nullable=True)
    body_text                = Column(Text, nullable=True)
    media                    = Column(JSONB, nullable=True)     # metadata only, no binaries
    raw_payload              = Column(JSONB, nullable=True)     # original webhook event
    error                    = Column(JSONB, nullable=True)

    conversation = relationship("CommConversation", back_populates="messages")
    events       = relationship("CommMessageEvent",  back_populates="message", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_comm_messages_conv_date", "tenant_id", "conversation_id", "created_at"),
        Index("ix_comm_messages_provider_id", "tenant_id", "provider_message_id"),
    )


class CommMessageEvent(Base):
    """Tracks delivery receipts and state changes for a message."""
    __tablename__ = "comm_message_events"

    tenant_id  = Column(UUID(as_uuid=True), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("comm_messages.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(PgEnum(MessageEventType, name="comm_message_event_type", create_type=True), nullable=False)
    event_data = Column(JSONB, default=dict)

    message = relationship("CommMessage", back_populates="events")

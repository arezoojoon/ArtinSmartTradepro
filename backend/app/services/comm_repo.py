"""
Comm Repository
================
Minimal, reusable async database functions for comm_* tables.
"""
import uuid
import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.communication import (
    CommChannel, CommIdentity, CommConversation,
    CommMessage, CommMessageEvent,
    ChannelType, ProviderType, IdentityType, MessageDirection, MessageStatus, MessageEventType
)


async def get_or_create_channel(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    channel_type: ChannelType = ChannelType.whatsapp,
    provider: ProviderType = ProviderType.waha,
    display_name: str = "WhatsApp (WAHA)",
) -> CommChannel:
    """Return existing active channel or create a default one."""
    res = await db.execute(
        select(CommChannel).where(
            CommChannel.tenant_id == tenant_id,
            CommChannel.type == channel_type,
            CommChannel.provider == provider,
            CommChannel.is_active == True,
        )
    )
    ch = res.scalar_one_or_none()
    if ch:
        return ch
    ch = CommChannel(
        tenant_id=tenant_id,
        type=channel_type,
        provider=provider,
        display_name=display_name,
        is_active=True,
    )
    db.add(ch)
    await db.flush()
    return ch


async def upsert_identity(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    channel_id: uuid.UUID,
    identity_type: IdentityType,
    identity_value: str,
    company_id: Optional[uuid.UUID] = None,
    contact_id: Optional[uuid.UUID] = None,
) -> CommIdentity:
    """Upsert a CommIdentity row. Returns the existing or newly created record."""
    res = await db.execute(
        select(CommIdentity).where(
            CommIdentity.tenant_id == tenant_id,
            CommIdentity.channel_id == channel_id,
            CommIdentity.identity_type == identity_type,
            CommIdentity.identity_value == identity_value,
        )
    )
    identity = res.scalar_one_or_none()
    if identity:
        # Update CRM links if provided
        if company_id is not None:
            identity.company_id = company_id
        if contact_id is not None:
            identity.contact_id = contact_id
        return identity
    identity = CommIdentity(
        tenant_id=tenant_id,
        channel_id=channel_id,
        identity_type=identity_type,
        identity_value=identity_value,
        company_id=company_id,
        contact_id=contact_id,
    )
    db.add(identity)
    await db.flush()
    return identity


async def get_or_create_conversation(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    channel_id: uuid.UUID,
    identity_id: uuid.UUID,
) -> CommConversation:
    """Get existing conversation or create one."""
    res = await db.execute(
        select(CommConversation).where(
            CommConversation.tenant_id == tenant_id,
            CommConversation.channel_id == channel_id,
            CommConversation.identity_id == identity_id,
        )
    )
    conv = res.scalar_one_or_none()
    if conv:
        return conv
    conv = CommConversation(
        tenant_id=tenant_id,
        channel_id=channel_id,
        identity_id=identity_id,
        status="open",
    )
    db.add(conv)
    await db.flush()
    return conv


async def append_message(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    conversation_id: uuid.UUID,
    direction: MessageDirection,
    status: MessageStatus,
    body_text: Optional[str] = None,
    sender_identity_value: Optional[str] = None,
    recipient_identity_value: Optional[str] = None,
    provider_message_id: Optional[str] = None,
    media: Optional[dict] = None,
    raw_payload: Optional[dict] = None,
) -> CommMessage:
    """Append a CommMessage to a conversation and update last_message_at."""
    msg = CommMessage(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        direction=direction,
        status=status,
        body_text=body_text,
        sender_identity_value=sender_identity_value,
        recipient_identity_value=recipient_identity_value,
        provider_message_id=provider_message_id,
        media=media,
        raw_payload=raw_payload,
    )
    db.add(msg)
    await db.flush()

    # Update conversation last_message_at
    await db.execute(
        update(CommConversation)
        .where(CommConversation.id == conversation_id)
        .values(last_message_at=datetime.datetime.utcnow())
    )
    return msg


async def append_message_event(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    message_id: uuid.UUID,
    event_type: MessageEventType,
    event_data: dict,
) -> CommMessageEvent:
    """Log a CommMessageEvent."""
    ev = CommMessageEvent(
        tenant_id=tenant_id,
        message_id=message_id,
        event_type=event_type,
        event_data=event_data,
    )
    db.add(ev)
    await db.flush()
    return ev


async def update_message_status(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    provider_message_id: str,
    new_status: MessageStatus,
    error: Optional[dict] = None,
) -> Optional[CommMessage]:
    """Update CommMessage status by provider_message_id."""
    res = await db.execute(
        select(CommMessage).where(
            CommMessage.tenant_id == tenant_id,
            CommMessage.provider_message_id == provider_message_id,
        )
    )
    msg = res.scalar_one_or_none()
    if msg:
        msg.status = new_status
        if error is not None:
            msg.error = error
    return msg

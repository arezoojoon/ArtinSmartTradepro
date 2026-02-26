"""
Audit logging helper — Phase 1 Architecture.
Every write endpoint must call log_audit() to create an audit trail.
"""
from sqlalchemy.orm import Session as SyncSession
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
import uuid
from typing import Optional


async def log_audit_async(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    details: dict = None,
    ip_address: str = None,
    user_agent: str = None,
):
    """Async audit logger for use with async DB sessions."""
    # Convert resource_id to UUID if it's a string
    rid = None
    if resource_id:
        try:
            rid = uuid.UUID(str(resource_id))
        except (ValueError, AttributeError):
            rid = None

    entry = AuditLog(
        tenant_id=tenant_id,
        user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=rid,
        metadata_json=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    # Caller is responsible for commit


def log_audit_sync(
    db: SyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    details: dict = None,
    ip_address: str = None,
    user_agent: str = None,
):
    """Sync audit logger for use with sync DB sessions (e.g. WAHA routes)."""
    # Convert resource_id to UUID if it's a string
    rid = None
    if resource_id:
        try:
            rid = uuid.UUID(str(resource_id))
        except (ValueError, AttributeError):
            rid = None

    entry = AuditLog(
        tenant_id=tenant_id,
        user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=rid,
        metadata_json=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    # Caller is responsible for commit

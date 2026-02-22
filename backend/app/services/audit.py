from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.user import User
from app.models.tenant import Tenant
import json
from uuid import UUID
from datetime import datetime

def log_audit_event(
    db: Session, 
    action: str, 
    user_id: UUID | str | None = None, 
    tenant_id: UUID | str | None = None, 
    details: dict = None,
    resource_type: str = None,
    resource_id: str | None = None,
    ip_address: str = None
):
    """
    Creates an audit log entry.
    """
    try:
        log_entry = AuditLog(
            action=action,
            user_id=user_id if user_id else None,
            tenant_id=tenant_id if tenant_id else None,
            metadata_json=details if details else {},
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            ip_address=ip_address,
            user_agent="Unknown", # Could be passed if needed
            created_at=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        # Don't crash the whole request if auditing fails
        print(f"[AUDIT ERROR] Failed to log action: {action}. Error: {e}")

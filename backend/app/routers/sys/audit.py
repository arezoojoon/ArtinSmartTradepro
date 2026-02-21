"""
/sys/audit — Super admin audit log viewer.
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.phase6 import SystemAdmin, SysAuditLog
from app.services.sys_admin_auth import get_current_sys_admin

router = APIRouter()


@router.get("", summary="Query Audit Logs")
def get_audit_logs(
    tenant_id: Optional[UUID] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: SystemAdmin = Depends(get_current_sys_admin),
):
    query = db.query(SysAuditLog)
    if tenant_id:
        query = query.filter(SysAuditLog.tenant_id == tenant_id)
    if action:
        query = query.filter(SysAuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        query = query.filter(SysAuditLog.resource_type == resource_type)

    total = query.count()
    logs = query.order_by(SysAuditLog.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": str(l.id),
                "action": l.action,
                "resource_type": l.resource_type,
                "resource_id": l.resource_id,
                "tenant_id": str(l.tenant_id) if l.tenant_id else None,
                "actor_sys_admin_id": str(l.actor_sys_admin_id) if l.actor_sys_admin_id else None,
                "before_state": l.before_state,
                "after_state": l.after_state,
                "metadata": l.metadata,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
    }

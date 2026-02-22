from fastapi import Request, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.audit import AuditLog
from app.core.auth import getattr_safe, get_current_user, get_current_tenant
import logging

logger = logging.getLogger(__name__)

async def create_audit_log(
    request: Request,
    action: str,
    resource_type: str,
    resource_id: str = None,
    old_value: dict = None,
    new_value: dict = None,
    meta: dict = None,
    db: Session = None,
    user_id: str = None,
    tenant_id: str = None
):
    """
    Core function for V3 Traceability and RBAC 2.0.
    Silently logs actions without blocking the main thread.
    """
    if not db:
        # In middleware context, db might need to be resolved
        return
        
    try:
        # Resolve IDs if not explicitly passed
        if not user_id and getattr(request.state, "user", None):
            user_id = request.state.user.id
            
        if not tenant_id and getattr(request.state, "tenant", None):
            tenant_id = request.state.tenant.id

        if not tenant_id:
            logger.warning(f"AuditLog skipped: No tenant_id for {action} {resource_type}")
            return

        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            old_value=old_value,
            new_value=new_value,
            metadata_json=meta or {}
        )
        
        db.add(audit)
        db.commit()
        
    except Exception as e:
        logger.error(f"Failed to write audit log: {str(e)}")
        # Do not rollback or raise: Audit failure should not break the user's transaction if possible,
        # but in strict mode, it might. For now, log the error.

class AuditLogger:
    """Dependency injector for route-level auditing"""
    def __init__(self, resource_type: str, action: str):
        self.resource_type = resource_type
        self.action = action

    async def __call__(
        self, 
        request: Request, 
        db: Session = Depends(get_db)
    ):
        # We attach the logger to the request state so the endpoint can call it
        # with the specific resource_id once created/modified.
        def log_event(resource_id: str, old_val: dict = None, new_val: dict = None, meta: dict = None):
            import asyncio
            # Fire and forget if needed, or await directly
            asyncio.create_task(
                create_audit_log(
                    request=request,
                    action=self.action,
                    resource_type=self.resource_type,
                    resource_id=str(resource_id),
                    old_value=old_val,
                    new_value=new_val,
                    meta=meta,
                    db=db
                )
            )
            
        request.state.audit = log_event
        return log_event

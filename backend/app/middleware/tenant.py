"""
Tenant Context Middleware — Phase 1 Architecture.
Extracts tenant_id from JWT or header and sets:
  1) ContextVar for async DB session (RLS enforcement via SET LOCAL)
  2) request.state.tenant_id for route access
"""
from fastapi import Header, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tenant import Tenant
from app.db.session import current_tenant_id
from uuid import UUID


def get_tenant(
    x_tenant_id: str = Header(None, alias="X-Tenant-ID"),
    db: Session = Depends(get_db)
) -> Tenant:
    """Legacy sync tenant resolver (used by WAHA routes)."""
    if not x_tenant_id:
        return None

    try:
        tenant_uuid = UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Tenant ID format")

    tenant = db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if not tenant.is_active:
        raise HTTPException(status_code=400, detail="Tenant is inactive")

    return tenant


def set_tenant_context(tenant_id: str | UUID) -> None:
    """
    Set the tenant context for the current request.
    This is called by auth middleware after JWT validation.
    The ContextVar is read by get_db() in db/session.py to
    execute SET LOCAL app.tenant_id for RLS enforcement.
    """
    current_tenant_id.set(str(tenant_id))


def clear_tenant_context() -> None:
    """Clear tenant context after request completes."""
    current_tenant_id.set(None)

"""
Tenant Settings Router — Integration configs & notification preferences
Provides GET/PUT endpoints for the Settings > Integrations and Settings > Notifications pages.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_active_user

router = APIRouter()


class IntegrationConfigIn(BaseModel):
    integration_name: str
    config: Dict[str, Any]


class NotificationSettingsIn(BaseModel):
    settings: Dict[str, bool]


# ─── Integration Config ──────────────────────────────────────────────

@router.get("/integrations")
def get_integrations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return all saved integration configs for the tenant."""
    from app.models.tenant_settings import IntegrationConfig

    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    rows = (
        db.query(IntegrationConfig)
        .filter(IntegrationConfig.tenant_id == tenant_id)
        .all()
    )
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "integration_type": r.integration_type,
            "config": r.config,
            "is_enabled": r.is_enabled,
            "sync_status": r.sync_status,
        }
        for r in rows
    ]


@router.put("/integrations")
def save_integration(
    body: IntegrationConfigIn,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upsert an integration config (by name) for the tenant."""
    from app.models.tenant_settings import IntegrationConfig

    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    existing = (
        db.query(IntegrationConfig)
        .filter(
            IntegrationConfig.tenant_id == tenant_id,
            IntegrationConfig.name == body.integration_name,
        )
        .first()
    )

    if existing:
        existing.config = body.config
        existing.is_enabled = True
        existing.sync_status = "success"
    else:
        new_row = IntegrationConfig(
            tenant_id=tenant_id,
            name=body.integration_name,
            integration_type=body.integration_name.lower().replace(" ", "_").replace("(", "").replace(")", ""),
            config=body.config,
            is_enabled=True,
            sync_status="success",
            created_by=current_user.id,
        )
        db.add(new_row)

    db.commit()
    return {"status": "saved", "integration": body.integration_name}


# ─── Notification Preferences ────────────────────────────────────────

@router.get("/notifications")
def get_notification_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return notification preferences for the tenant (category='notifications')."""
    from app.models.tenant_settings import TenantPreference

    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    row = (
        db.query(TenantPreference)
        .filter(
            TenantPreference.tenant_id == tenant_id,
            TenantPreference.category == "notifications",
            TenantPreference.key == "all",
        )
        .first()
    )

    if row:
        return {"settings": row.value}
    return {"settings": {}}


@router.put("/notifications")
def save_notification_settings(
    body: NotificationSettingsIn,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upsert notification preferences for the tenant."""
    from app.models.tenant_settings import TenantPreference

    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    existing = (
        db.query(TenantPreference)
        .filter(
            TenantPreference.tenant_id == tenant_id,
            TenantPreference.category == "notifications",
            TenantPreference.key == "all",
        )
        .first()
    )

    if existing:
        existing.value = body.settings
        existing.updated_by = current_user.id
    else:
        new_row = TenantPreference(
            tenant_id=tenant_id,
            category="notifications",
            key="all",
            value=body.settings,
            updated_by=current_user.id,
        )
        db.add(new_row)

    db.commit()
    return {"status": "saved"}

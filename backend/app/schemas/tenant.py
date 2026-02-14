from pydantic import BaseModel
from typing import Optional, Any, Dict
from uuid import UUID
from datetime import datetime
from app.models.tenant import TenantMode

class TenantBase(BaseModel):
    name: str
    mode: TenantMode = TenantMode.HYBRID
    settings: Optional[Dict[str, Any]] = {}

class TenantCreate(TenantBase):
    plan_id: Optional[UUID] = None

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    mode: Optional[TenantMode] = None
    settings: Optional[Dict[str, Any]] = None

class TenantRead(TenantBase):
    id: UUID
    slug: str
    domain: Optional[str] = None
    is_active: bool
    plan_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Alias for compatibility if needed
Tenant = TenantRead

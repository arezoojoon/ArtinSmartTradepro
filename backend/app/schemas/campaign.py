from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class CampaignSegmentBase(BaseModel):
    filter_json: Dict[str, Any] = {}

class CampaignCreate(BaseModel):
    name: str
    channel: str = "whatsapp"
    template_body: str
    segment: CampaignSegmentBase

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    template_body: Optional[str] = None
    status: Optional[str] = None

class CampaignMessageRead(BaseModel):
    id: UUID
    contact_id: UUID
    status: str
    sent_at: Optional[datetime]
    error: Optional[str]
    whatsapp_message_id: Optional[UUID]

    class Config:
        from_attributes = True

class CampaignRead(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    status: str
    channel: str
    template_body: Optional[str]
    total_contacts: int
    sent_count: int
    failed_count: int
    replied_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

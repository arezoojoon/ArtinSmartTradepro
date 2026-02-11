from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID

# --- Tags ---
class CRMTagBase(BaseModel):
    name: str
    color: str = "#CCCCCC"
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None

class CRMTagCreate(CRMTagBase):
    pass

class CRMTag(CRMTagBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- Notes ---
class CRMNoteBase(BaseModel):
    content: str
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None

class CRMNoteCreate(CRMNoteBase):
    pass

class CRMNote(CRMNoteBase):
    id: UUID
    tenant_id: UUID
    author_id: Optional[UUID]
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Companies ---
class CRMCompanyBase(BaseModel):
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None

class CRMCompanyCreate(CRMCompanyBase):
    pass

class CRMCompany(CRMCompanyBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    contacts: List["CRMContact"] = []
    notes: List[CRMNote] = []

    class Config:
        from_attributes = True

# --- Contacts ---
class CRMContactBase(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_id: Optional[UUID] = None

class CRMContactCreate(CRMContactBase):
    pass

class CRMContact(CRMContactBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    company: Optional[CRMCompanyBase] = None
    notes: List[CRMNote] = []

    class Config:
        from_attributes = True

# --- Pipelines ---
class CRMPipelineBase(BaseModel):
    name: str
    stages: List[dict]  # [{"id": "new", "name": "New"}, ...]
    is_default: int = 0

class CRMPipelineCreate(CRMPipelineBase):
    pass

class CRMPipeline(CRMPipelineBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- Deals ---
class CRMDealBase(BaseModel):
    name: str
    value: float = 0.0
    currency: str = "AED"
    probability: float = 0.5
    stage_id: str
    pipeline_id: UUID
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    expected_close_date: Optional[datetime] = None
    status: str = "open"

class CRMDealCreate(CRMDealBase):
    pass

class CRMDeal(CRMDealBase):
    id: UUID
    tenant_id: UUID
    closed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    pipeline: Optional[CRMPipelineBase] = None
    
    class Config:
        from_attributes = True

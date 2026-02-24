from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel


class CRMCompanyBase(BaseModel):
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None

class CRMCompanyCreate(CRMCompanyBase):
    pass

class CRMCompanyUpdate(CRMCompanyBase):
    name: Optional[str] = None

class CRMCompanyResponse(CRMCompanyBase):
    id: UUID
    tenant_id: UUID
    country: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    risk_score: Optional[float] = None
    size: Optional[str] = None

    class Config:
        from_attributes = True


class CRMContactBase(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    company_id: Optional[UUID] = None

class CRMContactCreate(CRMContactBase):
    pass

class CRMContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    company_id: Optional[UUID] = None

class CRMContactResponse(CRMContactBase):
    id: UUID
    tenant_id: UUID
    preferred_language: Optional[str] = None
    whatsapp_verified: bool = False

    class Config:
        from_attributes = True

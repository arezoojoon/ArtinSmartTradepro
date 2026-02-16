from typing import Optional
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

    class Config:
        from_attributes = True

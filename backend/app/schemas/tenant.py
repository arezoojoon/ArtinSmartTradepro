from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from uuid import UUID
from datetime import datetime
from typing import List, Optional, enum

class TenantPlan(str, enum.Enum):
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    WHITELABEL = "whitelabel"

class TenantMode(str, enum.Enum):
    BUYER = "buyer"
    SELLER = "seller"
    HYBRID = "hybrid"

class TenantRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

# Request schemas
class TenantCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Tenant name")
    slug: Optional[str] = Field(None, description="Tenant slug (auto-generated if not provided)")
    plan: TenantPlan = Field(default=TenantPlan.PROFESSIONAL, description="Tenant plan")

class TenantUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Tenant name")
    settings: Optional[Dict[str, Any]] = Field(None, description="Tenant settings")

class TenantSwitchRequest(BaseModel):
    tenant_id: UUID = Field(..., description="Target tenant ID")

class TenantInviteRequest(BaseModel):
    email: str = Field(..., description="Email to invite")
    role: TenantRole = Field(default=TenantRole.MEMBER, description="Role for invited user")

class TenantInviteAcceptRequest(BaseModel):
    token: str = Field(..., description="Invitation token")

# Response schemas
class TenantResponse(BaseModel):
    id: UUID = Field(..., description="Tenant ID")
    name: str = Field(..., description="Tenant name")
    slug: str = Field(..., description="Tenant slug")
    domain: Optional[str] = Field(None, description="Custom domain")
    plan: TenantPlan = Field(..., description="Tenant plan")
    mode: TenantMode = Field(..., description="Operating mode")
    is_active: bool = Field(..., description="Tenant active status")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Tenant settings")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True

class TenantMembershipResponse(BaseModel):
    tenant_id: UUID = Field(..., description="Tenant ID")
    tenant_name: str = Field(..., description="Tenant name")
    role: TenantRole = Field(..., description="User role in tenant")
    created_at: datetime = Field(..., description="Membership creation timestamp")

    class Config:
        from_attributes = True

class TenantListResponse(BaseModel):
    tenants: List[TenantMembershipResponse] = Field(..., description="User's tenant memberships")
    current_tenant_id: Optional[UUID] = Field(None, description="Currently selected tenant")

class TenantInvitationResponse(BaseModel):
    id: UUID = Field(..., description="Invitation ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    tenant_name: str = Field(..., description="Tenant name")
    email: str = Field(..., description="Invited email")
    role: TenantRole = Field(..., description="Invited role")
    expires_at: datetime = Field(..., description="Invitation expiration")
    created_at: datetime = Field(..., description="Invitation creation timestamp")

    class Config:
        from_attributes = True

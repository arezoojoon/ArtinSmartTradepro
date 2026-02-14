from typing import Optional
from pydantic import BaseModel, EmailStr, Field
import uuid


# Request schemas
class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=10, description="Password (min 10 chars)")
    full_name: Optional[str] = Field(None, description="User full name")


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token")
    password: str = Field(..., min_length=10, description="New password (min 10 chars)")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="JWT refresh token")


# Response schemas
class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class UserResponse(BaseModel):
    id: uuid.UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: Optional[str] = Field(None, description="User full name")
    email_verified: bool = Field(..., description="Email verification status")
    is_active: bool = Field(..., description="User active status")
    current_tenant_id: Optional[uuid.UUID] = Field(None, description="Current selected tenant")
    created_at: str = Field(..., description="Account creation timestamp")
    last_login_at: Optional[str] = Field(None, description="Last login timestamp")

    class Config:
        from_attributes = True


class MeResponse(UserResponse):
    """Extended user info for /me endpoint"""
    tenants: list["TenantResponse"] = Field(default_factory=list, description="User's tenants")


class TenantResponse(BaseModel):
    id: uuid.UUID = Field(..., description="Tenant ID")
    name: str = Field(..., description="Tenant name")
    slug: str = Field(..., description="Tenant slug")
    plan: str = Field(..., description="Tenant plan")
    role: str = Field(..., description="User's role in this tenant")
    created_at: str = Field(..., description="Tenant creation timestamp")

    class Config:
        from_attributes = True


# Update forward references
MeResponse.model_rebuild()

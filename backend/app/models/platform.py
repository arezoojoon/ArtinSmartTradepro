from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import enum
import uuid
from datetime import datetime

class TenantRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class TenantMembership(Base):
    """
    Many-to-Many link between User and Tenant.
    Stores the user's role within a specific tenant.
    """
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, default=TenantRole.MEMBER.value, nullable=False)
    
    tenant = relationship("Tenant", back_populates="memberships")
    user = relationship("User", back_populates="memberships")

class TenantInvitation(Base):
    """
    Pending invitation for a user (email) to join a tenant.
    """
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    role = Column(String, default=TenantRole.MEMBER.value, nullable=False)
    token_hash = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    
    tenant = relationship("Tenant", back_populates="invitations")

class PasswordResetToken(Base):
    """
    Token for password reset flow.
    """
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    
    user = relationship("User")

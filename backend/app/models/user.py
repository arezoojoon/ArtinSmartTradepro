from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import enum

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"

class UserPersona(str, enum.Enum):
    TRADER = "trader"
    LOGISTICS = "logistics"
    FINANCE = "finance"
    ADMIN = "admin"

class User(Base):
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String, default=UserRole.USER.value, nullable=False)
    
    # V3: User Persona for customized UX
    persona = Column(String, default=UserPersona.TRADER.value, nullable=False)
    
    # Multi-Tenancy (Many-to-Many via Membership)
    memberships = relationship("TenantMembership", back_populates="user")
    
    # Sessions
    sessions = relationship("Session", back_populates="user")

    # State
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user")
    
    # Current tenant selection
    current_tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)

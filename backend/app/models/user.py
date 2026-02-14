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
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    role = Column(String, default=UserRole.USER.value)
    
    # V3: User Persona for customized UX
    persona = Column(String, default=UserPersona.TRADER.value)
    
    # Multi-Tenancy (Many-to-Many via Membership)
    memberships = relationship("TenantMembership", back_populates="user")
    
    # Sessions
    sessions = relationship("Session", back_populates="user")

    # State
    last_login_at = Column(DateTime, nullable=True)
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user")

    # Helper: Current tenant logic is handled at request context level, 
    # but we can implement helper methods on the model if needed.

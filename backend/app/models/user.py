from sqlalchemy import Column, String, Boolean, ForeignKey, Enum
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
    role = Column(String, default=UserRole.USER.value)
    
    # V3: User Persona for customized UX
    persona = Column(String, default=UserPersona.TRADER.value)
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)  # Nullable for Super Admins
    tenant = relationship("Tenant", back_populates="users")

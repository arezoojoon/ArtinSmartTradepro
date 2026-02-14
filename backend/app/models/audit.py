from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class AuditLog(Base):
    """Audit log for tracking important actions."""
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=True)
    
    action = Column(String, index=True, nullable=False)  # login, create_tenant, billing_upgrade
    resource_type = Column(String, nullable=True)  # user, tenant, subscription
    resource_id = Column(String, nullable=True)
    
    details = Column(JSON, default={})
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    actor_user = relationship("User")

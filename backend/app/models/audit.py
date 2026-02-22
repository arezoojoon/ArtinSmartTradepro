from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class AuditLog(Base):
    """
    Mandatory Audit Log for tracking user actions and resource changes.
    Required for V3 Traceability and RBAC 2.0.
    """
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    action = Column(String, nullable=False, index=True)  # e.g., "CREATE", "UPDATE", "DELETE", "PUSH_TO_CRM"
    resource_type = Column(String, nullable=False, index=True)  # e.g., "deal", "lead", "company", "brain_run"
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Metadata for traceability
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Snapshot of changes
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    
    # Context
    metadata_json = Column(JSON, default={}, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    user = relationship("User", foreign_keys=[user_id])

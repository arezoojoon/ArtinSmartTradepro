from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class AuditLog(Base):
    tenant_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    user_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    
    action = Column(String, index=True)  # login, create_lead, delete_product
    resource_type = Column(String)  # user, lead, product
    resource_id = Column(String, nullable=True)
    
    details = Column(JSON, default={})
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

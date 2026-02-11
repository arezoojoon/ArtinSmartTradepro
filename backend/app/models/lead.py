from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class Lead(Base):
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    scraped_source_id = Column(UUID(as_uuid=True), ForeignKey("scraped_sources.id"), nullable=True)
    
    # Core Data
    company_name = Column(String, index=True)
    contact_name = Column(String, nullable=True)
    email = Column(String, index=True, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    country = Column(String, index=True, nullable=True)
    city = Column(String, nullable=True)
    
    # Enrichment
    source = Column(String)  # google_maps, linkedin, etc. (Redundant but useful for quick filters)
    intent_score = Column(Float, default=0.0)
    status = Column(String, default="new")  # new, contacted, interested, closed
    tags = Column(JSON, default=[])
    
    tenant = relationship("Tenant", back_populates="leads")
    scraped_source = relationship("ScrapedSource", back_populates="leads")

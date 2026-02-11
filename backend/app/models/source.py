from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class ScrapedSource(Base):
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    name = Column(String, nullable=False) # e.g. "Google Maps - Dubai Sugar"
    source_type = Column(String, nullable=False) # google_maps, linkedin_serp
    lead_count = Column(Integer, default=0)
    status = Column(String, default="completed")
    
    tenant = relationship("Tenant", back_populates="scraped_sources")
    leads = relationship("Lead", back_populates="scraped_source")

from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class Lead(Base):
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Core Data
    company_name = Column(String, index=True)
    contact_name = Column(String, nullable=True)
    email = Column(String, index=True, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    country = Column(String, index=True, nullable=True)
    city = Column(String, nullable=True)
    
    # Enrichment
    source = Column(String)  # google_maps, linkedin, expo, csv, etc.
    intent_score = Column(Float, default=0.0)
    status = Column(String, default="new")  # new, contacted, interested, closed
    tags = Column(JSON, default=[])
    
    # Expo Specific enhancements
    telegram_username = Column(String, nullable=True)
    lead_quality = Column(String, nullable=True) # hot, warm, cold
    aida_stage = Column(String, nullable=True) # Attention, Interest, Desire, Action
    priority = Column(String, default="medium")
    notes = Column(String, nullable=True)
    
    tenant = relationship("Tenant")


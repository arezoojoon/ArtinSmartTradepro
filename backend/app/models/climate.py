from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import datetime
import uuid

class ClimateRisk(Base):
    """
    Weather or Geopolitical risk affecting a specific region.
    Used by Execution Service to warn about active deals.
    """
    __tablename__ = "climate_risks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    region = Column(String, nullable=False) # e.g. "Red Sea", "Panama Canal"
    risk_type = Column(String, nullable=False) # storm, drought, conflict, port_congestion
    severity = Column(String, default="medium") # low, medium, high, critical
    
    description = Column(String, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

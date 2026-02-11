from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import uuid

class HunterRun(Base):
    """
    Log of a Hunter execution (scraping or API fetch).
    Linked to AIJob for async tracking.
    """
    __tablename__ = "hunter_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("ai_jobs.id"), nullable=True) # Optional link to AIJob
    
    target_keyword = Column(String, nullable=False)
    target_location = Column(String, nullable=True)
    sources = Column(JSON, nullable=False) # List of sources used ["maps", "un_comtrade"]
    
    status = Column(String, default="pending") # pending, completed, failed
    leads_found = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    results = relationship("HunterResult", back_populates="run", cascade="all, delete-orphan")


class HunterResult(Base):
    """
    Individual lead/data point found by Hunter.
    Can be converted to CRMContact/Company.
    """
    __tablename__ = "hunter_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("hunter_runs.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    source = Column(String, nullable=False) # e.g. "maps", "un_comtrade"
    type = Column(String, nullable=False) # lead, supplier, buyer, trade_data
    
    # Lead Data
    name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    address = Column(String, nullable=True)
    
    # Trade Data (JSON for flexibility)
    raw_data = Column(JSON, nullable=True) 
    
    confidence_score = Column(Numeric(5, 2), default=0.0)
    is_imported = Column(Boolean, default=False) # If true, already added to CRM
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    run = relationship("HunterRun", back_populates="results")


class TradeSignal(Base):
    """
    Raw data from Official APIs (Macro level).
    Not specific to a 'run', but global reference data (optionally tenant-scoped if paid).
    """
    __tablename__ = "trade_signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String, nullable=False) # un_comtrade, fx, weather
    category = Column(String, nullable=False) # macro, risk, tariff
    
    key_identifier = Column(String, index=True) # e.g. "USD_EUR", "CN_US_100630"
    value = Column(JSON, nullable=False)
    
    valid_from = Column(DateTime, default=datetime.datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

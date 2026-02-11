from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, JSON, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import uuid

class TradeData(Base):
    """
    Global Trade Data (e.g. UN Comtrade, TradeMap).
    Granular data for Analysis.
    """
    __tablename__ = "toolbox_trade_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # No tenant_id because this is global public data (usually), 
    # but we might want to scope it if we buy specific data for a tenant.
    # For now, let's keep it global but accessible.
    
    hs_code = Column(String, nullable=False, index=True)
    reporter_country = Column(String(3), nullable=False, index=True) # ISO3
    partner_country = Column(String(3), nullable=True, index=True) # ISO3, null = World
    
    trade_flow = Column(String, nullable=False) # import, export
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=True) # Null for annual data
    
    quantity = Column(Numeric)
    quantity_unit = Column(String)
    trade_value_usd = Column(Numeric, nullable=False)
    
    source = Column(String, default="mock") # uncomtrade, trademap, mock
    last_updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index("idx_trade_hs_reporter_year", "hs_code", "reporter_country", "trade_flow", "year"),
        Index("idx_trade_reporter_partner_year", "reporter_country", "partner_country", "year"),
    )

class FreightRate(Base):
    """
    Freight Rates (Freightos equivalent).
    Deterministic & Historical.
    """
    __tablename__ = "toolbox_freight_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    origin_country = Column(String, nullable=False)
    origin_port = Column(String, nullable=True)
    destination_country = Column(String, nullable=False)
    destination_port = Column(String, nullable=True)
    
    equipment_type = Column(String, nullable=False) # 20GP, 40GP, 40HC, AIR
    incoterm = Column(String, nullable=False) # FOB, CIF, EXW
    
    rate_amount = Column(Numeric, nullable=False)
    currency = Column(String, default="USD")
    transit_days_estimate = Column(Integer)
    
    provider = Column(String, default="mock")
    effective_date = Column(DateTime, default=datetime.datetime.utcnow)
    
    __table_args__ = (
        Index("idx_freight_route", "origin_country", "destination_country", "equipment_type", "effective_date"),
    )

class FXRateTick(Base):
    """
    FX Rates Time Series (Bloomberg equivalent).
    No volatility stored here; computed from time series.
    """
    __tablename__ = "toolbox_fx_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    base_currency = Column(String(3), nullable=False)
    quote_currency = Column(String(3), nullable=False)
    rate = Column(Numeric(18, 6), nullable=False)
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    provider = Column(String, default="mock")

    __table_args__ = (
        Index("idx_fx_pair_time", "base_currency", "quote_currency", "timestamp"),
    )

class MarketShockAlert(Base):
    """
    Deterministic Market Shocks.
    """
    __tablename__ = "toolbox_market_shocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    metric = Column(String, nullable=False) # fx_spike, freight_jump, risk_elevated, trade_shift
    baseline = Column(Numeric)
    delta = Column(Numeric)
    severity = Column(String) # low, medium, high, critical
    
    confidence = Column(Numeric, default=1.0) # 1.0 = deterministic
    message = Column(String)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_read = Column(Boolean, default=False)

class ExportJob(Base):
    """
    Secure Data Export.
    Prevents tenant data leak.
    """
    __tablename__ = "toolbox_export_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    type = Column(String, nullable=False) # crm_leads, toolbox_trade, ai_analysis
    status = Column(String, default="pending") # pending, processing, completed, failed
    
    file_path = Column(String, nullable=True) # S3 or local path
    download_url = Column(String, nullable=True) # Signed URL
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

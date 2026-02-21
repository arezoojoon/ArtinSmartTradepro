"""
Phase 5 Brain Asset Database Models
SQLAlchemy models for asset databases and brain engine infrastructure
"""
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, Date, Enum, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

Base = declarative_base()

class ArbitrageOutcome(enum.Enum):
    WON = "won"
    LOST = "lost"
    NO_GO = "no_go"
    UNKNOWN = "unknown"

class BrainEngineType(enum.Enum):
    ARBITRAGE = "arbitrage"
    RISK = "risk"
    DEMAND = "demand"
    CULTURAL = "cultural"

class BrainRunStatus(enum.Enum):
    SUCCESS = "success"
    INSUFFICIENT_DATA = "insufficient_data"
    FAILED = "failed"

class AssetArbitrageHistory(Base):
    __tablename__ = "asset_arbitrage_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_key = Column(String, nullable=False, index=True)
    buy_market = Column(String, nullable=False)
    sell_market = Column(String, nullable=False)
    incoterms = Column(String, nullable=False)
    buy_price = Column(Numeric(precision=15, scale=2), nullable=False)
    buy_currency = Column(String, nullable=False)
    sell_price = Column(Numeric(precision=15, scale=2), nullable=False)
    sell_currency = Column(String, nullable=False)
    freight_cost = Column(Numeric(precision=15, scale=2), nullable=True)
    fx_rate = Column(Numeric(precision=10, scale=6), nullable=True)
    estimated_margin_pct = Column(Numeric(precision=5, scale=2), nullable=True)
    realized_margin_pct = Column(Numeric(precision=5, scale=2), nullable=True)
    outcome = Column(Enum(ArbitrageOutcome), nullable=True)
    decision_reason = Column(String, nullable=True)
    data_used = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    __table_args__ = (
        {"schema": "public"},
    )

class AssetSupplierReliability(Base):
    __tablename__ = "asset_supplier_reliability"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name = Column(String, nullable=False, index=True)
    supplier_country = Column(String, nullable=False, index=True)
    identifiers = Column(JSON, nullable=True)
    on_time_rate = Column(Numeric(precision=5, scale=2), nullable=True)
    defect_rate = Column(Numeric(precision=5, scale=2), nullable=True)
    dispute_count = Column(Integer, server_default='0', nullable=False)
    avg_lead_time_days = Column(Integer, nullable=True)
    reliability_score = Column(Integer, server_default='0', nullable=False, index=True)
    evidence = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        {"schema": "public"},
    )

class AssetBuyerPaymentBehavior(Base):
    __tablename__ = "asset_buyer_payment_behavior"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    buyer_country = Column(String, nullable=False, index=True)
    buyer_name = Column(String, nullable=True)
    segment = Column(String, nullable=True, index=True)
    avg_payment_delay_days = Column(Integer, nullable=True)
    default_rate = Column(Numeric(precision=5, scale=2), nullable=True)
    preferred_terms = Column(String, nullable=True)
    payment_risk_score = Column(Integer, server_default='0', nullable=False, index=True)
    evidence = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        {"schema": "public"},
    )

class AssetSeasonalityMatrix(Base):
    __tablename__ = "asset_seasonality_matrix"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_key = Column(String, nullable=False, index=True)
    country = Column(String, nullable=False, index=True)
    season_key = Column(String, nullable=False, index=True)
    demand_index = Column(Numeric(precision=8, scale=3), nullable=True)
    price_index = Column(Numeric(precision=8, scale=3), nullable=True)
    volatility_index = Column(Numeric(precision=8, scale=3), nullable=True)
    data_used = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        {"schema": "public"},
    )

class BrainEngineRun(Base):
    __tablename__ = "brain_engine_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engine_type = Column(Enum(BrainEngineType), nullable=False, index=True)
    input_payload = Column(JSON, nullable=False)
    output_payload = Column(JSON, nullable=True)
    explainability = Column(JSON, nullable=True)
    status = Column(Enum(BrainRunStatus), nullable=False, index=True)
    error = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    __table_args__ = (
        {"schema": "public"},
    )

class BrainDataSource(Base):
    __tablename__ = "brain_data_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    is_active = Column(Boolean, server_default='true', nullable=False, index=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        {"schema": "public"},
    )

class CulturalProfile(Base):
    __tablename__ = "cultural_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    country = Column(String, nullable=False, index=True)
    negotiation_style = Column(JSON, nullable=True)
    do_dont = Column(JSON, nullable=True)
    typical_terms = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        {"schema": "public"},
    )

class DemandTimeSeries(Base):
    __tablename__ = "demand_time_series"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_key = Column(String, nullable=False, index=True)
    country = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    demand_value = Column(Numeric(precision=15, scale=2), nullable=True)
    source_name = Column(String, nullable=False)
    data_used = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        {"schema": "public"},
    )

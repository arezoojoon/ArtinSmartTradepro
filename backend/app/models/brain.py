from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Numeric, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import uuid

class ArbitrageResult(Base):
    __tablename__ = "brain_arbitrage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    product_hs = Column(String, nullable=False)
    origin_country = Column(String, nullable=False)
    destination_country = Column(String, nullable=False)
    
    buy_price = Column(Numeric(12, 2))
    sell_price = Column(Numeric(12, 2))
    margin_net = Column(Numeric(12, 2))
    roi_percentage = Column(Float)
    
    breakdown = Column(JSON) # Detailed cost breakdown (freight, tariff, etc.)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class RiskAssessment(Base):
    __tablename__ = "brain_risk"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    origin_country = Column(String, nullable=False)
    destination_country = Column(String, nullable=False)
    commodity = Column(String)
    
    risk_score = Column(Integer) # 0-100
    risk_level = Column(String) # Low, Medium, High
    
    factors = Column(JSON) # Political, Currency, Counterparty scores
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class DemandForecast(Base):
    __tablename__ = "brain_demand"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    commodity = Column(String, nullable=False)
    market = Column(String, nullable=False)
    forecast_period = Column(String) # "Q3 2026"
    
    predicted_growth_pct = Column(Float)
    confidence_score = Column(Float)
    
    seasonality_factors = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class CulturalStrategy(Base):
    __tablename__ = "brain_cultural"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    target_country = Column(String, nullable=False)
    deal_context = Column(String)
    
    strategy_summary = Column(String)
    do_and_donts = Column(JSON)
    negotiation_tactics = Column(JSON)
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

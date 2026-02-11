from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Numeric, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import uuid

class TradeScenario(Base):
    """
    Groups cost assumptions for a specific trade opportunity.
    Allows A/B testing: "What if freight doubles?" (Pessimistic) vs "Standard" (Base).
    """
    __tablename__ = "trade_scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    name = Column(String, nullable=False) # e.g. "Deal #105 - Base Case"
    status = Column(String, default="draft") # draft, active, archived
    
    target_margin_percent = Column(Numeric(5,2), default=15.0)
    currency = Column(String, default="USD")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    cost_components = relationship("CostComponent", back_populates="scenario")
    risk_factors = relationship("RiskFactor", back_populates="scenario")


class CostComponent(Base):
    """
    Granular cost element.
    "Transaction-Aware" means we handle fixed vs variable costs explicitly.
    """
    __tablename__ = "cost_components"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("trade_scenarios.id"), nullable=False)
    
    name = Column(String, nullable=False) # Freight, Insurance, Customs, LastMile
    cost_type = Column(String, default="variable") # fixed (per container), variable (per unit/kg)
    
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="USD")
    
    # Scenario Variant: allows overrides within the same group if we restructure later,
    # but for now TradeScenario acts as the container. 
    # We can keep this for simpler "one-table" queries if needed.
    variant = Column(String, default="base") # base, optimistic, pessimistic
    
    comments = Column(String, nullable=True)

    scenario = relationship("TradeScenario", back_populates="cost_components")


class RiskFactor(Base):
    """
    Deductions from Net Margin to calculate Risk-Adjusted Margin.
    """
    __tablename__ = "risk_factors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("trade_scenarios.id"), nullable=False)
    
    factor_type = Column(String, nullable=False) # fx_volatility, compliance, logistics_delay, payment_default
    probability = Column(Numeric(3, 2), default=0.0) # 0.00 to 1.00
    impact_percent = Column(Numeric(5, 2), default=0.0) # Impact on margin (e.g. 5%)
    
    mitigation_cost = Column(Numeric(12, 2), default=0.0) # Cost to hedge/insure
    
    description = Column(String, nullable=True)

    scenario = relationship("TradeScenario", back_populates="risk_factors")

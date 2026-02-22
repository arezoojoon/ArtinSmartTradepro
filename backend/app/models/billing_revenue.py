"""
Billing Revenue Tracking for Super Admin MRR/ARR Dashboard
Phase 6 Enhancement - Revenue analytics and churn tracking
"""
from sqlalchemy import Column, String, DateTime, Numeric, Integer, JSON, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime

from .base import Base


class RevenuePeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class RevenueEventType(str, Enum):
    SUBSCRIPTION_START = "subscription_start"
    SUBSCRIPTION_CANCEL = "subscription_cancel"
    SUBSCRIPTION_UPGRADE = "subscription_upgrade"
    SUBSCRIPTION_DOWNGRADE = "subscription_downgrade"
    USAGE_CHARGE = "usage_charge"
    ONE_TIME_PAYMENT = "one_time_payment"
    REFUND = "refund"


class RevenueSnapshot(Base):
    """Daily/Weekly/Monthly revenue snapshots for MRR/ARR calculation"""
    __tablename__ = "revenue_snapshots"

    period = Column(String(20), nullable=False, index=True)  # daily, weekly, monthly, yearly
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Revenue metrics
    mrr = Column(Numeric(12, 2), nullable=False, default=0)  # Monthly Recurring Revenue
    arr = Column(Numeric(12, 2), nullable=False, default=0)  # Annual Recurring Revenue
    nrr = Column(Numeric(12, 2), nullable=False, default=0)  # Net Revenue Retention
    
    # Customer metrics
    active_customers = Column(Integer, nullable=False, default=0)
    new_customers = Column(Integer, nullable=False, default=0)
    churned_customers = Column(Integer, nullable=False, default=0)
    
    # Usage metrics
    total_usage_units = Column(Integer, nullable=False, default=0)
    avg_usage_per_customer = Column(Numeric(10, 2), nullable=False, default=0)
    
    # Plan breakdown
    plan_breakdown = Column(JSON, nullable=False, default={})  # {"starter": {"customers": 10, "mrr": 990}, ...}
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RevenueEvent(Base):
    """Individual revenue events for tracking and churn analysis"""
    __tablename__ = "revenue_events"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Financial details
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Subscription details
    plan_code = Column(String(50), nullable=True)
    previous_plan_code = Column(String(50), nullable=True)  # For upgrades/downgrades
    
    # Usage details
    usage_metric = Column(String(50), nullable=True)  # e.g., "messages_sent", "api_calls"
    usage_quantity = Column(Integer, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    processed = Column(Boolean, default=False, nullable=False)  # For event processing
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="revenue_events")


class ChurnPrediction(Base):
    """ML-based churn prediction for proactive retention"""
    __tablename__ = "churn_predictions"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    
    # Prediction scores
    churn_probability = Column(Numeric(5, 4), nullable=False)  # 0.0000 to 1.0000
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Contributing factors
    risk_factors = Column(JSON, nullable=False)  # [{"factor": "low_usage", "weight": 0.3}, ...]
    
    # Prediction metadata
    model_version = Column(String(20), nullable=False)
    prediction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    data_freshness = Column(DateTime(timezone=True), nullable=False)  # Last data update
    
    # Action taken
    retention_action_taken = Column(Boolean, default=False, nullable=False)
    retention_action_type = Column(String(50), nullable=True)
    retention_action_date = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="churn_prediction")


class RevenueAlert(Base):
    """Automated revenue alerts for anomalies and thresholds"""
    __tablename__ = "revenue_alerts"

    alert_type = Column(String(50), nullable=False, index=True)  # mrr_drop, churn_spike, usage_anomaly
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Alert details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Metrics
    current_value = Column(Numeric(12, 2), nullable=True)
    previous_value = Column(Numeric(12, 2), nullable=True)
    threshold_value = Column(Numeric(12, 2), nullable=True)
    percentage_change = Column(Numeric(5, 2), nullable=True)
    
    # Context
    affected_tenant_ids = Column(JSON, nullable=True)  # Array of tenant UUIDs
    time_period = Column(String(20), nullable=True)  # last_7_days, last_30_days, etc.
    
    # Status
    status = Column(String(20), default="active", nullable=False)  # active, acknowledged, resolved
    acknowledged_by = Column(UUID(as_uuid=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

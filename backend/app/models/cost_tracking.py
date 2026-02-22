"""
Cost Tracking for Super Admin Dashboard
Phase 6 Enhancement - Track LLM, scraping, storage, and infrastructure costs
"""
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime

from .base import Base


class CostCategory(str, Enum):
    LLM_API = "llm_api"
    SCRAPING = "scraping"
    STORAGE = "storage"
    INFRASTRUCTURE = "infrastructure"
    BANDWIDTH = "bandwidth"
    THIRD_PARTY = "third_party"
    SUPPORT = "support"
    OTHER = "other"


class CostProvider(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    STRIPE = "stripe"
    TWILIO = "twilio"
    SENDGRID = "sendgrid"
    INTERNAL = "internal"


class CostMetric(Base):
    """Individual cost metric entries"""
    __tablename__ = "cost_metrics"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)  # Null for system-wide costs
    
    # Cost details
    category = Column(String(20), nullable=False, index=True)
    provider = Column(String(20), nullable=False, index=True)
    service = Column(String(50), nullable=False)  # e.g., "gemini-1.5-pro", "s3-storage"
    
    # Usage and cost
    usage_quantity = Column(Numeric(15, 4), nullable=False)  # e.g., tokens, GB, API calls
    usage_unit = Column(String(20), nullable=False)  # e.g., "tokens", "GB", "calls"
    unit_cost = Column(Numeric(10, 6), nullable=False)  # Cost per unit
    total_cost = Column(Numeric(12, 4), nullable=False)  # Total cost for this entry
    
    # Cost breakdown
    cost_breakdown = Column(JSON, nullable=True)  # Detailed breakdown of costs
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional context
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="cost_metrics")


class CostBudget(Base):
    """Budget tracking and alerts"""
    __tablename__ = "cost_budgets"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)  # Null for system-wide
    
    # Budget details
    category = Column(String(20), nullable=False, index=True)
    provider = Column(String(20), nullable=True)  # Null for category-wide budget
    budget_type = Column(String(20), nullable=False)  # monthly, quarterly, yearly
    
    # Budget amounts
    budget_amount = Column(Numeric(12, 2), nullable=False)
    warning_threshold = Column(Numeric(5, 2), nullable=False, default=80.0)  # Percentage
    critical_threshold = Column(Numeric(5, 2), nullable=False, default=95.0)  # Percentage
    
    # Alert settings
    alert_enabled = Column(Boolean, default=True, nullable=False)
    alert_emails = Column(JSON, nullable=True)  # Array of email addresses
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="cost_budgets")


class CostAlert(Base):
    """Cost alerts and notifications"""
    __tablename__ = "cost_alerts"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    
    # Alert details
    alert_type = Column(String(20), nullable=False)  # budget_warning, budget_critical, cost_spike
    category = Column(String(20), nullable=False)
    provider = Column(String(20), nullable=True)
    
    # Alert data
    current_spend = Column(Numeric(12, 2), nullable=False)
    budget_amount = Column(Numeric(12, 2), nullable=True)
    percentage_used = Column(Numeric(5, 2), nullable=False)
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Alert content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Status
    status = Column(String(20), default="active", nullable=False)  # active, acknowledged, resolved
    acknowledged_by = Column(UUID(as_uuid=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="cost_alerts")


class CostForecast(Base):
    """Cost forecasting and predictions"""
    __tablename__ = "cost_forecasts"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    
    # Forecast details
    category = Column(String(20), nullable=False, index=True)
    provider = Column(String(20), nullable=True)
    
    # Forecast period
    forecast_period = Column(String(10), nullable=False)  # YYYY-MM format
    forecast_start = Column(DateTime(timezone=True), nullable=False)
    forecast_end = Column(DateTime(timezone=True), nullable=False)
    
    # Forecast values
    predicted_cost = Column(Numeric(12, 2), nullable=False)
    confidence_level = Column(Numeric(3, 2), nullable=False)  # 0.00 to 1.00
    
    # Model information
    model_version = Column(String(20), nullable=False)
    training_data_period = Column(String(20), nullable=True)  # e.g., "2023-01-01:2023-12-31"
    
    # Forecast breakdown
    cost_drivers = Column(JSON, nullable=True)  # Factors influencing the forecast
    assumptions = Column(JSON, nullable=True)  # Forecast assumptions
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="cost_forecasts")


class CostOptimization(Base):
    """Cost optimization recommendations"""
    __tablename__ = "cost_optimizations"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    
    # Optimization details
    category = Column(String(20), nullable=False)
    provider = Column(String(20), nullable=True)
    
    # Recommendation
    recommendation_type = Column(String(30), nullable=False)  # switch_provider, reduce_usage, optimize_config
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Potential savings
    current_monthly_cost = Column(Numeric(12, 2), nullable=False)
    projected_monthly_savings = Column(Numeric(12, 2), nullable=False)
    savings_percentage = Column(Numeric(5, 2), nullable=False)
    
    # Implementation
    implementation_complexity = Column(String(20), nullable=False)  # low, medium, high
    implementation_steps = Column(JSON, nullable=True)  # Array of implementation steps
    risks = Column(JSON, nullable=True)  # Potential risks
    
    # Status
    status = Column(String(20), default="pending", nullable=False)  # pending, in_progress, completed, rejected
    priority = Column(String(10), nullable=False, default="medium")  # low, medium, high
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="cost_optimizations")


class CostSummary(Base):
    """Aggregated cost summaries for reporting"""
    __tablename__ = "cost_summaries"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    
    # Summary period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(10), nullable=False)  # daily, weekly, monthly, yearly
    
    # Total costs
    total_cost = Column(Numeric(12, 2), nullable=False)
    
    # Category breakdown
    llm_cost = Column(Numeric(12, 2), nullable=False, default=0)
    scraping_cost = Column(Numeric(12, 2), nullable=False, default=0)
    storage_cost = Column(Numeric(12, 2), nullable=False, default=0)
    infrastructure_cost = Column(Numeric(12, 2), nullable=False, default=0)
    bandwidth_cost = Column(Numeric(12, 2), nullable=False, default=0)
    third_party_cost = Column(Numeric(12, 2), nullable=False, default=0)
    support_cost = Column(Numeric(12, 2), nullable=False, default=0)
    other_cost = Column(Numeric(12, 2), nullable=False, default=0)
    
    # Provider breakdown
    provider_breakdown = Column(JSON, nullable=False, default={})  # {"gemini": 1000, "aws": 500, ...}
    
    # Usage metrics
    total_tokens = Column(Integer, nullable=False, default=0)
    total_api_calls = Column(Integer, nullable=False, default=0)
    total_storage_gb = Column(Numeric(10, 2), nullable=False, default=0)
    total_bandwidth_gb = Column(Numeric(10, 2), nullable=False, default=0)
    
    # Cost efficiency metrics
    cost_per_token = Column(Numeric(10, 6), nullable=True)  # Average cost per token
    cost_per_api_call = Column(Numeric(10, 6), nullable=True)  # Average cost per API call
    cost_per_gb_storage = Column(Numeric(8, 4), nullable=True)  # Cost per GB of storage
    
    # Comparison metrics
    previous_period_cost = Column(Numeric(12, 2), nullable=True)
    cost_change_percentage = Column(Numeric(5, 2), nullable=True)
    cost_change_amount = Column(Numeric(12, 2), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="cost_summaries")

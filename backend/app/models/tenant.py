from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import enum
from datetime import datetime

class TenantPlan(str, enum.Enum):
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    WHITELABEL = "whitelabel"

class TenantMode(str, enum.Enum):
    BUYER = "buyer"
    SELLER = "seller"
    HYBRID = "hybrid"

class TenantRole(str, enum.Enum):
    OWNER = "owner"
    TRADE_MANAGER = "trade_manager"
    SALES_AGENT = "sales_agent"
    SOURCING_AGENT = "sourcing_agent"
    FINANCE = "finance"
    OPS_LOGISTICS = "ops_logistics"
    VIEWER = "viewer"

class Tenant(Base):
    name = Column(String, index=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    domain = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSON, default={})
    
    # V3: Operating Mode
    mode = Column(String, default=TenantMode.HYBRID.value, nullable=False)

    # Plan = source of truth for features (NEVER null after registration)
    plan = Column(String, default=TenantPlan.PROFESSIONAL.value, nullable=False)
    
    # Explicit timestamp columns (matching Base)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    # Multi-Tenancy (Many-to-Many via Membership)
    memberships = relationship("TenantMembership", back_populates="tenant")
    invitations = relationship("TenantInvitation", back_populates="tenant")
    whatsapp_messages = relationship("WhatsAppMessage", back_populates="tenant")
    
    # Billing relationships
    billing_customers = relationship("BillingCustomer", back_populates="tenant")
    subscriptions = relationship("Subscription", back_populates="tenant")
    invoices = relationship("Invoice", back_populates="tenant")
    wallets = relationship("Wallet", back_populates="tenant")
    revenue_events = relationship("RevenueEvent", back_populates="tenant")
    churn_prediction = relationship("ChurnPrediction", back_populates="tenant")
    support_tickets = relationship("SupportTicket", back_populates="tenant")
    cost_metrics = relationship("CostMetric", back_populates="tenant")
    cost_budgets = relationship("CostBudget", back_populates="tenant")
    cost_alerts = relationship("CostAlert", back_populates="tenant")
    cost_forecasts = relationship("CostForecast", back_populates="tenant")
    cost_optimizations = relationship("CostOptimization", back_populates="tenant")
    cost_summaries = relationship("CostSummary", back_populates="tenant")
    deals = relationship("Deal", back_populates="tenant")
    deal_templates = relationship("DealTemplate", back_populates="tenant")
    
    # Advanced settings relationships
    custom_pipelines = relationship("CustomPipeline", back_populates="tenant")
    scoring_profiles = relationship("ScoringProfile", back_populates="tenant")
    alert_rules = relationship("AlertRule", back_populates="tenant")
    custom_email_templates = relationship("CustomEmailTemplate", back_populates="tenant")
    integration_configs = relationship("IntegrationConfig", back_populates="tenant")
    api_keys = relationship("ApiKey", back_populates="tenant")
    webhook_configs = relationship("WebhookConfig", back_populates="tenant")
    preferences = relationship("TenantPreference", back_populates="tenant")
    feature_flags = relationship("FeatureFlag", back_populates="tenant")



class TenantMembership(Base):
    """Many-to-many relationship between users and tenants."""
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String, default=TenantRole.VIEWER.value, nullable=False)
    
    # Explicit timestamp columns (matching Base)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="memberships")
    user = relationship("User", back_populates="memberships")


class TenantInvitation(Base):
    """Invitations for users to join tenants."""
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String, nullable=False)
    role = Column(String, default=TenantRole.VIEWER.value, nullable=False)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    invited_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="invitations")
    invited_by = relationship("User")

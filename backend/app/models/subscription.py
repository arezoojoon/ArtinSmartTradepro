from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class Plan(Base):
    """Subscription plan definition. Stored in DB, not hardcoded."""
    name = Column(String, unique=True, nullable=False)        # professional, enterprise, white_label
    display_name = Column(String, nullable=False)              # "Professional", "Enterprise", "White Label"
    price_monthly = Column(Numeric(12, 2), default=0.00)
    price_yearly = Column(Numeric(12, 2), default=0.00)
    currency = Column(String(3), default="AED")
    is_white_label = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    stripe_price_id_monthly = Column(String, nullable=True)    # Stripe Price ID for monthly
    stripe_price_id_yearly = Column(String, nullable=True)     # Stripe Price ID for yearly
    
    features = relationship("PlanFeature", back_populates="plan")
    subscriptions = relationship("Subscription", back_populates="plan")

class PlanFeature(Base):
    """Feature flags per plan. Read from DB, cached in memory."""
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    feature_key = Column(String, nullable=False, index=True)   # Must match constants.Feature values
    
    plan = relationship("Plan", back_populates="features")

class Subscription(Base):
    """A tenant's active subscription."""
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), unique=True, nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    
    # Stripe fields
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True, unique=True)
    
    # Lifecycle
    status = Column(String, default="active")    # active, past_due, canceled, trialing
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    
    tenant = relationship("Tenant", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base

class CheckoutSessionStatus(str, enum.Enum):
    OPEN = "open"
    COMPLETED = "completed"
    EXPIRED = "expired"

class ProvisioningState(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    READY = "ready"
    PARTIAL = "partial"
    FAILED = "failed"

class BillingCheckoutSession(Base):
    """Binds a Stripe Checkout Session to a specific Tenant and User for security."""
    __tablename__ = "billing_checkout_sessions"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    stripe_session_id = Column(String, unique=True, nullable=False, index=True)
    stripe_customer_id = Column(String, nullable=True)
    plan_code = Column(String, nullable=False)  # professional, enterprise
    status = Column(SQLEnum(CheckoutSessionStatus), default=CheckoutSessionStatus.OPEN)
    mode = Column(String, default="subscription") # subscription, setup
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant = relationship("Tenant")
    user = relationship("User")

class StripeEvent(Base):
    """Ensures Webhook Idempotency by tracking processed Event IDs."""
    __tablename__ = "stripe_events"

    event_id = Column(String, primary_key=True) # Stripe Event ID (e.g. evt_...)
    event_type = Column(String, nullable=False)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())

class ProvisioningStatus(Base):
    """Tracks the status of automated resource setup after purchase."""
    __tablename__ = "tenant_provisioning_status"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), primary_key=True)
    overall_status = Column(SQLEnum(ProvisioningState), default=ProvisioningState.PENDING)
    
    waha_status = Column(SQLEnum(ProvisioningState), default=ProvisioningState.PENDING)
    crm_status = Column(SQLEnum(ProvisioningState), default=ProvisioningState.PENDING)
    telegram_status = Column(SQLEnum(ProvisioningState), default=ProvisioningState.PENDING)
    
    waha_session_name = Column(String, nullable=True)
    qr_ref = Column(String, nullable=True)
    telegram_deeplink = Column(String, nullable=True)
    
    retry_count = Column(Integer, default=0)
    last_error = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant = relationship("Tenant")

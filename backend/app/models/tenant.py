from sqlalchemy import Column, String, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import enum

class TenantMode(str, enum.Enum):
    BUYER = "buyer"
    SELLER = "seller"
    HYBRID = "hybrid"

class Tenant(Base):
    name = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    domain = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default={})
    
    # V3: Operating Mode
    mode = Column(String, default=TenantMode.HYBRID.value)

    # Plan = source of truth for features (NEVER null after registration)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=True)
    
    # Relationships
    # Multi-Tenancy (Many-to-Many via Membership)
    memberships = relationship("TenantMembership", back_populates="tenant")
    invitations = relationship("TenantInvitation", back_populates="tenant")
    
    # Relationships
    leads = relationship("Lead", back_populates="tenant")
    wallets = relationship("Wallet", back_populates="tenant")
    whatsapp_messages = relationship("WhatsAppMessage", back_populates="tenant")
    scraped_sources = relationship("ScrapedSource", back_populates="tenant")
    plan = relationship("Plan")  # Plan controls features
    subscription = relationship("Subscription", back_populates="tenant", uselist=False)  # Subscription controls billing
    billing_customers = relationship("BillingCustomer", back_populates="tenant")
    invoices = relationship("Invoice", back_populates="tenant")
    products = relationship("Product", back_populates="tenant")

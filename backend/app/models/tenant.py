from sqlalchemy import Column, String, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class Tenant(Base):
    name = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    domain = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default={})
    
    # Plan = source of truth for features (NEVER null after registration)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    leads = relationship("Lead", back_populates="tenant")
    wallets = relationship("Wallet", back_populates="tenant")
    whatsapp_messages = relationship("WhatsAppMessage", back_populates="tenant")
    scraped_sources = relationship("ScrapedSource", back_populates="tenant")
    plan = relationship("Plan")  # Plan controls features
    subscription = relationship("Subscription", back_populates="tenant", uselist=False)  # Subscription controls billing
    products = relationship("Product", back_populates="tenant")

from sqlalchemy import Column, String, ForeignKey, DateTime, Numeric, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import enum

class SubscriptionStatus(str, enum.Enum):
    TRIALING = "trialing"
    ACTIVE = "active"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"

class BillingProvider(str, enum.Enum):
    STRIPE = "stripe"
    LOCAL_STUB = "local_stub"

class Wallet(Base):
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), unique=True, nullable=False)
    # Use Numeric for financial calculations to avoid floating point errors
    balance = Column(Numeric(12, 2), default=0.00, nullable=False)
    currency = Column(String(3), default="AED", nullable=False)
    
    tenant = relationship("Tenant", back_populates="wallets")
    transactions = relationship("WalletTransaction", back_populates="wallet")

class WalletTransaction(Base):
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String, nullable=False)  # credit, debit
    description = Column(String, nullable=False)
    reference_id = Column(String, nullable=True)  # Stripe Charge ID or internal ref
    status = Column(String, default="completed") # pending, completed, failed
    
    wallet = relationship("Wallet", back_populates="transactions")

class BillingCustomer(Base):
    """
    Stores payment provider customer IDs (Stripe, etc.)
    """
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    provider = Column(String, default=BillingProvider.STRIPE.value, nullable=False)
    provider_customer_id = Column(String, nullable=False, index=True)
    
    tenant = relationship("Tenant", back_populates="billing_customers")



class Invoice(Base):
    """
    Invoices from payment provider.
    """
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    provider_invoice_id = Column(String, nullable=False, unique=True, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="usd", nullable=False)
    status = Column(String, default="draft", nullable=False)  # draft, open, paid, void, uncollectible
    hosted_url = Column(String, nullable=True) # Link to provider invoice page
    pdf_url = Column(String, nullable=True)
    
    tenant = relationship("Tenant", back_populates="invoices")

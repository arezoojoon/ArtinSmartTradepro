from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Numeric, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import uuid

class Supplier(Base):
    """
    Enhanced Supplier model for Sourcing Intelligence.
    Tracks reliability and capacity.
    """
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    name = Column(String, nullable=False, index=True)
    country = Column(String, nullable=True) # ISO code
    categories = Column(JSON, default=list) # e.g. ["electronics", "pcb"]
    
    # Intelligence Scores
    reliability_score = Column(Numeric(5, 2), default=50.0) # 0-100
    capacity_index = Column(Numeric(5, 2), default=50.0) # 0-100 (Factory load/scale)
    
    is_audit_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    quotes = relationship("SupplierQuote", back_populates="supplier")
    issues = relationship("SupplierIssue", back_populates="supplier")


class RFQ(Base):
    """
    Request For Quote - The starting point of a Buy-Side trade.
    """
    __tablename__ = "rfqs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    hs_code = Column(String, nullable=True, index=True)
    product_name = Column(String, nullable=False)
    product_specs = Column(JSON, nullable=True) # Tech specs, grades, packaging
    
    target_qty = Column(Numeric(12, 2), nullable=False)
    target_incoterm = Column(String, nullable=True) # e.g. FOB, CIF
    
    deadline = Column(DateTime, nullable=True)
    status = Column(String, default="draft") # draft, open, closed, awarded
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    quotes = relationship("SupplierQuote", back_populates="rfq")


class SupplierQuote(Base):
    """
    A specific offer from a supplier for an RFQ.
    Comparing these is key to the "Sourcing Engine".
    """
    __tablename__ = "supplier_quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    
    # Commercial Terms
    incoterm = Column(String, nullable=False) # FOB, EXW, DDP
    unit_price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="USD")
    
    moq = Column(Numeric(12, 2), default=0)
    lead_time_days = Column(Integer, nullable=True)
    
    payment_terms = Column(String, nullable=True) # e.g. "30% Advance, 70% LC"
    valid_until = Column(DateTime, nullable=True)
    
    is_selected = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    supplier = relationship("Supplier", back_populates="quotes")
    rfq = relationship("RFQ", back_populates="quotes")


class SupplierIssue(Base):
    """
    Logs negative events to impact reliability score.
    Critical for 'Explainable Reliability'.
    """
    __tablename__ = "supplier_issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    
    issue_type = Column(String, nullable=False) # delay, quality, documents, communication
    severity = Column(Integer, default=1) # 1 (minor) to 5 (critical)
    description = Column(Text, nullable=True)
    
    evidence_doc_id = Column(String, nullable=True) # Link to document vault
    
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    supplier = relationship("Supplier", back_populates="issues")

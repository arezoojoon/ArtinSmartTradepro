from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, JSON
from app.models.crm import CRMCompany
from app.models.sourcing import Supplier
from app.models.financial import TradeScenario
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import uuid

class OutreachQueue(Base):
    """
    Queue for automated outreach (Campaigns, Follow-ups).
    Execution Layer picks these up.
    """
    __tablename__ = "execution_outreach_queue"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    contact_id = Column(UUID(as_uuid=True), ForeignKey("crm_contacts.id"), nullable=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("crm_campaigns.id"), nullable=True)
    
    channel = Column(String, nullable=False) # email, whatsapp, linkedin
    status = Column(String, default="pending") # pending, processing, sent, failed
    
    scheduled_for = Column(DateTime, default=datetime.datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    
    content_payload = Column(JSON) # Template ID, variables, etc.
    error_log = Column(String, nullable=True)
    

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class TradeOpportunity(Base):
    """
    The 'One-Click' Deal Object.
    Connects [Hunter: Buyer] + [Sourcing: Supplier] + [Finance: Scenario].
    """
    __tablename__ = "trade_opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    title = Column(String, nullable=False) # e.g. "Sell Tiles to ABC Corp"
    
    # The Triad
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("crm_companies.id"), nullable=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True)
    financial_scenario_id = Column(UUID(as_uuid=True), ForeignKey("trade_scenarios.id"), nullable=True)
    
    # State
    stage = Column(String, default="identified") # identified, matching, validating, negotiating, closed_won, closed_lost
    win_probability = Column(Integer, default=50) # 0-100
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships (Optional, for easy access)
    buyer = relationship("CRMCompany", foreign_keys=[buyer_id])
    supplier = relationship("Supplier", foreign_keys=[supplier_id])
    financial_scenario = relationship("TradeScenario", foreign_keys=[financial_scenario_id])

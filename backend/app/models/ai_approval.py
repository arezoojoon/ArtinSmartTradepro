"""
AI Approval Queue — Human-in-the-Loop Model
Pillar 4: Every sensitive AI action requires human approval before execution.
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, JSON, Boolean, Integer, Enum, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import enum
import uuid


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


class ApprovalPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ApprovalCategory(str, enum.Enum):
    OUTBOUND_MESSAGE = "outbound_message"
    PRICE_QUOTE = "price_quote"
    PROFORMA_INVOICE = "proforma_invoice"
    LEAD_CONTACT = "lead_contact"
    SHIPMENT_UPDATE = "shipment_update"
    PAYMENT_ACTION = "payment_action"
    CRM_UPDATE = "crm_update"
    DOCUMENT_ROUTING = "document_routing"
    BULK_CAMPAIGN = "bulk_campaign"
    VOICE_COMMAND = "voice_command"


class AIApprovalQueue(Base):
    """
    Every AI-generated action that touches external systems or sensitive data
    goes through this queue for human approval.
    """
    __tablename__ = "ai_approval_queue"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # What AI wants to do
    category = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # The actual payload AI prepared
    ai_payload = Column(JSON, nullable=False, default={})
    
    # AI confidence and reasoning
    ai_confidence = Column(Float, default=0.0)
    ai_reasoning = Column(Text, nullable=True)
    
    # Source context
    source_type = Column(String, nullable=True)  # voice_command, document_scan, hunter, auto_followup
    source_id = Column(String, nullable=True)  # ID of the source (voice recording, document, etc.)
    source_preview = Column(Text, nullable=True)  # Human-readable preview of source
    
    # Status
    status = Column(String, default=ApprovalStatus.PENDING.value, nullable=False, index=True)
    priority = Column(String, default=ApprovalPriority.MEDIUM.value, nullable=False)
    
    # Who approved/rejected
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_note = Column(Text, nullable=True)
    
    # Execution result
    executed = Column(Boolean, default=False)
    execution_result = Column(JSON, nullable=True)
    execution_error = Column(Text, nullable=True)
    
    # Expiry
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")


class AIActionLog(Base):
    """
    Audit log for all AI actions — both approved and auto-executed.
    """
    __tablename__ = "ai_action_logs"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    approval_id = Column(UUID(as_uuid=True), ForeignKey("ai_approval_queue.id"), nullable=True)
    
    action_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    payload = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    
    was_auto_approved = Column(Boolean, default=False)
    confidence = Column(Float, default=0.0)
    
    tenant = relationship("Tenant")

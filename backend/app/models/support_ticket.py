"""
Support Ticketing System for Super Admin
Phase 6 Enhancement - Tenant support with ticket management and escalation
"""
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime

from .base import Base


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    PENDING_INTERNAL = "pending_internal"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketCategory(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    SECURITY = "security"
    OTHER = "other"


class SupportTicket(Base):
    """Main support ticket model"""
    __tablename__ = "support_tickets"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Ticket details
    ticket_number = Column(String(20), nullable=False, unique=True, index=True)  # Auto-generated
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Classification
    category = Column(String(20), nullable=False, default=TicketCategory.OTHER.value)
    priority = Column(String(10), nullable=False, default=TicketPriority.MEDIUM.value)
    status = Column(String(20), nullable=False, default=TicketStatus.OPEN.value, index=True)
    
    # Contact information
    contact_name = Column(String(100), nullable=False)
    contact_email = Column(String(255), nullable=False)
    
    # Assignment and escalation
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("system_admins.id"), nullable=True, index=True)
    escalated = Column(Boolean, default=False, nullable=False)
    escalation_level = Column(Integer, default=0, nullable=False)  # 0=none, 1=L1, 2=L2, 3=management
    
    # Timestamps
    first_response_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)  # SLA due date
    
    # Metadata
    tags = Column(JSON, nullable=True)  # Array of tags
    custom_fields = Column(JSON, nullable=True)  # Flexible custom fields
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="support_tickets")
    assigned_admin = relationship("SystemAdmin", back_populates="assigned_tickets")
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")
    time_logs = relationship("TicketTimeLog", back_populates="ticket", cascade="all, delete-orphan")


class TicketMessage(Base):
    """Messages within a support ticket"""
    __tablename__ = "ticket_messages"

    ticket_id = Column(UUID(as_uuid=True), ForeignKey("support_tickets.id"), nullable=False, index=True)
    
    # Message details
    message_type = Column(String(20), nullable=False, default="message")  # message, note, system_update
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False, nullable=False)  # True = internal note, False = customer visible
    
    # Author information
    author_type = Column(String(20), nullable=False)  # customer, admin, system
    author_id = Column(UUID(as_uuid=True), nullable=True)  # Customer ID or Admin ID
    author_name = Column(String(100), nullable=False)
    author_email = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    ticket = relationship("SupportTicket", back_populates="messages")


class TicketAttachment(Base):
    """File attachments for support tickets"""
    __tablename__ = "ticket_attachments"

    ticket_id = Column(UUID(as_uuid=True), ForeignKey("support_tickets.id"), nullable=False, index=True)
    
    # File details
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # Upload information
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("system_admins.id"), nullable=True)
    uploaded_by_customer = Column(UUID(as_uuid=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    ticket = relationship("SupportTicket", back_populates="attachments")


class TicketTimeLog(Base):
    """Time tracking for support tickets"""
    __tablename__ = "ticket_time_logs"

    ticket_id = Column(UUID(as_uuid=True), ForeignKey("support_tickets.id"), nullable=False, index=True)
    
    # Time details
    admin_id = Column(UUID(as_uuid=True), ForeignKey("system_admins.id"), nullable=False, index=True)
    time_spent_minutes = Column(Integer, nullable=False)
    activity_type = Column(String(50), nullable=False)  # investigation, response, resolution, etc.
    description = Column(Text, nullable=True)
    
    # Billing information
    billable = Column(Boolean, default=True, nullable=False)
    hourly_rate = Column(Integer, nullable=True)  # In cents
    
    logged_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    ticket = relationship("SupportTicket", back_populates="time_logs")
    admin = relationship("SystemAdmin", back_populates="time_logs")


class TicketTemplate(Base):
    """Ticket response templates"""
    __tablename__ = "ticket_templates"

    name = Column(String(100), nullable=False)
    subject = Column(String(200), nullable=True)
    category = Column(String(20), nullable=False)
    priority = Column(String(10), nullable=False)
    
    # Template content
    template_text = Column(Text, nullable=False)
    variables = Column(JSON, nullable=True)  # Array of variable names for substitution
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("system_admins.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("SystemAdmin")


class TicketSla(Base):
    """SLA definitions for different ticket categories and priorities"""
    __tablename__ = "ticket_slas"

    category = Column(String(20), nullable=False)
    priority = Column(String(10), nullable=False)
    
    # SLA times (in hours)
    first_response_time = Column(Integer, nullable=False)  # Hours to first response
    resolution_time = Column(Integer, nullable=False)  # Hours to resolution
    
    # Business hours configuration
    business_hours_only = Column(Boolean, default=False, nullable=False)
    business_hours_start = Column(String(5), nullable=True)  # "09:00"
    business_hours_end = Column(String(5), nullable=True)    # "17:00"
    business_days_only = Column(Boolean, default=False, nullable=False)  # Mon-Fri only
    
    # Escalation rules
    auto_escalate_hours = Column(Integer, nullable=True)  # Auto-escalate after X hours
    escalation_priority = Column(String(10), nullable=True)  # Priority when escalated
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TicketMetrics(Base):
    """Aggregated metrics for reporting"""
    __tablename__ = "ticket_metrics"

    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(10), nullable=False)  # daily, weekly, monthly
    
    # Metrics
    total_tickets = Column(Integer, nullable=False, default=0)
    open_tickets = Column(Integer, nullable=False, default=0)
    resolved_tickets = Column(Integer, nullable=False, default=0)
    
    # Response times
    avg_first_response_hours = Column(Integer, nullable=False, default=0)
    avg_resolution_hours = Column(Integer, nullable=False, default=0)
    
    # SLA compliance
    sla_first_response_compliance = Column(Integer, nullable=False, default=0)  # Percentage
    sla_resolution_compliance = Column(Integer, nullable=False, default=0)  # Percentage
    
    # Breakdown by category
    category_breakdown = Column(JSON, nullable=False, default={})  # {"billing": {"count": 10, "resolved": 8}, ...}
    
    # Breakdown by priority
    priority_breakdown = Column(JSON, nullable=False, default={})  # {"high": {"count": 5, "resolved": 3}, ...}
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

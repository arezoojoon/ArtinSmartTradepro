"""
/sys/support — Support Ticketing System
Phase 6 Enhancement - Tenant support with ticket management and escalation
"""
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.database import get_db
from app.models.phase6 import SystemAdmin
from app.models.tenant import Tenant
from app.models.support_ticket import (
    SupportTicket, TicketMessage, TicketAttachment, TicketTimeLog,
    TicketTemplate, TicketSla, TicketMetrics,
    TicketStatus, TicketPriority, TicketCategory
)
from app.services.sys_admin_auth import get_current_sys_admin, write_sys_audit

router = APIRouter()


# Pydantic Models
class TicketCreate(BaseModel):
    tenant_id: str
    subject: str
    description: str
    category: str
    priority: str
    contact_name: str
    contact_email: str
    tags: Optional[List[str]] = None


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    escalated: Optional[bool] = None
    tags: Optional[List[str]] = None


class MessageCreate(BaseModel):
    content: str
    is_internal: bool = False


class TimeLogCreate(BaseModel):
    time_spent_minutes: int
    activity_type: str
    description: Optional[str] = None
    billable: bool = True


class TicketResponse(BaseModel):
    id: str
    ticket_number: str
    tenant_id: str
    tenant_name: str
    subject: str
    description: str
    category: str
    priority: str
    status: str
    contact_name: str
    contact_email: str
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    escalated: bool
    escalation_level: int
    first_response_at: Optional[str] = None
    resolved_at: Optional[str] = None
    due_date: Optional[str] = None
    tags: List[str]
    created_at: str
    updated_at: str
    message_count: int
    last_message_at: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    ticket_id: str
    message_type: str
    content: str
    is_internal: bool
    author_type: str
    author_name: str
    author_email: Optional[str]
    created_at: str


class TicketMetricsResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    avg_first_response_hours: float
    avg_resolution_hours: float
    sla_first_response_compliance: float
    sla_resolution_compliance: float


@router.get("", response_model=List[TicketResponse], summary="List Support Tickets")
def list_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> List[TicketResponse]:
    """
    List support tickets with filtering options
    """
    query = db.query(SupportTicket).join(Tenant)
    
    # Apply filters
    if status:
        query = query.filter(SupportTicket.status == status)
    if priority:
        query = query.filter(SupportTicket.priority == priority)
    if category:
        query = query.filter(SupportTicket.category == category)
    if tenant_id:
        query = query.filter(SupportTicket.tenant_id == tenant_id)
    if assigned_to:
        query = query.filter(SupportTicket.assigned_to == assigned_to)
    
    # Order by created date (newest first)
    query = query.order_by(SupportTicket.created_at.desc())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    tickets = query.offset(offset).limit(limit).all()
    
    # Build response
    ticket_responses = []
    for ticket in tickets:
        # Get message count and last message
        message_count = db.query(TicketMessage).filter(TicketMessage.ticket_id == ticket.id).count()
        last_message = db.query(TicketMessage).filter(
            TicketMessage.ticket_id == ticket.id
        ).order_by(TicketMessage.created_at.desc()).first()
        
        # Get assigned admin name
        assigned_to_name = None
        if ticket.assigned_to:
            assigned_admin = db.query(SystemAdmin).filter(SystemAdmin.id == ticket.assigned_to).first()
            assigned_to_name = assigned_admin.name if assigned_admin else None
        
        ticket_responses.append(TicketResponse(
            id=str(ticket.id),
            ticket_number=ticket.ticket_number,
            tenant_id=str(ticket.tenant_id),
            tenant_name=ticket.tenant.name if ticket.tenant else "Unknown",
            subject=ticket.subject,
            description=ticket.description,
            category=ticket.category,
            priority=ticket.priority,
            status=ticket.status,
            contact_name=ticket.contact_name,
            contact_email=ticket.contact_email,
            assigned_to=str(ticket.assigned_to) if ticket.assigned_to else None,
            assigned_to_name=assigned_to_name,
            escalated=ticket.escalated,
            escalation_level=ticket.escalation_level,
            first_response_at=ticket.first_response_at.isoformat() if ticket.first_response_at else None,
            resolved_at=ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            due_date=ticket.due_date.isoformat() if ticket.due_date else None,
            tags=ticket.tags or [],
            created_at=ticket.created_at.isoformat(),
            updated_at=ticket.updated_at.isoformat(),
            message_count=message_count,
            last_message_at=last_message.created_at.isoformat() if last_message else None
        ))
    
    # Log audit
    write_sys_audit(
        db=db,
        action="list_support_tickets",
        resource_type="support",
        actor_sys_admin_id=admin.id,
        metadata={
            "filters": {"status": status, "priority": priority, "category": category},
            "total": total,
            "returned": len(ticket_responses)
        }
    )
    
    return ticket_responses


@router.post("", response_model=TicketResponse, summary="Create Support Ticket")
def create_ticket(
    ticket_data: TicketCreate,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> TicketResponse:
    """
    Create a new support ticket
    """
    # Validate tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == ticket_data.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Generate ticket number
    ticket_number = generate_ticket_number(db)
    
    # Calculate due date based on SLA
    due_date = calculate_due_date(db, ticket_data.category, ticket_data.priority)
    
    # Create ticket
    ticket = SupportTicket(
        tenant_id=ticket_data.tenant_id,
        ticket_number=ticket_number,
        subject=ticket_data.subject,
        description=ticket_data.description,
        category=ticket_data.category,
        priority=ticket_data.priority,
        contact_name=ticket_data.contact_name,
        contact_email=ticket_data.contact_email,
        tags=ticket_data.tags,
        due_date=due_date
    )
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    # Create initial message
    initial_message = TicketMessage(
        ticket_id=ticket.id,
        message_type="message",
        content=ticket_data.description,
        is_internal=False,
        author_type="admin",
        author_id=admin.id,
        author_name=admin.name or "System Admin",
        author_email=admin.email
    )
    
    db.add(initial_message)
    db.commit()
    
    # Log audit
    write_sys_audit(
        db=db,
        action="create_support_ticket",
        resource_type="support",
        resource_id=str(ticket.id),
        actor_sys_admin_id=admin.id,
        before_state=None,
        after_state={
            "ticket_number": ticket_number,
            "tenant_id": ticket_data.tenant_id,
            "priority": ticket_data.priority,
            "category": ticket_data.category
        }
    )
    
    return TicketResponse(
        id=str(ticket.id),
        ticket_number=ticket.ticket_number,
        tenant_id=str(ticket.tenant_id),
        tenant_name=tenant.name,
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority,
        status=ticket.status,
        contact_name=ticket.contact_name,
        contact_email=ticket.contact_email,
        assigned_to=None,
        assigned_to_name=None,
        escalated=ticket.escalated,
        escalation_level=ticket.escalation_level,
        first_response_at=None,
        resolved_at=None,
        due_date=ticket.due_date.isoformat() if ticket.due_date else None,
        tags=ticket.tags or [],
        created_at=ticket.created_at.isoformat(),
        updated_at=ticket.updated_at.isoformat(),
        message_count=1,
        last_message_at=initial_message.created_at.isoformat()
    )


@router.get("/{ticket_id}", response_model=TicketResponse, summary="Get Support Ticket")
def get_ticket(
    ticket_id: str,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> TicketResponse:
    """
    Get detailed support ticket information
    """
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get message count and last message
    message_count = db.query(TicketMessage).filter(TicketMessage.ticket_id == ticket.id).count()
    last_message = db.query(TicketMessage).filter(
        TicketMessage.ticket_id == ticket.id
    ).order_by(TicketMessage.created_at.desc()).first()
    
    # Get assigned admin name
    assigned_to_name = None
    if ticket.assigned_to:
        assigned_admin = db.query(SystemAdmin).filter(SystemAdmin.id == ticket.assigned_to).first()
        assigned_to_name = assigned_admin.name if assigned_admin else None
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_support_ticket",
        resource_type="support",
        resource_id=ticket_id,
        actor_sys_admin_id=admin.id
    )
    
    return TicketResponse(
        id=str(ticket.id),
        ticket_number=ticket.ticket_number,
        tenant_id=str(ticket.tenant_id),
        tenant_name=ticket.tenant.name if ticket.tenant else "Unknown",
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority,
        status=ticket.status,
        contact_name=ticket.contact_name,
        contact_email=ticket.contact_email,
        assigned_to=str(ticket.assigned_to) if ticket.assigned_to else None,
        assigned_to_name=assigned_to_name,
        escalated=ticket.escalated,
        escalation_level=ticket.escalation_level,
        first_response_at=ticket.first_response_at.isoformat() if ticket.first_response_at else None,
        resolved_at=ticket.resolved_at.isoformat() if ticket.resolved_at else None,
        due_date=ticket.due_date.isoformat() if ticket.due_date else None,
        tags=ticket.tags or [],
        created_at=ticket.created_at.isoformat(),
        updated_at=ticket.updated_at.isoformat(),
        message_count=message_count,
        last_message_at=last_message.created_at.isoformat() if last_message else None
    )


@router.put("/{ticket_id}", response_model=TicketResponse, summary="Update Support Ticket")
def update_ticket(
    ticket_id: str,
    ticket_update: TicketUpdate,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> TicketResponse:
    """
    Update support ticket
    """
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Store before state
    before_state = {
        "status": ticket.status,
        "priority": ticket.priority,
        "assigned_to": str(ticket.assigned_to) if ticket.assigned_to else None,
        "escalated": ticket.escalated
    }
    
    # Update fields
    if ticket_update.status:
        ticket.status = ticket_update.status
        if ticket_update.status == TicketStatus.RESOLVED.value:
            ticket.resolved_at = datetime.utcnow()
    
    if ticket_update.priority:
        ticket.priority = ticket_update.priority
    
    if ticket_update.assigned_to is not None:
        ticket.assigned_to = UUID(ticket_update.assigned_to) if ticket_update.assigned_to else None
    
    if ticket_update.escalated is not None:
        ticket.escalated = ticket_update.escalated
        if ticket_update.escalated:
            ticket.escalation_level = (ticket.escalation_level or 0) + 1
    
    if ticket_update.tags is not None:
        ticket.tags = ticket_update.tags
    
    ticket.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Log audit
    write_sys_audit(
        db=db,
        action="update_support_ticket",
        resource_type="support",
        resource_id=ticket_id,
        actor_sys_admin_id=admin.id,
        before_state=before_state,
        after_state={
            "status": ticket.status,
            "priority": ticket.priority,
            "assigned_to": str(ticket.assigned_to) if ticket.assigned_to else None,
            "escalated": ticket.escalated
        }
    )
    
    # Return updated ticket
    return get_ticket(ticket_id, admin, db)


@router.get("/{ticket_id}/messages", response_model=List[MessageResponse], summary="Get Ticket Messages")
def get_ticket_messages(
    ticket_id: str,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> List[MessageResponse]:
    """
    Get all messages for a ticket
    """
    # Verify ticket exists
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get messages
    messages = db.query(TicketMessage).filter(
        TicketMessage.ticket_id == ticket_id
    ).order_by(TicketMessage.created_at.asc()).all()
    
    message_responses = []
    for message in messages:
        message_responses.append(MessageResponse(
            id=str(message.id),
            ticket_id=str(message.ticket_id),
            message_type=message.message_type,
            content=message.content,
            is_internal=message.is_internal,
            author_type=message.author_type,
            author_name=message.author_name,
            author_email=message.author_email,
            created_at=message.created_at.isoformat()
        ))
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_ticket_messages",
        resource_type="support",
        resource_id=ticket_id,
        actor_sys_admin_id=admin.id,
        metadata={"message_count": len(message_responses)}
    )
    
    return message_responses


@router.post("/{ticket_id}/messages", response_model=MessageResponse, summary="Add Ticket Message")
def add_ticket_message(
    ticket_id: str,
    message_data: MessageCreate,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Add a message to a ticket
    """
    # Verify ticket exists
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Create message
    message = TicketMessage(
        ticket_id=ticket.id,
        message_type="message",
        content=message_data.content,
        is_internal=message_data.is_internal,
        author_type="admin",
        author_id=admin.id,
        author_name=admin.name or "System Admin",
        author_email=admin.email
    )
    
    db.add(message)
    
    # Update ticket first response time if this is the first admin response
    if not ticket.first_response_at and not message_data.is_internal:
        ticket.first_response_at = datetime.utcnow()
        ticket.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(message)
    
    # Log audit
    write_sys_audit(
        db=db,
        action="add_ticket_message",
        resource_type="support",
        resource_id=ticket_id,
        actor_sys_admin_id=admin.id,
        metadata={
            "message_id": str(message.id),
            "is_internal": message_data.is_internal
        }
    )
    
    return MessageResponse(
        id=str(message.id),
        ticket_id=str(message.ticket_id),
        message_type=message.message_type,
        content=message.content,
        is_internal=message.is_internal,
        author_type=message.author_type,
        author_name=message.author_name,
        author_email=message.author_email,
        created_at=message.created_at.isoformat()
    )


@router.get("/metrics/summary", response_model=TicketMetricsResponse, summary="Get Ticket Metrics")
def get_ticket_metrics(
    days: int = Query(30, description="Number of days for metrics"),
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> TicketMetricsResponse:
    """
    Get ticket metrics for reporting
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get tickets in date range
    tickets = db.query(SupportTicket).filter(
        SupportTicket.created_at >= start_date,
        SupportTicket.created_at <= end_date
    ).all()
    
    # Calculate metrics
    total_tickets = len(tickets)
    open_tickets = len([t for t in tickets if t.status in [TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value]])
    resolved_tickets = len([t for t in tickets if t.status == TicketStatus.RESOLVED.value])
    
    # Calculate response times
    first_response_times = []
    resolution_times = []
    
    for ticket in tickets:
        if ticket.first_response_at:
            response_hours = (ticket.first_response_at - ticket.created_at).total_seconds() / 3600
            first_response_times.append(response_hours)
        
        if ticket.resolved_at:
            resolution_hours = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
            resolution_times.append(resolution_hours)
    
    avg_first_response_hours = sum(first_response_times) / len(first_response_times) if first_response_times else 0
    avg_resolution_hours = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    
    # Calculate SLA compliance (simplified)
    sla_first_response_compliance = 85.0  # Mock value
    sla_resolution_compliance = 78.0  # Mock value
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_ticket_metrics",
        resource_type="support",
        actor_sys_admin_id=admin.id,
        metadata={"days": days, "total_tickets": total_tickets}
    )
    
    return TicketMetricsResponse(
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        resolved_tickets=resolved_tickets,
        avg_first_response_hours=avg_first_response_hours,
        avg_resolution_hours=avg_resolution_hours,
        sla_first_response_compliance=sla_first_response_compliance,
        sla_resolution_compliance=sla_resolution_compliance
    )


# Helper functions
def generate_ticket_number(db: Session) -> str:
    """Generate unique ticket number"""
    # Get current date in YYYYMMDD format
    date_str = datetime.utcnow().strftime("%Y%m%d")
    
    # Get count of tickets created today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(SupportTicket).filter(
        SupportTicket.created_at >= today_start
    ).count()
    
    # Generate ticket number: TICKET-YYYYMMDD-NNNN
    ticket_number = f"TICKET-{date_str}-{today_count + 1:04d}"
    
    # Ensure uniqueness
    existing = db.query(SupportTicket).filter(SupportTicket.ticket_number == ticket_number).first()
    if existing:
        # Add random suffix if collision
        import random
        ticket_number = f"TICKET-{date_str}-{random.randint(1000, 9999)}"
    
    return ticket_number


def calculate_due_date(db: Session, category: str, priority: str) -> datetime:
    """Calculate due date based on SLA"""
    # Get SLA for category and priority
    sla = db.query(TicketSla).filter(
        TicketSla.category == category,
        TicketSla.priority == priority,
        TicketSla.is_active == True
    ).first()
    
    if not sla:
        # Default SLA: 24 hours for first response
        return datetime.utcnow() + timedelta(hours=24)
    
    # Calculate due date based on business hours if configured
    if sla.business_hours_only:
        # Simplified business hours calculation
        # In production, this would account for weekends and business hours
        return datetime.utcnow() + timedelta(hours=sla.first_response_time)
    else:
        return datetime.utcnow() + timedelta(hours=sla.first_response_time)

"""
CRM Router — CRUD for Contacts, Companies, Pipelines, Deals, Notes, Tags.
All endpoints require authentication and tenant scoping.
Advanced features gated to CRM_ADVANCED plan.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.crm import (
    CRMCompany, CRMContact, CRMPipeline, CRMDeal,
    CRMNote, CRMTag, CRMConversation
)
from app.middleware.auth import get_current_active_user
from app.middleware.plan_gate import require_feature
from app.constants import Feature
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────

class ContactCreate(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company_id: Optional[UUID] = None
    position: Optional[str] = None
    source: Optional[str] = "manual"
    notes: Optional[str] = None

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company_id: Optional[UUID] = None
    position: Optional[str] = None
    source: Optional[str] = None

class CompanyCreate(BaseModel):
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None

class PipelineCreate(BaseModel):
    name: str
    stages: Optional[list] = ["Lead", "Contacted", "Proposal", "Negotiation", "Won", "Lost"]

class DealCreate(BaseModel):
    title: str
    contact_id: UUID
    pipeline_id: UUID
    stage: Optional[str] = "Lead"
    value: Optional[float] = 0.0
    currency: Optional[str] = "AED"

class DealUpdate(BaseModel):
    title: Optional[str] = None
    stage: Optional[str] = None
    value: Optional[float] = None

class NoteCreate(BaseModel):
    contact_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None
    body: str

class TagCreate(BaseModel):
    name: str
    color: Optional[str] = "#3B82F6"


# ─── Contacts ─────────────────────────────────────────────────────────

@router.get("/contacts")
@require_feature(Feature.CRM_BASIC)
async def list_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List contacts for current tenant with optional search."""
    query = db.query(CRMContact).filter(CRMContact.tenant_id == current_user.tenant_id)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (CRMContact.first_name.ilike(search_filter)) |
            (CRMContact.last_name.ilike(search_filter)) |
            (CRMContact.email.ilike(search_filter)) |
            (CRMContact.phone.ilike(search_filter))
        )
    total = query.count()
    contacts = query.order_by(CRMContact.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "contacts": contacts}


@router.post("/contacts")
@require_feature(Feature.CRM_BASIC)
async def create_contact(
    data: ContactCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new contact."""
    contact = CRMContact(
        tenant_id=current_user.tenant_id,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        company_id=data.company_id,
        position=data.position,
        source=data.source,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.get("/contacts/{contact_id}")
@require_feature(Feature.CRM_BASIC)
async def get_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get single contact by ID."""
    contact = db.query(CRMContact).filter(
        CRMContact.id == contact_id,
        CRMContact.tenant_id == current_user.tenant_id,
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.put("/contacts/{contact_id}")
@require_feature(Feature.CRM_BASIC)
async def update_contact(
    contact_id: UUID,
    data: ContactUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a contact."""
    contact = db.query(CRMContact).filter(
        CRMContact.id == contact_id,
        CRMContact.tenant_id == current_user.tenant_id,
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/contacts/{contact_id}")
@require_feature(Feature.CRM_BASIC)
async def delete_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a contact."""
    contact = db.query(CRMContact).filter(
        CRMContact.id == contact_id,
        CRMContact.tenant_id == current_user.tenant_id,
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(contact)
    db.commit()
    return {"detail": "Contact deleted"}


# ─── Companies ────────────────────────────────────────────────────────

@router.get("/companies")
@require_feature(Feature.CRM_BASIC)
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List companies for current tenant."""
    query = db.query(CRMCompany).filter(CRMCompany.tenant_id == current_user.tenant_id)
    total = query.count()
    companies = query.order_by(CRMCompany.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "companies": companies}


@router.post("/companies")
@require_feature(Feature.CRM_BASIC)
async def create_company(
    data: CompanyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new company."""
    company = CRMCompany(
        tenant_id=current_user.tenant_id,
        name=data.name,
        website=data.website,
        industry=data.industry,
        country=data.country,
        city=data.city,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/companies/{company_id}")
@require_feature(Feature.CRM_BASIC)
async def get_company(
    company_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get single company by ID."""
    company = db.query(CRMCompany).filter(
        CRMCompany.id == company_id,
        CRMCompany.tenant_id == current_user.tenant_id,
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/companies/{company_id}")
@require_feature(Feature.CRM_BASIC)
async def update_company(
    company_id: UUID,
    data: CompanyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a company."""
    company = db.query(CRMCompany).filter(
        CRMCompany.id == company_id,
        CRMCompany.tenant_id == current_user.tenant_id,
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(company, field, value)

    db.commit()
    db.refresh(company)
    return company


@router.delete("/companies/{company_id}")
@require_feature(Feature.CRM_BASIC)
async def delete_company(
    company_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a company."""
    company = db.query(CRMCompany).filter(
        CRMCompany.id == company_id,
        CRMCompany.tenant_id == current_user.tenant_id,
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
    return {"detail": "Company deleted"}


# ─── Pipelines ────────────────────────────────────────────────────────

@router.get("/pipelines")
@require_feature(Feature.CRM_ADVANCED)
async def list_pipelines(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List pipelines for current tenant."""
    query = db.query(CRMPipeline).filter(
        CRMPipeline.tenant_id == current_user.tenant_id
    )
    total = query.count()
    pipelines = query.offset(skip).limit(limit).all()
    return {"total": total, "pipelines": pipelines}


@router.post("/pipelines")
@require_feature(Feature.CRM_ADVANCED)
async def create_pipeline(
    data: PipelineCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new pipeline."""
    pipeline = CRMPipeline(
        tenant_id=current_user.tenant_id,
        name=data.name,
        stages=data.stages,
    )
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return pipeline


# ─── Deals ────────────────────────────────────────────────────────────

@router.get("/deals")
@require_feature(Feature.CRM_ADVANCED)
async def list_deals(
    pipeline_id: Optional[UUID] = None,
    stage: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List deals with optional pipeline/stage filter."""
    query = db.query(CRMDeal).filter(CRMDeal.tenant_id == current_user.tenant_id)
    if pipeline_id:
        query = query.filter(CRMDeal.pipeline_id == pipeline_id)
    if stage:
        query = query.filter(CRMDeal.stage == stage)
    total = query.count()
    deals = query.order_by(CRMDeal.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "deals": deals}


@router.post("/deals")
@require_feature(Feature.CRM_ADVANCED)
async def create_deal(
    data: DealCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new deal."""
    deal = CRMDeal(
        tenant_id=current_user.tenant_id,
        title=data.title,
        contact_id=data.contact_id,
        pipeline_id=data.pipeline_id,
        stage=data.stage,
        value=data.value,
        currency=data.currency,
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


@router.put("/deals/{deal_id}")
@require_feature(Feature.CRM_ADVANCED)
async def update_deal(
    deal_id: UUID,
    data: DealUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update deal (move stage, update value)."""
    deal = db.query(CRMDeal).filter(
        CRMDeal.id == deal_id,
        CRMDeal.tenant_id == current_user.tenant_id,
    ).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(deal, field, value)

    db.commit()
    db.refresh(deal)
    return deal


# ─── Notes ────────────────────────────────────────────────────────────

@router.post("/notes")
@require_feature(Feature.CRM_BASIC)
async def create_note(
    data: NoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Add a note to a contact or deal."""
    if not data.contact_id and not data.deal_id:
        raise HTTPException(status_code=400, detail="contact_id or deal_id is required")

    note = CRMNote(
        tenant_id=current_user.tenant_id,
        contact_id=data.contact_id,
        deal_id=data.deal_id,
        body=data.body,
        created_by=current_user.id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/contacts/{contact_id}/notes")
@require_feature(Feature.CRM_BASIC)
async def list_contact_notes(
    contact_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List notes for a contact."""
    notes = db.query(CRMNote).filter(
        CRMNote.contact_id == contact_id,
        CRMNote.tenant_id == current_user.tenant_id,
    ).order_by(CRMNote.created_at.desc()).all()
    return notes


# ─── Tags ─────────────────────────────────────────────────────────────

@router.get("/tags")
@require_feature(Feature.CRM_BASIC)
async def list_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all tags for the tenant."""
    query = db.query(CRMTag).filter(CRMTag.tenant_id == current_user.tenant_id)
    total = query.count()
    tags = query.offset(skip).limit(limit).all()
    return {"total": total, "tags": tags}


@router.post("/tags")
@require_feature(Feature.CRM_BASIC)
async def create_tag(
    data: TagCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new tag."""
    tag = CRMTag(
        tenant_id=current_user.tenant_id,
        name=data.name,
        color=data.color,
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


# ─── Conversations / Inbox ───────────────────────────────────────────

@router.get("/conversations")
@require_feature(Feature.CRM_ADVANCED)
async def list_conversations(
    contact_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List CRM conversations (inbox)."""
    query = db.query(CRMConversation).filter(
        CRMConversation.tenant_id == current_user.tenant_id
    )
    if contact_id:
        query = query.filter(CRMConversation.contact_id == contact_id)
    if status:
        query = query.filter(CRMConversation.status == status)

    total = query.count()
    conversations = query.order_by(
        CRMConversation.last_message_at.desc()
    ).offset(skip).limit(limit).all()
    return {"total": total, "conversations": conversations}


@router.get("/conversations/{conversation_id}")
@require_feature(Feature.CRM_ADVANCED)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get conversation with messages."""
    conv = db.query(CRMConversation).filter(
        CRMConversation.id == conversation_id,
        CRMConversation.tenant_id == current_user.tenant_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


# ─── Stats ────────────────────────────────────────────────────────────

@router.get("/stats")
@require_feature(Feature.CRM_BASIC)
async def crm_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """CRM overview stats for the dashboard."""
    tid = current_user.tenant_id
    total_contacts = db.query(func.count(CRMContact.id)).filter(
        CRMContact.tenant_id == tid
    ).scalar() or 0
    total_companies = db.query(func.count(CRMCompany.id)).filter(
        CRMCompany.tenant_id == tid
    ).scalar() or 0
    total_deals = db.query(func.count(CRMDeal.id)).filter(
        CRMDeal.tenant_id == tid
    ).scalar() or 0
    total_pipeline_value = db.query(func.sum(CRMDeal.value)).filter(
        CRMDeal.tenant_id == tid
    ).scalar() or 0

    return {
        "total_contacts": total_contacts,
        "total_companies": total_companies,
        "total_deals": total_deals,
        "total_pipeline_value": float(total_pipeline_value),
    }

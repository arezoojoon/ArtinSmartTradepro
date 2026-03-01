"""
Deals Router - Complete Deal Management
Phase 6 Enhancement - Full deal lifecycle with parties, incoterms, documents, and margin tracking
"""
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.deal import (
    Deal, DealPriceComponent, DealDocument, DealMilestone, DealRiskAssessment,
    DealCommunication, DealTemplate, DealStatus, DealPriority
)
from app.models.crm import CRMCompany
from app.middleware.auth import get_current_active_user

router = APIRouter()


# Pydantic Models
class DealCreate(BaseModel):
    title: str
    description: Optional[str] = None
    buyer_company_id: Optional[str] = None
    seller_company_id: Optional[str] = None
    currency: str = "USD"
    product_category: Optional[str] = None
    product_key: Optional[str] = None
    incoterms: Optional[str] = None
    origin_country: Optional[str] = None
    origin_port: Optional[str] = None
    destination_country: Optional[str] = None
    destination_port: Optional[str] = None
    expected_delivery_date: Optional[str] = None
    priority: str = DealPriority.MEDIUM.value
    tags: Optional[List[str]] = None


class DealUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    buyer_company_id: Optional[str] = None
    seller_company_id: Optional[str] = None
    total_value: Optional[float] = None
    estimated_margin_pct: Optional[float] = None
    expected_delivery_date: Optional[str] = None
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None


class DealResponse(BaseModel):
    id: str
    deal_number: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    currency: str
    total_value: Optional[float]
    estimated_margin_pct: Optional[float]
    realized_margin_pct: Optional[float]
    product_category: Optional[str]
    product_key: Optional[str]
    incoterms: Optional[str]
    origin_country: Optional[str]
    origin_port: Optional[str]
    destination_country: Optional[str]
    destination_port: Optional[str]
    expected_delivery_date: Optional[str]
    actual_delivery_date: Optional[str]
    buyer_company_id: Optional[str]
    buyer_company_name: Optional[str]
    seller_company_id: Optional[str]
    seller_company_name: Optional[str]
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    created_by: str
    created_by_name: Optional[str]
    tags: List[str]
    created_at: str
    updated_at: str
    closed_at: Optional[str]
    document_count: int
    milestone_count: int
    risk_count: int


class PriceComponentCreate(BaseModel):
    component_type: str
    component_name: str
    amount: float
    currency: str = "USD"
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    provider: Optional[str] = None
    notes: Optional[str] = None


class PriceComponentResponse(BaseModel):
    id: str
    component_type: str
    component_name: str
    amount: float
    currency: str
    quantity: Optional[float]
    unit: Optional[str]
    unit_price: Optional[float]
    provider: Optional[str]
    notes: Optional[str]
    created_at: str


class MilestoneCreate(BaseModel):
    title: str
    description: Optional[str] = None
    milestone_type: str
    due_date: str
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class MilestoneResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    milestone_type: str
    due_date: str
    completed_at: Optional[str]
    status: str
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    notes: Optional[str]
    created_at: str


class DocumentResponse(BaseModel):
    id: str
    document_type: str
    title: str
    description: Optional[str]
    original_filename: str
    file_size: int
    status: str
    signed_by: Optional[str]
    signed_by_name: Optional[str]
    signed_at: Optional[str]
    uploaded_by: str
    uploaded_by_name: Optional[str]
    uploaded_at: str


class RiskAssessmentCreate(BaseModel):
    risk_category: str
    risk_level: str
    risk_score: int
    description: str
    mitigation_plan: Optional[str] = None


class RiskAssessmentResponse(BaseModel):
    id: str
    risk_category: str
    risk_level: str
    risk_score: int
    description: str
    mitigation_plan: Optional[str]
    assessed_by: str
    assessed_by_name: Optional[str]
    assessment_date: str
    status: str
    created_at: str


def generate_deal_number(db: Session) -> str:
    """Generate unique deal number"""
    # Get current date in YYYYMMDD format
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    
    # Get count of deals created today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(Deal).filter(
        Deal.created_at >= today_start
    ).count()
    
    # Generate deal number: DEAL-YYYYMMDD-NNNN
    deal_number = f"DEAL-{date_str}-{today_count + 1:04d}"
    
    # Ensure uniqueness
    existing = db.query(Deal).filter(Deal.deal_number == deal_number).first()
    if existing:
        # Add random suffix if collision
        import random
        deal_number = f"DEAL-{date_str}-{random.randint(1000, 9999)}"
    
    return deal_number


@router.get("", response_model=List[DealResponse], summary="List Deals")
def list_deals(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[DealResponse]:
    """
    List deals with filtering options
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    query = db.query(Deal).filter(Deal.tenant_id == tenant_id)
    
    # Apply filters
    if status:
        query = query.filter(Deal.status == status)
    if priority:
        query = query.filter(Deal.priority == priority)
    if assigned_to:
        query = query.filter(Deal.assigned_to == UUID(assigned_to))
    
    # Order by created date (newest first)
    query = query.order_by(Deal.created_at.desc())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    deals = query.offset(offset).limit(limit).all()
    
    # Build response
    deal_responses = []
    for deal in deals:
        # Get counts
        document_count = db.query(DealDocument).filter(DealDocument.deal_id == deal.id).count()
        milestone_count = db.query(DealMilestone).filter(DealMilestone.deal_id == deal.id).count()
        risk_count = db.query(DealRiskAssessment).filter(DealRiskAssessment.deal_id == deal.id).count()
        
        # Get company names
        buyer_name = None
        if deal.buyer_company_id:
            buyer = db.query(CRMCompany).filter(CRMCompany.id == deal.buyer_company_id).first()
            buyer_name = buyer.name if buyer else None
        
        seller_name = None
        if deal.seller_company_id:
            seller = db.query(CRMCompany).filter(CRMCompany.id == deal.seller_company_id).first()
            seller_name = seller.name if seller else None
        
        # Get assigned user name
        assigned_to_name = None
        if deal.assigned_to:
            assigned_user = db.query(User).filter(User.id == deal.assigned_to).first()
            assigned_to_name = assigned_user.full_name if assigned_user else None
        
        # Get creator name
        creator = db.query(User).filter(User.id == deal.created_by).first()
        creator_name = creator.full_name if creator else None
        
        deal_responses.append(DealResponse(
            id=str(deal.id),
            deal_number=deal.deal_number,
            title=deal.title,
            description=deal.description,
            status=deal.status,
            priority=deal.priority,
            currency=deal.currency,
            total_value=float(deal.total_value) if deal.total_value else None,
            estimated_margin_pct=float(deal.estimated_margin_pct) if deal.estimated_margin_pct else None,
            realized_margin_pct=float(deal.realized_margin_pct) if deal.realized_margin_pct else None,
            product_category=deal.product_category,
            product_key=deal.product_key,
            incoterms=deal.incoterms,
            origin_country=deal.origin_country,
            origin_port=deal.origin_port,
            destination_country=deal.destination_country,
            destination_port=deal.destination_port,
            expected_delivery_date=deal.expected_delivery_date.isoformat() if deal.expected_delivery_date else None,
            actual_delivery_date=deal.actual_delivery_date.isoformat() if deal.actual_delivery_date else None,
            buyer_company_id=str(deal.buyer_company_id) if deal.buyer_company_id else None,
            buyer_company_name=buyer_name,
            seller_company_id=str(deal.seller_company_id) if deal.seller_company_id else None,
            seller_company_name=seller_name,
            assigned_to=str(deal.assigned_to) if deal.assigned_to else None,
            assigned_to_name=assigned_to_name,
            created_by=str(deal.created_by),
            created_by_name=creator_name,
            tags=deal.tags or [],
            created_at=deal.created_at.isoformat(),
            updated_at=deal.updated_at.isoformat(),
            closed_at=deal.closed_at.isoformat() if deal.closed_at else None,
            document_count=document_count,
            milestone_count=milestone_count,
            risk_count=risk_count
        ))
    
    return deal_responses


@router.post("", response_model=DealResponse, summary="Create Deal")
def create_deal(
    deal_data: DealCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DealResponse:
    """
    Create a new deal
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Validate companies if provided
    if deal_data.buyer_company_id:
        buyer = db.query(CRMCompany).filter(
            CRMCompany.id == deal_data.buyer_company_id,
            CRMCompany.tenant_id == tenant_id
        ).first()
        if not buyer:
            raise HTTPException(status_code=404, detail="Buyer company not found")
    
    if deal_data.seller_company_id:
        seller = db.query(CRMCompany).filter(
            CRMCompany.id == deal_data.seller_company_id,
            CRMCompany.tenant_id == tenant_id
        ).first()
        if not seller:
            raise HTTPException(status_code=404, detail="Seller company not found")
    
    # Generate deal number
    deal_number = generate_deal_number(db)
    
    # Parse dates
    expected_delivery_date = None
    if deal_data.expected_delivery_date:
        expected_delivery_date = datetime.fromisoformat(deal_data.expected_delivery_date)
    
    # Create deal
    deal = Deal(
        tenant_id=tenant_id,
        deal_number=deal_number,
        title=deal_data.title,
        description=deal_data.description,
        status=DealStatus.IDENTIFIED.value,
        priority=deal_data.priority,
        currency=deal_data.currency,
        buyer_company_id=UUID(deal_data.buyer_company_id) if deal_data.buyer_company_id else None,
        seller_company_id=UUID(deal_data.seller_company_id) if deal_data.seller_company_id else None,
        product_category=deal_data.product_category,
        product_key=deal_data.product_key,
        incoterms=deal_data.incoterms,
        origin_country=deal_data.origin_country,
        origin_port=deal_data.origin_port,
        destination_country=deal_data.destination_country,
        destination_port=deal_data.destination_port,
        expected_delivery_date=expected_delivery_date,
        created_by=current_user.id,
        tags=deal_data.tags
    )
    
    db.add(deal)
    db.commit()
    db.refresh(deal)
    
    # Return created deal
    return list_deals(
        status=DealStatus.IDENTIFIED.value,
        limit=1,
        offset=0,
        current_user=current_user,
        db=db
    )[0]


@router.get("/{deal_id}", response_model=DealResponse, summary="Get Deal")
def get_deal(
    deal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DealResponse:
    """
    Get detailed deal information
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    deal = db.query(Deal).filter(
        Deal.id == UUID(deal_id),
        Deal.tenant_id == tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Return deal (reuse list_deals logic for consistency)
    return list_deals(
        limit=1,
        offset=0,
        current_user=current_user,
        db=db
    )[0]


@router.put("/{deal_id}", response_model=DealResponse, summary="Update Deal")
def update_deal(
    deal_id: str,
    deal_update: DealUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DealResponse:
    """
    Update deal information
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    deal = db.query(Deal).filter(
        Deal.id == UUID(deal_id),
        Deal.tenant_id == tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Update fields
    if deal_update.title:
        deal.title = deal_update.title
    if deal_update.description:
        deal.description = deal_update.description
    if deal_update.status:
        deal.status = deal_update.status
        if deal_update.status == DealStatus.CLOSED_WON.value or deal_update.status == DealStatus.CLOSED_LOST.value:
            deal.closed_at = datetime.now(timezone.utc)
    if deal_update.priority:
        deal.priority = deal_update.priority
    if deal_update.total_value:
        deal.total_value = deal_update.total_value
    if deal_update.estimated_margin_pct:
        deal.estimated_margin_pct = deal_update.estimated_margin_pct
    if deal_update.expected_delivery_date:
        deal.expected_delivery_date = datetime.fromisoformat(deal_update.expected_delivery_date)
    if deal_update.assigned_to:
        deal.assigned_to = UUID(deal_update.assigned_to) if deal_update.assigned_to else None
    if deal_update.tags is not None:
        deal.tags = deal_update.tags
    
    deal.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    
    # Return updated deal
    return get_deal(deal_id, current_user, db)


@router.get("/{deal_id}/price-components", response_model=List[PriceComponentResponse], summary="Get Price Components")
def get_price_components(
    deal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[PriceComponentResponse]:
    """
    Get all price components for a deal
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Verify deal exists
    deal = db.query(Deal).filter(
        Deal.id == UUID(deal_id),
        Deal.tenant_id == tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Get price components
    components = db.query(DealPriceComponent).filter(
        DealPriceComponent.deal_id == deal.id
    ).order_by(DealPriceComponent.created_at.asc()).all()
    
    component_responses = []
    for component in components:
        component_responses.append(PriceComponentResponse(
            id=str(component.id),
            component_type=component.component_type,
            component_name=component.component_name,
            amount=float(component.amount),
            currency=component.currency,
            quantity=float(component.quantity) if component.quantity else None,
            unit=component.unit,
            unit_price=float(component.unit_price) if component.unit_price else None,
            provider=component.provider,
            notes=component.notes,
            created_at=component.created_at.isoformat()
        ))
    
    return component_responses


@router.post("/{deal_id}/price-components", response_model=PriceComponentResponse, summary="Add Price Component")
def add_price_component(
    deal_id: str,
    component_data: PriceComponentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PriceComponentResponse:
    """
    Add a price component to a deal
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Verify deal exists
    deal = db.query(Deal).filter(
        Deal.id == UUID(deal_id),
        Deal.tenant_id == tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Create price component
    component = DealPriceComponent(
        deal_id=deal.id,
        component_type=component_data.component_type,
        component_name=component_data.component_name,
        amount=component_data.amount,
        currency=component_data.currency,
        quantity=component_data.quantity,
        unit=component_data.unit,
        unit_price=component_data.unit_price,
        provider=component_data.provider,
        notes=component_data.notes
    )
    
    db.add(component)
    db.commit()
    db.refresh(component)
    
    return PriceComponentResponse(
        id=str(component.id),
        component_type=component.component_type,
        component_name=component.component_name,
        amount=float(component.amount),
        currency=component.currency,
        quantity=float(component.quantity) if component.quantity else None,
        unit=component.unit,
        unit_price=float(component.unit_price) if component.unit_price else None,
        provider=component.provider,
        notes=component.notes,
        created_at=component.created_at.isoformat()
    )


@router.get("/{deal_id}/milestones", response_model=List[MilestoneResponse], summary="Get Milestones")
def get_milestones(
    deal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[MilestoneResponse]:
    """
    Get all milestones for a deal
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Verify deal exists
    deal = db.query(Deal).filter(
        Deal.id == UUID(deal_id),
        Deal.tenant_id == tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Get milestones
    milestones = db.query(DealMilestone).filter(
        DealMilestone.deal_id == deal.id
    ).order_by(DealMilestone.due_date.asc()).all()
    
    milestone_responses = []
    for milestone in milestones:
        # Get assignee name
        assignee_name = None
        if milestone.assigned_to:
            assignee = db.query(User).filter(User.id == milestone.assigned_to).first()
            assignee_name = assignee.full_name if assignee else None
        
        milestone_responses.append(MilestoneResponse(
            id=str(milestone.id),
            title=milestone.title,
            description=milestone.description,
            milestone_type=milestone.milestone_type,
            due_date=milestone.due_date.isoformat(),
            completed_at=milestone.completed_at.isoformat() if milestone.completed_at else None,
            status=milestone.status,
            assigned_to=str(milestone.assigned_to) if milestone.assigned_to else None,
            assigned_to_name=assignee_name,
            notes=milestone.notes,
            created_at=milestone.created_at.isoformat()
        ))
    
    return milestone_responses


@router.get("/{deal_id}/documents", response_model=List[DocumentResponse], summary="Get Documents")
def get_documents(
    deal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[DocumentResponse]:
    """
    Get all documents for a deal
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Verify deal exists
    deal = db.query(Deal).filter(
        Deal.id == UUID(deal_id),
        Deal.tenant_id == tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Get documents
    documents = db.query(DealDocument).filter(
        DealDocument.deal_id == deal.id
    ).order_by(DealDocument.created_at.desc()).all()
    
    document_responses = []
    for doc in documents:
        # Get uploader and signer names
        uploader = db.query(User).filter(User.id == doc.uploaded_by).first()
        uploader_name = uploader.full_name if uploader else None
        
        signer_name = None
        if doc.signed_by:
            signer = db.query(User).filter(User.id == doc.signed_by).first()
            signer_name = signer.full_name if signer else None
        
        document_responses.append(DocumentResponse(
            id=str(doc.id),
            document_type=doc.document_type,
            title=doc.title,
            description=doc.description,
            original_filename=doc.original_filename,
            file_size=doc.file_size,
            status=doc.status,
            signed_by=str(doc.signed_by) if doc.signed_by else None,
            signed_by_name=signer_name,
            signed_at=doc.signed_at.isoformat() if doc.signed_at else None,
            uploaded_by=str(doc.uploaded_by),
            uploaded_by_name=uploader_name,
            uploaded_at=doc.uploaded_at.isoformat()
        ))
    
    return document_responses


@router.get("/{deal_id}/risk-assessments", response_model=List[RiskAssessmentResponse], summary="Get Risk Assessments")
def get_risk_assessments(
    deal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[RiskAssessmentResponse]:
    """
    Get all risk assessments for a deal
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Verify deal exists
    deal = db.query(Deal).filter(
        Deal.id == UUID(deal_id),
        Deal.tenant_id == tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Get risk assessments
    risks = db.query(DealRiskAssessment).filter(
        DealRiskAssessment.deal_id == deal.id
    ).order_by(DealRiskAssessment.risk_score.desc()).all()
    
    risk_responses = []
    for risk in risks:
        # Get assessor name
        assessor = db.query(User).filter(User.id == risk.assessed_by).first()
        assessor_name = assessor.full_name if assessor else None
        
        risk_responses.append(RiskAssessmentResponse(
            id=str(risk.id),
            risk_category=risk.risk_category,
            risk_level=risk.risk_level,
            risk_score=risk.risk_score,
            description=risk.description,
            mitigation_plan=risk.mitigation_plan,
            assessed_by=str(risk.assessed_by),
            assessed_by_name=assessor_name,
            assessment_date=risk.assessment_date.isoformat(),
            status=risk.status,
            created_at=risk.created_at.isoformat()
        ))
    
    return risk_responses


@router.get("/pipeline-summary", summary="Get Pipeline Summary")
def get_pipeline_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get pipeline summary by status
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get deals by status
    pipeline_data = {}
    for status in [DealStatus.IDENTIFIED.value, DealStatus.MATCHING.value, DealStatus.VALIDATING.value, 
                   DealStatus.NEGOTIATING.value, DealStatus.CLOSED_WON.value, DealStatus.CLOSED_LOST.value]:
        count = db.query(Deal).filter(
            Deal.tenant_id == tenant_id,
            Deal.status == status
        ).count()
        
        total_value = db.query(func.sum(Deal.total_value)).filter(
            Deal.tenant_id == tenant_id,
            Deal.status == status,
            Deal.total_value.is_not(None)
        ).scalar() or 0
        
        pipeline_data[status] = {
            "count": count,
            "total_value": float(total_value)
        }
    
    return pipeline_data

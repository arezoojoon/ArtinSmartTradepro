from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_active_user
from app.middleware.plan_gate import require_feature
from app.constants import Feature
from app.models.user import User
from app.models.sourcing import Supplier, RFQ, SupplierQuote, SupplierIssue
from app.services.sourcing_service import SupplierIntelligenceService
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

router = APIRouter()

# --- Schemas ---

class SupplierCreate(BaseModel):
    name: str
    country: Optional[str] = None
    categories: List[str] = []

class RFQCreate(BaseModel):
    product_name: str
    hs_code: Optional[str] = None
    target_qty: float
    target_incoterm: Optional[str] = "FOB"
    deadline: Optional[datetime] = None

class QuoteCreate(BaseModel):
    rfq_id: str
    supplier_id: str
    incoterm: str
    unit_price: float
    currency: str = "USD"
    moq: float = 0
    lead_time_days: int
    payment_terms: str

class IssueCreate(BaseModel):
    supplier_id: str
    issue_type: str # delay, quality, etc.
    severity: int = 1
    description: Optional[str] = None

# --- Supplier Endpoints ---

@router.post("/suppliers")
def create_supplier(
    sup: SupplierCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        new_sup = Supplier(
            tenant_id=current_user.tenant_id,
            name=sup.name,
            country=sup.country,
            categories=sup.categories
        )
        db.add(new_sup)
        db.commit()
        db.refresh(new_sup)
        return new_sup
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suppliers/{id}/scorecard")
def get_supplier_scorecard(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        supplier = db.query(Supplier).filter(
            Supplier.id == uuid.UUID(id),
            Supplier.tenant_id == current_user.tenant_id
        ).first()
        
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
            
        score_data = SupplierIntelligenceService.calculate_reliability_score(db, supplier.id)
        
        return {
            "supplier": {
                "id": str(supplier.id),
                "name": supplier.name,
                "country": supplier.country,
                "capacity_index": float(supplier.capacity_index)
            },
            "reliability": score_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suppliers/issues")
def report_issue(
    issue: IssueCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        supplier = db.query(Supplier).filter(
            Supplier.id == uuid.UUID(issue.supplier_id),
            Supplier.tenant_id == current_user.tenant_id
        ).first()
        
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
            
        new_issue = SupplierIssue(
            tenant_id=current_user.tenant_id,
            supplier_id=supplier.id,
            issue_type=issue.issue_type,
            severity=issue.severity,
            description=issue.description
        )
        db.add(new_issue)
        db.commit()
        
        # Trigger re-scoring immediately
        SupplierIntelligenceService.calculate_reliability_score(db, supplier.id)
        
        return {"status": "success", "message": "Issue reported and score updated."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- RFQ Endpoints ---

@router.post("/rfqs")
def create_rfq(
    rfq: RFQCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    new_rfq = RFQ(
        tenant_id=current_user.tenant_id,
        product_name=rfq.product_name,
        hs_code=rfq.hs_code,
        target_qty=rfq.target_qty,
        target_incoterm=rfq.target_incoterm,
        deadline=rfq.deadline
    )
    db.add(new_rfq)
    db.commit()
    db.refresh(new_rfq)
    return new_rfq

@router.get("/rfqs")
def list_rfqs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(RFQ).filter(RFQ.tenant_id == current_user.tenant_id).all()

@router.post("/quotes")
def add_quote(
    q: QuoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    rfq = db.query(RFQ).filter(
        RFQ.id == uuid.UUID(q.rfq_id),
        RFQ.tenant_id == current_user.tenant_id
    ).first()
    
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
        
    supplier = db.query(Supplier).filter(
        Supplier.id == uuid.UUID(q.supplier_id),
        Supplier.tenant_id == current_user.tenant_id
    ).first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
        
    new_quote = SupplierQuote(
        tenant_id=current_user.tenant_id,
        rfq_id=rfq.id,
        supplier_id=supplier.id,
        incoterm=q.incoterm,
        unit_price=q.unit_price,
        currency=q.currency,
        moq=q.moq,
        lead_time_days=q.lead_time_days,
        payment_terms=q.payment_terms
    )
    db.add(new_quote)
    db.commit()
    db.refresh(new_quote)
    return new_quote

@router.get("/rfqs/{id}/compare")
def compare_rfq_quotes(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    rfq = db.query(RFQ).filter(
        RFQ.id == uuid.UUID(id),
        RFQ.tenant_id == current_user.tenant_id
    ).first()
    
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
        
    comparison = SupplierIntelligenceService.compare_quotes(db, rfq.id)
    return comparison

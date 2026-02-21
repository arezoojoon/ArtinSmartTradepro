"""
Hunter Phase 4 Qualification API Endpoints
Endpoints for lead qualification and CRM integration
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from ..database import get_db
from ..services.hunter_qualification import HunterQualificationService
from ..schemas.hunter import QualificationRequest, RejectionRequest, PushToCRMRequest
from ..core.auth import get_current_user, get_current_tenant
from ..models.user import User
from ..models.tenant import Tenant

router = APIRouter(prefix="/hunter", tags=["hunter"])

@router.post("/leads/{lead_id}/qualify")
def qualify_lead(
    lead_id: UUID,
    request: QualificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Qualify a lead"""
    service = HunterQualificationService(db)
    
    try:
        success = service.qualify_lead(current_tenant.id, lead_id, request.reason)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to qualify lead")
        
        return {"message": "Lead qualified successfully", "lead_id": str(lead_id)}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/leads/{lead_id}/reject")
def reject_lead(
    lead_id: UUID,
    request: RejectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Reject a lead"""
    service = HunterQualificationService(db)
    
    try:
        success = service.reject_lead(current_tenant.id, lead_id, request.reason)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reject lead")
        
        return {"message": "Lead rejected successfully", "lead_id": str(lead_id)}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/leads/{lead_id}/push-to-crm")
def push_to_crm(
    lead_id: UUID,
    request: PushToCRMRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Push lead to CRM with evidence summary"""
    service = HunterQualificationService(db)
    
    try:
        result = service.push_to_crm(
            tenant_id=current_tenant.id,
            lead_id=lead_id,
            create_company=request.create_company,
            create_contact=request.create_contact,
            create_task=request.create_task,
            task_due_days=request.task_due_days
        )
        
        return {
            "message": "Lead pushed to CRM successfully",
            "lead_id": str(lead_id),
            "company_id": str(result["company"].id) if result["company"] else None,
            "contact_id": str(result["contact"].id) if result["contact"] else None,
            "task_id": str(result["task"].id) if result["task"] else None,
            "note_id": str(result["note"].id) if result["note"] else None,
            "evidence_summary": result["evidence_summary"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/{lead_id}/crm-status")
def get_crm_status(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get CRM integration status for a lead"""
    from ..models.hunter_phase4 import HunterLead
    from ..models.crm import CRMCompany, CRMContact, CRMTask, CRMNote
    
    # Get lead
    lead = db.query(HunterLead).filter(
        HunterLead.tenant_id == current_tenant.id,
        HunterLead.id == lead_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check for related CRM objects
    company = None
    contact = None
    task = None
    note = None
    
    if lead.website:
        # Try to find company by website
        domain = lead.website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
        company = db.query(CRMCompany).filter(
            CRMCompany.tenant_id == current_tenant.id,
            CRMCompany.website.ilike(f"%{domain}%")
        ).first()
    
    if company:
        # Find contacts for this company
        contact = db.query(CRMContact).filter(
            CRMContact.tenant_id == current_tenant.id,
            CRMContact.company_id == company.id,
            CRMContact.source == "hunter"
        ).first()
        
        # Find recent tasks for this company
        task = db.query(CRMTask).filter(
            CRMTask.tenant_id == current_tenant.id,
            CRMTask.company_id == company.id,
            CRMTask.source == "hunter"
        ).order_by(CRMTask.created_at.desc()).first()
        
        # Find recent notes for this company
        note = db.query(CRMNote).filter(
            CRMNote.tenant_id == current_tenant.id,
            CRMNote.company_id == company.id,
            CRMNote.source == "hunter"
        ).order_by(CRMNote.created_at.desc()).first()
    
    return {
        "lead_id": str(lead_id),
        "lead_status": lead.status,
        "crm_company": {
            "id": str(company.id),
            "name": company.name,
            "website": company.website
        } if company else None,
        "crm_contact": {
            "id": str(contact.id),
            "email": contact.email,
            "phone": contact.phone
        } if contact else None,
        "crm_task": {
            "id": str(task.id),
            "title": task.title,
            "status": task.status,
            "due_date": task.due_date.isoformat() if task.due_date else None
        } if task else None,
        "crm_note": {
            "id": str(note.id),
            "created_at": note.created_at.isoformat() if note.created_at else None
        } if note else None,
        "can_push": lead.status in ["qualified", "enriched"] and lead.status != "pushed_to_crm"
    }

"""
Hunter Phase 4 Guardrails API Endpoints
Evidence validation and data quality endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from ..database import get_db
from ..services.hunter_guardrails import HunterGuardrails
from ..core.auth import get_current_user, get_current_tenant
from ..models.user import User
from ..models.tenant import Tenant

router = APIRouter(prefix="/hunter", tags=["hunter"])

@router.get("/leads/{lead_id}/evidence/summary")
def get_evidence_summary(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get evidence summary with field counts and top sources"""
    guardrails = HunterGuardrails(db)
    
    try:
        summary = guardrails.validate_evidence_summary(current_tenant.id, lead_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/leads/{lead_id}/quality")
def get_lead_quality(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get data quality metrics for a lead"""
    guardrails = HunterGuardrails(db)
    
    try:
        quality = guardrails.check_data_quality(current_tenant.id, lead_id)
        return quality
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/leads/{lead_id}/validate")
def validate_lead_data(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Validate lead data and ensure evidence requirements
    Returns lead data with evidence status for each field
    """
    guardrails = HunterGuardrails(db)
    
    try:
        # Get lead data
        from ..services.hunter_repository import HunterRepository
        repo = HunterRepository(db)
        lead = repo.get_lead_with_details(current_tenant.id, lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Convert to dict for validation
        lead_data = {
            "id": str(lead.id),
            "primary_name": lead.primary_name,
            "country": lead.country,
            "city": lead.city,
            "website": lead.website,
            "industry": lead.industry,
            "status": lead.status,
            "score_total": lead.score_total,
            "created_at": lead.created_at.isoformat()
        }
        
        # Validate and return
        validated_data = guardrails.validate_lead_response(current_tenant.id, lead_data)
        return validated_data
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/leads/{lead_id}/enrich/validate")
def validate_enrichment_eligibility(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Check if lead meets requirements for enrichment status
    """
    guardrails = HunterGuardrails(db)
    
    try:
        meets_requirement = guardrails.enforce_enrichment_evidence_requirement(
            current_tenant.id, lead_id
        )
        
        return {
            "lead_id": str(lead_id),
            "meets_requirement": meets_requirement,
            "message": (
                "Lead meets enrichment evidence requirement" if meets_requirement
                else "Lead must have at least one evidence item added after creation to be marked as enriched"
            )
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/health/evidence")
def evidence_health_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Health check for evidence system
    Returns statistics about evidence quality across all leads
    """
    from ..services.hunter_repository import HunterRepository
    from sqlalchemy import func, text
    from ..models.hunter_phase4 import HunterEvidence
    
    repo = HunterRepository(db)
    
    # Get overall statistics
    total_leads = db.query(func.count(HunterLead.id)).filter(
        HunterLead.tenant_id == current_tenant.id
    ).scalar()
    
    total_evidence = db.query(func.count(HunterEvidence.id)).filter(
        HunterEvidence.tenant_id == current_tenant.id
    ).scalar()
    
    # Evidence by source
    source_counts = db.query(
        HunterEvidence.source_name,
        func.count(HunterEvidence.id).label('count')
    ).filter(
        HunterEvidence.tenant_id == current_tenant.id
    ).group_by(HunterEvidence.source_name).all()
    
    # Evidence by field
    field_counts = db.query(
        HunterEvidence.field_name,
        func.count(HunterEvidence.id).label('count')
    ).filter(
        HunterEvidence.tenant_id == current_tenant.id
    ).group_by(HunterEvidence.field_name).all()
    
    # Average confidence
    avg_confidence = db.query(
        func.avg(HunterEvidence.confidence).label('avg_confidence')
    ).filter(
        HunterEvidence.tenant_id == current_tenant.id
    ).scalar()
    
    # Recent evidence (last 30 days)
    from datetime import datetime, timedelta
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_evidence = db.query(func.count(HunterEvidence.id)).filter(
        HunterEvidence.tenant_id == current_tenant.id,
        HunterEvidence.collected_at >= thirty_days_ago
    ).scalar()
    
    return {
        "total_leads": total_leads or 0,
        "total_evidence": total_evidence or 0,
        "avg_evidence_per_lead": round((total_evidence or 0) / max(total_leads or 1), 2),
        "avg_confidence": round(float(avg_confidence or 0) * 100, 2),
        "recent_evidence_count": recent_evidence or 0,
        "source_distribution": [
            {"source": row.source_name, "count": row.count}
            for row in source_counts
        ],
        "field_distribution": [
            {"field": row.field_name, "count": row.count}
            for row in field_counts
        ]
    }

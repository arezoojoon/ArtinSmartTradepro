"""
Hunter Phase 4 Enrichment API Endpoints
Endpoints for triggering enrichment and checking job status
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..services.hunter_repository import HunterRepository
from ..schemas.hunter import EnrichmentJobResponse
from ..core.auth import get_current_user, get_current_tenant
from ..models.user import User
from ..models.tenant import Tenant

router = APIRouter(prefix="/hunter", tags=["hunter"])

@router.post("/leads/{lead_id}/enrich")
def enqueue_enrichment(
    lead_id: UUID,
    provider: str = "web_basic",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Enqueue enrichment job for a lead"""
    # Check if provider is supported
    supported_providers = ["web_basic"]  # Add more as they're implemented
    if provider not in supported_providers:
        raise HTTPException(
            status_code=400, 
            detail=f"Provider '{provider}' not supported. Supported: {supported_providers}"
        )
    
    repo = HunterRepository(db)
    
    # Check if lead exists
    lead = repo.get_lead_with_details(current_tenant.id, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check if there's already a pending job for this lead and provider
    existing_jobs = db.query(HunterEnrichmentJob).filter(
        HunterEnrichmentJob.tenant_id == current_tenant.id,
        HunterEnrichmentJob.lead_id == lead_id,
        HunterEnrichmentJob.provider == provider,
        HunterEnrichmentJob.status.in_(["queued", "running"])
    ).first()
    
    if existing_jobs:
        raise HTTPException(
            status_code=409, 
            detail=f"Enrichment job already in progress for this lead with provider '{provider}'"
        )
    
    # Create enrichment job
    job = repo.enqueue_enrichment_job(
        tenant_id=current_tenant.id,
        lead_id=lead_id,
        provider=provider,
        scheduled_for=datetime.utcnow()
    )
    
    return {
        "status": "queued",
        "job_id": str(job.id),
        "provider": provider,
        "message": "Enrichment job queued successfully"
    }

@router.get("/leads/{lead_id}/enrichment/jobs")
def get_enrichment_jobs(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get enrichment jobs for a lead"""
    repo = HunterRepository(db)
    
    # Check if lead exists
    lead = repo.get_lead_with_details(current_tenant.id, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get jobs for this lead
    jobs = db.query(HunterEnrichmentJob).filter(
        HunterEnrichmentJob.tenant_id == current_tenant.id,
        HunterEnrichmentJob.lead_id == lead_id
    ).order_by(HunterEnrichmentJob.created_at.desc()).all()
    
    return [EnrichmentJobResponse.from_orm(job) for job in jobs]

@router.get("/enrichment/jobs/{job_id}")
def get_enrichment_job_status(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get status of a specific enrichment job"""
    job = db.query(HunterEnrichmentJob).filter(
        HunterEnrichmentJob.tenant_id == current_tenant.id,
        HunterEnrichmentJob.id == job_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return EnrichmentJobResponse.from_orm(job)

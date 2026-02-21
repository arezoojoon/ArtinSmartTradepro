"""
Hunter Phase 4 API Router - NEW VERSION
Lead Intake endpoints: manual, CSV import, search, trade query stub
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import csv
import io
from datetime import datetime

from ..database import get_db
from ..services.hunter_repository import HunterRepository
from ..schemas.hunter import (
    ManualLeadWithIdentitiesRequest, LeadResponse, LeadDetailResponse,
    LeadSearchRequest, CSVImportSummary, TradeDataQueryRequest,
    IdentityCreate
)
from ..core.auth import get_current_user, get_current_tenant
from ..models.user import User
from ..models.tenant import Tenant

router = APIRouter(prefix="/hunter", tags=["hunter"])

@router.post("/leads/manual", response_model=LeadResponse)
def create_manual_lead(
    request: ManualLeadWithIdentitiesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Create a lead manually with identities"""
    repo = HunterRepository(db)
    
    # Create lead
    lead = repo.create_lead(
        tenant_id=current_tenant.id,
        primary_name=request.primary_name,
        country=request.country,
        city=request.city,
        website=request.website,
        industry=request.industry,
        source_hint="manual"
    )
    
    # Add identities if provided
    if request.identities:
        for identity in request.identities:
            repo.attach_identity(
                tenant_id=current_tenant.id,
                lead_id=lead.id,
                type=identity.type.value,
                value=identity.value
            )
    
    # Add notes as evidence if provided
    if request.notes:
        repo.attach_evidence(
            tenant_id=current_tenant.id,
            lead_id=lead.id,
            field_name="notes",
            source_name="manual",
            confidence=1.0,
            snippet=request.notes,
            collected_at=datetime.utcnow()
        )
    
    # Refresh to get all related data
    db.refresh(lead)
    return lead

@router.post("/leads/import/csv", response_model=CSVImportSummary)
def import_leads_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Import leads from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    repo = HunterRepository(db)
    summary = CSVImportSummary()
    
    try:
        # Read CSV content
        content = file.file.read()
        csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig')))
        
        # Validate required columns
        required_columns = ['name', 'country']
        if not all(col in csv_reader.fieldnames for col in required_columns):
            missing = [col for col in required_columns if col not in csv_reader.fieldnames]
            raise HTTPException(
                status_code=400, 
                detail=f"CSV missing required columns: {missing}"
            )
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for line numbers
            try:
                # Validate required fields
                if not row.get('name', '').strip():
                    summary.errors.append(f"Row {row_num}: Name is required")
                    summary.skipped += 1
                    continue
                
                if not row.get('country', '').strip():
                    summary.errors.append(f"Row {row_num}: Country is required")
                    summary.skipped += 1
                    continue
                
                # Check for duplicates by name + country
                existing_leads = repo.search_leads(
                    tenant_id=current_tenant.id,
                    query=row['name'].strip(),
                    country=row['country'].strip(),
                    limit=1
                )
                
                if existing_leads:
                    summary.duplicates += 1
                    continue
                
                # Create lead
                lead = repo.create_lead(
                    tenant_id=current_tenant.id,
                    primary_name=row['name'].strip(),
                    country=row['country'].strip(),
                    city=row.get('city', '').strip() or None,
                    website=row.get('website', '').strip() or None,
                    industry=row.get('industry', '').strip() or None,
                    source_hint="csv_import"
                )
                
                # Add identities if provided
                for field in ['email', 'phone']:
                    value = row.get(field, '').strip()
                    if value:
                        repo.attach_identity(
                            tenant_id=current_tenant.id,
                            lead_id=lead.id,
                            type=field,
                            value=value
                        )
                
                summary.created += 1
                
            except Exception as e:
                summary.errors.append(f"Row {row_num}: {str(e)}")
                summary.skipped += 1
                continue
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV processing error: {str(e)}")
    
    return summary

@router.get("/leads", response_model=List[LeadResponse])
def search_leads(
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Search leads with filters"""
    repo = HunterRepository(db)
    
    leads = repo.search_leads(
        tenant_id=current_tenant.id,
        query=q,
        status=status,
        country=country,
        min_score=min_score,
        limit=limit,
        offset=offset
    )
    
    return leads

@router.get("/leads/{lead_id}", response_model=LeadDetailResponse)
def get_lead_detail(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get lead with all details including grouped evidence"""
    repo = HunterRepository(db)
    
    lead = repo.get_lead_with_details(current_tenant.id, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Group evidence by field
    evidence_by_field = repo.group_evidence_by_field(lead.evidence)
    
    return LeadDetailResponse(
        **lead.__dict__,
        evidence_by_field=evidence_by_field
    )

@router.post("/query/trade")
def query_trade_data(
    request: TradeDataQueryRequest,
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Query trade data - STUB: returns 501 until provider is configured"""
    raise HTTPException(
        status_code=501,
        detail="Trade data provider not configured. Connect provider first."
    )

@router.get("/leads/{lead_id}/evidence/summary")
def get_evidence_summary(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get evidence summary for a lead"""
    repo = HunterRepository(db)
    
    lead = repo.get_lead_with_details(current_tenant.id, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Calculate field counts
    field_counts = {}
    top_sources = {}
    total_evidence = len(lead.evidence)
    last_collected = None
    
    for evidence in lead.evidence:
        # Count by field
        if evidence.field_name not in field_counts:
            field_counts[evidence.field_name] = 0
        field_counts[evidence.field_name] += 1
        
        # Track top sources per field
        if evidence.field_name not in top_sources:
            top_sources[evidence.field_name] = []
        if evidence.source_name not in top_sources[evidence.field_name]:
            top_sources[evidence.field_name].append(evidence.source_name)
        
        # Track last collected
        if last_collected is None or evidence.collected_at > last_collected:
            last_collected = evidence.collected_at
    
    return {
        "lead_id": lead_id,
        "field_counts": field_counts,
        "top_sources": top_sources,
        "total_evidence": total_evidence,
        "last_collected": last_collected
    }

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.lead import Lead
from app.middleware.auth import get_current_active_user
from app.middleware.plan_gate import require_feature
from app.constants import Feature
from app.services.billing import BillingService
from pydantic import BaseModel
from typing import List, Optional
import csv
import io

router = APIRouter()

COST_PER_LEAD = 0.1  # 0.1 credits per imported lead

REQUIRED_COLUMNS = {"company_name"}
VALID_COLUMNS = {"company_name", "contact_name", "email", "phone", "website", "country", "city"}

class LeadStatsResponse(BaseModel):
    total_leads: int = 0
    hot_leads: int = 0
    potential_revenue: float = 0.0

@router.get("/stats", response_model=LeadStatsResponse)
def get_lead_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Dashboard stats endpoint."""
    total = db.query(Lead).filter(Lead.tenant_id == current_user.tenant_id).count()
    hot = db.query(Lead).filter(
        Lead.tenant_id == current_user.tenant_id,
        Lead.status.in_(["interested", "contacted"])
    ).count()
    
    # Rough estimate: each hot lead = $500 potential
    potential = hot * 500.0
    
    return LeadStatsResponse(total_leads=total, hot_leads=hot, potential_revenue=potential)

@router.post("/import/csv")
@require_feature(Feature.CSV_IMPORT)
def import_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Import leads from CSV with strict validation and billing.
    Cost: 0.1 credits per lead.
    """
    # 1. VALIDATE FILE
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    
    # 2. READ AND PARSE
    try:
        content = file.file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        
        # Validate headers
        if not reader.fieldnames:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        headers = set(h.strip().lower() for h in reader.fieldnames)
        if not REQUIRED_COLUMNS.issubset(headers):
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {REQUIRED_COLUMNS - headers}. Got: {headers}"
            )
        
        # Parse rows
        rows = []
        for i, row in enumerate(reader):
            cleaned = {k.strip().lower(): v.strip() for k, v in row.items() if k.strip().lower() in VALID_COLUMNS}
            if not cleaned.get("company_name"):
                continue  # Skip empty rows silently
            rows.append(cleaned)
        
        if not rows:
            raise HTTPException(status_code=400, detail="No valid leads found in CSV")
            
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV file must be UTF-8 encoded")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parsing error: {str(e)}")
    
    # 3. BILLING CHECK (atomic deduction for total cost)
    total_cost = len(rows) * COST_PER_LEAD
    try:
        with db.begin_nested():
            BillingService.deduct_balance(
                db=db,
                tenant_id=current_user.tenant_id,
                amount=total_cost,
                description=f"CSV import: {len(rows)} leads @ {COST_PER_LEAD}/lead"
            )
    except HTTPException as e:
        raise e
    
    # 4. INSERT LEADS (all belong to tenant)
    imported = 0
    failed = 0
    for row in rows:
        try:
            lead = Lead(
                tenant_id=current_user.tenant_id,
                company_name=row.get("company_name"),
                contact_name=row.get("contact_name"),
                email=row.get("email"),
                phone=row.get("phone"),
                website=row.get("website"),
                country=row.get("country"),
                city=row.get("city"),
                source="csv_import",
                status="new"
            )
            db.add(lead)
            imported += 1
        except Exception:
            failed += 1
    
    db.commit()
    
    return {"imported": imported, "failed": failed, "cost_deducted": total_cost}

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.models.execution import TradeOpportunity
from app.services.execution_service import ExecutionService
from pydantic import BaseModel
import uuid

router = APIRouter()

# --- Schemas ---

class OpportunityCreate(BaseModel):
    title: str
    buyer_id: str
    supplier_id: str

class OpportunityResponse(BaseModel):
    id: uuid.UUID
    title: str
    stage: str
    win_probability: int
    buyer_name: str = "Unknown"
    supplier_name: str = "Unknown"
    scenario_id: uuid.UUID | None

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.post("/opportunities", response_model=OpportunityResponse)
def create_opportunity(
    opp: OpportunityCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        new_opp = ExecutionService.create_opportunity(
            db, 
            current_user.tenant_id, 
            opp.title, 
            uuid.UUID(opp.buyer_id), 
            uuid.UUID(opp.supplier_id)
        )
        return OpportunityResponse(
            id=new_opp.id,
            title=new_opp.title,
            stage=new_opp.stage,
            win_probability=new_opp.win_probability,
            buyer_name=new_opp.buyer.company_name if new_opp.buyer else "Unknown",
            supplier_name=new_opp.supplier.name if new_opp.supplier else "Unknown",
            scenario_id=new_opp.financial_scenario_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/opportunities", response_model=List[OpportunityResponse])
def list_opportunities(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    opps = db.query(TradeOpportunity).filter(TradeOpportunity.tenant_id == current_user.tenant_id).all()
    results = []
    for o in opps:
        results.append(OpportunityResponse(
            id=o.id,
            title=o.title,
            stage=o.stage,
            win_probability=o.win_probability,
            buyer_name=o.buyer.company_name if o.buyer else "Unknown",
            supplier_name=o.supplier.name if o.supplier else "Unknown",
            scenario_id=o.financial_scenario_id
        ))
    return results

@router.post("/opportunities/{id}/advance")
def advance_stage(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Stub for advancing workflow stages
    opp = db.query(TradeOpportunity).get(uuid.UUID(id))
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    stages = ["identified", "matching", "validating", "negotiating", "closed_won"]
    try:
        current_idx = stages.index(opp.stage)
        if current_idx < len(stages) - 1:
            opp.stage = stages[current_idx + 1]
            db.commit()
    except ValueError:
        pass # unknown stage
        
    return {"status": "success", "new_stage": opp.stage}

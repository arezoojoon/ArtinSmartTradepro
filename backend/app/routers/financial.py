from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.models.financial import TradeScenario, CostComponent, RiskFactor
from app.services.financial_service import FinancialService
from pydantic import BaseModel
import uuid

router = APIRouter()

# --- Schemas ---

class ScenarioCreate(BaseModel):
    name: str # e.g. "Deal 101 Base"
    currency: str = "USD"

class CostCreate(BaseModel):
    scenario_id: str
    name: str # Freight, etc.
    amount: float
    cost_type: str = "variable" # fixed/variable

class RiskCreate(BaseModel):
    scenario_id: str
    factor_type: str # fx, compliance
    probability: float # 0-1
    impact_percent: float # 5.0

class CloneRequest(BaseModel):
    new_name: str

# --- Endpoints ---

@router.post("/scenarios")
def create_scenario(
    s: ScenarioCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    new_s = TradeScenario(
        tenant_id=current_user.tenant_id,
        name=s.name,
        currency=s.currency
    )
    db.add(new_s)
    db.commit()
    db.refresh(new_s)
    return new_s

@router.get("/scenarios")
def list_scenarios(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(TradeScenario).filter(TradeScenario.tenant_id == current_user.tenant_id).all()

@router.get("/scenarios/{id}/simulation")
def get_simulation(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        return FinancialService.calculate_scenario(db, uuid.UUID(id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scenarios/{id}/clone")
def clone_scenario(
    id: str,
    req: CloneRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        return FinancialService.clone_scenario(db, uuid.UUID(id), req.new_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/costs")
def add_cost(
    c: CostCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    new_c = CostComponent(
        scenario_id=uuid.UUID(c.scenario_id),
        name=c.name,
        amount=c.amount,
        cost_type=c.cost_type
    )
    db.add(new_c)
    db.commit()
    return new_c

@router.post("/risks")
def add_risk(
    r: RiskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    new_r = RiskFactor(
        scenario_id=uuid.UUID(r.scenario_id),
        factor_type=r.factor_type,
        probability=r.probability,
        impact_percent=r.impact_percent
    )
    db.add(new_r)
    db.commit()
    return new_r

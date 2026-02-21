"""
Phase 5 Brain API Router
Brain engine endpoints with deterministic validation and explainability
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any

from ..database import get_db
from ..schemas.brain import (
    ArbitrageInput, ArbitrageOutput, RiskInput, RiskOutput,
    DemandInput, DemandOutput, CulturalInput, CulturalOutput,
    EngineRunResponse, BrainRunStatus
)
from ..services.brain_registry import BrainEngineRegistry, BrainEngineValidator, make_insufficient_data_bundle
from ..services.brain_assets_repository import BrainAssetRepository
from ..services.brain_arbitrage_engine import ArbitrageEngine
from ..services.brain_risk_engine import RiskEngine
from ..services.brain_demand_engine import DemandForecastEngine
from ..services.brain_cultural_engine import CulturalStrategyEngine
from ..models.brain_assets import BrainEngineType
from ..core.auth import get_current_user, get_current_tenant
from ..models.user import User
from ..models.tenant import Tenant

router = APIRouter(prefix="/brain", tags=["brain"])

# Permission guard for brain operations
def require_brain_run_permission(current_user: User):
    """Check if user has brain.run permission"""
    # For now, all authenticated users have brain.run permission
    # In production, this would check user permissions
    return current_user

@router.post("/arbitrage/run", response_model=ArbitrageOutput)
def run_arbitrage_engine(
    input_data: ArbitrageInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_brain_run_permission),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Run arbitrage analysis engine"""
    engine = ArbitrageEngine(db)
    
    try:
        return engine.run_analysis(current_tenant.id, input_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Arbitrage engine error: {str(e)}"
        )

@router.post("/risk/run", response_model=RiskOutput)
def run_risk_engine(
    input_data: RiskInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_brain_run_permission),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Run risk analysis engine"""
    engine = RiskEngine(db)
    
    try:
        return engine.run_analysis(current_tenant.id, input_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk engine error: {str(e)}"
        )

@router.post("/demand/run", response_model=DemandOutput)
def run_demand_engine(
    input_data: DemandInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_brain_run_permission),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Run demand forecast engine"""
    engine = DemandForecastEngine(db)
    
    try:
        return engine.run_forecast(current_tenant.id, input_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demand engine error: {str(e)}"
        )

@router.post("/cultural/run", response_model=CulturalOutput)
def run_cultural_engine(
    input_data: CulturalInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_brain_run_permission),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Run cultural strategy engine"""
    engine = CulturalStrategyEngine(db)
    
    try:
        return engine.run_analysis(current_tenant.id, input_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cultural engine error: {str(e)}"
        )

@router.get("/runs", response_model=Dict[str, Any])
def list_engine_runs(
    engine_type: str = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_brain_run_permission),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """List brain engine runs"""
    registry = BrainEngineRegistry(db)
    
    # Validate engine type
    engine_type_enum = None
    if engine_type:
        try:
            engine_type_enum = BrainEngineType(engine_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid engine type: {engine_type}"
            )
    
    runs = registry.get_run_history(current_tenant.id, engine_type_enum, limit)
    
    return {
        "runs": [
            {
                "id": run.id,
                "engine_type": run.engine_type.value,
                "status": run.status.value,
                "created_at": run.created_at,
                "input_payload": run.input_payload,
                "output_payload": run.output_payload,
                "explainability": run.explainability
            }
            for run in runs
        ],
        "total": len(runs)
    }

@router.get("/runs/{run_id}", response_model=Dict[str, Any])
def get_engine_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_brain_run_permission),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get specific brain engine run"""
    registry = BrainEngineRegistry(db)
    
    run = registry.get_run(current_tenant.id, run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engine run not found"
        )
    
    return {
        "id": run.id,
        "engine_type": run.engine_type.value,
        "status": run.status.value,
        "created_at": run.created_at,
        "input_payload": run.input_payload,
        "output_payload": run.output_payload,
        "explainability": run.explainability,
        "error": run.error
    }

@router.get("/data-sources", response_model=Dict[str, Any])
def list_data_sources(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_brain_run_permission),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """List available brain data sources"""
    registry = BrainEngineRegistry(db)
    
    sources = registry.get_data_sources(current_tenant.id, active_only)
    
    return {
        "sources": [
            {
                "id": source.id,
                "name": source.name,
                "type": source.type,
                "is_active": source.is_active,
                "meta": source.meta,
                "created_at": source.created_at
            }
            for source in sources
        ],
        "total": len(sources)
    }

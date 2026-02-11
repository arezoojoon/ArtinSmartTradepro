from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_active_user
from app.middleware.plan_gate import require_feature
from app.constants import Feature
from app.services.toolbox_service import ToolboxService
from app.services.analytics_service import AnalyticsService
from app.services.shock_service import ShockService

router = APIRouter()

@router.get("/trade-data")
@require_feature(Feature.AI_BRAIN)
async def get_trade_data(
    hs_code: str = None, 
    country: str = None, 
    year: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search Global Trade Data."""
    return ToolboxService.get_trade_data(db, hs_code, country, year)

@router.get("/freight")
@require_feature(Feature.AI_BRAIN)
async def get_freight_rates(
    origin: str, 
    dest: str, 
    equipment: str = "20GP",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get Freight Estimates."""
    rate = ToolboxService.get_freight_rate(db, origin, dest, equipment)
    if not rate:
        raise HTTPException(status_code=404, detail="No rate found for route")
    return rate

@router.get("/fx")
@require_feature(Feature.AI_BRAIN)
async def get_fx_rate(
    base: str = "USD", 
    quote: str = "EUR",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get Latest FX Rate."""
    rate = ToolboxService.get_latest_fx(db, base, quote)
    if not rate:
        raise HTTPException(status_code=404, detail="No rate found for pair")
    return rate

@router.get("/analytics")
@require_feature(Feature.ANALYTICS)
async def get_bi_kpis(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get BI KPIs (DSO, Conversion, etc)."""
    return AnalyticsService.get_kpis(db, current_user.tenant_id)

@router.get("/shocks")
@require_feature(Feature.AI_BRAIN)
async def get_market_shocks(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Check and retrieve market shock alerts."""
    # Run deterministic checks now (Real-time)
    fx_alerts = ShockService.check_fx_shocks(db, current_user.tenant_id)
    return fx_alerts

@router.post("/seed")
async def seed_toolbox_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Seed Demo Data (Admin Only - simplified for MVP)."""
    ToolboxService.seed_all_data(db)
    return {"status": "seeded"}

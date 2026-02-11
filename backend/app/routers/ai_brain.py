"""
AI Brain Router — Trade Intelligence Decision Engine.
Endpoint for one-click trade decisions combining all engines.
Enterprise+ only.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_active_user
from app.middleware.plan_gate import require_feature
from app.constants import Feature
from app.services.billing import BillingService
from app.services.ai_worker import AIWorkerService
from app.services.engines.decision_engine import DecisionEngine
from app.services.engines.arbitrage_engine import ArbitrageEngine
from app.services.engines.risk_engine import RiskEngine
from app.services.engines.demand_forecast_engine import DemandForecastEngine
from app.services.engines.cultural_engine import CulturalNegotiationEngine
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

CREDIT_COST_FULL = 10.0    # Full decision analysis
CREDIT_COST_SINGLE = 3.0   # Single engine query


# --- Request Schemas ---
class TradeAnalysisRequest(BaseModel):
    product_hs: str
    product_name: str
    origin_country: str
    destination_country: str
    buy_price_per_kg: float
    sell_price_per_kg: float
    quantity_kg: float
    buy_currency: str = "USD"
    sell_currency: str = "USD"
    trader_country: str = "IR"


class ArbitrageRequest(BaseModel):
    product_hs: str
    origin_country: str
    destination_country: str
    buy_price_per_kg: float
    sell_price_per_kg: float
    quantity_kg: float
    buy_currency: str = "USD"
    sell_currency: str = "USD"


class RiskRequest(BaseModel):
    origin_country: str
    destination_country: str
    commodity: str
    sell_currency: str = "USD"
    buyer_company_age: int = 5


class DemandRequest(BaseModel):
    commodity: str
    target_market: str
    months_ahead: int = 12


class CulturalRequest(BaseModel):
    counterpart_country: str
    your_country: str = "IR"
    product_category: str = "FMCG"
    deal_size_usd: float = 50000
    relationship_stage: str = "new"


# --- Full Decision Endpoint ---
@router.post("/decide")
@require_feature(Feature.AI_BRAIN)
async def full_trade_decision(
    req: TradeAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    One-click trade decision.
    Combines: Arbitrage + Risk + Demand + Cultural → GO / CONDITIONAL / CAUTION / AVOID.
    Cost: 10 credits.
    """
    # Kill switch
    AIWorkerService.check_kill_switch(db)

    # Billing
    BillingService.deduct_balance(db, current_user.tenant_id, CREDIT_COST_FULL,
                                  f"Brain decision: {req.origin_country}→{req.destination_country} HS:{req.product_hs}")
    db.commit()

    try:
        result = await DecisionEngine.analyze_opportunity(
            db=db,
            tenant_id=current_user.tenant_id,
            product_hs=req.product_hs,
            product_name=req.product_name,
            origin_country=req.origin_country,
            destination_country=req.destination_country,
            buy_price_per_kg=req.buy_price_per_kg,
            sell_price_per_kg=req.sell_price_per_kg,
            quantity_kg=req.quantity_kg,
            buy_currency=req.buy_currency,
            sell_currency=req.sell_currency,
            trader_country=req.trader_country,
        )
        return {"cost": CREDIT_COST_FULL, "result": result}
    except Exception as e:
        logger.error(f"Brain decision failed: {e}")
        BillingService.refund(db, current_user.tenant_id, CREDIT_COST_FULL,
                              f"Refund: brain decision failed")
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# --- Individual Engine Endpoints ---
@router.post("/arbitrage")
@require_feature(Feature.AI_BRAIN)
async def arbitrage_analysis(
    req: ArbitrageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Arbitrage calculation only. Cost: 3 credits."""
    AIWorkerService.check_kill_switch(db)
    BillingService.deduct_balance(db, current_user.tenant_id, CREDIT_COST_SINGLE,
                                  f"Arbitrage: {req.origin_country}→{req.destination_country}")
    db.commit()

    try:
        result = await ArbitrageEngine.calculate(
            db=db,
            tenant_id=current_user.tenant_id,
            product_hs=req.product_hs,
            origin_country=req.origin_country,
            destination_country=req.destination_country,
            buy_price_per_kg=req.buy_price_per_kg,
            sell_price_per_kg=req.sell_price_per_kg,
            quantity_kg=req.quantity_kg,
            buy_currency=req.buy_currency,
            sell_currency=req.sell_currency,
        )
        return {"cost": CREDIT_COST_SINGLE, "result": result}
    except Exception as e:
        BillingService.refund(db, current_user.tenant_id, CREDIT_COST_SINGLE, "Refund: arbitrage failed")
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk")
@require_feature(Feature.AI_BRAIN)
async def risk_assessment(
    req: RiskRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Risk assessment only. Cost: 3 credits."""
    AIWorkerService.check_kill_switch(db)
    BillingService.deduct_balance(db, current_user.tenant_id, CREDIT_COST_SINGLE,
                                  f"Risk: {req.origin_country}→{req.destination_country}")
    db.commit()

    try:
        result = await RiskEngine.assess(
            db=db,
            tenant_id=current_user.tenant_id,
            destination_country=req.destination_country,
            origin_country=req.origin_country,
            commodity=req.commodity,
            sell_currency=req.sell_currency,
            buyer_company_age=req.buyer_company_age,
        )
        return {"cost": CREDIT_COST_SINGLE, "result": result}
    except Exception as e:
        BillingService.refund(db, current_user.tenant_id, CREDIT_COST_SINGLE, "Refund: risk failed")
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demand")
@require_feature(Feature.AI_BRAIN)
async def demand_forecast(
    req: DemandRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Demand forecast only. Cost: 3 credits."""
    AIWorkerService.check_kill_switch(db)
    BillingService.deduct_balance(db, current_user.tenant_id, CREDIT_COST_SINGLE,
                                  f"Demand: {req.commodity} in {req.target_market}")
    db.commit()

    try:
        result = await DemandForecastEngine.forecast(
            db=db,
            tenant_id=current_user.tenant_id,
            commodity=req.commodity,
            target_market=req.target_market,
            months_ahead=req.months_ahead,
        )
        return {"cost": CREDIT_COST_SINGLE, "result": result}
    except Exception as e:
        BillingService.refund(db, current_user.tenant_id, CREDIT_COST_SINGLE, "Refund: demand failed")
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cultural")
@require_feature(Feature.AI_BRAIN)
async def cultural_strategy(
    req: CulturalRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cultural negotiation strategy. Cost: 3 credits."""
    AIWorkerService.check_kill_switch(db)
    BillingService.deduct_balance(db, current_user.tenant_id, CREDIT_COST_SINGLE,
                                  f"Cultural: {req.your_country}→{req.counterpart_country}")
    db.commit()

    try:
        result = await CulturalNegotiationEngine.get_strategy(
            db=db,
            tenant_id=current_user.tenant_id,
            counterpart_country=req.counterpart_country,
            your_country=req.your_country,
            product_category=req.product_category,
            deal_size_usd=req.deal_size_usd,
            relationship_stage=req.relationship_stage,
        )
        return {"cost": CREDIT_COST_SINGLE, "result": result}
    except Exception as e:
        BillingService.refund(db, current_user.tenant_id, CREDIT_COST_SINGLE, "Refund: cultural failed")
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

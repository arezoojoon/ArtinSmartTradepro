"""
AI Brain Router — Trade Intelligence Decision Engine.
Endpoint for one-click trade decisions combining all engines.
Enterprise+ only.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.brain import TradeOpportunity, MarketSignal
from app.middleware.auth import get_current_active_user
from app.middleware.plan_gate import require_feature
from app.constants import Feature
from app.services.billing import BillingService
from app.services.ai_worker import AIWorkerService
from app.services.engines.decision_engine import DecisionEngine
from app.services.brain_arbitrage_engine import ArbitrageEngine as BrainArbitrageEngine
from app.services.engines.risk_engine import RiskEngine
from app.services.engines.demand_forecast_engine import DemandForecastEngine
from app.services.engines.cultural_engine import CulturalNegotiationEngine
from pydantic import BaseModel
from typing import Optional, List
import logging
import uuid
import random
from datetime import datetime

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
        from app.schemas.brain import ArbitrageInput
        
        # Bridge ArbitrageRequest to ArbitrageInput
        input_data = ArbitrageInput(
            product_key=req.product_hs,
            origin_country=req.origin_country,
            destination_country=req.destination_country,
            buy_market=req.origin_country, # Port not provided in request, use country as proxy
            sell_market=req.destination_country,
            buy_price=req.buy_price_per_kg,
            buy_currency=req.buy_currency,
            sell_price=req.sell_price_per_kg,
            sell_currency=req.sell_currency,
            # We skip freight_cost here to let the engine fetch it from integration
        )
        
        engine = BrainArbitrageEngine(db)
        result = await engine.run_analysis(
            tenant_id=current_user.tenant_id,
            input_data=input_data
        )
        return {"cost": CREDIT_COST_SINGLE, "result": result.dict()}
    except Exception as e:
        BillingService.refund(db, current_user.tenant_id, CREDIT_COST_SINGLE, f"Refund: arbitrage failed: {str(e)}")
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


# --- Proactive V3 Brain Endpoints ---

@router.post("/scan")
def trigger_brain_scan(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Trigger a proactive AI scan for the user's tenant.
    This simulates 'The Brain' waking up and finding deals.
    """
    # In production, this would be an async Celery task
    # For MVP, we run it as a background task
    background_tasks.add_task(run_proactive_scan, current_user.tenant_id, db)
    return {"message": "AI Brain scan initiated. You will be notified of new opportunities."}

@router.get("/feed")
def get_brain_feed(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the personalized intelligence feed for the dashboard.
    Returns Opportunities and Signals.
    """
    opportunities = db.query(TradeOpportunity).filter(
        TradeOpportunity.tenant_id == current_user.tenant_id,
        TradeOpportunity.status != 'rejected'
    ).order_by(TradeOpportunity.created_at.desc()).limit(10).all()
    
    signals = db.query(MarketSignal).filter(
        (MarketSignal.tenant_id == current_user.tenant_id) | (MarketSignal.tenant_id == None)
    ).order_by(MarketSignal.created_at.desc()).limit(5).all()
    
    return {
        "opportunities": opportunities,
        "signals": signals
    }

# Mock Service Logic (should be in services/brain_service.py)
def run_proactive_scan(tenant_id: uuid.UUID, db: Session):
    """
    Simulates the AI finding new arbitrage or risk signals.
    """
    # 1. Simulate finding an Arbitrage Opportunity
    opp = TradeOpportunity(
        tenant_id=tenant_id,
        title=f"Arbitrage Opportunity: {random.choice(['Brazilian Coffee', 'Turkish Hazelnuts', 'Indian Spices'])}",
        description="Detected price gap between local supplier and EU market.",
        type="Arbitrage",
        status="new",
        estimated_profit=random.uniform(5000, 50000),
        confidence_score=random.uniform(0.7, 0.99),
        actions={"next_step": "Request Quote"},
        created_at=datetime.utcnow()
    )
    db.add(opp)
    
    # 2. Simulate a Market Signal
    sig = MarketSignal(
        tenant_id=tenant_id,
        headline=f"Supply Chain Alert: {random.choice(['Port Congestion', 'Recall', 'Strike'])} in {random.choice(['Rotterdam', 'Shanghai', 'Jebel Ali'])}",
        summary="Expect delays of 3-5 days for shipments routed through this hub.",
        severity="medium",
        impact_area="Logistics",
        sentiment_score=-0.6,
        created_at=datetime.utcnow()
    )
    db.add(sig)
    
    db.commit()
    print(f"[BRAIN] Generated proactive insights for Tenant {tenant_id}")
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
from app.services.engines.arbitrage_engine import ArbitrageEngine
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
f r o m   f a s t a p i   i m p o r t   A P I R o u t e r ,   D e p e n d s ,   H T T P E x c e p t i o n ,   B a c k g r o u n d T a s k s 
 
 f r o m   s q l a l c h e m y . o r m   i m p o r t   S e s s i o n 
 
 f r o m   t y p i n g   i m p o r t   L i s t ,   O p t i o n a l 
 
 i m p o r t   u u i d 
 
 
 
 f r o m   a p p . d a t a b a s e   i m p o r t   g e t _ d b 
 
 f r o m   a p p . m o d e l s . u s e r   i m p o r t   U s e r 
 
 f r o m   a p p . m o d e l s . t e n a n t   i m p o r t   T e n a n t 
 
 f r o m   a p p . m o d e l s . b r a i n   i m p o r t   T r a d e O p p o r t u n i t y ,   M a r k e t S i g n a l 
 
 f r o m   a p p . m i d d l e w a r e . a u t h   i m p o r t   g e t _ c u r r e n t _ a c t i v e _ u s e r 
 
 
 
 r o u t e r   =   A P I R o u t e r ( ) 
 
 
 
 @ r o u t e r . p o s t ( " / s c a n " ) 
 
 d e f   t r i g g e r _ b r a i n _ s c a n ( 
 
         b a c k g r o u n d _ t a s k s :   B a c k g r o u n d T a s k s , 
 
         c u r r e n t _ u s e r :   U s e r   =   D e p e n d s ( g e t _ c u r r e n t _ a c t i v e _ u s e r ) , 
 
         d b :   S e s s i o n   =   D e p e n d s ( g e t _ d b ) 
 
 ) : 
 
         " " " 
 
         T r i g g e r   a   p r o a c t i v e   A I   s c a n   f o r   t h e   u s e r ' s   t e n a n t . 
 
         T h i s   s i m u l a t e s   ' T h e   B r a i n '   w a k i n g   u p   a n d   f i n d i n g   d e a l s . 
 
         " " " 
 
         #   I n   p r o d u c t i o n ,   t h i s   w o u l d   b e   a n   a s y n c   C e l e r y   t a s k 
 
         #   F o r   M V P ,   w e   r u n   i t   a s   a   b a c k g r o u n d   t a s k 
 
         b a c k g r o u n d _ t a s k s . a d d _ t a s k ( r u n _ p r o a c t i v e _ s c a n ,   c u r r e n t _ u s e r . t e n a n t _ i d ,   d b ) 
 
         r e t u r n   { " m e s s a g e " :   " A I   B r a i n   s c a n   i n i t i a t e d .   Y o u   w i l l   b e   n o t i f i e d   o f   n e w   o p p o r t u n i t i e s . " } 
 
 
 
 @ r o u t e r . g e t ( " / f e e d " ) 
 
 d e f   g e t _ b r a i n _ f e e d ( 
 
         c u r r e n t _ u s e r :   U s e r   =   D e p e n d s ( g e t _ c u r r e n t _ a c t i v e _ u s e r ) , 
 
         d b :   S e s s i o n   =   D e p e n d s ( g e t _ d b ) 
 
 ) : 
 
         " " " 
 
         G e t   t h e   p e r s o n a l i z e d   i n t e l l i g e n c e   f e e d   f o r   t h e   d a s h b o a r d . 
 
         R e t u r n s   O p p o r t u n i t i e s   a n d   S i g n a l s . 
 
         " " " 
 
         o p p o r t u n i t i e s   =   d b . q u e r y ( T r a d e O p p o r t u n i t y ) . f i l t e r ( 
 
                 T r a d e O p p o r t u n i t y . t e n a n t _ i d   = =   c u r r e n t _ u s e r . t e n a n t _ i d , 
 
                 T r a d e O p p o r t u n i t y . s t a t u s   ! =   ' r e j e c t e d ' 
 
         ) . o r d e r _ b y ( T r a d e O p p o r t u n i t y . c r e a t e d _ a t . d e s c ( ) ) . l i m i t ( 1 0 ) . a l l ( ) 
 
         
 
         s i g n a l s   =   d b . q u e r y ( M a r k e t S i g n a l ) . f i l t e r ( 
 
                 ( M a r k e t S i g n a l . t e n a n t _ i d   = =   c u r r e n t _ u s e r . t e n a n t _ i d )   |   ( M a r k e t S i g n a l . t e n a n t _ i d   = =   N o n e ) 
 
         ) . o r d e r _ b y ( M a r k e t S i g n a l . c r e a t e d _ a t . d e s c ( ) ) . l i m i t ( 5 ) . a l l ( ) 
 
         
 
         r e t u r n   { 
 
                 " o p p o r t u n i t i e s " :   o p p o r t u n i t i e s , 
 
                 " s i g n a l s " :   s i g n a l s 
 
         } 
 
 
 
 #   M o c k   S e r v i c e   L o g i c   ( s h o u l d   b e   i n   s e r v i c e s / b r a i n _ s e r v i c e . p y ) 
 
 i m p o r t   r a n d o m 
 
 f r o m   d a t e t i m e   i m p o r t   d a t e t i m e ,   t i m e d e l t a 
 
 
 
 d e f   r u n _ p r o a c t i v e _ s c a n ( t e n a n t _ i d :   u u i d . U U I D ,   d b :   S e s s i o n ) : 
 
         " " " 
 
         S i m u l a t e s   t h e   A I   f i n d i n g   n e w   a r b i t r a g e   o r   r i s k   s i g n a l s . 
 
         " " " 
 
         #   1 .   S i m u l a t e   f i n d i n g   a n   A r b i t r a g e   O p p o r t u n i t y 
 
         o p p   =   T r a d e O p p o r t u n i t y ( 
 
                 t e n a n t _ i d = t e n a n t _ i d , 
 
                 t i t l e = f " A r b i t r a g e   O p p o r t u n i t y :   { r a n d o m . c h o i c e ( [ ' B r a z i l i a n   C o f f e e ' ,   ' T u r k i s h   H a z e l n u t s ' ,   ' I n d i a n   S p i c e s ' ] ) } " , 
 
                 d e s c r i p t i o n = " D e t e c t e d   p r i c e   g a p   b e t w e e n   l o c a l   s u p p l i e r   a n d   E U   m a r k e t . " , 
 
                 t y p e = " A r b i t r a g e " , 
 
                 s t a t u s = " n e w " , 
 
                 e s t i m a t e d _ p r o f i t = r a n d o m . u n i f o r m ( 5 0 0 0 ,   5 0 0 0 0 ) , 
 
                 c o n f i d e n c e _ s c o r e = r a n d o m . u n i f o r m ( 0 . 7 ,   0 . 9 9 ) , 
 
                 a c t i o n s = { " n e x t _ s t e p " :   " R e q u e s t   Q u o t e " } , 
 
                 c r e a t e d _ a t = d a t e t i m e . u t c n o w ( ) 
 
         ) 
 
         d b . a d d ( o p p ) 
 
         
 
         #   2 .   S i m u l a t e   a   M a r k e t   S i g n a l 
 
         s i g   =   M a r k e t S i g n a l ( 
 
                 t e n a n t _ i d = t e n a n t _ i d , 
 
                 h e a d l i n e = f " S u p p l y   C h a i n   A l e r t :   { r a n d o m . c h o i c e ( [ ' P o r t   C o n g e s t i o n ' ,   ' R e c a l l ' ,   ' S t r i k e ' ] ) }   i n   { r a n d o m . c h o i c e ( [ ' R o t t e r d a m ' ,   ' S h a n g h a i ' ,   ' J e b e l   A l i ' ] ) } " , 
 
                 s u m m a r y = " E x p e c t   d e l a y s   o f   3 - 5   d a y s   f o r   s h i p m e n t s   r o u t e d   t h r o u g h   t h i s   h u b . " , 
 
                 s e v e r i t y = " m e d i u m " , 
 
                 i m p a c t _ a r e a = " L o g i s t i c s " , 
 
                 s e n t i m e n t _ s c o r e = - 0 . 6 , 
 
                 c r e a t e d _ a t = d a t e t i m e . u t c n o w ( ) 
 
         ) 
 
         d b . a d d ( s i g ) 
 
         
 
         d b . c o m m i t ( ) 
 
         p r i n t ( f " [ B R A I N ]   G e n e r a t e d   p r o a c t i v e   i n s i g h t s   f o r   T e n a n t   { t e n a n t _ i d } " ) 
 
 
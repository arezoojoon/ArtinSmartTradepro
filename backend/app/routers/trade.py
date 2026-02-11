"""
Trade Intelligence Router — AI-powered market, seasonal, brand, and shipping analysis.
All endpoints gated to Enterprise+ plans via @require_feature().
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_active_user
from app.middleware.plan_gate import require_feature
from app.services.gemini_service import GeminiService
from app.services.billing import BillingService
from app.constants import Feature
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# --- Costs ---
COST_SEASONAL = 1.0
COST_MARKET = 1.5
COST_BRAND = 2.0
COST_SHIPPING = 1.0
COST_CARD_SCAN = 0.5
COST_INSIGHTS = 1.0

# --- Schemas ---
class SeasonalQuery(BaseModel):
    product: str
    region: str = "global"

class MarketQuery(BaseModel):
    product: str
    season: str = "Q4"

class BrandQuery(BaseModel):
    brand_name: str

class ShippingQuery(BaseModel):
    product: str
    origin: str
    destination: str

class InsightsQuery(BaseModel):
    data_summary: str

# --- Endpoints ---

@router.post("/analyze/seasonal")
@require_feature(Feature.TRADE_INTELLIGENCE)
async def analyze_seasonal(
    query: SeasonalQuery,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Seasonal demand analysis.
    Example: "Which season is best to sell cocoa-based products in Europe?"
    Cost: 1.0 credit
    """
    # Deduct credits
    with db.begin_nested():
        BillingService.deduct_balance(
            db=db,
            tenant_id=current_user.tenant_id,
            amount=COST_SEASONAL,
            description=f"Seasonal analysis: {query.product} in {query.region}"
        )
    
    try:
        result = GeminiService.analyze_seasonal(query.product, query.region)
        db.commit()
        return {"cost": COST_SEASONAL, "result": result}
    except Exception as e:
        BillingService.refund(db, current_user.tenant_id, COST_SEASONAL,
                             f"Refund: seasonal analysis failed")
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/analyze/market")
@require_feature(Feature.TRADE_INTELLIGENCE)
async def analyze_market(
    query: MarketQuery,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Market intelligence.
    Example: "Which countries have peak demand for FMCG products in summer?"
    Cost: 1.5 credits
    """
    with db.begin_nested():
        BillingService.deduct_balance(
            db=db,
            tenant_id=current_user.tenant_id,
            amount=COST_MARKET,
            description=f"Market analysis: {query.product} in {query.season}"
        )
    
    try:
        result = GeminiService.analyze_market(query.product, query.season)
        db.commit()
        return {"cost": COST_MARKET, "result": result}
    except Exception as e:
        BillingService.refund(db, current_user.tenant_id, COST_MARKET,
                             f"Refund: market analysis failed")
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/analyze/brand")
@require_feature(Feature.BRAND_DATA)
async def analyze_brand(
    query: BrandQuery,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Brand & supply chain intelligence.
    Example: "Show me all raw material suppliers for Nutella"
    Cost: 2.0 credits
    """
    with db.begin_nested():
        BillingService.deduct_balance(
            db=db,
            tenant_id=current_user.tenant_id,
            amount=COST_BRAND,
            description=f"Brand analysis: {query.brand_name}"
        )
    
    try:
        result = GeminiService.analyze_brand(query.brand_name)
        db.commit()
        return {"cost": COST_BRAND, "result": result}
    except Exception as e:
        BillingService.refund(db, current_user.tenant_id, COST_BRAND,
                             f"Refund: brand analysis failed")
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/shipping")
@require_feature(Feature.SHIPPING_TOOLS)
async def estimate_shipping(
    query: ShippingQuery,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Shipping cost estimation + compliance check.
    Cost: 1.0 credit
    """
    with db.begin_nested():
        BillingService.deduct_balance(
            db=db,
            tenant_id=current_user.tenant_id,
            amount=COST_SHIPPING,
            description=f"Shipping: {query.product} from {query.origin} to {query.destination}"
        )
    
    try:
        result = GeminiService.analyze_shipping(query.product, query.origin, query.destination)
        db.commit()
        return {"cost": COST_SHIPPING, "result": result}
    except Exception as e:
        BillingService.refund(db, current_user.tenant_id, COST_SHIPPING,
                             f"Refund: shipping analysis failed")
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/scan-card")
@require_feature(Feature.AI_VISION)
async def scan_business_card(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    DEPRECATED — Use POST /api/v1/crm/ai/vision/scan instead.
    Kept for backward compatibility. Redirects to new async pipeline.
    """
    raise HTTPException(
        status_code=301,
        detail="This endpoint is deprecated. Use POST /api/v1/crm/ai/vision/scan for async processing with rate limiting, billing, and per-field confidence."
    )

@router.post("/insights")
@require_feature(Feature.AI_BRAIN)
async def generate_insights(
    query: InsightsQuery,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    AI Brain: Generate insights from data summary.
    Cost: 1.0 credit
    """
    with db.begin_nested():
        BillingService.deduct_balance(
            db=db,
            tenant_id=current_user.tenant_id,
            amount=COST_INSIGHTS,
            description="AI insights generation"
        )
    
    try:
        result = GeminiService.generate_insights(query.data_summary)
        db.commit()
        return {"cost": COST_INSIGHTS, "result": result}
    except Exception as e:
        BillingService.refund(db, current_user.tenant_id, COST_INSIGHTS,
                             f"Refund: insights generation failed")
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

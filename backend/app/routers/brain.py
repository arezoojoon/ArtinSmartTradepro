"""
Brain Router - API Endpoints for Strategic Trade Intelligence (Phase 5).
Connects the frontend to the Arbitrage, Risk, Demand, and Cultural engines.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Dict, Any
import logging

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.brain import (
    RiskEngineOutput,
    DemandForecastOutput,
    PlaybookRequest, CulturalEngineOutput,
)

# Import the deterministic engines
from app.services.engines.risk_engine import RiskEngine
from app.services.engines.demand_forecast_engine import DemandForecastEngine
from app.services.engines.cultural_engine import CulturalEngine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Strategic Intelligence Brain"])

# Initialize stateless engines
demand_engine = DemandForecastEngine()
cultural_engine = CulturalEngine()


# -------------------------------------------------------------------
# Individual Engine Endpoints
# -------------------------------------------------------------------

@router.get("/risk/assess", response_model=RiskEngineOutput)
async def assess_trade_risk(
    origin_country: str,
    destination_country: str,
    commodity: str = "General",
    sell_currency: str = "USD",
    supplier_id: str = None,
    buyer_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assess comprehensive trade risk (Sanctions, USD Liquidity, Logistics).
    Returns a Risk-Adjusted Margin penalty score.
    """
    logger.info(
        f"Tenant {current_user.tenant_id} requested risk assessment: "
        f"{origin_country} -> {destination_country}"
    )
    try:
        risk_data = await RiskEngine.assess(
            db=db,
            tenant_id=current_user.tenant_id,
            destination_country=destination_country,
            origin_country=origin_country,
            commodity=commodity,
            sell_currency=sell_currency,
            buyer_id=buyer_id,
            supplier_id=supplier_id,
        )
        return risk_data
    except Exception as e:
        logger.error(f"Risk Assessment failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute risk metrics.")


@router.get("/demand/forecast", response_model=DemandForecastOutput)
async def forecast_market_demand(
    product_key: str,
    hs_code: str,
    target_country: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Predicts stockout risks, seasonal peaks, and calculates the optimal profit window.
    """
    logger.info(
        f"Tenant {current_user.tenant_id} requested demand forecast for "
        f"HS:{hs_code} in {target_country}"
    )
    try:
        demand_data = await demand_engine.assess(
            product_key=product_key,
            hs_code=hs_code,
            target_country=target_country,
        )
        return demand_data
    except Exception as e:
        logger.error(f"Demand Forecast failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to forecast market demand.")


@router.get("/culture/playbook", response_model=CulturalEngineOutput)
async def get_negotiation_playbook(
    target_country: str,
    deal_type: str,
    product_key: str = "General Commodity",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates an AI-driven "Deal Closer" playbook (GET version).
    Includes region-specific objection handling and strict walk-away points.
    """
    if deal_type not in ("sourcing", "sales"):
        raise HTTPException(status_code=400, detail="deal_type must be 'sourcing' or 'sales'")

    logger.info(
        f"Tenant {current_user.tenant_id} requested {deal_type} playbook for {target_country}"
    )
    try:
        playbook_data = await cultural_engine.generate_playbook(
            country=target_country,
            deal_type=deal_type,
            product=product_key,
        )
        return CulturalEngineOutput(**playbook_data)
    except Exception as e:
        logger.error(f"Cultural Playbook generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate strategic playbook.")


@router.post("/cultural/playbook", response_model=CulturalEngineOutput)
async def generate_negotiation_playbook(
    input_data: PlaybookRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate a full negotiation playbook for a target country (POST version).

    Example: POST /api/v1/brain/cultural/playbook
    {
        "country": "AE",
        "deal_type": "sales",
        "product": "Sunflower Oil"
    }
    """
    try:
        result = await cultural_engine.generate_playbook(
            country=input_data.country,
            deal_type=input_data.deal_type,
            product=input_data.product,
        )
        return CulturalEngineOutput(**result)
    except Exception as e:
        logger.error(f"Cultural playbook engine error: {e}")
        raise HTTPException(status_code=500, detail=f"Cultural playbook engine error: {str(e)}")


# -------------------------------------------------------------------
# Macro Engine: The "One-Click" Decision Intelligence Hub
# -------------------------------------------------------------------

@router.post("/run-macro-intelligence")
async def run_full_macro_intelligence(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Orchestrates all Brain Engines (Risk, Demand, Culture) simultaneously.
    This is what the 'Hunter Control Tower' frontend calls to display
    the Arbitrage Score, Climate Matrix, and Playbook boxes.

    Expected payload keys: product, hs_code, origin_country, destination_country, deal_type
    """
    product = payload.get("product", "Unknown")
    hs_code = payload.get("hs_code", "0000.00")
    origin = payload.get("origin_country", "Global")
    destination = payload.get("destination_country", "Global")
    deal_type = payload.get("deal_type", "sales")

    # Fallback values
    safe_dest = destination if destination != "Global" else "AE"
    safe_orig = origin if origin != "Global" else "CN"

    try:
        # Run all three engines (could use asyncio.gather in production)
        risk_res = await RiskEngine.assess(
            db=db,
            tenant_id=current_user.tenant_id,
            destination_country=safe_dest,
            origin_country=safe_orig,
            commodity=product,
        )
        demand_res = await demand_engine.assess(product, hs_code, safe_dest)
        culture_res = await cultural_engine.generate_playbook(safe_dest, deal_type, product)

        # Merge the strategic insights into one unified JSON response
        return {
            "status": "success",
            "engines_executed": ["risk", "demand", "culture"],
            "insights": {
                "arbitrage_score": round(100 - risk_res.get("composite_risk_score", 50), 2),
                "est_margin": (
                    f"Target Gross: 20% | Risk Adjusted: "
                    f"{20 - risk_res.get('risk_adjusted_margin_penalty_pct', 0):.1f}%"
                ),
                "climate_impact": " | ".join(
                    demand_res.get("forecast", {}).get("catalysts", ["Normal conditions"])
                ),
                "cultural_playbook": culture_res.get("strategic_playbook", {}).get(
                    "negotiation_tactic", "Standard negotiation."
                ),
                "stockout_alert": demand_res.get("forecast", {}).get("stockout_risk", {}).get(
                    "reason", "Stable"
                ),
                "walk_away_points": culture_res.get("walk_away_points", []),
            },
            "raw_engine_data": {
                "risk": risk_res,
                "demand": demand_res,
                "culture": culture_res,
            },
        }
    except Exception as e:
        logger.error(f"Macro Engine failure: {e}")
        raise HTTPException(status_code=500, detail="Macro Intelligence execution failed.")

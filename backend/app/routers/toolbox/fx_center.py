"""
FX Center Router - Live Currency Exchange Rates
Phase 6 Enhancement - Real FX data with hedging recommendations and volatility analysis
"""
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_active_user
from app.services.fx_rates import get_fx_rates_service

router = APIRouter()


# Pydantic Models
class FXRateRequest(BaseModel):
    base_currency: str
    quote_currency: str
    amount: Optional[float] = None


class FXRateResponse(BaseModel):
    base_currency: str
    quote_currency: str
    rate: float
    bid: Optional[float]
    ask: Optional[float]
    timestamp: str
    source: str
    high_24h: Optional[float]
    low_24h: Optional[float]
    change_24h: Optional[float]
    change_pct_24h: Optional[float]
    converted_amount: Optional[float]
    amount: Optional[float]


class MultipleRatesRequest(BaseModel):
    base_currency: str
    quote_currencies: List[str]


class MultipleRatesResponse(BaseModel):
    base_currency: str
    rates: Dict[str, Dict[str, Any]]
    timestamp: str


class VolatilityAnalysisResponse(BaseModel):
    currency_pair: str
    volatility_30d: float
    volatility_90d: float
    volatility_1y: float
    trend: str
    risk_level: str
    recommended_hedge: bool


class HedgeRequest(BaseModel):
    base_currency: str
    quote_currency: str
    exposure_amount: float
    timeframe_months: int = 3


class HedgeRecommendationResponse(BaseModel):
    currency_pair: str
    hedge_type: str
    hedge_percentage: float
    reasoning: str
    estimated_cost: float
    risk_reduction: float
    timeframe: str


class HistoricalRatesRequest(BaseModel):
    base_currency: str
    quote_currency: str
    start_date: str
    end_date: str


class HistoricalRatesResponse(BaseModel):
    base_currency: str
    quote_currency: str
    period: Dict[str, Any]
    data: List[Dict[str, Any]]
    statistics: Dict[str, Any]


class ForwardRateRequest(BaseModel):
    base_currency: str
    quote_currency: str
    forward_months: int


class ForwardRateResponse(BaseModel):
    base_currency: str
    quote_currency: str
    spot_rate: float
    forward_rate: float
    forward_months: int
    forward_points: float
    forward_premium_pct: float
    base_interest_rate: float
    quote_interest_rate: float
    calculation_date: str


@router.post("/rate", response_model=FXRateResponse, summary="Get FX Rate")
async def get_fx_rate(
    request: FXRateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FXRateResponse:
    """
    Get current FX rate for a currency pair
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get FX rates service
    fx_service = get_fx_rates_service(db)
    
    try:
        # Get FX rate
        rate_data = await fx_service.get_fx_rate(
            base_currency=request.base_currency,
            quote_currency=request.quote_currency,
            amount=request.amount
        )
        
        return FXRateResponse(**rate_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FX rate query failed: {str(e)}")


@router.post("/multiple-rates", response_model=MultipleRatesResponse, summary="Get Multiple FX Rates")
async def get_multiple_rates(
    request: MultipleRatesRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MultipleRatesResponse:
    """
    Get FX rates for multiple quote currencies
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get FX rates service
    fx_service = get_fx_rates_service(db)
    
    try:
        # Get multiple rates
        rates_data = await fx_service.get_multiple_rates(
            base_currency=request.base_currency,
            quote_currencies=request.quote_currencies
        )
        
        return MultipleRatesResponse(**rates_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multiple FX rates query failed: {str(e)}")


@router.get("/volatility/{base_currency}/{quote_currency}", response_model=VolatilityAnalysisResponse, summary="Analyze Volatility")
async def analyze_volatility(
    base_currency: str,
    quote_currency: str,
    period_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> VolatilityAnalysisResponse:
    """
    Analyze volatility for a currency pair
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get FX rates service
    fx_service = get_fx_rates_service(db)
    
    try:
        # Analyze volatility
        volatility = await fx_service.analyze_volatility(
            base_currency=base_currency,
            quote_currency=quote_currency,
            period_days=period_days
        )
        
        return VolatilityAnalysisResponse(
            currency_pair=volatility.currency_pair,
            volatility_30d=volatility.volatility_30d,
            volatility_90d=volatility.volatility_90d,
            volatility_1y=volatility.volatility_1y,
            trend=volatility.trend,
            risk_level=volatility.risk_level,
            recommended_hedge=volatility.recommended_hedge
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Volatility analysis failed: {str(e)}")


@router.post("/hedge-recommendations", response_model=List[HedgeRecommendationResponse], summary="Get Hedge Recommendations")
async def get_hedge_recommendations(
    request: HedgeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[HedgeRecommendationResponse]:
    """
    Get hedging recommendations for currency exposure
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get FX rates service
    fx_service = get_fx_rates_service(db)
    
    try:
        # Get hedge recommendations
        recommendations = await fx_service.get_hedge_recommendations(
            base_currency=request.base_currency,
            quote_currency=request.quote_currency,
            exposure_amount=request.exposure_amount,
            timeframe_months=request.timeframe_months
        )
        
        return [
            HedgeRecommendationResponse(
                currency_pair=rec.currency_pair,
                hedge_type=rec.hedge_type,
                hedge_percentage=rec.hedge_percentage,
                reasoning=rec.reasoning,
                estimated_cost=rec.estimated_cost,
                risk_reduction=rec.risk_reduction,
                timeframe=rec.timeframe
            )
            for rec in recommendations
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hedge recommendations failed: {str(e)}")


@router.post("/historical-rates", response_model=HistoricalRatesResponse, summary="Get Historical Rates")
async def get_historical_rates(
    request: HistoricalRatesRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> HistoricalRatesResponse:
    """
    Get historical FX rates for a period
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get FX rates service
    fx_service = get_fx_rates_service(db)
    
    try:
        # Get historical rates
        historical_data = await fx_service.get_historical_rates(
            base_currency=request.base_currency,
            quote_currency=request.quote_currency,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return HistoricalRatesResponse(**historical_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Historical rates query failed: {str(e)}")


@router.post("/forward-rate", response_model=ForwardRateResponse, summary="Calculate Forward Rate")
async def calculate_forward_rate(
    request: ForwardRateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ForwardRateResponse:
    """
    Calculate forward FX rate based on interest rate differential
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get FX rates service
    fx_service = get_fx_rates_service(db)
    
    try:
        # Calculate forward rate
        forward_data = await fx_service.calculate_forward_rate(
            base_currency=request.base_currency,
            quote_currency=request.quote_currency,
            forward_months=request.forward_months
        )
        
        return ForwardRateResponse(**forward_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forward rate calculation failed: {str(e)}")


@router.get("/market-overview", summary="Get Market Overview")
async def get_market_overview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get FX market overview with major currency pairs
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get FX rates service
    fx_service = get_fx_rates_service(db)
    
    try:
        # Get market overview
        overview = await fx_service.get_market_overview()
        
        return overview
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market overview failed: {str(e)}")


@router.get("/currencies", summary="Get Supported Currencies")
async def get_supported_currencies(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get list of supported currencies
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    currencies = [
        {
            "code": "USD",
            "name": "United States Dollar",
            "symbol": "$",
            "country": "United States",
            "is_major": True,
            "decimal_places": 2
        },
        {
            "code": "EUR",
            "name": "Euro",
            "symbol": "€",
            "country": "Eurozone",
            "is_major": True,
            "decimal_places": 2
        },
        {
            "code": "GBP",
            "name": "British Pound Sterling",
            "symbol": "£",
            "country": "United Kingdom",
            "is_major": True,
            "decimal_places": 2
        },
        {
            "code": "JPY",
            "name": "Japanese Yen",
            "symbol": "¥",
            "country": "Japan",
            "is_major": True,
            "decimal_places": 0
        },
        {
            "code": "CNY",
            "name": "Chinese Yuan",
            "symbol": "¥",
            "country": "China",
            "is_major": True,
            "decimal_places": 2
        },
        {
            "code": "CAD",
            "name": "Canadian Dollar",
            "symbol": "C$",
            "country": "Canada",
            "is_major": True,
            "decimal_places": 2
        },
        {
            "code": "AUD",
            "name": "Australian Dollar",
            "symbol": "A$",
            "country": "Australia",
            "is_major": True,
            "decimal_places": 2
        },
        {
            "code": "CHF",
            "name": "Swiss Franc",
            "symbol": "Fr",
            "country": "Switzerland",
            "is_major": True,
            "decimal_places": 2
        },
        {
            "code": "HKD",
            "name": "Hong Kong Dollar",
            "symbol": "HK$",
            "country": "Hong Kong",
            "is_major": True,
            "decimal_places": 2
        },
        {
            "code": "SGD",
            "name": "Singapore Dollar",
            "symbol": "S$",
            "country": "Singapore",
            "is_major": True,
            "decimal_places": 2
        },
        {
            "code": "KRW",
            "name": "South Korean Won",
            "symbol": "₩",
            "country": "South Korea",
            "is_major": False,
            "decimal_places": 0
        },
        {
            "code": "INR",
            "name": "Indian Rupee",
            "symbol": "₹",
            "country": "India",
            "is_major": False,
            "decimal_places": 2
        },
        {
            "code": "MXN",
            "name": "Mexican Peso",
            "symbol": "Mex$",
            "country": "Mexico",
            "is_major": False,
            "decimal_places": 2
        },
        {
            "code": "BRL",
            "name": "Brazilian Real",
            "symbol": "R$",
            "country": "Brazil",
            "is_major": False,
            "decimal_places": 2
        },
        {
            "code": "RUB",
            "name": "Russian Ruble",
            "symbol": "₽",
            "country": "Russia",
            "is_major": False,
            "decimal_places": 2
        },
        {
            "code": "ZAR",
            "name": "South African Rand",
            "symbol": "R",
            "country": "South Africa",
            "is_major": False,
            "decimal_places": 2
        },
        {
            "code": "THB",
            "name": "Thai Baht",
            "symbol": "฿",
            "country": "Thailand",
            "is_major": False,
            "decimal_places": 2
        },
        {
            "code": "MYR",
            "name": "Malaysian Ringgit",
            "symbol": "RM",
            "country": "Malaysia",
            "is_major": False,
            "decimal_places": 2
        },
        {
            "code": "IDR",
            "name": "Indonesian Rupiah",
            "symbol": "Rp",
            "country": "Indonesia",
            "is_major": False,
            "decimal_places": 0
        },
        {
            "code": "PHP",
            "name": "Philippine Peso",
            "symbol": "₱",
            "country": "Philippines",
            "is_major": False,
            "decimal_places": 2
        }
    ]
    
    return {
        "currencies": currencies,
        "total_count": len(currencies),
        "major_currencies": [c for c in currencies if c["is_major"]],
        "data_source": "Currency Database",
        "last_updated": datetime.utcnow().isoformat()
    }


@router.get("/major-pairs", summary="Get Major Currency Pairs")
async def get_major_pairs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get major currency pairs
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    major_pairs = [
        {
            "pair": "EUR/USD",
            "base_currency": "EUR",
            "quote_currency": "USD",
            "description": "Euro to US Dollar",
            "category": "major",
            "avg_daily_volume": "High",
            "liquidity": "Very High"
        },
        {
            "pair": "GBP/USD",
            "base_currency": "GBP",
            "quote_currency": "USD",
            "description": "British Pound to US Dollar",
            "category": "major",
            "avg_daily_volume": "High",
            "liquidity": "Very High"
        },
        {
            "pair": "USD/JPY",
            "base_currency": "USD",
            "quote_currency": "JPY",
            "description": "US Dollar to Japanese Yen",
            "category": "major",
            "avg_daily_volume": "High",
            "liquidity": "Very High"
        },
        {
            "pair": "USD/CHF",
            "base_currency": "USD",
            "quote_currency": "CHF",
            "description": "US Dollar to Swiss Franc",
            "category": "major",
            "avg_daily_volume": "Medium",
            "liquidity": "High"
        },
        {
            "pair": "AUD/USD",
            "base_currency": "AUD",
            "quote_currency": "USD",
            "description": "Australian Dollar to US Dollar",
            "category": "major",
            "avg_daily_volume": "Medium",
            "liquidity": "High"
        },
        {
            "pair": "USD/CAD",
            "base_currency": "USD",
            "quote_currency": "CAD",
            "description": "US Dollar to Canadian Dollar",
            "category": "major",
            "avg_daily_volume": "Medium",
            "liquidity": "High"
        },
        {
            "pair": "NZD/USD",
            "base_currency": "NZD",
            "quote_currency": "USD",
            "description": "New Zealand Dollar to US Dollar",
            "category": "major",
            "avg_daily_volume": "Low",
            "liquidity": "Medium"
        },
        {
            "pair": "EUR/GBP",
            "base_currency": "EUR",
            "quote_currency": "GBP",
            "description": "Euro to British Pound",
            "category": "cross",
            "avg_daily_volume": "Medium",
            "liquidity": "High"
        },
        {
            "pair": "EUR/JPY",
            "base_currency": "EUR",
            "quote_currency": "JPY",
            "description": "Euro to Japanese Yen",
            "category": "cross",
            "avg_daily_volume": "High",
            "liquidity": "Very High"
        },
        {
            "pair": "GBP/JPY",
            "base_currency": "GBP",
            "quote_currency": "JPY",
            "description": "British Pound to Japanese Yen",
            "category": "cross",
            "avg_daily_volume": "Medium",
            "liquidity": "High"
        },
        {
            "pair": "EUR/CHF",
            "base_currency": "EUR",
            "quote_currency": "CHF",
            "description": "Euro to Swiss Franc",
            "category": "cross",
            "avg_daily_volume": "Medium",
            "liquidity": "High"
        },
        {
            "pair": "USD/CNY",
            "base_currency": "USD",
            "quote_currency": "CNY",
            "description": "US Dollar to Chinese Yuan",
            "category": "exotic",
            "avg_daily_volume": "Medium",
            "liquidity": "Medium"
        },
        {
            "pair": "USD/INR",
            "base_currency": "USD",
            "quote_currency": "INR",
            "description": "US Dollar to Indian Rupee",
            "category": "exotic",
            "avg_daily_volume": "Medium",
            "liquidity": "Medium"
        },
        {
            "pair": "USD/BRL",
            "base_currency": "USD",
            "quote_currency": "BRL",
            "description": "US Dollar to Brazilian Real",
            "category": "exotic",
            "avg_daily_volume": "Low",
            "liquidity": "Low"
        },
        {
            "pair": "USD/RUB",
            "base_currency": "USD",
            "quote_currency": "RUB",
            "description": "US Dollar to Russian Ruble",
            "category": "exotic",
            "avg_daily_volume": "Low",
            "liquidity": "Low"
        }
    ]
    
    return {
        "major_pairs": major_pairs,
        "total_count": len(major_pairs),
        "categories": {
            "major": [p for p in major_pairs if p["category"] == "major"],
            "cross": [p for p in major_pairs if p["category"] == "cross"],
            "exotic": [p for p in major_pairs if p["category"] == "exotic"]
        },
        "data_source": "FX Market Data",
        "last_updated": datetime.utcnow().isoformat()
    }

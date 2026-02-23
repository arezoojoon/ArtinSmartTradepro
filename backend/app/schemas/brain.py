"""
Phase 5 Brain Schemas
Pydantic models for brain engine inputs, outputs, and explainability
"""
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum
from .evidence import InsightWrapper

# Enums
class BrainEngineType(str, Enum):
    ARBITRAGE = "arbitrage"
    RISK = "risk"
    DEMAND = "demand"
    CULTURAL = "cultural"

class BrainRunStatus(str, Enum):
    SUCCESS = "success"
    INSUFFICIENT_DATA = "insufficient_data"
    FAILED = "failed"

class ArbitrageOutcome(str, Enum):
    WON = "won"
    LOST = "lost"
    NO_GO = "no_go"
    UNKNOWN = "unknown"

class PaymentTerms(str, Enum):
    LC = "LC"
    TT = "TT"
    OA = "OA"

class RiskSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# Base Models
class DataUsedItem(InsightWrapper):
    """Single data source entry used in engine computation"""
    dataset: str = Field(..., description="Dataset or table name")
    record_count: Optional[int] = Field(None, description="Number of records used")
    # Inherits source, timestamp, confidence, reasoning from InsightWrapper

class ExplainabilityBundle(BaseModel):
    """Complete explainability bundle for brain engine outputs"""
    data_used: List[DataUsedItem] = Field(..., description="Data sources used in computation")
    assumptions: List[str] = Field(..., description="Explicit assumptions made")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    confidence_rationale: str = Field(..., description="How confidence was calculated")
    action_plan: List[str] = Field(..., description="Deterministic next steps")
    limitations: List[str] = Field(default_factory=list, description="Known limitations")
    computation_method: str = Field(..., description="Method used for computation")
    missing_fields: List[str] = Field(default_factory=list, description="Required fields that were missing")

# Arbitrage Engine Models
class ArbitrageInput(BaseModel):
    """Input for arbitrage engine"""
    product_key: str = Field(..., description="Internal product ID or generic name")
    hs_code: Optional[str] = Field(None, description="HS code for tariff lookup (6-8 digits)")
    origin_country: str = Field(..., description="Origin country ISO 2-letter code")
    destination_country: str = Field(..., description="Destination country ISO 2-letter code")
    buy_market: str = Field(..., description="Buy market (port/city)")
    sell_market: str = Field(..., description="Sell market (port/city)")
    buy_price: float = Field(..., gt=0, description="Buy price")
    buy_currency: str = Field(..., description="Buy currency code")
    sell_price: float = Field(..., gt=0, description="Sell price")
    sell_currency: str = Field(..., description="Sell currency code")
    freight_cost: Optional[float] = Field(None, ge=0, description="Freight cost")
    fx_rates: Optional[Dict[str, float]] = Field(None, description="FX rates to USD")
    fees: Optional[List[Dict[str, Any]]] = Field(None, description="Additional fees")
    target_margin_pct: Optional[float] = Field(None, description="Target margin percentage")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Constraints like MOQ, lead time")
    
    @validator('origin_country', 'destination_country')
    def validate_country(cls, v):
        if len(v) != 2:
            raise ValueError("Country code must be ISO 2-letter format")
        return v.upper()

    @validator('buy_currency', 'sell_currency')
    def validate_currency(cls, v):
        valid_currencies = {'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'AUD', 'CAD', 'CHF', 'SEK', 'NOK', 'DKK'}
        if v.upper() not in valid_currencies:
            raise ValueError(f"Invalid currency code: {v}")
        return v.upper()

class SimilarDeal(BaseModel):
    """Similar past arbitrage deal"""
    id: UUID
    product_key: str
    buy_market: str
    sell_market: str
    estimated_margin_pct: Optional[float]
    realized_margin_pct: Optional[float]
    outcome: ArbitrageOutcome
    created_at: datetime

class ArbitrageOpportunityCard(BaseModel):
    """Arbitrage opportunity analysis"""
    estimated_margin_pct: float = Field(..., description="Estimated margin percentage")
    key_drivers: List[str] = Field(..., description="Key factors driving the margin")
    next_actions: List[str] = Field(..., description="Recommended next steps")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")

class ArbitrageFinancials(BaseModel):
    """Detailed financial breakdown of an arbitrage opportunity"""
    buy_price_usd: float
    sell_price_usd: float
    total_cost_usd: float
    total_revenue_usd: float
    total_freight_cost: float
    tariff_cost_usd: float
    tariff_pct: float
    total_fees: float
    total_profit_usd: float
    estimated_margin_pct: float
    base_currency: str = "USD"

class ArbitrageOutput(BaseModel):
    """Output from arbitrage engine"""
    status: str = Field(..., description="Computation status")
    financials: Optional[ArbitrageFinancials] = None
    opportunity_card: Optional[ArbitrageOpportunityCard] = None
    similar_deals: List[SimilarDeal] = Field(default_factory=list)
    explainability: ExplainabilityBundle

# Risk Engine Models
class RiskInput(BaseModel):
    """Input for risk engine"""
    product_key: str = Field(..., description="HS code or internal product ID")
    origin_country: str = Field(..., description="Origin country")
    destination_country: str = Field(..., description="Destination country")
    hs_code: Optional[str] = Field(None, description="HS code")
    incoterms: str = Field(..., description="Incoterms")
    payment_terms: PaymentTerms = Field(..., description="Payment terms")
    supplier_id: Optional[str] = Field(None, description="Supplier identifier")
    buyer_country: Optional[str] = Field(None, description="Buyer country")
    route_tags: Optional[List[str]] = Field(None, description="Route tags like 'RedSea'")

class LogisticsRiskData(BaseModel):
    score: float = Field(..., description="0-100")
    port_efficiency: float = Field(..., description="0-100")
    lane_safety: float = Field(..., description="0-100")
    reason: str

class SanctionsData(BaseModel):
    score: float = Field(..., description="0-100")
    level: str
    primary: bool
    secondary: bool
    reason: str

class USDLiquidityData(BaseModel):
    score: float = Field(..., description="0-100")
    level: str
    reason: str

class RiskFactors(BaseModel):
    logistics_risk: LogisticsRiskData
    sanctions_depth: SanctionsData
    usd_liquidity: USDLiquidityData
    political_risk_score: float
    fx_volatility_score: float
    buyer_default_probability: float
    supplier_reliability_score: float

class RiskItem(BaseModel):
    """Individual risk item"""
    type: str = Field(..., description="Risk type (political/payment/supplier/customs/route)")
    severity: RiskSeverity = Field(..., description="Risk severity")
    reason: str = Field(..., description="Reason for risk")
    mitigation_steps: List[str] = Field(..., description="Mitigation steps")

class RiskOutput(BaseModel):
    """Output from risk engine"""
    status: str = Field(..., description="Computation status")
    risk_register: List[RiskItem] = Field(default_factory=list)
    overall_risk_level: Optional[RiskSeverity] = None
    composite_risk_score: float = Field(0.0, description="Overall risk score 0-100")
    risk_adjusted_margin_penalty_pct: float = Field(0.0, description="Percentage to deduct from expected margin due to risk")
    factors: Optional[RiskFactors] = None
    explainability: ExplainabilityBundle

# Demand Forecast Models
class DemandInput(BaseModel):
    """Input for demand forecast engine"""
    product_key: str = Field(..., description="HS code or internal product ID")
    country: str = Field(..., description="Country for forecast")
    forecast_months: int = Field(6, ge=1, le=12, description="Number of months to forecast")
    historical_start_date: Optional[date] = Field(None, description="Historical data start date")
    historical_end_date: Optional[date] = Field(None, description="Historical data end date")

class ForecastPoint(BaseModel):
    """Single forecast point"""
    forecast_date: date = Field(..., alias="date", description="Forecast date")
    demand_value: float = Field(..., description="Forecasted demand value")
    confidence_interval: Optional[Dict[str, float]] = Field(None, description="Confidence interval")

    class Config:
        populate_by_name = True

class PeakWindow(BaseModel):
    """Peak demand window"""
    start_date: date = Field(..., description="Peak window start")
    end_date: date = Field(..., description="Peak window end")
    demand_multiplier: float = Field(..., description="Demand multiplier during peak")

class DemandOutput(BaseModel):
    """Output from demand forecast engine"""
    status: str = Field(..., description="Computation status")
    forecast_points: List[ForecastPoint] = Field(default_factory=list)
    peak_windows: List[PeakWindow] = Field(default_factory=list)
    stockout_risk_score: float = Field(0.0, description="0-100")
    best_profit_month: Optional[str] = None
    best_shipment_month: Optional[str] = None
    method_used: str = Field(..., description="Forecast method used")
    data_points_used: int = Field(..., description="Number of historical data points used")
    explainability: ExplainabilityBundle

# Cultural Strategy Models
class CulturalInput(BaseModel):
    """Input for cultural strategy engine"""
    destination_country: str = Field(..., description="Destination country")
    buyer_type: str = Field(..., description="Buyer type (B2B/Distributor/Retail)")
    payment_terms_target: PaymentTerms = Field(..., description="Target payment terms")
    deal_context: str = Field(..., max_length=500, description="Short deal context")
    language: str = Field(..., description="Language (en/ar/fa/ru/hi/ur)")
    
    @validator('language')
    def validate_language(cls, v):
        valid_languages = {'en', 'ar', 'fa', 'ru', 'hi', 'ur'}
        if v.lower() not in valid_languages:
            raise ValueError(f"Invalid language code: {v}")
        return v.lower()

class CulturalTemplate(BaseModel):
    """Generated cultural template"""
    template_type: str = Field(..., description="Template type (email/whatsapp/negotiation)")
    content: str = Field(..., description="Template content")
    language: str = Field(..., description="Template language")
    referenced_profile_id: UUID = Field(..., description="Cultural profile ID used")

class CulturalOutput(BaseModel):
    """Output from cultural strategy engine"""
    status: str = Field(..., description="Computation status")
    templates: List[CulturalTemplate] = Field(default_factory=list)
    negotiation_tips: List[str] = Field(default_factory=list)
    objection_handling: List[str] = Field(default_factory=list)
    walk_away_points: List[str] = Field(default_factory=list)
    referenced_profile_ids: List[UUID] = Field(default_factory=list)
    explainability: ExplainabilityBundle

# Engine Run Models
class EngineRunCreate(BaseModel):
    """Create engine run request"""
    engine_type: BrainEngineType
    input_payload: Dict[str, Any]

class EngineRunResponse(BaseModel):
    """Engine run response"""
    id: UUID
    engine_type: BrainEngineType
    status: BrainRunStatus
    input_payload: Dict[str, Any]
    output_payload: Optional[Dict[str, Any]]
    explainability: Optional[ExplainabilityBundle]
    error: Optional[Dict[str, Any]]
    created_at: datetime

class EngineRunList(BaseModel):
    """List of engine runs"""
    runs: List[EngineRunResponse]
    total: int

# Asset Database Models
class ArbitrageHistoryCreate(BaseModel):
    """Create arbitrage history record"""
    product_key: str
    buy_market: str
    sell_market: str
    incoterms: str
    buy_price: float
    buy_currency: str
    sell_price: float
    sell_currency: str
    freight_cost: Optional[float]
    fx_rate: Optional[float]
    estimated_margin_pct: Optional[float]
    realized_margin_pct: Optional[float]
    outcome: Optional[ArbitrageOutcome]
    decision_reason: Optional[str]
    data_used: Optional[Dict[str, Any]]

class SupplierReliabilityCreate(BaseModel):
    """Create supplier reliability record"""
    supplier_name: str
    supplier_country: str
    identifiers: Optional[Dict[str, Any]]
    on_time_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    defect_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    dispute_count: int = Field(0, ge=0)
    avg_lead_time_days: Optional[int] = Field(None, ge=0)
    reliability_score: int = Field(0, ge=0, le=100)
    evidence: Optional[Dict[str, Any]]

class BuyerPaymentBehaviorCreate(BaseModel):
    """Create buyer payment behavior record"""
    buyer_country: str
    buyer_name: Optional[str]
    segment: Optional[str]
    avg_payment_delay_days: Optional[int] = Field(None, ge=0)
    default_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    preferred_terms: Optional[str]
    payment_risk_score: int = Field(0, ge=0, le=100)
    evidence: Optional[Dict[str, Any]]

class SeasonalityMatrixCreate(BaseModel):
    """Create seasonality matrix record"""
    product_key: str
    country: str
    season_key: str
    demand_index: Optional[float]
    price_index: Optional[float]
    volatility_index: Optional[float]
    data_used: Optional[Dict[str, Any]]

class CulturalProfileCreate(BaseModel):
    """Create cultural profile record"""
    country: str
    negotiation_style: Optional[Dict[str, Any]]
    do_dont: Optional[Dict[str, Any]]
    typical_terms: Optional[Dict[str, Any]]

class DemandTimeSeriesCreate(BaseModel):
    """Create demand time series record"""
    product_key: str
    country: str
    entry_date: date = Field(..., alias="date")
    demand_value: Optional[float]
    source_name: str
    data_used: Optional[Dict[str, Any]]

    class Config:
        populate_by_name = True

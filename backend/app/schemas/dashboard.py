from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from uuid import UUID

class InsightBase(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    source: str
    timestamp: datetime
    confidence: Optional[float] = Field(None, description="0-100 score")
    isInsufficientData: bool = False

class LiquidityData(BaseModel):
    balance: float
    currency: str
    pending_in: float
    pending_out: float
    dso: int
    source: str
    timestamp: datetime

class ShockData(BaseModel):
    id: str
    asset: str
    change: str
    trend: str # "up" or "down"
    source: str
    confidence: float

class DashboardMobileResponse(BaseModel):
    liquidity: LiquidityData
    opportunities: List[InsightBase]
    risks: List[InsightBase]
    shocks: List[ShockData]
    leads: List[InsightBase]

class PipelineStageData(BaseModel):
    name: str
    count: int
    value: float

class MarginMatrixRow(BaseModel):
    product: str
    origin: str
    destination: str
    net_margin: float
    roi: float

class CashFlowPoint(BaseModel):
    period: str # "Jan", "Feb", etc or timestamp
    cash_in: float
    cash_out: float

class RiskHeatmapPoint(BaseModel):
    country: str
    category: str
    score: int # 0-100

class PerformanceSnapshot(BaseModel):
    id: str
    name: str
    type: str # "supplier" or "buyer"
    score: float # 0-100

class DashboardWebResponse(BaseModel):
    pipeline: List[PipelineStageData]
    margin_matrix: List[MarginMatrixRow]
    cash_flow: List[CashFlowPoint]
    risk_heatmap: List[RiskHeatmapPoint]
    performance: List[PerformanceSnapshot]

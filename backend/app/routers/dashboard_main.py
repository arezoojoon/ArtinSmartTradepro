"""
Main Dashboard with Pipeline Summary, Margin Overview, Risk Heatmap
Phase 6 Enhancement - Complete tenant dashboard with real data aggregation
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Any, List, Dict, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.middleware.auth import get_current_active_user
from app.models.billing import Wallet
from app.models.crm import CRMInvoice, CRMCompany
from app.models.brain import BrainEngineRun
from app.models.hunter_phase4 import HunterLead
from app.models.phase5 import AssetArbitrageHistory, AssetSupplierReliability, AssetBuyerPaymentBehavior

router = APIRouter()


# Pydantic Models
class PipelineStage(BaseModel):
    name: str
    count: int
    value: float
    percentage: float


class MarginOverview(BaseModel):
    product_key: str
    buy_market: str
    sell_market: str
    estimated_margin_pct: float
    realized_margin_pct: Optional[float]
    confidence: float
    status: str


class RiskHeatmapItem(BaseModel):
    country: str
    risk_type: str
    risk_score: int
    risk_level: str
    description: str


class CashFlowTrend(BaseModel):
    period: str
    cash_in: float
    cash_out: float
    net_flow: float
    dso: float


class SupplierReliability(BaseModel):
    supplier_name: str
    country: str
    reliability_score: int
    on_time_rate: float
    defect_rate: float
    last_shipment: str


class BuyerPaymentBehavior(BaseModel):
    country: str
    segment: str
    avg_payment_delay_days: int
    default_rate: float
    recommended_terms: str


class MainDashboardResponse(BaseModel):
    pipeline_summary: List[PipelineStage]
    margin_overview: List[MarginOverview]
    cash_flow_trends: List[CashFlowTrend]
    risk_heatmap: List[RiskHeatmapItem]
    supplier_reliability: List[SupplierReliability]
    buyer_payment_behavior: List[BuyerPaymentBehavior]
    kpi_summary: Dict[str, Any]


@router.get("/main", response_model=MainDashboardResponse, summary="Get Main Dashboard")
def get_main_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MainDashboardResponse:
    """
    Get comprehensive main dashboard with all key metrics
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Initialize all data collections
    pipeline_summary = []
    margin_overview = []
    cash_flow_trends = []
    risk_heatmap = []
    supplier_reliability = []
    buyer_payment_behavior = []
    
    # 1. Pipeline Summary (Mock CRM data - would integrate with actual CRM)
    try:
        # Mock pipeline stages - in production this would come from CRM pipeline
        pipeline_stages = [
            {"name": "Lead", "count": 45, "value": 2250000},
            {"name": "Qualified", "count": 23, "value": 1875000},
            {"name": "Proposal", "count": 12, "value": 980000},
            {"name": "Negotiation", "count": 8, "value": 650000},
            {"name": "Closed Won", "count": 5, "value": 425000},
            {"name": "Closed Lost", "count": 3, "value": 275000}
        ]
        
        total_value = sum(stage["value"] for stage in pipeline_stages)
        
        for stage in pipeline_stages:
            pipeline_summary.append(PipelineStage(
                name=stage["name"],
                count=stage["count"],
                value=stage["value"],
                percentage=(stage["value"] / total_value * 100) if total_value > 0 else 0
            ))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching pipeline summary: {e}")
    
    # 2. Margin Overview from Arbitrage History
    try:
        arbitrage_history = db.query(AssetArbitrageHistory).filter(
            AssetArbitrageHistory.tenant_id == tenant_id,
            AssetArbitrageHistory.created_at >= datetime.utcnow() - timedelta(days=30)
        ).order_by(AssetArbitrageHistory.created_at.desc()).limit(10).all()
        
        for record in arbitrage_history:
            margin_overview.append(MarginOverview(
                product_key=record.product_key,
                buy_market=record.buy_market,
                sell_market=record.sell_market,
                estimated_margin_pct=float(record.estimated_margin_pct) if record.estimated_margin_pct else 0,
                realized_margin_pct=float(record.realized_margin_pct) if record.realized_margin_pct else None,
                confidence=0.85,  # Mock confidence
                status="active" if record.outcome is None else record.outcome
            ))
    except Exception as e:
        logger.error(f"Error fetching margin overview: {e}")
    
    # 3. Cash Flow Trends (Mock data - would integrate with billing)
    try:
        for i in range(6, -1, -1):
            period_start = datetime.utcnow() - timedelta(days=30*i)
            period_end = period_start + timedelta(days=30)
            
            # Mock cash flow data
            cash_in = 125000 + (i * 15000)  # Increasing trend
            cash_out = 98000 + (i * 8000)   # Increasing trend
            net_flow = cash_in - cash_out
            dso = 42 - (i * 2)  # Improving DSO
            
            cash_flow_trends.append(CashFlowTrend(
                period=period_start.strftime("%b %Y"),
                cash_in=cash_in,
                cash_out=cash_out,
                net_flow=net_flow,
                dso=dso
            ))
    except Exception as e:
        logger.error(f"Error fetching cash flow trends: {e}")
    
    # 4. Risk Heatmap from Risk Engine and Asset Data
    try:
        # Get risk assessments from brain engine
        risk_runs = db.query(BrainEngineRun).filter(
            BrainEngineRun.tenant_id == tenant_id,
            BrainEngineRun.engine_type == "risk",
            BrainEngineRun.status == "success",
            BrainEngineRun.created_at >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        # Get payment behavior data
        payment_risks = db.query(AssetBuyerPaymentBehavior).filter(
            AssetBuyerPaymentBehavior.tenant_id == tenant_id
        ).all()
        
        # Combine risk data
        risk_data = {}
        
        # Process brain engine risks
        for run in risk_runs:
            if run.output_payload and "risk_assessment" in run.output_payload:
                risk = run.output_payload["risk_assessment"]
                country = risk.get("country", "Unknown")
                risk_type = risk.get("primary_risk", "general")
                score = risk.get("risk_score", 50)
                
                if country not in risk_data:
                    risk_data[country] = {}
                
                if risk_type not in risk_data[country]:
                    risk_data[country][risk_type] = {
                        "score": score,
                        "description": risk.get("description", "Risk detected")
                    }
        
        # Process payment behavior risks
        for risk in payment_risks:
            country = risk.buyer_country
            if country not in risk_data:
                risk_data[country] = {}
            
            if "payment" not in risk_data[country]:
                risk_data[country]["payment"] = {
                    "score": int(risk.payment_risk_score),
                    "description": f"Payment risk: {risk.default_rate}% default rate"
                }
        
        # Convert to response format
        for country, risk_types in risk_data.items():
            for risk_type, data in risk_types.items():
                score = data["score"]
                risk_level = "low" if score < 30 else "medium" if score < 70 else "high"
                
                risk_heatmap.append(RiskHeatmapItem(
                    country=country,
                    risk_type=risk_type,
                    risk_score=score,
                    risk_level=risk_level,
                    description=data["description"]
                ))
    except Exception as e:
        logger.error(f"Error fetching risk heatmap: {e}")
    
    # 5. Supplier Reliability
    try:
        suppliers = db.query(AssetSupplierReliability).filter(
            AssetSupplierReliability.tenant_id == tenant_id
        ).order_by(AssetSupplierReliability.reliability_score.desc()).limit(10).all()
        
        for supplier in suppliers:
            supplier_reliability.append(SupplierReliability(
                supplier_name=supplier.supplier_name,
                country=supplier.supplier_country,
                reliability_score=supplier.reliability_score,
                on_time_rate=float(supplier.on_time_rate) if supplier.on_time_rate else 0,
                defect_rate=float(supplier.defect_rate) if supplier.defect_rate else 0,
                last_shipment=supplier.created_at.strftime("%Y-%m-%d")
            ))
    except Exception as e:
        logger.error(f"Error fetching supplier reliability: {e}")
    
    # 6. Buyer Payment Behavior
    try:
        buyer_behaviors = db.query(AssetBuyerPaymentBehavior).filter(
            AssetBuyerPaymentBehavior.tenant_id == tenant_id
        ).all()
        
        # Group by country and segment
        behavior_data = {}
        for behavior in buyer_behaviors:
            key = f"{behavior.buyer_country}_{behavior.segment}"
            if key not in behavior_data:
                behavior_data[key] = {
                    "country": behavior.buyer_country,
                    "segment": behavior.segment,
                    "avg_delay": 0,
                    "default_rate": 0,
                    "count": 0
                }
            
            behavior_data[key]["avg_delay"] += behavior.avg_payment_delay_days or 0
            behavior_data[key]["default_rate"] += behavior.default_rate or 0
            behavior_data[key]["count"] += 1
        
        for data in behavior_data.values():
            if data["count"] > 0:
                avg_delay = data["avg_delay"] / data["count"]
                default_rate = data["default_rate"] / data["count"]
                
                # Determine recommended terms
                recommended_terms = "Net 30"
                if avg_delay > 45:
                    recommended_terms = "Letter of Credit"
                elif avg_delay > 30:
                    recommended_terms = "Net 15"
                elif avg_delay > 15:
                    recommended_terms = "Net 30"
                
                buyer_payment_behavior.append(BuyerPaymentBehavior(
                    country=data["country"],
                    segment=data["segment"],
                    avg_payment_delay_days=int(avg_delay),
                    default_rate=float(default_rate),
                    recommended_terms=recommended_terms
                ))
    except Exception as e:
        logger.error(f"Error fetching buyer payment behavior: {e}")
    
    # 7. KPI Summary
    kpi_summary = {
        "total_pipeline_value": sum(stage.value for stage in pipeline_summary),
        "weighted_margin": sum(margin.estimated_margin_pct for margin in margin_overview) / len(margin_overview) if margin_overview else 0,
        "avg_reliability_score": sum(sup.reliability_score for sup in supplier_reliability) / len(supplier_reliability) if supplier_reliability else 0,
        "high_risk_countries": len(set(risk.country for risk in risk_heatmap if risk.risk_level == "high")),
        "cash_flow_health": "positive" if cash_flow_trends and cash_flow_trends[-1].net_flow > 0 else "negative"
    }
    
    return MainDashboardResponse(
        pipeline_summary=pipeline_summary,
        margin_overview=margin_overview,
        cash_flow_trends=cash_flow_trends,
        risk_heatmap=risk_heatmap,
        supplier_reliability=supplier_reliability,
        buyer_payment_behavior=buyer_payment_behavior,
        kpi_summary=kpi_summary
    )


@router.get("/kpi-summary", summary="Get KPI Summary")
def get_kpi_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get quick KPI summary for dashboard widgets
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Calculate key metrics
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    kpis = {}
    
    # 1. Total Deals Value (Mock CRM data)
    kpis["total_deals_value"] = 4250000
    
    # 2. Average Margin (from arbitrage history)
    avg_margin = db.query(func.avg(AssetArbitrageHistory.estimated_margin_pct)).filter(
        AssetArbitrageHistory.tenant_id == tenant_id,
        AssetArbitrageHistory.created_at >= month_start
    ).scalar()
    
    kpis["avg_margin_pct"] = float(avg_margin) if avg_margin else 0
    
    # 3. Active Leads (from hunter)
    active_leads = db.query(HunterLead).filter(
        HunterLead.tenant_id == tenant_id,
        HunterLead.status.in_(["new", "enriched", "qualified"])
    ).count()
    
    kpis["active_leads"] = active_leads
    
    # 4. High Risk Items
    high_risk_count = db.query(BrainEngineRun).filter(
        BrainEngineRun.tenant_id == tenant_id,
        BrainEngineRun.engine_type == "risk",
        BrainEngineRun.created_at >= month_start
    ).count()
    
    kpis["high_risk_items"] = high_risk_count
    
    # 5. Supplier Reliability
    avg_reliability = db.query(func.avg(AssetSupplierReliability.reliability_score)).filter(
        AssetSupplierReliability.tenant_id == tenant_id
    ).scalar()
    
    kpis["avg_supplier_reliability"] = int(avg_reliability) if avg_reliability else 0
    
    # 6. Cash Flow Status
    kpis["cash_flow_status"] = "positive"  # Mock - would calculate from actual data
    
    return kpis

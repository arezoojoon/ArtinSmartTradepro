"""
/sys/costs — Cost Dashboard and Tracking
Phase 6 Enhancement - Track LLM, scraping, storage, and infrastructure costs
"""
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.database import get_db
from app.models.phase6 import SystemAdmin
from app.models.tenant import Tenant
from app.models.cost_tracking import (
    CostMetric, CostBudget, CostAlert, CostForecast, CostOptimization, CostSummary,
    CostCategory, CostProvider
)
from app.services.sys_admin_auth import get_current_sys_admin, write_sys_audit

router = APIRouter()


# Pydantic Models
class CostSummaryResponse(BaseModel):
    period_start: str
    period_end: str
    total_cost: float
    llm_cost: float
    scraping_cost: float
    storage_cost: float
    infrastructure_cost: float
    bandwidth_cost: float
    third_party_cost: float
    support_cost: float
    other_cost: float
    provider_breakdown: Dict[str, float]
    cost_change_percentage: Optional[float]
    cost_change_amount: Optional[float]


class CostTrend(BaseModel):
    period: str
    total_cost: float
    llm_cost: float
    scraping_cost: float
    storage_cost: float
    infrastructure_cost: float


class CostAlertResponse(BaseModel):
    id: str
    alert_type: str
    category: str
    provider: Optional[str]
    current_spend: float
    budget_amount: Optional[float]
    percentage_used: float
    title: str
    message: str
    status: str
    created_at: str


class CostOptimizationResponse(BaseModel):
    id: str
    category: str
    provider: Optional[str]
    recommendation_type: str
    title: str
    description: str
    current_monthly_cost: float
    projected_monthly_savings: float
    savings_percentage: float
    implementation_complexity: str
    priority: str
    status: str


class CostForecastResponse(BaseModel):
    forecast_period: str
    forecast_start: str
    forecast_end: str
    predicted_cost: float
    confidence_level: float
    category: str
    provider: Optional[str]


@router.get("/summary", response_model=CostSummaryResponse, summary="Get Cost Summary")
def get_cost_summary(
    period: str = Query("monthly", description="Period: daily, weekly, monthly, yearly"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> CostSummaryResponse:
    """
    Get cost summary for the specified period
    """
    # Calculate period boundaries
    end_date = datetime.utcnow()
    if period == "daily":
        start_date = end_date - timedelta(days=1)
    elif period == "weekly":
        start_date = end_date - timedelta(weeks=1)
    elif period == "monthly":
        start_date = end_date - timedelta(days=30)
    else:  # yearly
        start_date = end_date - timedelta(days=365)
    
    # Query cost metrics
    query = db.query(CostMetric).filter(
        CostMetric.period_start >= start_date,
        CostMetric.period_end <= end_date
    )
    
    if tenant_id:
        query = query.filter(CostMetric.tenant_id == tenant_id)
    else:
        query = query.filter(CostMetric.tenant_id.is_(None))  # System-wide costs
    
    metrics = query.all()
    
    # Calculate totals by category
    totals = {
        "total_cost": 0,
        "llm_cost": 0,
        "scraping_cost": 0,
        "storage_cost": 0,
        "infrastructure_cost": 0,
        "bandwidth_cost": 0,
        "third_party_cost": 0,
        "support_cost": 0,
        "other_cost": 0,
        "provider_breakdown": {}
    }
    
    for metric in metrics:
        cost = float(metric.total_cost)
        totals["total_cost"] += cost
        totals[f"{metric.category}_cost"] += cost
        
        # Provider breakdown
        if metric.provider not in totals["provider_breakdown"]:
            totals["provider_breakdown"][metric.provider] = 0
        totals["provider_breakdown"][metric.provider] += cost
    
    # Get previous period for comparison
    previous_start = start_date - (end_date - start_date)
    previous_end = start_date
    
    previous_query = db.query(CostMetric).filter(
        CostMetric.period_start >= previous_start,
        CostMetric.period_end <= previous_end
    )
    
    if tenant_id:
        previous_query = previous_query.filter(CostMetric.tenant_id == tenant_id)
    else:
        previous_query = previous_query.filter(CostMetric.tenant_id.is_(None))
    
    previous_metrics = previous_query.all()
    previous_total = sum(float(m.total_cost) for m in previous_metrics)
    
    # Calculate change
    cost_change_percentage = None
    cost_change_amount = None
    
    if previous_total > 0:
        cost_change_amount = totals["total_cost"] - previous_total
        cost_change_percentage = (cost_change_amount / previous_total) * 100
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_cost_summary",
        resource_type="cost_tracking",
        actor_sys_admin_id=admin.id,
        metadata={
            "period": period,
            "tenant_id": tenant_id,
            "total_cost": totals["total_cost"]
        }
    )
    
    return CostSummaryResponse(
        period_start=start_date.isoformat(),
        period_end=end_date.isoformat(),
        total_cost=totals["total_cost"],
        llm_cost=totals["llm_cost"],
        scraping_cost=totals["scraping_cost"],
        storage_cost=totals["storage_cost"],
        infrastructure_cost=totals["infrastructure_cost"],
        bandwidth_cost=totals["bandwidth_cost"],
        third_party_cost=totals["third_party_cost"],
        support_cost=totals["support_cost"],
        other_cost=totals["other_cost"],
        provider_breakdown=totals["provider_breakdown"],
        cost_change_percentage=cost_change_percentage,
        cost_change_amount=cost_change_amount
    )


@router.get("/trends", response_model=List[CostTrend], summary="Get Cost Trends")
def get_cost_trends(
    period: str = Query("monthly", description="Period: daily, weekly, monthly, yearly"),
    periods: int = Query(12, description="Number of periods to return"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> List[CostTrend]:
    """
    Get cost trends over time
    """
    # Calculate date range
    end_date = datetime.utcnow()
    if period == "daily":
        start_date = end_date - timedelta(days=periods)
    elif period == "weekly":
        start_date = end_date - timedelta(weeks=periods)
    elif period == "monthly":
        start_date = end_date - timedelta(days=30 * periods)
    else:  # yearly
        start_date = end_date - timedelta(days=365 * periods)
    
    # Query cost summaries (or calculate from metrics)
    query = db.query(CostSummary).filter(
        CostSummary.period_type == period,
        CostSummary.period_start >= start_date,
        CostSummary.period_end <= end_date
    )
    
    if tenant_id:
        query = query.filter(CostSummary.tenant_id == tenant_id)
    else:
        query = query.filter(CostSummary.tenant_id.is_(None))
    
    summaries = query.order_by(CostSummary.period_start.asc()).all()
    
    trends = []
    for summary in summaries:
        trends.append(CostTrend(
            period=summary.period_start.strftime("%Y-%m-%d"),
            total_cost=float(summary.total_cost),
            llm_cost=float(summary.llm_cost),
            scraping_cost=float(summary.scraping_cost),
            storage_cost=float(summary.storage_cost),
            infrastructure_cost=float(summary.infrastructure_cost)
        ))
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_cost_trends",
        resource_type="cost_tracking",
        actor_sys_admin_id=admin.id,
        metadata={
            "period": period,
            "periods": periods,
            "tenant_id": tenant_id,
            "trends_count": len(trends)
        }
    )
    
    return trends


@router.get("/alerts", response_model=List[CostAlertResponse], summary="Get Cost Alerts")
def get_cost_alerts(
    status: Optional[str] = Query("active", description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    limit: int = Query(20, description="Maximum number of alerts"),
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> List[CostAlertResponse]:
    """
    Get cost alerts and notifications
    """
    query = db.query(CostAlert)
    
    if status:
        query = query.filter(CostAlert.status == status)
    
    if category:
        query = query.filter(CostAlert.category == category)
    
    if tenant_id:
        query = query.filter(CostAlert.tenant_id == tenant_id)
    else:
        query = query.filter(CostAlert.tenant_id.is_(None))
    
    alerts = query.order_by(CostAlert.created_at.desc()).limit(limit).all()
    
    alert_responses = []
    for alert in alerts:
        alert_responses.append(CostAlertResponse(
            id=str(alert.id),
            alert_type=alert.alert_type,
            category=alert.category,
            provider=alert.provider,
            current_spend=float(alert.current_spend),
            budget_amount=float(alert.budget_amount) if alert.budget_amount else None,
            percentage_used=float(alert.percentage_used),
            title=alert.title,
            message=alert.message,
            status=alert.status,
            created_at=alert.created_at.isoformat()
        ))
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_cost_alerts",
        resource_type="cost_tracking",
        actor_sys_admin_id=admin.id,
        metadata={
            "status": status,
            "category": category,
            "tenant_id": tenant_id,
            "alerts_count": len(alert_responses)
        }
    )
    
    return alert_responses


@router.get("/optimizations", response_model=List[CostOptimizationResponse], summary="Get Cost Optimizations")
def get_cost_optimizations(
    status: Optional[str] = Query("pending", description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> List[CostOptimizationResponse]:
    """
    Get cost optimization recommendations
    """
    query = db.query(CostOptimization)
    
    if status:
        query = query.filter(CostOptimization.status == status)
    
    if priority:
        query = query.filter(CostOptimization.priority == priority)
    
    if tenant_id:
        query = query.filter(CostOptimization.tenant_id == tenant_id)
    else:
        query = query.filter(CostOptimization.tenant_id.is_(None))
    
    optimizations = query.order_by(
        CostOptimization.priority.desc(),
        CostOptimization.projected_monthly_savings.desc()
    ).all()
    
    optimization_responses = []
    for opt in optimizations:
        optimization_responses.append(CostOptimizationResponse(
            id=str(opt.id),
            category=opt.category,
            provider=opt.provider,
            recommendation_type=opt.recommendation_type,
            title=opt.title,
            description=opt.description,
            current_monthly_cost=float(opt.current_monthly_cost),
            projected_monthly_savings=float(opt.projected_monthly_savings),
            savings_percentage=float(opt.savings_percentage),
            implementation_complexity=opt.implementation_complexity,
            priority=opt.priority,
            status=opt.status
        ))
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_cost_optimizations",
        resource_type="cost_tracking",
        actor_sys_admin_id=admin.id,
        metadata={
            "status": status,
            "priority": priority,
            "tenant_id": tenant_id,
            "optimizations_count": len(optimization_responses)
        }
    )
    
    return optimization_responses


@router.get("/forecasts", response_model=List[CostForecastResponse], summary="Get Cost Forecasts")
def get_cost_forecasts(
    months: int = Query(6, description="Number of months to forecast"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> List[CostForecastResponse]:
    """
    Get cost forecasts
    """
    # Calculate forecast period
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=30 * months)
    
    query = db.query(CostForecast).filter(
        CostForecast.forecast_start >= start_date,
        CostForecast.forecast_end <= end_date
    )
    
    if category:
        query = query.filter(CostForecast.category == category)
    
    if tenant_id:
        query = query.filter(CostForecast.tenant_id == tenant_id)
    else:
        query = query.filter(CostForecast.tenant_id.is_(None))
    
    forecasts = query.order_by(CostForecast.forecast_start.asc()).all()
    
    forecast_responses = []
    for forecast in forecasts:
        forecast_responses.append(CostForecastResponse(
            forecast_period=forecast.forecast_period,
            forecast_start=forecast.forecast_start.isoformat(),
            forecast_end=forecast.forecast_end.isoformat(),
            predicted_cost=float(forecast.predicted_cost),
            confidence_level=float(forecast.confidence_level),
            category=forecast.category,
            provider=forecast.provider
        ))
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_cost_forecasts",
        resource_type="cost_tracking",
        actor_sys_admin_id=admin.id,
        metadata={
            "months": months,
            "category": category,
            "tenant_id": tenant_id,
            "forecasts_count": len(forecast_responses)
        }
    )
    
    return forecast_responses


@router.get("/breakdown", summary="Get Detailed Cost Breakdown")
def get_cost_breakdown(
    period: str = Query("monthly", description="Period: daily, weekly, monthly, yearly"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get detailed cost breakdown by category and provider
    """
    # Calculate period boundaries
    end_date = datetime.utcnow()
    if period == "daily":
        start_date = end_date - timedelta(days=1)
    elif period == "weekly":
        start_date = end_date - timedelta(weeks=1)
    elif period == "monthly":
        start_date = end_date - timedelta(days=30)
    else:  # yearly
        start_date = end_date - timedelta(days=365)
    
    # Query cost metrics
    query = db.query(CostMetric).filter(
        CostMetric.period_start >= start_date,
        CostMetric.period_end <= end_date
    )
    
    if tenant_id:
        query = query.filter(CostMetric.tenant_id == tenant_id)
    else:
        query = query.filter(CostMetric.tenant_id.is_(None))
    
    metrics = query.all()
    
    # Build detailed breakdown
    breakdown = {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "type": period
        },
        "total_cost": sum(float(m.total_cost) for m in metrics),
        "categories": {},
        "providers": {},
        "services": {},
        "usage_metrics": {
            "total_tokens": 0,
            "total_api_calls": 0,
            "total_storage_gb": 0,
            "total_bandwidth_gb": 0
        }
    }
    
    for metric in metrics:
        cost = float(metric.total_cost)
        
        # Category breakdown
        if metric.category not in breakdown["categories"]:
            breakdown["categories"][metric.category] = {
                "total_cost": 0,
                "providers": {},
                "services": {}
            }
        
        breakdown["categories"][metric.category]["total_cost"] += cost
        
        if metric.provider not in breakdown["categories"][metric.category]["providers"]:
            breakdown["categories"][metric.category]["providers"][metric.provider] = 0
        breakdown["categories"][metric.category]["providers"][metric.provider] += cost
        
        if metric.service not in breakdown["categories"][metric.category]["services"]:
            breakdown["categories"][metric.category]["services"][metric.service] = 0
        breakdown["categories"][metric.category]["services"][metric.service] += cost
        
        # Provider breakdown
        if metric.provider not in breakdown["providers"]:
            breakdown["providers"][metric.provider] = {
                "total_cost": 0,
                "categories": {},
                "services": {}
            }
        
        breakdown["providers"][metric.provider]["total_cost"] += cost
        
        if metric.category not in breakdown["providers"][metric.provider]["categories"]:
            breakdown["providers"][metric.provider]["categories"][metric.category] = 0
        breakdown["providers"][metric.provider]["categories"][metric.category] += cost
        
        if metric.service not in breakdown["providers"][metric.provider]["services"]:
            breakdown["providers"][metric.provider]["services"][metric.service] = 0
        breakdown["providers"][metric.provider]["services"][metric.service] += cost
        
        # Service breakdown
        if metric.service not in breakdown["services"]:
            breakdown["services"][metric.service] = {
                "total_cost": 0,
                "provider": metric.provider,
                "category": metric.category,
                "usage_quantity": float(metric.usage_quantity),
                "usage_unit": metric.usage_unit,
                "unit_cost": float(metric.unit_cost)
            }
        
        breakdown["services"][metric.service]["total_cost"] += cost
        
        # Usage metrics (simplified aggregation)
        if metric.usage_unit == "tokens":
            breakdown["usage_metrics"]["total_tokens"] += int(metric.usage_quantity)
        elif metric.usage_unit == "calls":
            breakdown["usage_metrics"]["total_api_calls"] += int(metric.usage_quantity)
        elif metric.usage_unit == "GB":
            breakdown["usage_metrics"]["total_storage_gb"] += float(metric.usage_quantity)
    
    # Calculate cost efficiency metrics
    if breakdown["usage_metrics"]["total_tokens"] > 0:
        breakdown["cost_per_token"] = breakdown["total_cost"] / breakdown["usage_metrics"]["total_tokens"]
    
    if breakdown["usage_metrics"]["total_api_calls"] > 0:
        breakdown["cost_per_api_call"] = breakdown["total_cost"] / breakdown["usage_metrics"]["total_api_calls"]
    
    if breakdown["usage_metrics"]["total_storage_gb"] > 0:
        breakdown["cost_per_gb_storage"] = breakdown["total_cost"] / breakdown["usage_metrics"]["total_storage_gb"]
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_cost_breakdown",
        resource_type="cost_tracking",
        actor_sys_admin_id=admin.id,
        metadata={
            "period": period,
            "tenant_id": tenant_id,
            "total_cost": breakdown["total_cost"]
        }
    )
    
    return breakdown

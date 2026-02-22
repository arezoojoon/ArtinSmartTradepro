"""
/sys/revenue — MRR/ARR Dashboard for Super Admin
Phase 6 Enhancement - Revenue analytics, churn tracking, and growth metrics
"""
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.database import get_db
from app.models.phase6 import SystemAdmin, SysPlan, TenantSubscription
from app.models.tenant import Tenant
from app.models.billing_revenue import (
    RevenueSnapshot, RevenueEvent, ChurnPrediction, RevenueAlert,
    RevenuePeriod, RevenueEventType
)
from app.services.sys_admin_auth import get_current_sys_admin, write_sys_audit

router = APIRouter()


# Pydantic Models
class RevenueSummary(BaseModel):
    mrr: float
    arr: float
    nrr: float
    mrr_growth_pct: float
    arr_growth_pct: float
    active_customers: int
    new_customers: int
    churned_customers: int
    churn_rate: float
    ltv_cac_ratio: Optional[float] = None


class RevenueTrend(BaseModel):
    period: str
    mrr: float
    arr: float
    active_customers: int
    new_customers: int
    churned_customers: int


class PlanBreakdown(BaseModel):
    plan_code: str
    plan_name: str
    customers: int
    mrr: float
    avg_revenue_per_customer: float


class ChurnRisk(BaseModel):
    tenant_id: str
    tenant_name: str
    churn_probability: float
    risk_level: str
    risk_factors: List[Dict[str, Any]]
    days_since_prediction: int


class RevenueAlertItem(BaseModel):
    id: str
    alert_type: str
    severity: str
    title: str
    description: str
    current_value: Optional[float]
    percentage_change: Optional[float]
    created_at: str
    status: str


@router.get("/summary", response_model=RevenueSummary, summary="Get Revenue Summary")
def get_revenue_summary(
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> RevenueSummary:
    """
    Get current MRR/ARR summary with growth metrics
    """
    # Get latest monthly snapshot
    latest_snapshot = db.query(RevenueSnapshot).filter(
        RevenueSnapshot.period == "monthly"
    ).order_by(RevenueSnapshot.period_start.desc()).first()
    
    # Get previous month for growth calculation
    previous_snapshot = db.query(RevenueSnapshot).filter(
        RevenueSnapshot.period == "monthly",
        RevenueSnapshot.period_start < latest_snapshot.period_start if latest_snapshot else True
    ).order_by(RevenueSnapshot.period_start.desc()).offset(1).first() if latest_snapshot else None
    
    if not latest_snapshot:
        # Return empty summary if no data
        return RevenueSummary(
            mrr=0.0,
            arr=0.0,
            nrr=0.0,
            mrr_growth_pct=0.0,
            arr_growth_pct=0.0,
            active_customers=0,
            new_customers=0,
            churned_customers=0,
            churn_rate=0.0
        )
    
    # Calculate growth percentages
    mrr_growth = 0.0
    arr_growth = 0.0
    
    if previous_snapshot and previous_snapshot.mrr > 0:
        mrr_growth = ((float(latest_snapshot.mrr) - float(previous_snapshot.mrr)) / float(previous_snapshot.mrr)) * 100
    
    if previous_snapshot and previous_snapshot.arr > 0:
        arr_growth = ((float(latest_snapshot.arr) - float(previous_snapshot.arr)) / float(previous_snapshot.arr)) * 100
    
    # Calculate churn rate
    churn_rate = 0.0
    if latest_snapshot.active_customers > 0:
        churn_rate = (latest_snapshot.churned_customers / latest_snapshot.active_customers) * 100
    
    # TODO: Calculate LTV/CAC ratio when billing data is available
    ltv_cac_ratio = None
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_revenue_summary",
        resource_type="revenue",
        actor_sys_admin_id=admin.id,
        metadata={"mrr": float(latest_snapshot.mrr), "arr": float(latest_snapshot.arr)}
    )
    
    return RevenueSummary(
        mrr=float(latest_snapshot.mrr),
        arr=float(latest_snapshot.arr),
        nrr=float(latest_snapshot.nrr),
        mrr_growth_pct=mrr_growth,
        arr_growth_pct=arr_growth,
        active_customers=latest_snapshot.active_customers,
        new_customers=latest_snapshot.new_customers,
        churned_customers=latest_snapshot.churned_customers,
        churn_rate=churn_rate,
        ltv_cac_ratio=ltv_cac_ratio
    )


@router.get("/trends", response_model=List[RevenueTrend], summary="Get Revenue Trends")
def get_revenue_trends(
    period: str = Query("monthly", description="Period: daily, weekly, monthly, yearly"),
    months: int = Query(12, description="Number of periods to return"),
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> List[RevenueTrend]:
    """
    Get historical revenue trends for charts
    """
    # Calculate date range
    end_date = datetime.utcnow()
    if period == "monthly":
        start_date = end_date - timedelta(days=30 * months)
    elif period == "weekly":
        start_date = end_date - timedelta(weeks=months)
    elif period == "daily":
        start_date = end_date - timedelta(days=months)
    else:  # yearly
        start_date = end_date - timedelta(days=365 * months)
    
    # Query snapshots
    snapshots = db.query(RevenueSnapshot).filter(
        RevenueSnapshot.period == period,
        RevenueSnapshot.period_start >= start_date,
        RevenueSnapshot.period_start <= end_date
    ).order_by(RevenueSnapshot.period_start.asc()).all()
    
    trends = []
    for snapshot in snapshots:
        trends.append(RevenueTrend(
            period=snapshot.period_start.strftime("%Y-%m-%d"),
            mrr=float(snapshot.mrr),
            arr=float(snapshot.arr),
            active_customers=snapshot.active_customers,
            new_customers=snapshot.new_customers,
            churned_customers=snapshot.churned_customers
        ))
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_revenue_trends",
        resource_type="revenue",
        actor_sys_admin_id=admin.id,
        metadata={"period": period, "months": months}
    )
    
    return trends


@router.get("/plans", response_model=List[PlanBreakdown], summary="Get Plan Breakdown")
def get_plan_breakdown(
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> List[PlanBreakdown]:
    """
    Get revenue breakdown by plan
    """
    # Get latest monthly snapshot
    latest_snapshot = db.query(RevenueSnapshot).filter(
        RevenueSnapshot.period == "monthly"
    ).order_by(RevenueSnapshot.period_start.desc()).first()
    
    if not latest_snapshot or not latest_snapshot.plan_breakdown:
        return []
    
    # Get plan details
    plans = db.query(SysPlan).all()
    plan_map = {plan.code: plan.name for plan in plans}
    
    breakdowns = []
    for plan_code, data in latest_snapshot.plan_breakdown.items():
        plan_name = plan_map.get(plan_code, plan_code)
        customers = data.get("customers", 0)
        mrr = data.get("mrr", 0)
        
        avg_revenue = mrr / customers if customers > 0 else 0
        
        breakdowns.append(PlanBreakdown(
            plan_code=plan_code,
            plan_name=plan_name,
            customers=customers,
            mrr=float(mrr),
            avg_revenue_per_customer=float(avg_revenue)
        ))
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_plan_breakdown",
        resource_type="revenue",
        actor_sys_admin_id=admin.id,
        metadata={"plans_count": len(breakdowns)}
    )
    
    return breakdowns


@router.get("/churn-risks", response_model=List[ChurnRisk], summary="Get Churn Risks")
def get_churn_risks(
    risk_level: Optional[str] = Query(None, description="Filter by risk level: low, medium, high, critical"),
    limit: int = Query(50, description="Maximum number of risks to return"),
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> List[ChurnRisk]:
    """
    Get tenants at risk of churn
    """
    query = db.query(ChurnPrediction).join(Tenant)
    
    if risk_level:
        query = query.filter(ChurnPrediction.risk_level == risk_level)
    
    predictions = query.order_by(ChurnPrediction.churn_probability.desc()).limit(limit).all()
    
    risks = []
    for pred in predictions:
        days_since = (datetime.utcnow() - pred.prediction_date).days
        
        risks.append(ChurnRisk(
            tenant_id=str(pred.tenant_id),
            tenant_name=pred.tenant.name if pred.tenant else "Unknown",
            churn_probability=float(pred.churn_probability),
            risk_level=pred.risk_level,
            risk_factors=pred.risk_factors,
            days_since_prediction=days_since
        ))
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_churn_risks",
        resource_type="revenue",
        actor_sys_admin_id=admin.id,
        metadata={"risk_level": risk_level, "count": len(risks)}
    )
    
    return risks


@router.get("/alerts", response_model=List[RevenueAlertItem], summary="Get Revenue Alerts")
def get_revenue_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query("active", description="Filter by status"),
    limit: int = Query(20, description="Maximum number of alerts"),
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
) -> List[RevenueAlertItem]:
    """
    Get revenue alerts and anomalies
    """
    query = db.query(RevenueAlert)
    
    if severity:
        query = query.filter(RevenueAlert.severity == severity)
    
    if status:
        query = query.filter(RevenueAlert.status == status)
    
    alerts = query.order_by(RevenueAlert.created_at.desc()).limit(limit).all()
    
    alert_items = []
    for alert in alerts:
        alert_items.append(RevenueAlertItem(
            id=str(alert.id),
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            description=alert.description,
            current_value=float(alert.current_value) if alert.current_value else None,
            percentage_change=float(alert.percentage_change) if alert.percentage_change else None,
            created_at=alert.created_at.isoformat(),
            status=alert.status
        ))
    
    # Log audit
    write_sys_audit(
        db=db,
        action="view_revenue_alerts",
        resource_type="revenue",
        actor_sys_admin_id=admin.id,
        metadata={"severity": severity, "status": status, "count": len(alert_items)}
    )
    
    return alert_items


@router.post("/alerts/{alert_id}/acknowledge", summary="Acknowledge Revenue Alert")
def acknowledge_alert(
    alert_id: str,
    admin: SystemAdmin = Depends(get_current_sys_admin),
    db: Session = Depends(get_db),
):
    """
    Acknowledge a revenue alert
    """
    alert = db.query(RevenueAlert).filter(RevenueAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "acknowledged"
    alert.acknowledged_by = admin.id
    alert.acknowledged_at = datetime.utcnow()
    
    db.commit()
    
    # Log audit
    write_sys_audit(
        db=db,
        action="acknowledge_revenue_alert",
        resource_type="revenue_alert",
        resource_id=alert_id,
        actor_sys_admin_id=admin.id,
        before_state={"status": "active"},
        after_state={"status": "acknowledged", "acknowledged_by": str(admin.id)}
    )
    
    return {"message": "Alert acknowledged"}


# Service functions for revenue calculation (to be called by scheduled jobs)
def calculate_monthly_revenue(db: Session, year: int, month: int):
    """
    Calculate monthly revenue snapshot
    This should be called by a scheduled job on the first day of each month
    """
    # Calculate period boundaries
    if month == 12:
        period_start = datetime(year, month, 1)
        period_end = datetime(year + 1, 1, 1)
    else:
        period_start = datetime(year, month, 1)
        period_end = datetime(year, month + 1, 1)
    
    # Get active subscriptions
    active_subs = db.query(TenantSubscription).filter(
        TenantSubscription.status == "active",
        TenantSubscription.current_period_start < period_end,
        or_(
            TenantSubscription.current_period_end.is_(None),
            TenantSubscription.current_period_end > period_start
        )
    ).all()
    
    # Calculate MRR from subscriptions
    total_mrr = 0
    plan_breakdown = {}
    active_customers = len(active_subs)
    
    for sub in active_subs:
        plan = sub.plan
        monthly_price = float(plan.monthly_price_usd) if plan.monthly_price_usd else 0
        
        total_mrr += monthly_price
        
        # Update plan breakdown
        plan_code = plan.code
        if plan_code not in plan_breakdown:
            plan_breakdown[plan_code] = {"customers": 0, "mrr": 0}
        
        plan_breakdown[plan_code]["customers"] += 1
        plan_breakdown[plan_code]["mrr"] += monthly_price
    
    # Get new customers (subscriptions started this month)
    new_customers = db.query(TenantSubscription).filter(
        TenantSubscription.status == "active",
        TenantSubscription.current_period_start >= period_start,
        TenantSubscription.current_period_start < period_end
    ).count()
    
    # Get churned customers (subscriptions ended this month)
    churned_customers = db.query(TenantSubscription).filter(
        TenantSubscription.status == "canceled",
        TenantSubscription.current_period_end >= period_start,
        TenantSubscription.current_period_end < period_end
    ).count()
    
    # Create or update snapshot
    snapshot = RevenueSnapshot(
        period="monthly",
        period_start=period_start,
        period_end=period_end,
        mrr=total_mrr,
        arr=total_mrr * 12,  # Simple ARR calculation
        nrr=total_mrr,  # TODO: Calculate actual NRR with expansion and contraction
        active_customers=active_customers,
        new_customers=new_customers,
        churned_customers=churned_customers,
        plan_breakdown=plan_breakdown
    )
    
    db.add(snapshot)
    db.commit()
    
    return snapshot

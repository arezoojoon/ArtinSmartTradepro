"""
BI Analytics Router - Advanced Business Intelligence
Phase 6 Enhancement - Comprehensive analytics with custom dashboards and reporting
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
from app.services.bi_analytics import get_bi_analytics_service

router = APIRouter()


# Pydantic Models
class MetricRequest(BaseModel):
    metric_name: str
    filters: Optional[Dict[str, Any]] = None
    date_range: Optional[Dict[str, str]] = None


class MetricResponse(BaseModel):
    value: Any
    unit: str
    grouped_by: Optional[str] = None


class DashboardRequest(BaseModel):
    dashboard_type: str
    filters: Optional[Dict[str, Any]] = None
    date_range: Optional[Dict[str, str]] = None


class DashboardResponse(BaseModel):
    dashboard_type: str
    generated_at: str
    widgets: List[Dict[str, Any]]


class ReportRequest(BaseModel):
    report_type: str
    format_type: str = "json"
    date_range: Optional[Dict[str, str]] = None


class ReportResponse(BaseModel):
    report_type: str
    tenant_id: str
    date_range: Dict[str, str]
    generated_at: str
    sections: Dict[str, Any]


@router.post("/metrics/{metric_name}", response_model=MetricResponse, summary="Calculate Metric")
async def calculate_metric(
    metric_name: str,
    request: MetricRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MetricResponse:
    """
    Calculate a specific metric
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get BI analytics service
    bi_service = get_bi_analytics_service(db)
    
    try:
        # Calculate metric
        metric_data = await bi_service.calculate_metric(
            metric_name=metric_name,
            tenant_id=str(tenant_id),
            filters=request.filters,
            date_range=request.date_range
        )
        
        return MetricResponse(**metric_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metric calculation failed: {str(e)}")


@router.post("/dashboard", response_model=DashboardResponse, summary="Generate Dashboard")
async def generate_dashboard(
    request: DashboardRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """
    Generate a complete dashboard
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get BI analytics service
    bi_service = get_bi_analytics_service(db)
    
    try:
        # Generate dashboard
        dashboard_data = await bi_service.generate_dashboard(
            dashboard_type=request.dashboard_type,
            tenant_id=str(tenant_id),
            filters=request.filters,
            date_range=request.date_range
        )
        
        return DashboardResponse(**dashboard_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")


@router.post("/report", response_model=ReportResponse, summary="Generate Report")
async def generate_report(
    request: ReportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ReportResponse:
    """
    Generate a comprehensive report
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get BI analytics service
    bi_service = get_bi_analytics_service(db)
    
    try:
        # Generate report
        report_data = await bi_service.generate_report(
            report_type=request.report_type,
            tenant_id=str(tenant_id),
            format_type=request.format_type,
            date_range=request.date_range
        )
        
        return ReportResponse(**report_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/metrics", summary="Get Available Metrics")
async def get_available_metrics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get list of available metrics
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get BI analytics service
    bi_service = get_bi_analytics_service(db)
    
    metrics = []
    for metric_name, metric_def in bi_service.metric_definitions.items():
        metrics.append({
            "name": metric_name,
            "display_name": metric_def.name,
            "description": metric_def.description,
            "calculation_type": metric_def.calculation_type,
            "data_source": metric_def.data_source,
            "group_by": metric_def.group_by,
            "filters": metric_def.filters
        })
    
    return {
        "metrics": metrics,
        "total_count": len(metrics),
        "categories": {
            "deals": [m for m in metrics if m["data_source"] == "deals"],
            "leads": [m for m in metrics if m["data_source"] == "leads"],
            "financial": [m for m in metrics if m["data_source"] in ["wallet", "invoices"]],
            "performance": [m for m in metrics if m["data_source"] in ["supplier_reliability", "leads_deals"]]
        }
    }


@router.get("/dashboard-templates", summary="Get Dashboard Templates")
async def get_dashboard_templates(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get available dashboard templates
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get BI analytics service
    bi_service = get_bi_analytics_service(db)
    
    templates = []
    for template_name, widgets in bi_service.dashboard_templates.items():
        template_info = {
            "name": template_name,
            "display_name": template_name.replace("_", " ").title(),
            "widget_count": len(widgets),
            "widgets": [
                {
                    "id": widget.id,
                    "title": widget.title,
                    "widget_type": widget.widget_type,
                    "visualization": widget.visualization,
                    "metrics": widget.metrics
                }
                for widget in widgets
            ]
        }
        templates.append(template_info)
    
    return {
        "templates": templates,
        "total_count": len(templates),
        "categories": {
            "executive": [t for t in templates if t["name"] == "executive_overview"],
            "sales": [t for t in templates if t["name"] == "sales_performance"],
            "marketing": [t for t in templates if t["name"] == "lead_generation"],
            "financial": [t for t in templates if t["name"] == "financial_overview"]
        }
    }


@router.get("/report-types", summary="Get Report Types")
async def get_report_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get available report types
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    report_types = [
        {
            "type": "monthly",
            "display_name": "Monthly Report",
            "description": "Comprehensive monthly performance report",
            "sections": [
                "executive_summary",
                "sales_performance", 
                "financial_overview",
                "lead_generation",
                "recommendations"
            ],
            "default_date_range": "current_month"
        },
        {
            "type": "quarterly",
            "display_name": "Quarterly Report",
            "description": "Strategic quarterly business review",
            "sections": [
                "executive_summary",
                "sales_performance",
                "financial_overview", 
                "lead_generation",
                "recommendations"
            ],
            "default_date_range": "current_quarter"
        },
        {
            "type": "annual",
            "display_name": "Annual Report",
            "description": "Year-end comprehensive business analysis",
            "sections": [
                "executive_summary",
                "sales_performance",
                "financial_overview",
                "lead_generation", 
                "recommendations"
            ],
            "default_date_range": "current_year"
        },
        {
            "type": "custom",
            "display_name": "Custom Report",
            "description": "Custom date range and metrics",
            "sections": [
                "executive_summary",
                "sales_performance",
                "financial_overview",
                "lead_generation",
                "recommendations"
            ],
            "default_date_range": "custom"
        }
    ]
    
    return {
        "report_types": report_types,
        "total_count": len(report_types),
        "formats": ["json", "csv", "pdf"]
    }


@router.get("/data-sources", summary="Get Data Sources")
async def get_data_sources(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get available data sources for analytics
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    data_sources = [
        {
            "name": "deals",
            "display_name": "Deals",
            "description": "Deal management data including pipeline, values, and stages",
            "tables": ["deals"],
            "key_fields": ["total_value", "status", "created_at", "closed_at", "estimated_margin_pct"],
            "record_count": 1000,  # Mock count
            "last_updated": datetime.utcnow().isoformat()
        },
        {
            "name": "leads",
            "display_name": "Leads",
            "description": "Lead generation and qualification data",
            "tables": ["hunter_leads"],
            "key_fields": ["status", "score_total", "created_at", "primary_name", "country"],
            "record_count": 2500,  # Mock count
            "last_updated": datetime.utcnow().isoformat()
        },
        {
            "name": "wallet",
            "display_name": "Wallet",
            "description": "Financial wallet and balance information",
            "tables": ["wallets"],
            "key_fields": ["balance", "currency", "created_at", "updated_at"],
            "record_count": 1,  # Mock count
            "last_updated": datetime.utcnow().isoformat()
        },
        {
            "name": "invoices",
            "display_name": "Invoices",
            "description": "Billing and invoice data",
            "tables": ["invoices"],
            "key_fields": ["amount", "status", "due_date", "created_at", "paid_at"],
            "record_count": 150,  # Mock count
            "last_updated": datetime.utcnow().isoformat()
        },
        {
            "name": "supplier_reliability",
            "display_name": "Supplier Reliability",
            "description": "Supplier performance and reliability metrics",
            "tables": ["asset_supplier_reliability"],
            "key_fields": ["reliability_score", "on_time_rate", "defect_rate", "supplier_name"],
            "record_count": 50,  # Mock count
            "last_updated": datetime.utcnow().isoformat()
        }
    ]
    
    return {
        "data_sources": data_sources,
        "total_count": len(data_sources),
        "total_records": sum(ds["record_count"] for ds in data_sources)
    }


@router.get("/visualization-types", summary="Get Visualization Types")
async def get_visualization_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get available visualization types
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    visualization_types = [
        {
            "type": "number",
            "display_name": "Number",
            "description": "Single numeric value display",
            "suitable_for": ["kpi", "metrics", "counts"],
            "examples": ["Total Revenue", "Number of Deals", "Win Rate"]
        },
        {
            "type": "currency",
            "display_name": "Currency",
            "description": "Currency formatted number",
            "suitable_for": ["financial_metrics", "revenue", "costs"],
            "examples": ["Revenue", "Profit", "Average Deal Size"]
        },
        {
            "type": "percentage",
            "display_name": "Percentage",
            "description": "Percentage formatted value",
            "suitable_for": ["ratios", "rates", "margins"],
            "examples": ["Win Rate", "Profit Margin", "Conversion Rate"]
        },
        {
            "type": "bar",
            "display_name": "Bar Chart",
            "description": "Vertical or horizontal bar chart",
            "suitable_for": ["comparisons", "rankings", "categorical_data"],
            "examples": ["Deals by Country", "Revenue by Product", "Leads by Source"]
        },
        {
            "type": "line",
            "display_name": "Line Chart",
            "description": "Time series line chart",
            "suitable_for": ["trends", "time_series", "performance_over_time"],
            "examples": ["Revenue Trend", "Deal Velocity", "Lead Generation Trend"]
        },
        {
            "type": "pie",
            "display_name": "Pie Chart",
            "description": "Circular chart for proportions",
            "suitable_for": ["composition", "percentages", "parts_of_whole"],
            "examples": ["Deal Status Distribution", "Lead Source Mix", "Market Share"]
        },
        {
            "type": "funnel",
            "display_name": "Funnel Chart",
            "description": "Staged conversion funnel",
            "suitable_for": ["pipelines", "conversions", "stages"],
            "examples": ["Sales Pipeline", "Lead Conversion Funnel", "Deal Stages"]
        },
        {
            "type": "gauge",
            "display_name": "Gauge",
            "description": "Gauge meter for performance metrics",
            "suitable_for": ["performance", "targets", "kpi"],
            "examples": ["Win Rate", "Utilization", "Goal Achievement"]
        },
        {
            "type": "table",
            "display_name": "Table",
            "description": "Data table with sorting and filtering",
            "suitable_for": ["detailed_data", "lists", "records"],
            "examples": ["Deal List", "Lead Details", "Transaction History"]
        }
    ]
    
    return {
        "visualization_types": visualization_types,
        "total_count": len(visualization_types),
        "categories": {
            "basic": ["number", "currency", "percentage"],
            "charts": ["bar", "line", "pie", "funnel"],
            "advanced": ["gauge", "table"]
        }
    }


@router.get("/refresh-status", summary="Get Data Refresh Status")
async def get_refresh_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get data refresh status for analytics
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Mock refresh status data
    refresh_status = [
        {
            "data_source": "deals",
            "last_refresh": datetime.utcnow().isoformat(),
            "status": "success",
            "records_processed": 1000,
            "next_refresh": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "refresh_frequency": "hourly"
        },
        {
            "data_source": "leads",
            "last_refresh": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
            "status": "success",
            "records_processed": 2500,
            "next_refresh": (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
            "refresh_frequency": "30_minutes"
        },
        {
            "data_source": "financial",
            "last_refresh": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "status": "success",
            "records_processed": 150,
            "next_refresh": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "refresh_frequency": "hourly"
        },
        {
            "data_source": "supplier_reliability",
            "last_refresh": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
            "status": "success",
            "records_processed": 50,
            "next_refresh": (datetime.utcnow() + timedelta(hours=6)).isoformat(),
            "refresh_frequency": "6_hours"
        }
    ]
    
    return {
        "refresh_status": refresh_status,
        "overall_status": "healthy",
        "last_check": datetime.utcnow().isoformat()
    }

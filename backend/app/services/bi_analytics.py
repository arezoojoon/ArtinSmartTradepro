"""
BI Analytics Service - Advanced Business Intelligence
Phase 6 Enhancement - Comprehensive analytics with custom dashboards and reporting
"""
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract
import pandas as pd
import numpy as np
from dataclasses import dataclass

from app.models.deal import Deal
from app.models.crm import CRMCompany
from app.models.billing import Wallet, Invoice
from app.models.hunter_phase4 import HunterLead
from app.models.phase5 import AssetArbitrageHistory
from app.models.tenant import Tenant


@dataclass
class MetricDefinition:
    """Metric definition for analytics"""
    name: str
    description: str
    calculation_type: str  # sum, avg, count, custom
    data_source: str
    filters: Optional[Dict[str, Any]] = None
    group_by: Optional[List[str]] = None


@dataclass
class DashboardWidget:
    """Dashboard widget definition"""
    id: str
    title: str
    widget_type: str  # chart, table, kpi, gauge
    metrics: List[str]
    visualization: str
    filters: Optional[Dict[str, Any]] = None
    refresh_interval: int = 300  # seconds


class BIAnalyticsService:
    """Service for business intelligence and analytics"""
    
    def __init__(self, db: Session):
        self.db = db
        self.metric_definitions = self._initialize_metric_definitions()
        self.dashboard_templates = self._initialize_dashboard_templates()
    
    def _initialize_metric_definitions(self) -> Dict[str, MetricDefinition]:
        """Initialize predefined metric definitions"""
        return {
            # Deal metrics
            "total_deals_value": MetricDefinition(
                name="Total Deals Value",
                description="Total value of all deals",
                calculation_type="sum",
                data_source="deals",
                filters={"status": ["identified", "matching", "validating", "negotiating"]}
            ),
            "deals_count": MetricDefinition(
                name="Number of Deals",
                description="Total number of deals",
                calculation_type="count",
                data_source="deals"
            ),
            "avg_deal_size": MetricDefinition(
                name="Average Deal Size",
                description="Average value per deal",
                calculation_type="avg",
                data_source="deals",
                filters={"total_value": {"gt": 0}}
            ),
            "deals_by_stage": MetricDefinition(
                name="Deals by Stage",
                description="Number of deals by pipeline stage",
                calculation_type="count",
                data_source="deals",
                group_by=["status"]
            ),
            "deals_by_country": MetricDefinition(
                name="Deals by Country",
                description="Deals grouped by destination country",
                calculation_type="count",
                data_source="deals",
                group_by=["destination_country"]
            ),
            
            # Lead metrics
            "total_leads": MetricDefinition(
                name="Total Leads",
                description="Total number of leads",
                calculation_type="count",
                data_source="leads"
            ),
            "qualified_leads": MetricDefinition(
                name="Qualified Leads",
                description="Number of qualified leads",
                calculation_type="count",
                data_source="leads",
                filters={"status": "qualified"}
            ),
            "lead_conversion_rate": MetricDefinition(
                name="Lead Conversion Rate",
                description="Percentage of leads converted to deals",
                calculation_type="custom",
                data_source="leads_deals"
            ),
            "leads_by_source": MetricDefinition(
                name="Leads by Source",
                description="Leads grouped by source",
                calculation_type="count",
                data_source="leads",
                group_by=["source"]
            ),
            
            # Financial metrics
            "revenue": MetricDefinition(
                name="Revenue",
                description="Total revenue from closed deals",
                calculation_type="sum",
                data_source="deals",
                filters={"status": "closed_won"}
            ),
            "profit_margin": MetricDefinition(
                name="Profit Margin",
                description="Average profit margin percentage",
                calculation_type="avg",
                data_source="deals",
                filters={"status": "closed_won", "realized_margin_pct": {"gt": 0}}
            ),
            "wallet_balance": MetricDefinition(
                name="Wallet Balance",
                description="Current wallet balance",
                calculation_type="sum",
                data_source="wallet"
            ),
            "outstanding_invoices": MetricDefinition(
                name="Outstanding Invoices",
                description="Total value of unpaid invoices",
                calculation_type="sum",
                data_source="invoices",
                filters={"status": "unpaid"}
            ),
            
            # Performance metrics
            "deal_velocity": MetricDefinition(
                name="Deal Velocity",
                description="Average time to close deals",
                calculation_type="avg",
                data_source="deals",
                filters={"status": "closed_won"}
            ),
            "win_rate": MetricDefinition(
                name="Win Rate",
                description="Percentage of deals won",
                calculation_type="custom",
                data_source="deals"
            ),
            "supplier_reliability": MetricDefinition(
                name="Supplier Reliability",
                description="Average supplier reliability score",
                calculation_type="avg",
                data_source="supplier_reliability"
            )
        }
    
    def _initialize_dashboard_templates(self) -> Dict[str, List[DashboardWidget]]:
        """Initialize predefined dashboard templates"""
        return {
            "executive_overview": [
                DashboardWidget(
                    id="total_revenue",
                    title="Total Revenue",
                    widget_type="kpi",
                    metrics=["revenue"],
                    visualization="number"
                ),
                DashboardWidget(
                    id="deals_pipeline",
                    title="Deals Pipeline",
                    widget_type="chart",
                    metrics=["deals_by_stage"],
                    visualization="funnel"
                ),
                DashboardWidget(
                    id="profit_trend",
                    title="Profit Trend",
                    widget_type="chart",
                    metrics=["profit_margin"],
                    visualization="line"
                ),
                DashboardWidget(
                    id="top_countries",
                    title="Top Markets",
                    widget_type="chart",
                    metrics=["deals_by_country"],
                    visualization="bar"
                )
            ],
            "sales_performance": [
                DashboardWidget(
                    id="total_deals",
                    title="Total Deals",
                    widget_type="kpi",
                    metrics=["deals_count"],
                    visualization="number"
                ),
                DashboardWidget(
                    id="avg_deal_size",
                    title="Average Deal Size",
                    widget_type="kpi",
                    metrics=["avg_deal_size"],
                    visualization="currency"
                ),
                DashboardWidget(
                    id="win_rate",
                    title="Win Rate",
                    widget_type="gauge",
                    metrics=["win_rate"],
                    visualization="percentage"
                ),
                DashboardWidget(
                    id="deal_velocity",
                    title="Deal Velocity",
                    widget_type="kpi",
                    metrics=["deal_velocity"],
                    visualization="days"
                )
            ],
            "lead_generation": [
                DashboardWidget(
                    id="total_leads",
                    title="Total Leads",
                    widget_type="kpi",
                    metrics=["total_leads"],
                    visualization="number"
                ),
                DashboardWidget(
                    id="qualified_leads",
                    title="Qualified Leads",
                    widget_type="kpi",
                    metrics=["qualified_leads"],
                    visualization="number"
                ),
                DashboardWidget(
                    id="conversion_rate",
                    title="Conversion Rate",
                    widget_type="gauge",
                    metrics=["lead_conversion_rate"],
                    visualization="percentage"
                ),
                DashboardWidget(
                    id="leads_by_source",
                    title="Leads by Source",
                    widget_type="chart",
                    metrics=["leads_by_source"],
                    visualization="pie"
                )
            ],
            "financial_overview": [
                DashboardWidget(
                    id="revenue",
                    title="Revenue",
                    widget_type="kpi",
                    metrics=["revenue"],
                    visualization="currency"
                ),
                DashboardWidget(
                    id="profit_margin",
                    title="Profit Margin",
                    widget_type="kpi",
                    metrics=["profit_margin"],
                    visualization="percentage"
                ),
                DashboardWidget(
                    id="wallet_balance",
                    title="Wallet Balance",
                    widget_type="kpi",
                    metrics=["wallet_balance"],
                    visualization="currency"
                ),
                DashboardWidget(
                    id="outstanding_invoices",
                    title="Outstanding Invoices",
                    widget_type="kpi",
                    metrics=["outstanding_invoices"],
                    visualization="currency"
                )
            ]
        }
    
    async def calculate_metric(
        self,
        metric_name: str,
        tenant_id: str,
        filters: Optional[Dict[str, Any]] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate a specific metric
        
        Args:
            metric_name: Name of the metric to calculate
            tenant_id: Tenant ID for filtering
            filters: Additional filters to apply
            date_range: Date range for filtering
        """
        metric_def = self.metric_definitions.get(metric_name)
        
        if not metric_def:
            raise ValueError(f"Metric '{metric_name}' not found")
        
        # Combine metric filters with provided filters
        combined_filters = {}
        if metric_def.filters:
            combined_filters.update(metric_def.filters)
        if filters:
            combined_filters.update(filters)
        
        # Calculate based on data source
        if metric_def.data_source == "deals":
            return await self._calculate_deals_metric(metric_def, tenant_id, combined_filters, date_range)
        elif metric_def.data_source == "leads":
            return await self._calculate_leads_metric(metric_def, tenant_id, combined_filters, date_range)
        elif metric_def.data_source == "leads_deals":
            return await self._calculate_leads_deals_metric(metric_def, tenant_id, combined_filters, date_range)
        elif metric_def.data_source == "wallet":
            return await self._calculate_wallet_metric(metric_def, tenant_id, combined_filters, date_range)
        elif metric_def.data_source == "invoices":
            return await self._calculate_invoices_metric(metric_def, tenant_id, combined_filters, date_range)
        elif metric_def.data_source == "supplier_reliability":
            return await self._calculate_supplier_reliability_metric(metric_def, tenant_id, combined_filters, date_range)
        else:
            raise ValueError(f"Unknown data source: {metric_def.data_source}")
    
    async def _calculate_deals_metric(
        self,
        metric_def: MetricDefinition,
        tenant_id: str,
        filters: Dict[str, Any],
        date_range: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Calculate deals-related metrics"""
        query = self.db.query(Deal).filter(Deal.tenant_id == tenant_id)
        
        # Apply date range filter
        if date_range:
            start_date = datetime.fromisoformat(date_range["start"])
            end_date = datetime.fromisoformat(date_range["end"])
            query = query.filter(Deal.created_at >= start_date, Deal.created_at <= end_date)
        
        # Apply filters
        if "status" in filters:
            query = query.filter(Deal.status.in_(filters["status"]))
        
        if "total_value" in filters:
            if "gt" in filters["total_value"]:
                query = query.filter(Deal.total_value > filters["total_value"]["gt"])
            if "lt" in filters["total_value"]:
                query = query.filter(Deal.total_value < filters["total_value"]["lt"])
        
        if "realized_margin_pct" in filters:
            if "gt" in filters["realized_margin_pct"]:
                query = query.filter(Deal.realized_margin_pct > filters["realized_margin_pct"]["gt"])
        
        # Calculate based on calculation type
        if metric_def.calculation_type == "sum":
            if metric_def.name == "Total Deals Value":
                result = query.with_entities(func.sum(Deal.total_value)).scalar() or 0
                return {"value": float(result), "unit": "currency"}
            else:
                result = query.count()
                return {"value": result, "unit": "count"}
        
        elif metric_def.calculation_type == "count":
            result = query.count()
            return {"value": result, "unit": "count"}
        
        elif metric_def.calculation_type == "avg":
            if metric_def.name == "Average Deal Size":
                result = query.with_entities(func.avg(Deal.total_value)).scalar() or 0
                return {"value": float(result), "unit": "currency"}
            elif metric_def.name == "Profit Margin":
                result = query.with_entities(func.avg(Deal.realized_margin_pct)).scalar() or 0
                return {"value": float(result), "unit": "percentage"}
            else:
                result = query.count()
                return {"value": result, "unit": "count"}
        
        elif metric_def.calculation_type == "custom":
            if metric_def.name == "Win Rate":
                total_deals = query.count()
                won_deals = query.filter(Deal.status == "closed_won").count()
                win_rate = (won_deals / total_deals * 100) if total_deals > 0 else 0
                return {"value": win_rate, "unit": "percentage"}
            else:
                result = query.count()
                return {"value": result, "unit": "count"}
        
        # Group by logic
        if metric_def.group_by:
            if "status" in metric_def.group_by:
                results = query.with_entities(Deal.status, func.count(Deal.id)).group_by(Deal.status).all()
                return {
                    "value": {status: count for status, count in results},
                    "unit": "count",
                    "grouped_by": "status"
                }
            elif "destination_country" in metric_def.group_by:
                results = query.with_entities(
                    Deal.destination_country, func.count(Deal.id)
                ).group_by(Deal.destination_country).all()
                return {
                    "value": {country: count for country, count in results if country},
                    "unit": "count",
                    "grouped_by": "destination_country"
                }
        
        # Default
        result = query.count()
        return {"value": result, "unit": "count"}
    
    async def _calculate_leads_metric(
        self,
        metric_def: MetricDefinition,
        tenant_id: str,
        filters: Dict[str, Any],
        date_range: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Calculate leads-related metrics"""
        query = self.db.query(HunterLead).filter(HunterLead.tenant_id == tenant_id)
        
        # Apply date range filter
        if date_range:
            start_date = datetime.fromisoformat(date_range["start"])
            end_date = datetime.fromisoformat(date_range["end"])
            query = query.filter(HunterLead.created_at >= start_date, HunterLead.created_at <= end_date)
        
        # Apply filters
        if "status" in filters:
            query = query.filter(HunterLead.status.in_(filters["status"]))
        
        # Calculate based on calculation type
        if metric_def.calculation_type == "count":
            result = query.count()
            return {"value": result, "unit": "count"}
        
        # Group by logic
        if metric_def.group_by and "source" in metric_def.group_by:
            # Mock source data - in real implementation, this would come from the lead source field
            results = [
                ("Hunter", query.count() // 3),
                ("Manual", query.count() // 4),
                ("Import", query.count() // 5),
                ("API", query.count() // 6)
            ]
            return {
                "value": {source: count for source, count in results},
                "unit": "count",
                "grouped_by": "source"
            }
        
        # Default
        result = query.count()
        return {"value": result, "unit": "count"}
    
    async def _calculate_leads_deals_metric(
        self,
        metric_def: MetricDefinition,
        tenant_id: str,
        filters: Dict[str, Any],
        date_range: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Calculate leads-to-deals conversion metrics"""
        # Get total leads
        leads_query = self.db.query(HunterLead).filter(HunterLead.tenant_id == tenant_id)
        if date_range:
            start_date = datetime.fromisoformat(date_range["start"])
            end_date = datetime.fromisoformat(date_range["end"])
            leads_query = leads_query.filter(HunterLead.created_at >= start_date, HunterLead.created_at <= end_date)
        
        total_leads = leads_query.count()
        
        # Get deals created from leads (mock calculation)
        deals_query = self.db.query(Deal).filter(Deal.tenant_id == tenant_id)
        if date_range:
            deals_query = deals_query.filter(Deal.created_at >= start_date, Deal.created_at <= end_date)
        
        deals_from_leads = deals_query.count() // 2  # Mock: assume 50% of deals come from leads
        
        # Calculate conversion rate
        conversion_rate = (deals_from_leads / total_leads * 100) if total_leads > 0 else 0
        
        return {"value": conversion_rate, "unit": "percentage"}
    
    async def _calculate_wallet_metric(
        self,
        metric_def: MetricDefinition,
        tenant_id: str,
        filters: Dict[str, Any],
        date_range: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Calculate wallet metrics"""
        query = self.db.query(Wallet).filter(Wallet.tenant_id == tenant_id)
        
        # Get wallet balance
        wallet = query.first()
        balance = wallet.balance if wallet else 0
        
        return {"value": float(balance), "unit": "currency"}
    
    async def _calculate_invoices_metric(
        self,
        metric_def: MetricDefinition,
        tenant_id: str,
        filters: Dict[str, Any],
        date_range: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Calculate invoice metrics"""
        query = self.db.query(Invoice).filter(Invoice.tenant_id == tenant_id)
        
        # Apply filters
        if "status" in filters:
            query = query.filter(Invoice.status.in_(filters["status"]))
        
        # Calculate based on calculation type
        if metric_def.calculation_type == "sum":
            result = query.with_entities(func.sum(Invoice.amount)).scalar() or 0
            return {"value": float(result), "unit": "currency"}
        
        # Default
        result = query.count()
        return {"value": result, "unit": "count"}
    
    async def _calculate_supplier_reliability_metric(
        self,
        metric_def: MetricDefinition,
        tenant_id: str,
        filters: Dict[str, Any],
        date_range: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Calculate supplier reliability metrics"""
        # Mock supplier reliability data
        # In real implementation, this would query AssetSupplierReliability table
        mock_reliability = 85.5  # Mock average reliability score
        
        return {"value": mock_reliability, "unit": "score"}
    
    async def generate_dashboard(
        self,
        dashboard_type: str,
        tenant_id: str,
        filters: Optional[Dict[str, Any]] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete dashboard
        
        Args:
            dashboard_type: Type of dashboard (executive_overview, sales_performance, etc.)
            tenant_id: Tenant ID
            filters: Filters to apply to all widgets
            date_range: Date range for all widgets
        """
        template = self.dashboard_templates.get(dashboard_type)
        
        if not template:
            raise ValueError(f"Dashboard template '{dashboard_type}' not found")
        
        dashboard_data = {
            "dashboard_type": dashboard_type,
            "generated_at": datetime.utcnow().isoformat(),
            "widgets": []
        }
        
        # Calculate each widget
        for widget in template:
            try:
                # Calculate primary metric
                primary_metric = widget.metrics[0]
                metric_data = await self.calculate_metric(
                    primary_metric,
                    tenant_id,
                    widget.filters,
                    date_range
                )
                
                widget_data = {
                    "id": widget.id,
                    "title": widget.title,
                    "widget_type": widget.widget_type,
                    "visualization": widget.visualization,
                    "data": metric_data,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
                # Add additional metrics if needed
                if len(widget.metrics) > 1:
                    widget_data["additional_metrics"] = {}
                    for metric_name in widget.metrics[1:]:
                        try:
                            additional_data = await self.calculate_metric(
                                metric_name,
                                tenant_id,
                                widget.filters,
                                date_range
                            )
                            widget_data["additional_metrics"][metric_name] = additional_data
                        except Exception as e:
                            widget_data["additional_metrics"][metric_name] = {"error": str(e)}
                
                dashboard_data["widgets"].append(widget_data)
                
            except Exception as e:
                # Add error widget
                dashboard_data["widgets"].append({
                    "id": widget.id,
                    "title": widget.title,
                    "widget_type": widget.widget_type,
                    "visualization": widget.visualization,
                    "data": {"error": str(e)},
                    "last_updated": datetime.utcnow().isoformat()
                })
        
        return dashboard_data
    
    async def generate_report(
        self,
        report_type: str,
        tenant_id: str,
        format_type: str = "json",
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report
        
        Args:
            report_type: Type of report (monthly, quarterly, annual)
            tenant_id: Tenant ID
            format_type: Output format (json, csv, pdf)
            date_range: Date range for the report
        """
        # Default date range if not provided
        if not date_range:
            end_date = datetime.utcnow()
            if report_type == "monthly":
                start_date = end_date.replace(day=1)
            elif report_type == "quarterly":
                quarter = (end_date.month - 1) // 3
                start_date = datetime(end_date.year, quarter * 3 + 1, 1)
            else:  # annual
                start_date = end_date.replace(month=1, day=1)
            
            date_range = {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        
        # Generate report data
        report_data = {
            "report_type": report_type,
            "tenant_id": tenant_id,
            "date_range": date_range,
            "generated_at": datetime.utcnow().isoformat(),
            "sections": {}
        }
        
        # Executive summary
        report_data["sections"]["executive_summary"] = await self._generate_executive_summary(tenant_id, date_range)
        
        # Sales performance
        report_data["sections"]["sales_performance"] = await self._generate_sales_performance_section(tenant_id, date_range)
        
        # Financial overview
        report_data["sections"]["financial_overview"] = await self._generate_financial_section(tenant_id, date_range)
        
        # Lead generation
        report_data["sections"]["lead_generation"] = await self._generate_lead_section(tenant_id, date_range)
        
        # Recommendations
        report_data["sections"]["recommendations"] = await self._generate_recommendations(tenant_id, date_range)
        
        return report_data
    
    async def _generate_executive_summary(self, tenant_id: str, date_range: Dict[str, str]) -> Dict[str, Any]:
        """Generate executive summary section"""
        # Get key metrics
        revenue = await self.calculate_metric("revenue", tenant_id, date_range=date_range)
        deals_count = await self.calculate_metric("deals_count", tenant_id, date_range=date_range)
        profit_margin = await self.calculate_metric("profit_margin", tenant_id, date_range=date_range)
        win_rate = await self.calculate_metric("win_rate", tenant_id, date_range=date_range)
        
        return {
            "key_metrics": {
                "revenue": revenue,
                "deals_count": deals_count,
                "profit_margin": profit_margin,
                "win_rate": win_rate
            },
            "highlights": [
                f"Generated ${revenue['value']:,.2f} in revenue",
                f"Closed {deals_count['value']} deals",
                f"Achieved {profit_margin['value']:.1f}% average profit margin",
                f"{win_rate['value']:.1f}% win rate"
            ]
        }
    
    async def _generate_sales_performance_section(self, tenant_id: str, date_range: Dict[str, str]) -> Dict[str, Any]:
        """Generate sales performance section"""
        deals_by_stage = await self.calculate_metric("deals_by_stage", tenant_id, date_range=date_range)
        avg_deal_size = await self.calculate_metric("avg_deal_size", tenant_id, date_range=date_range)
        deal_velocity = await self.calculate_metric("deal_velocity", tenant_id, date_range=date_range)
        
        return {
            "pipeline": deals_by_stage,
            "deal_metrics": {
                "avg_deal_size": avg_deal_size,
                "deal_velocity": deal_velocity
            }
        }
    
    async def _generate_financial_section(self, tenant_id: str, date_range: Dict[str, str]) -> Dict[str, Any]:
        """Generate financial section"""
        revenue = await self.calculate_metric("revenue", tenant_id, date_range=date_range)
        profit_margin = await self.calculate_metric("profit_margin", tenant_id, date_range=date_range)
        wallet_balance = await self.calculate_metric("wallet_balance", tenant_id)
        outstanding_invoices = await self.calculate_metric("outstanding_invoices", tenant_id)
        
        return {
            "financial_metrics": {
                "revenue": revenue,
                "profit_margin": profit_margin,
                "wallet_balance": wallet_balance,
                "outstanding_invoices": outstanding_invoices
            }
        }
    
    async def _generate_lead_section(self, tenant_id: str, date_range: Dict[str, str]) -> Dict[str, Any]:
        """Generate lead generation section"""
        total_leads = await self.calculate_metric("total_leads", tenant_id, date_range=date_range)
        qualified_leads = await self.calculate_metric("qualified_leads", tenant_id, date_range=date_range)
        conversion_rate = await self.calculate_metric("lead_conversion_rate", tenant_id, date_range=date_range)
        leads_by_source = await self.calculate_metric("leads_by_source", tenant_id, date_range=date_range)
        
        return {
            "lead_metrics": {
                "total_leads": total_leads,
                "qualified_leads": qualified_leads,
                "conversion_rate": conversion_rate,
                "leads_by_source": leads_by_source
            }
        }
    
    async def _generate_recommendations(self, tenant_id: str, date_range: Dict[str, str]) -> List[str]:
        """Generate recommendations based on metrics"""
        recommendations = []
        
        # Get key metrics for analysis
        win_rate = await self.calculate_metric("win_rate", tenant_id, date_range=date_range)
        profit_margin = await self.calculate_metric("profit_margin", tenant_id, date_range=date_range)
        conversion_rate = await self.calculate_metric("lead_conversion_rate", tenant_id, date_range=date_range)
        
        # Generate recommendations based on metrics
        if win_rate["value"] < 50:
            recommendations.append("Consider improving sales training and qualification process to increase win rate")
        
        if profit_margin["value"] < 15:
            recommendations.append("Review pricing strategy and cost structure to improve profit margins")
        
        if conversion_rate["value"] < 20:
            recommendations.append("Optimize lead nurturing process to improve conversion rates")
        
        if not recommendations:
            recommendations.append("Performance metrics are within target ranges - continue current strategy")
        
        return recommendations


# Helper function to get BI analytics service
def get_bi_analytics_service(db: Session) -> BIAnalyticsService:
    """Get BI analytics service instance"""
    return BIAnalyticsService(db)

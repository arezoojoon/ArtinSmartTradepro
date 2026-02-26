from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models.crm import CRMInvoice, CRMDeal, CRMPipeline
import datetime
from collections import defaultdict

class AnalyticsService:
    """
    Business Intelligence & KPIs.
    Calculates DSO, Conversion Rates, etc.
    """

    @staticmethod
    def get_kpis(db: Session, tenant_id):
        realized_dso = AnalyticsService.calculate_realized_dso(db, tenant_id)
        projected_dso = AnalyticsService.calculate_projected_dso(db, tenant_id)
        
        return {
            "dso_realized": realized_dso,
            "dso_projected": projected_dso,
            "conversion_rate": AnalyticsService.calculate_conversion_rate(db, tenant_id),
            "response_time_avg": 4.2 # Placeholder (hours)
        }

    @staticmethod
    def calculate_realized_dso(db: Session, tenant_id):
        """
        Realized DSO: Only for fully PAID invoices.
        Formula: Avg(Paid Date - Issued Date)
        """
        paid_invoices = db.query(CRMInvoice).filter(
            CRMInvoice.tenant_id == tenant_id,
            CRMInvoice.status == "paid",
            CRMInvoice.paid_date.isnot(None)
        ).all()

        if not paid_invoices:
            return 0

        total_days = 0
        for inv in paid_invoices:
            delta = (inv.paid_date - inv.issued_date).days
            total_days += max(0, delta)
            
        return round(total_days / len(paid_invoices), 1)

    @staticmethod
    def calculate_projected_dso(db: Session, tenant_id):
        """
        Projected DSO: For OPEN invoices.
        Formula: Avg(Due Date - Issued Date) or (Current Date - Issued Date)
        """
        open_invoices = db.query(CRMInvoice).filter(
            CRMInvoice.tenant_id == tenant_id,
            CRMInvoice.status == "open"
        ).all()
        
        if not open_invoices:
            return 0
            
        total_days = 0
        now = datetime.datetime.utcnow()
        for inv in open_invoices:
            # If due date passed, it's overdue duration
            # Standard simple projection: Time open so far
            delta = (now - inv.issued_date).days
            total_days += max(0, delta)
            
        return round(total_days / len(open_invoices), 1)

    @staticmethod
    def calculate_conversion_rate(db: Session, tenant_id):
        """
        Win Rate = Won / (Won + Lost)
        """
        won = db.query(func.count(CRMDeal.id)).filter(
            CRMDeal.tenant_id == tenant_id,
            CRMDeal.status == "won"
        ).scalar()
        
        lost = db.query(func.count(CRMDeal.id)).filter(
            CRMDeal.tenant_id == tenant_id,
            CRMDeal.status == "lost"
        ).scalar()
        
        total = won + lost
        if total == 0:
            return 0.0
            
        return round((won / total) * 100, 1)

    @staticmethod
    def get_monthly_performance(db: Session, tenant_id):
        """
        Monthly revenue vs target derived from real CRM deal data.
        Returns last 6 months of data.
        """
        months = []
        now = datetime.datetime.utcnow()
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        for i in range(5, -1, -1):
            d = now - datetime.timedelta(days=i * 30)
            month_idx = d.month
            year = d.year

            # Sum deal values closed (won) in this month
            revenue = db.query(func.coalesce(func.sum(CRMDeal.value), 0)).filter(
                CRMDeal.tenant_id == tenant_id,
                CRMDeal.status == "won",
                extract("month", CRMDeal.updated_at) == month_idx,
                extract("year", CRMDeal.updated_at) == year,
            ).scalar()

            # Sum paid invoices in this month
            invoice_rev = db.query(func.coalesce(func.sum(CRMInvoice.total_amount), 0)).filter(
                CRMInvoice.tenant_id == tenant_id,
                CRMInvoice.status == "paid",
                extract("month", CRMInvoice.paid_date) == month_idx,
                extract("year", CRMInvoice.paid_date) == year,
            ).scalar()

            total_revenue = float(revenue or 0) + float(invoice_rev or 0)

            # Target = simple growth model based on total pipeline
            total_pipeline = db.query(func.coalesce(func.sum(CRMDeal.value), 0)).filter(
                CRMDeal.tenant_id == tenant_id,
            ).scalar()
            target = float(total_pipeline or 0) / 6  # evenly spread

            months.append({
                "month": month_names[month_idx - 1],
                "revenue": round(total_revenue),
                "target": round(target),
            })

        return months

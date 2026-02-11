from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.crm import CRMInvoice, CRMDeal, CRMPipeline
import datetime

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

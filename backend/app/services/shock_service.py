from sqlalchemy.orm import Session
from app.models.toolbox import FXRateTick, FreightRate, MarketShockAlert
from app.models.user import User
import datetime
from sqlalchemy import func

class ShockService:
    """
    Market Shock Detection.
    Deterministic rules for alerting.
    """

    @staticmethod
    def check_fx_shocks(db: Session, tenant_id):
        """
        Rule: Alert if current rate deviates > 2% from 7-day Avg.
        """
        pairs = db.query(
            FXRateTick.base_currency, FXRateTick.quote_currency
        ).distinct().all()

        alerts = []
        now = datetime.datetime.utcnow()
        week_ago = now - datetime.timedelta(days=7)

        for base, quote in pairs:
            # Get latest
            latest = db.query(FXRateTick).filter(
                FXRateTick.base_currency == base,
                FXRateTick.quote_currency == quote
            ).order_by(FXRateTick.timestamp.desc()).first()

            if not latest:
                continue

            # Get 7d Avg
            avg_rate = db.query(func.avg(FXRateTick.rate)).filter(
                FXRateTick.base_currency == base,
                FXRateTick.quote_currency == quote,
                FXRateTick.timestamp >= week_ago
            ).scalar()

            if not avg_rate:
                continue

            # Check Delta
            avg = float(avg_rate)
            current = float(latest.rate)
            delta_pct = abs((current - avg) / avg) * 100

            if delta_pct > 2.0: # Threshold
                alert = MarketShockAlert(
                    tenant_id=tenant_id,
                    metric="fx_spike",
                    baseline=avg,
                    delta=delta_pct,
                    severity="high" if delta_pct > 5 else "medium",
                    message=f"FX Spike: {base}/{quote} moved {delta_pct:.1f}% (Curr: {current}, 7d Avg: {avg:.2f})"
                )
                db.add(alert)
                alerts.append(alert)
        
        db.commit()
        return alerts

    @staticmethod
    def check_freight_shocks(db: Session, tenant_id):
        """
        Rule: Alert if latest rate > 15% vs 30-day Median (approx via Avg for MVP).
        """
        # Logic similar to FX but query FreightRate
        # Left as stub for brevity in this step
        pass

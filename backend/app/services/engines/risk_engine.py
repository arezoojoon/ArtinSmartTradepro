"""
Risk Engine — Deterministic weighted scoring model.
NO LLM. Audit-safe.

Combines: political risk, FX volatility, buyer default probability,
supplier reliability, weather impact → composite Risk-Adjusted Margin.
"""
from app.integrations.fx_client import FXClient
from app.integrations.political_risk_client import PoliticalRiskClient
from app.integrations.weather_client import WeatherClient
from typing import Optional
import logging

logger = logging.getLogger(__name__)

fx = FXClient()
risk_client = PoliticalRiskClient()
weather = WeatherClient()

# Scoring weights
WEIGHTS = {
    "political": 0.25,
    "fx_volatility": 0.20,
    "buyer_default": 0.20,
    "weather": 0.15,
    "supplier": 0.10,
    "trade_openness": 0.10,
}


class RiskEngine:
    """
    Weighted composite risk scoring.
    Every factor is transparent and auditable.
    """

    @staticmethod
    async def assess(
        db,
        tenant_id,
        destination_country: str,
        origin_country: str,
        commodity: str,
        sell_currency: str = "USD",
        buyer_company_age: int = 5,
        supplier_reliability_override: Optional[float] = None,
    ) -> dict:
        """
        Composite risk assessment for a trade opportunity.
        Returns: risk score (0-1), individual factors, recommendation.
        Persists to RiskAssessment table.
        """
        from app.models.brain import RiskAssessment
        
        # 1. Political risk
        dest_risk = await risk_client.get_country_risk(destination_country)
        origin_risk = await risk_client.get_country_risk(origin_country)
        political_score = (dest_risk["risk_score"] * 0.7 + origin_risk["risk_score"] * 0.3)

        # 2. FX volatility
        fx_vol = await fx.get_volatility(sell_currency, "USD")

        # 3. Buyer default
        buyer_default = await risk_client.get_buyer_default_probability(
            destination_country, buyer_company_age
        )

        # 4. Weather impact
        weather_data = await weather.get_crop_impact(origin_country, commodity)
        weather_score = weather_data["risk_score"]

        # 5. Supplier reliability (from dataset or override)
        supplier_score = supplier_reliability_override if supplier_reliability_override is not None else 0.15

        # 6. Trade openness (inverse)
        trade_openness_risk = 1.0 - dest_risk["trade_openness_index"]

        # 7. Composite score
        composite = (
            political_score * WEIGHTS["political"]
            + fx_vol * WEIGHTS["fx_volatility"]
            + buyer_default * WEIGHTS["buyer_default"]
            + weather_score * WEIGHTS["weather"]
            + supplier_score * WEIGHTS["supplier"]
            + trade_openness_risk * WEIGHTS["trade_openness"]
        )
        composite = round(min(1.0, max(0.0, composite)), 3)

        # 8. Risk level
        if composite < 0.15:
            level = "LOW"
            color = "green"
        elif composite < 0.30:
            level = "MODERATE"
            color = "yellow"
        elif composite < 0.50:
            level = "ELEVATED"
            color = "orange"
        elif composite < 0.70:
            level = "HIGH"
            color = "red"
        else:
            level = "CRITICAL"
            color = "darkred"

        # 9. Sanctions check
        sanctions = await risk_client.get_sanctions_check(destination_country)

        # 10. Factors dict
        factors = {
            "political_risk": {"score": round(political_score, 3), "weight": WEIGHTS["political"]},
            "fx_volatility": {"score": round(fx_vol, 3), "weight": WEIGHTS["fx_volatility"]},
            "buyer_default": {"score": round(buyer_default, 3), "weight": WEIGHTS["buyer_default"]},
            "weather_impact": {"score": round(weather_score, 3), "weight": WEIGHTS["weather"], "event": weather_data["weather_event"]},
            "supplier_reliability": {"score": round(supplier_score, 3), "weight": WEIGHTS["supplier"]},
            "trade_openness": {"score": round(trade_openness_risk, 3), "weight": WEIGHTS["trade_openness"]},
        }

        result = {
            "destination": destination_country,
            "origin": origin_country,
            "commodity": commodity,

            "composite_risk_score": composite,
            "risk_level": level,
            "risk_color": color,

            "factors": factors,

            "sanctions": sanctions,
            "payment_terms": dest_risk["recommended_payment_terms"],
            "risk_adjusted_factor": round(1.0 - composite, 3),

            "alerts": RiskEngine._generate_alerts(composite, sanctions, weather_data, fx_vol),
        }

        # PERSISTENCE
        try:
            record = RiskAssessment(
                tenant_id=tenant_id,
                origin_country=origin_country,
                destination_country=destination_country,
                commodity=commodity,
                risk_score=int(composite * 100),
                risk_level=level,
                factors=factors
            )
            db.add(record)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save RiskAssessment: {e}")

        logger.info(f"Risk assessment: {origin_country}→{destination_country} composite={composite:.3f} level={level}")
        return result

    @staticmethod
    def _generate_alerts(composite: float, sanctions: dict, weather: dict, fx_vol: float) -> list:
        """Generate actionable risk alerts."""
        alerts = []
        if sanctions["sanctioned"]:
            alerts.append({"severity": "critical", "message": f"Country under sanctions by {', '.join(sanctions['sanction_bodies'])}"})
        if sanctions.get("license_required"):
            alerts.append({"severity": "warning", "message": "Export license required for this destination"})
        if weather.get("alert"):
            alerts.append({"severity": "warning", "message": weather["alert"]})
        if fx_vol > 0.5:
            alerts.append({"severity": "warning", "message": f"High currency volatility ({fx_vol:.0%}). Consider hedging."})
        if composite > 0.6:
            alerts.append({"severity": "critical", "message": "Overall risk exceeds acceptable threshold. Require prepayment."})
        return alerts

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

# Scoring weights (Phase 5 Strategic Intelligence)
WEIGHTS = {
    "sanctions": 0.25,      # Legal risk
    "usd_liquidity": 0.20,  # Financial trap risk
    "logistics": 0.15,      # Demurrage/Loss risk
    "political": 0.10,      # Macro risk
    "fx_volatility": 0.10,  # Margin erosion risk
    "supplier": 0.10,       # Supply chain failure
    "buyer_default": 0.10,  # Non-payment risk
}


class RiskEngine:
    """
    Risk Engine — Deterministic weighted scoring model (Phase 5).
    NO LLM. Audit-safe.
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
        buyer_id: str = None,
        supplier_id: str = None
    ) -> dict:
        """
        Assess comprehensive trade risk to calculate a Risk-Adjusted Margin impact.
        Returns a composite score and explicit explainability factors.
        """
        from app.models.brain import RiskAssessment
        logger.info(f"[RiskEngine] Running strategic assessment: {origin_country} -> {destination_country}")

        # 1. Political Risk & Sanctions Depth
        political_res = await risk_client.get_country_risk(destination_country)
        political_score = political_res["risk_score"] * 100
        sanctions_data = RiskEngine._check_sanctions_depth(destination_country)
        
        # 2. Financial & FX Risk (USD Liquidity)
        fx_vol_score = await fx.get_volatility(sell_currency, "USD") * 100
        usd_liquidity = RiskEngine._get_usd_liquidity(destination_country)
        
        # 3. Logistics Risk (Port & Lane Safety)
        logistics_risk = RiskEngine._get_logistics_risk(origin_country, destination_country)
        
        # 4. Entity Risk (Supplier/Buyer)
        supplier_reliability = supplier_reliability_override * 100 if supplier_reliability_override is not None else 85.0
        buyer_default_risk = await risk_client.get_buyer_default_probability(destination_country, buyer_company_age) * 100
        
        # Calculate Risk Score (0-100)
        composite_risk_score = (
            sanctions_data['score'] * WEIGHTS["sanctions"] +
            usd_liquidity['score'] * WEIGHTS["usd_liquidity"] +
            logistics_risk['score'] * WEIGHTS["logistics"] +
            political_score * WEIGHTS["political"] +
            fx_vol_score * WEIGHTS["fx_volatility"] +
            (100 - supplier_reliability) * WEIGHTS["supplier"] +
            buyer_default_risk * WEIGHTS["buyer_default"]
        )
        
        # Convert risk score to a margin discount penalty
        # Example: A score of 50 implies the trader should deduct 5.0% from their gross margin buffer
        margin_penalty_pct = composite_risk_score * 0.1 
        
        # Risk level determination
        if composite_risk_score < 15:
            level = "LOW"
            color = "green"
        elif composite_risk_score < 35:
            level = "MODERATE"
            color = "yellow"
        elif composite_risk_score < 55:
            level = "ELEVATED"
            color = "orange"
        elif composite_risk_score < 75:
            level = "HIGH"
            color = "red"
        else:
            level = "CRITICAL"
            color = "darkred"

        factors = {
            "logistics_risk": logistics_risk,
            "sanctions_depth": sanctions_data,
            "usd_liquidity": usd_liquidity,
            "political_risk_score": round(political_score, 2),
            "fx_volatility_score": round(fx_vol_score, 2),
            "buyer_default_probability": round(buyer_default_risk, 2),
            "supplier_reliability_score": round(supplier_reliability, 2)
        }

        result = {
            "composite_risk_score": round(composite_risk_score, 2),
            "risk_adjusted_margin_penalty_pct": round(margin_penalty_pct, 2),
            "risk_level": level,
            "risk_color": color,
            "factors": factors,
            "explainability": [
                f"Logistics Alert: {logistics_risk['reason']}",
                f"Sanctions Status: {sanctions_data['reason']}",
                f"Liquidity Insight: {usd_liquidity['reason']}"
            ],
            "alerts": RiskEngine._generate_alerts(composite_risk_score, sanctions_data, fx_vol_score)
        }

        # PERSISTENCE
        try:
            record = RiskAssessment(
                tenant_id=tenant_id,
                origin_country=origin_country,
                destination_country=destination_country,
                commodity=commodity,
                risk_score=int(composite_risk_score),
                risk_level=level,
                factors=factors
            )
            db.add(record)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save RiskAssessment: {e}")

        return result

    @staticmethod
    def _check_sanctions_depth(country: str) -> dict:
        """Granular check for primary vs. secondary sanctions risk."""
        high_risk = ['IR', 'RU', 'CU', 'KP', 'SY']
        med_risk = ['VE', 'BY', 'MM', 'SD']
        
        country_code = country.upper()
        if country_code in high_risk:
            return {"score": 95, "level": "High", "primary": True, "secondary": True, "reason": "Comprehensive primary and secondary sanctions detected. Severe compliance risk."}
        elif country_code in med_risk:
            return {"score": 60, "level": "Medium", "primary": False, "secondary": True, "reason": "Secondary sanctions or sector-specific restrictions apply. Enhanced Due Diligence required."}
        return {"score": 5, "level": "Low", "primary": False, "secondary": False, "reason": "No major sanctions lists match."}

    @staticmethod
    def _get_usd_liquidity(country: str) -> dict:
        """Liquidity risk scoring for fund repatriation (Access to USD)."""
        poor_liquidity = ['EG', 'NG', 'AR', 'PK', 'LB', 'ZW']
        med_liquidity = ['TR', 'KE', 'BD']
        
        country_code = country.upper()
        if country_code in poor_liquidity:
            return {"score": 85, "level": "Poor", "reason": "Severe USD shortage reported by central bank. Repatriation of funds highly delayed. Recommend TT advance only."}
        elif country_code in med_liquidity:
            return {"score": 45, "level": "Moderate", "reason": "Occasional FX liquidity crunches. LC confirmation by top-tier bank advised."}
        return {"score": 10, "level": "Good", "reason": "Normal central bank FX reserves. Standard swift transfers clear without delay."}

    @staticmethod
    def _get_logistics_risk(origin: str, destination: str) -> dict:
        """Port efficiency and shipping lane safety scores."""
        chokepoints = ['YE', 'SO', 'ER', 'DJ', 'SD'] # Red sea / Horn of Africa proxies
        congested_ports = ['ZA', 'NG', 'BD']
        
        dest_code = destination.upper()
        if dest_code in chokepoints or origin.upper() in chokepoints:
            return {"score": 90, "port_efficiency": 40, "lane_safety": 20, "reason": "High piracy/war risk in transit lane. War risk insurance premiums spiked."}
        elif dest_code in congested_ports:
             return {"score": 65, "port_efficiency": 30, "lane_safety": 85, "reason": "High risk of destination port congestion leading to demurrage costs."}
             
        return {"score": 20, "port_efficiency": 85, "lane_safety": 95, "reason": "Standard port processing times. Safe transit corridor."}

    @staticmethod
    def _generate_alerts(composite_score: float, sanctions: dict, fx_vol: float) -> list:
        """Generate actionable risk alerts."""
        alerts = []
        if sanctions["score"] > 80:
            alerts.append({"severity": "critical", "message": sanctions["reason"]})
        elif sanctions["score"] > 50:
            alerts.append({"severity": "warning", "message": sanctions["reason"]})
            
        if fx_vol > 50:
            alerts.append({"severity": "warning", "message": f"High currency volatility ({fx_vol:.0f}%). Consider hedging."})
            
        if composite_score > 60:
            alerts.append({"severity": "critical", "message": "Overall risk exceeds acceptable threshold. Require prepayment or LC."})
            
        return alerts

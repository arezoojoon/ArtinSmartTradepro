"""
Political Risk Client — Country risk assessment.
Interface-first: mock data now, swap to real API later.
Frequency: Monthly.
"""
from app.integrations import BaseIntegrationClient
from typing import Optional
import random


# Mock political risk index (0=safe, 1=high risk)
COUNTRY_RISK = {
    "CH": 0.05, "DE": 0.10, "US": 0.12, "JP": 0.08, "AU": 0.09,
    "NL": 0.07, "SE": 0.06, "CA": 0.10, "UK": 0.13, "FR": 0.14,
    "AE": 0.20, "SA": 0.25, "KR": 0.15, "SG": 0.08, "NZ": 0.07,
    "CN": 0.35, "IN": 0.30, "BR": 0.40, "MX": 0.38, "TR": 0.55,
    "RU": 0.70, "NG": 0.60, "PK": 0.55, "EG": 0.45, "IR": 0.80,
    "VE": 0.85, "ZW": 0.75, "MM": 0.78, "AF": 0.90, "SY": 0.92,
}


class PoliticalRiskClient(BaseIntegrationClient):
    """Country-level political and trade risk assessment."""

    provider_name = "political_risk"
    is_mock = True

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        if api_key:
            self.is_mock = False

    async def health_check(self) -> bool:
        self.log_request("health_check", {})
        return True

    async def get_country_risk(self, country_code: str) -> dict:
        """
        Get composite risk score for a country.
        Covers: political stability, trade policy, sanctions, currency controls.
        """
        base = COUNTRY_RISK.get(country_code.upper(), 0.30)
        variance = random.uniform(-0.03, 0.03)
        score = max(0.0, min(1.0, round(base + variance, 2)))

        # Risk level
        if score < 0.15:
            level = "low"
        elif score < 0.35:
            level = "moderate"
        elif score < 0.60:
            level = "elevated"
        else:
            level = "high"

        # Generate risk factors
        factors = []
        if score > 0.5:
            factors.append("Sanctions risk")
        if score > 0.3:
            factors.append("Currency control restrictions")
        if score > 0.4:
            factors.append("Trade policy volatility")
        if score > 0.6:
            factors.append("Payment default risk")
        if score > 0.7:
            factors.append("Force majeure exposure")

        result = {
            "country": country_code.upper(),
            "risk_score": score,
            "risk_level": level,
            "factors": factors,
            "trade_openness_index": round(1.0 - score * 0.7, 2),
            "payment_reliability": round(1.0 - score * 0.8, 2),
            "recommended_payment_terms": self._get_payment_terms(score),
        }

        self.log_request("get_country_risk", {"country_code": country_code})
        return result

    def _get_payment_terms(self, risk_score: float) -> str:
        """Recommend payment terms based on risk."""
        if risk_score < 0.15:
            return "Net 60 / Open Account"
        elif risk_score < 0.30:
            return "Net 30 / Documents against Payment"
        elif risk_score < 0.50:
            return "Letter of Credit (Confirmed)"
        elif risk_score < 0.70:
            return "Cash in Advance (50%+)"
        else:
            return "Full Prepayment Required"

    async def get_sanctions_check(self, country_code: str) -> dict:
        """Quick sanctions status check."""
        sanctioned = country_code.upper() in {"IR", "SY", "KP", "CU", "VE", "RU", "MM"}
        return {
            "country": country_code.upper(),
            "sanctioned": sanctioned,
            "sanction_bodies": ["OFAC", "EU", "UN"] if sanctioned else [],
            "trade_allowed": not sanctioned,
            "license_required": country_code.upper() in {"RU", "MM", "CU"},
        }

    async def get_buyer_default_probability(self, country_code: str, company_age_years: int = 5) -> float:
        """Estimated probability of buyer payment default."""
        base_risk = COUNTRY_RISK.get(country_code.upper(), 0.30)
        age_factor = max(0.5, 1.0 - (company_age_years * 0.05))  # Older = more reliable
        return round(base_risk * age_factor * random.uniform(0.8, 1.2), 3)

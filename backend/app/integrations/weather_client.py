"""
Weather Client — Weather impact data for commodity trade.
Interface-first: mock data now, swap to real API later.
Frequency: Daily.
"""
from app.integrations import BaseIntegrationClient
from typing import Optional
import random


class WeatherClient(BaseIntegrationClient):
    """Weather data for agricultural commodity impact analysis."""

    provider_name = "weather"
    is_mock = True

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        if api_key:
            self.is_mock = False

    async def health_check(self) -> bool:
        self.log_request("health_check", {})
        return True

    async def get_crop_impact(self, region: str, commodity: str) -> dict:
        """
        Weather impact on commodity production.
        Returns: risk score, expected yield impact, alerts.
        """
        # Mock weather impact scenarios
        scenarios = [
            {"event": "drought", "risk": 0.7, "yield_impact": -0.15, "alert": "Severe drought conditions in key growing area"},
            {"event": "flood", "risk": 0.5, "yield_impact": -0.10, "alert": "Flooding risk in production zone"},
            {"event": "normal", "risk": 0.1, "yield_impact": 0.0, "alert": None},
            {"event": "favorable", "risk": 0.05, "yield_impact": 0.08, "alert": None},
            {"event": "frost", "risk": 0.6, "yield_impact": -0.20, "alert": "Frost warning may impact harvest"},
        ]

        scenario = random.choice(scenarios)

        result = {
            "region": region,
            "commodity": commodity,
            "weather_event": scenario["event"],
            "risk_score": scenario["risk"],
            "expected_yield_impact": scenario["yield_impact"],
            "price_impact_estimate": round(scenario["yield_impact"] * -1.5, 3),  # Inverse yield→price
            "alert": scenario["alert"],
            "data_source": "mock" if self.is_mock else "weather_api"
        }

        self.log_request("get_crop_impact", {"region": region, "commodity": commodity})
        return result

    async def get_shipping_weather(self, route_origin: str, route_destination: str) -> dict:
        """Weather conditions affecting shipping routes."""
        conditions = random.choice(["clear", "moderate_seas", "storm_warning", "typhoon_alert"])
        delay_risk = {"clear": 0, "moderate_seas": 1, "storm_warning": 3, "typhoon_alert": 7}

        return {
            "route": f"{route_origin} → {route_destination}",
            "conditions": conditions,
            "delay_risk_days": delay_risk[conditions],
            "insurance_premium_modifier": 1.0 + (delay_risk[conditions] * 0.05),
        }

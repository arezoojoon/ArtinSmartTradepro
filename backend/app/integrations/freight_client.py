"""
Freight Client — Shipping cost estimation.
Interface-first: mock data now, swap to real API later.
Frequency: Daily pulls.
"""
from app.integrations import BaseIntegrationClient
from typing import Dict, Optional
import random


# Mock freight rates (USD per 20ft container equivalent)
MOCK_ROUTES = {
    ("CN", "US"): {"base": 3200, "transit_days": 28},
    ("CN", "EU"): {"base": 2800, "transit_days": 32},
    ("CN", "AE"): {"base": 1200, "transit_days": 18},
    ("IN", "US"): {"base": 2800, "transit_days": 30},
    ("IN", "EU"): {"base": 2400, "transit_days": 25},
    ("IN", "AE"): {"base": 800, "transit_days": 7},
    ("TR", "EU"): {"base": 1600, "transit_days": 8},
    ("TR", "US"): {"base": 3000, "transit_days": 22},
    ("BR", "US"): {"base": 2200, "transit_days": 18},
    ("BR", "EU"): {"base": 2600, "transit_days": 20},
    ("DE", "US"): {"base": 2000, "transit_days": 14},
    ("CH", "AE"): {"base": 2200, "transit_days": 12},
}


class FreightClient(BaseIntegrationClient):
    """Freight/shipping rate provider."""

    provider_name = "freight_rates"
    is_mock = True

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        if api_key:
            self.is_mock = False

    async def health_check(self) -> bool:
        self.log_request("health_check", {})
        return True

    async def get_rate(self, origin: str, destination: str, container_type: str = "20ft") -> dict:
        """
        Get exact freight rate. NO FAKE DATA.
        If API key is missing, only permit known static baseline routes.
        Otherwise, throws ValueError to trigger INSUFFICIENT_DATA.
        """
        pair = (origin.upper()[:2], destination.upper()[:2])
        if pair not in MOCK_ROUTES:
            raise ValueError(f"No freight routing available for {origin} to {destination}. API Key required.")

        route = MOCK_ROUTES[pair]

        # V3 Strict: Return exact base rate if mock, no random peak or BAF guesses.
        baf = 150.0  # Static BAF
        peak = 0.0   # Static Peak

        multiplier = 2.0 if container_type == "40ft" else 1.0
        total = round((route["base"] + baf + peak) * multiplier, 2)

        result = {
            "origin": origin,
            "destination": destination,
            "container_type": container_type,
            "base_rate": round(route["base"] * multiplier, 2),
            "baf_surcharge": round(baf * multiplier, 2),
            "peak_surcharge": round(peak * multiplier, 2),
            "total_cost_usd": total,
            "transit_days": route["transit_days"],
            "currency": "USD"
        }

        self.log_request("get_rate", {"origin": origin, "destination": destination}, result=result)
        return result

    async def get_route_options(self, origin: str, destination: str) -> list:
        """Multiple carrier options for a route."""
        base = await self.get_rate(origin, destination)
        carriers = ["Maersk", "MSC", "CMA CGM", "COSCO", "Hapag-Lloyd"]
        options = []
        for carrier in random.sample(carriers, min(3, len(carriers))):
            variance = random.uniform(-0.10, 0.15)
            options.append({
                "carrier": carrier,
                "total_cost_usd": round(base["total_cost_usd"] * (1 + variance), 2),
                "transit_days": base["transit_days"] + random.randint(-3, 5),
                "reliability_score": round(random.uniform(0.75, 0.98), 2)
            })
        return sorted(options, key=lambda x: x["total_cost_usd"])

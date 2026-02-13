"""
Freight Integration (Mock)
Provides freight rate estimates for shipping routes.
"""
import random
from typing import Dict, Any

class FreightClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.source_name = "Freightos (Mock)"

    async def get_rates(self, origin: str, destination: str, container_type: str = "40HC") -> Dict[str, Any]:
        """
        Mock fetches freight rates.
        """
        base_price = random.randint(1500, 8000)
        
        # Volatility factor
        trend = random.choice(["stable", "increasing", "decreasing"])
        
        return {
            "origin": origin,
            "destination": destination,
            "container": container_type,
            "price_usd": base_price,
            "transit_time_days": random.randint(15, 45),
            "trend": trend,
            "valid_until": "2026-12-31",
            "provider": "Maersk / MSC / CMA CGM (Mock)",
            "source": self.source_name
        }

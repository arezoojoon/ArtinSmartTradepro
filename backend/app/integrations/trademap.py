from .base import BaseIntegration
from typing import List, Dict, Any
import random
import datetime

class TradeMapClient(BaseIntegration):
    @property
    def provider_name(self) -> str:
        return "trademap"

    async def fetch_data(self, product_code: str = None, country: str = None) -> List[Dict[str, Any]]:
        # MOCK IMPLEMENTATION
        results = []
        countries = ["USA", "China", "Germany", "Japan", "Netherlands"]
        
        for partner in countries:
            if partner == country: continue
            
            results.append({
                "source": "trademap",
                "product_code": product_code or "TOTAL",
                "reporter": country or "World",
                "partner": partner,
                "import_value_usd": random.randint(1000000, 50000000),
                "export_value_usd": random.randint(1000000, 50000000),
                "growth_rate_pct": round(random.uniform(-5.0, 15.0), 2),
                "year": datetime.datetime.now().year - 1
            })
        return results

    async def health_check(self) -> bool:
        return True

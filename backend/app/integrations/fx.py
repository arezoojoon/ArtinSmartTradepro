from .base import BaseIntegration
from typing import List, Dict, Any
import random
import datetime

class RXClient(BaseIntegration):
    @property
    def provider_name(self) -> str:
        return "fx_rates"

    async def fetch_data(self, base_currency: str = "USD", target_currencies: List[str] = None) -> List[Dict[str, Any]]:
        if not target_currencies:
            target_currencies = ["EUR", "AED", "CNY", "INR", "RUB"]
        
        results = []
        base_rates = {
            "EUR": 0.92, "AED": 3.67, "CNY": 7.20, "INR": 83.00, "RUB": 90.00
        }
        
        for curr in target_currencies:
            rate = base_rates.get(curr, 1.0)
            # Add some volatility
            rate = rate * (1 + random.uniform(-0.01, 0.01))
            results.append({
                "source": "fx_mock",
                "base": base_currency,
                "target": curr,
                "rate": round(rate, 4),
                "timestamp": datetime.datetime.now().isoformat()
            })
        return results

    async def health_check(self) -> bool:
        return True

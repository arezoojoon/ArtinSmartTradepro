from .base import BaseIntegration
from typing import List, Dict, Any
import random
import datetime

class UNComtradeClient(BaseIntegration):
    @property
    def provider_name(self) -> str:
        return "un_comtrade"

    async def fetch_data(self, commodity_code: str = None, reporter: str = None, partner: str = None) -> List[Dict[str, Any]]:
        # MOCK IMPLEMENTATION
        # Generates sample trade flows
        results = []
        for _ in range(5):
            results.append({
                "source": "un_comtrade",
                "commodity_code": commodity_code or "100630",
                "reporter": reporter or random.choice(["China", "India", "USA", "Brazil"]),
                "partner": partner or random.choice(["UAE", "Saudi Arabia", "Germany", "Turkey"]),
                "trade_value_usd": random.randint(100000, 5000000),
                "net_weight_kg": random.randint(50000, 1000000),
                "year": datetime.datetime.now().year - random.randint(0, 2),
                "timestamp": datetime.datetime.now().isoformat()
            })
        return results

    async def health_check(self) -> bool:
        return True

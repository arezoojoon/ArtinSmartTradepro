from .base import BaseIntegration
from typing import List, Dict, Any
import random
import datetime

class PoliticalRiskClient(BaseIntegration):
    @property
    def provider_name(self) -> str:
        return "political_risk"

    async def fetch_data(self, country_code: str = None) -> List[Dict[str, Any]]:
        # MOCK IMPLEMENTATION
        # Returns stability index
        results = []
        score = random.randint(10, 100) # 100 is stable
        
        results.append({
            "source": "risk_api",
            "country": country_code or "Unknown",
            "stability_score": score,
            "corruption_index": random.randint(10, 90),
            "trade_embargo_risk": score < 40,
            "last_updated": datetime.datetime.now().isoformat()
        })
        return results

    async def health_check(self) -> bool:
        return True

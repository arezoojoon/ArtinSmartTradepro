from .base import BaseIntegration
from typing import List, Dict, Any
import random
import datetime

class WeatherClient(BaseIntegration):
    @property
    def provider_name(self) -> str:
        return "weather_risk"

    async def fetch_data(self, location: str = None, date_range: str = None) -> List[Dict[str, Any]]:
        # MOCK IMPLEMENTATION
        # Returns weather alerts relevant to trade (storms, droughts)
        results = []
        risks = ["Storm", "Drought", "Flood", "Clear"]
        
        results.append({
            "source": "weather_api",
            "location": location or "Indian Ocean",
            "condition": random.choice(risks),
            "severity": random.choice(["Low", "Medium", "High", "Critical"]),
            "impact_probability": round(random.uniform(0.1, 0.9), 2),
            "timestamp": datetime.datetime.now().isoformat()
        })
        return results

    async def health_check(self) -> bool:
        return True

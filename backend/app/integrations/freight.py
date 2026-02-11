from .base import BaseIntegration
from typing import List, Dict, Any
import random
import datetime

class FreightClient(BaseIntegration):
    @property
    def provider_name(self) -> str:
        return "freight_market"

    async def fetch_data(self, origin_port: str = None, dest_port: str = None) -> List[Dict[str, Any]]:
        # MOCK IMPLEMENTATION
        results = []
        origin = origin_port or "Shanghai"
        dest = dest_port or "Jebel Ali"
        
        results.append({
            "source": "freight_mock",
            "origin": origin,
            "destination": dest,
            "container_20ft_usd": random.randint(800, 2500),
            "container_40ft_usd": random.randint(1500, 4500),
            "transit_time_days": random.randint(15, 35),
            "valid_until": (datetime.datetime.now() + datetime.timedelta(days=7)).date().isoformat()
        })
        return results

    async def health_check(self) -> bool:
        return True

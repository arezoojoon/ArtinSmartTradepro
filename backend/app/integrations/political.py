"""
Political Risk Integration (Mock)
Provides political risk scores and sanctions data.
"""
import random
from typing import Dict, Any

class PoliticalRiskClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.source_name = "Global Risk Index (Mock)"

    async def get_risk_score(self, country: str) -> Dict[str, Any]:
        """
        Mock fetches political risk score (0-100, where 100 is stable).
        """
        # Roughly realistic assignments
        high_risk = ["Iran", "Russia", "Sudan", "Yemen"]
        medium_risk = ["Brazil", "Turkey", "South Africa", "India"]
        low_risk = ["UAE", "Germany", "USA", "Singapore", "Switzerland"]
        
        if country in high_risk:
            score = random.randint(20, 50)
            status = "High Risk"
        elif country in medium_risk:
            score = random.randint(50, 75)
            status = "Moderate Risk"
        else:
            score = random.randint(75, 95)
            status = "Stable"
            
        return {
            "country": country,
            "stability_score": score,
            "risk_level": status,
            "sanctions_active": True if country in high_risk else False,
            "last_updated": "2026-02-01",
            "source": self.source_name
        }

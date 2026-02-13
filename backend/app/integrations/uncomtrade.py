"""
UN Comtrade Integration (Mock)
Provides trade flow data (Import/Export volumes) by HS Code and Country.
"""
import random
from typing import List, Dict, Any
import datetime

class UNComtradeClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.source_name = "UN Comtrade (Mock)"

    async def get_trade_data(self, hs_code: str, reporting_area: str, partner_area: str = "World") -> List[Dict[str, Any]]:
        """
        Mock fetches trade data.
        """
        # Simulate API delay
        # await asyncio.sleep(0.5)
        
        current_year = datetime.datetime.now().year
        data = []
        
        # Generate last 5 years of data
        for i in range(5):
            year = current_year - 1 - i
            import_value = random.uniform(1000000, 50000000)
            export_value = random.uniform(500000, 20000000)
            
            data.append({
                "year": year,
                "hs_code": hs_code,
                "reporter": reporting_area,
                "partner": partner_area,
                "import_value_usd": round(import_value, 2),
                "export_value_usd": round(export_value, 2),
                "net_trade_usd": round(export_value - import_value, 2),
                "source": self.source_name
            })
            
        return data

    async def get_top_importers(self, hs_code: str) -> List[Dict[str, Any]]:
        """
        Returns top importing countries for an HS code.
        """
        countries = ["China", "USA", "Germany", "India", "UAE", "Saudi Arabia", "France", "Brazil"]
        results = []
        for country in random.sample(countries, 5):
            results.append({
                "country": country,
                "hs_code": hs_code,
                "import_volume_usd": round(random.uniform(10_000_000, 500_000_000), 2),
                "growth_pct": round(random.uniform(-5.0, 15.0), 2)
            })
        return sorted(results, key=lambda x: x["import_volume_usd"], reverse=True)

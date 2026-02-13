"""
TradeMap Integration (Mock)
Provides detailed company-level trade signals and market access info.
"""
import random
from typing import List, Dict, Any

class TradeMapClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.source_name = "TradeMap (Mock)"

    async def get_companies(self, product_keyword: str, country: str = "Global") -> List[Dict[str, Any]]:
        """
        Mock fetches trading companies (Importers/Exporters).
        """
        roles = ["importer", "exporter", "distributor"]
        companies = []
        
        base_names = ["Global", "Inter", "Trans", "Pacific", "Euro", "Asia", "Middle East"]
        suffixes = ["Trade", "Logistics", "Foods", "Industries", "Holdings", "Group"]
        
        for _ in range(random.randint(5, 12)):
            name = f"{random.choice(base_names)} {random.choice(suffixes)} {random.choice(['Ltd', 'Inc', 'GmbH', 'LLC'])}"
            role = random.choice(roles)
            
            companies.append({
                "name": name,
                "country": country if country != "Global" else random.choice(["USA", "UAE", "Germany", "China"]),
                "role": role,
                "product_focus": product_keyword,
                "website": f"www.{name.lower().replace(' ', '')}.com",
                "estimated_revenue": f"${random.randint(1, 100)}M",
                "source": self.source_name
            })
            
        return companies

    async def get_barriers(self, country: str, hs_code: str) -> List[Dict[str, Any]]:
        """
        Mock fetches tariffs and non-tariff barriers.
        """
        return [
            {
                "country": country,
                "hs_code": hs_code,
                "tariff_rate": f"{random.uniform(0, 15):.1f}%",
                "agreement": "MFN",
                "regulations": ["Health Cert Required", "Origin Cert Required"] if random.random() > 0.5 else []
            }
        ]

"""
UN Comtrade Client — International trade data.
Interface-first: mock data now, swap to real API later.
Frequency: Weekly.
"""
from app.integrations import BaseIntegrationClient
from typing import Optional, List, Dict
import random


# Mock trade data (realistic HS codes and volumes)
MOCK_TRADE_DATA = {
    "1806": {  # Chocolate
        "name": "Chocolate & cocoa preparations",
        "top_exporters": [
            {"country": "DE", "value_usd": 5.8e9, "share": 15.2},
            {"country": "BE", "value_usd": 4.2e9, "share": 11.0},
            {"country": "NL", "value_usd": 3.9e9, "share": 10.2},
            {"country": "IT", "value_usd": 3.1e9, "share": 8.1},
            {"country": "PL", "value_usd": 2.3e9, "share": 6.0},
        ],
        "top_importers": [
            {"country": "US", "value_usd": 4.1e9, "share": 12.8},
            {"country": "DE", "value_usd": 3.2e9, "share": 10.0},
            {"country": "FR", "value_usd": 2.8e9, "share": 8.7},
            {"country": "UK", "value_usd": 2.6e9, "share": 8.1},
            {"country": "JP", "value_usd": 1.9e9, "share": 5.9},
        ],
        "avg_unit_value": 4.50,  # USD/kg
    },
    "2106": {  # Food preparations
        "name": "Food preparations NES",
        "top_exporters": [
            {"country": "DE", "value_usd": 4.2e9, "share": 12.1},
            {"country": "US", "value_usd": 3.8e9, "share": 10.9},
            {"country": "NL", "value_usd": 3.3e9, "share": 9.5},
            {"country": "IE", "value_usd": 2.8e9, "share": 8.0},
            {"country": "CH", "value_usd": 2.1e9, "share": 6.0},
        ],
        "top_importers": [
            {"country": "US", "value_usd": 5.2e9, "share": 14.8},
            {"country": "JP", "value_usd": 3.1e9, "share": 8.8},
            {"country": "DE", "value_usd": 2.7e9, "share": 7.7},
            {"country": "UK", "value_usd": 2.4e9, "share": 6.8},
            {"country": "CN", "value_usd": 2.0e9, "share": 5.7},
        ],
        "avg_unit_value": 3.20,
    },
    "0901": {  # Coffee
        "name": "Coffee",
        "top_exporters": [
            {"country": "BR", "value_usd": 7.8e9, "share": 22.5},
            {"country": "VN", "value_usd": 4.1e9, "share": 11.8},
            {"country": "CO", "value_usd": 3.2e9, "share": 9.2},
            {"country": "ET", "value_usd": 1.5e9, "share": 4.3},
            {"country": "HN", "value_usd": 1.3e9, "share": 3.7},
        ],
        "top_importers": [
            {"country": "US", "value_usd": 7.2e9, "share": 20.7},
            {"country": "DE", "value_usd": 4.8e9, "share": 13.8},
            {"country": "FR", "value_usd": 2.9e9, "share": 8.3},
            {"country": "IT", "value_usd": 2.6e9, "share": 7.5},
            {"country": "JP", "value_usd": 2.1e9, "share": 6.0},
        ],
        "avg_unit_value": 5.10,
    },
}


class UNComtradeClient(BaseIntegrationClient):
    """UN Comtrade international trade data provider."""

    provider_name = "un_comtrade"
    is_mock = True

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        if api_key:
            self.is_mock = False

    async def health_check(self) -> bool:
        self.log_request("health_check", {})
        return True

    async def get_trade_flows(self, hs_code: str) -> dict:
        """
        Get trade flow data for a product (HS code).
        Returns: top exporters, importers, volumes, unit values.
        """
        data = MOCK_TRADE_DATA.get(hs_code[:4])

        if not data:
            # Generate generic data for unknown codes
            data = {
                "name": f"Product HS {hs_code}",
                "top_exporters": [
                    {"country": c, "value_usd": random.uniform(1e9, 5e9), "share": random.uniform(5, 15)}
                    for c in ["CN", "DE", "US", "NL", "IT"]
                ],
                "top_importers": [
                    {"country": c, "value_usd": random.uniform(1e9, 5e9), "share": random.uniform(5, 15)}
                    for c in ["US", "DE", "JP", "UK", "FR"]
                ],
                "avg_unit_value": random.uniform(2.0, 10.0),
            }

        self.log_request("get_trade_flows", {"hs_code": hs_code})
        return data

    async def get_bilateral_trade(self, exporter: str, importer: str, hs_code: str) -> dict:
        """Get bilateral trade value between two countries for a product."""
        base_value = random.uniform(5e7, 2e9)
        growth_rate = random.uniform(-0.05, 0.15)

        result = {
            "exporter": exporter,
            "importer": importer,
            "hs_code": hs_code,
            "trade_value_usd": round(base_value, 2),
            "yoy_growth": round(growth_rate, 3),
            "quantity_tons": round(base_value / random.uniform(3, 8), 0),
        }

        self.log_request("get_bilateral_trade", {"exporter": exporter, "importer": importer, "hs_code": hs_code})
        return result

    async def get_tariff_rate(self, exporter: str, importer: str, hs_code: str) -> dict:
        """Estimated tariff rate for a trade lane."""
        # Mock tariff rates by importer
        base_tariffs = {
            "US": 5.0, "EU": 8.0, "CN": 12.0, "IN": 15.0,
            "AE": 5.0, "JP": 6.5, "BR": 14.0, "RU": 10.0,
        }
        base = base_tariffs.get(importer.upper(), 8.0)
        applied = round(base + random.uniform(-2, 3), 1)

        return {
            "hs_code": hs_code,
            "exporter": exporter,
            "importer": importer,
            "mfn_rate": round(base, 1),
            "applied_rate": max(0, applied),
            "preferential_available": random.choice([True, False]),
        }

"""
FX Client — Foreign Exchange Rates.
Interface-first: mock data now, swap to real API later.
Frequency: Every 10 minutes (real-time).
"""
from app.integrations import BaseIntegrationClient
from typing import Dict, Optional
import random
import datetime


# Mock rates (realistic baselines)
MOCK_RATES = {
    ("USD", "EUR"): 0.92, ("USD", "GBP"): 0.79, ("USD", "AED"): 3.67,
    ("USD", "CNY"): 7.24, ("USD", "INR"): 83.12, ("USD", "JPY"): 149.5,
    ("USD", "CHF"): 0.88, ("USD", "RUB"): 92.5, ("USD", "TRY"): 30.8,
    ("USD", "IRR"): 42000.0, ("EUR", "USD"): 1.09, ("EUR", "GBP"): 0.86,
    ("GBP", "USD"): 1.27, ("AED", "USD"): 0.27, ("CNY", "USD"): 0.14,
}


class FXClient(BaseIntegrationClient):
    """Foreign exchange rate provider."""

    provider_name = "fx_rates"
    is_mock = True

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        if api_key:
            self.is_mock = False

    async def health_check(self) -> bool:
        self.log_request("health_check", {})
        return True

    async def get_rate(self, base: str, quote: str) -> float:
        """
        Get exact exchange rate. NO FAKE DATA.
        If API key is missing, only permit known static baseline pairs.
        Otherwise, throws ValueError to trigger INSUFFICIENT_DATA.
        """
        pair = (base.upper(), quote.upper())
        if self.is_mock:
            if pair in MOCK_RATES:
                # V3 Strict: return exact dictionary value. No random variance.
                rate = MOCK_RATES[pair]
                self.log_request("get_rate", {"base": base, "quote": quote}, result=rate)
                return rate
            else:
                # V3 Strict: Do not guess. Force Insufficient Data.
                raise ValueError(f"No FX data available for pair {base}/{quote}. API Key required.")

        # TODO: Real API implementation
        raise NotImplementedError("Real FX API not configured")

    async def get_historical_rates(self, base: str, quote: str, days: int = 30) -> list:
        """Historical daily rates for trend analysis."""
        pair = (base.upper(), quote.upper())
        base_rate = MOCK_RATES.get(pair, 1.0)

        rates = []
        for i in range(days, 0, -1):
            date = datetime.date.today() - datetime.timedelta(days=i)
            drift = base_rate * random.uniform(-0.02, 0.02)
            rates.append({
                "date": date.isoformat(),
                "rate": round(base_rate + drift, 4)
            })

        self.log_request("get_historical_rates", {"base": base, "quote": quote, "days": days})
        return rates

    async def get_volatility(self, base: str, quote: str) -> float:
        """30-day volatility score (0.0 = stable, 1.0 = highly volatile)."""
        volatile_pairs = {("USD", "TRY"), ("USD", "IRR"), ("USD", "RUB")}
        pair = (base.upper(), quote.upper())

        if pair in volatile_pairs:
            return round(random.uniform(0.6, 0.9), 2)
        return round(random.uniform(0.05, 0.25), 2)

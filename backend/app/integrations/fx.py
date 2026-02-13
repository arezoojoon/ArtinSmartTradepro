"""
FX Integration (Mock)
Provides live currency exchange rates and historical volatility.
"""
import random
from typing import Dict, Any

class FXClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.source_name = "Bloomberg FX (Mock)"

    async def get_rate(self, base: str, quote: str) -> Dict[str, Any]:
        """
        Mock fetches FX rate.
        """
        # Realistic mock rates
        rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "AED": 3.67,
            "CNY": 7.15,
            "INR": 83.5,
            "SAR": 3.75,
            "IRR": 42000.0, # Official (mock)
        }
        
        base_val = rates.get(base, 1.0)
        quote_val = rates.get(quote, 1.0)
        
        rate = quote_val / base_val
        
        # Add some random noise
        rate = rate * random.uniform(0.99, 1.01)
        
        return {
            "base": base,
            "quote": quote,
            "rate": round(rate, 4),
            "timestamp": "Now",
            "change_24h": round(random.uniform(-0.5, 0.5), 2),
            "volatility": "Low" if abs(random.uniform(-1, 1)) < 0.5 else "High",
            "source": self.source_name
        }

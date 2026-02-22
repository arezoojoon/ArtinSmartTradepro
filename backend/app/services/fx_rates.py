"""
FX Rates Service - Real-time Currency Exchange Rates
Phase 6 Enhancement - Live FX data with hedging recommendations and volatility analysis
"""
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import aiohttp
import pandas as pd
from dataclasses import dataclass
import numpy as np

from app.models.phase5 import AssetSeasonalityMatrix
from app.models.tenant import Tenant
from app.config import get_settings


@dataclass
class FXRate:
    """FX rate information"""
    base_currency: str
    quote_currency: str
    rate: float
    timestamp: datetime
    source: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    change_24h: Optional[float] = None
    change_pct_24h: Optional[float] = None


@dataclass
class VolatilityAnalysis:
    """Volatility analysis results"""
    currency_pair: str
    volatility_30d: float
    volatility_90d: float
    volatility_1y: float
    trend: str  # increasing, decreasing, stable
    risk_level: str  # low, medium, high
    recommended_hedge: bool


@dataclass
class HedgeRecommendation:
    """Hedging recommendation"""
    currency_pair: str
    hedge_type: str  # forward, option, swap
    hedge_percentage: float
    reasoning: str
    estimated_cost: float
    risk_reduction: float
    timeframe: str


class FXRatesService:
    """Service for accessing and analyzing FX rates"""
    
    def __init__(self, db: Session):
        self.db = db
        self.api_key = get_settings().FX_API_KEY
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        self.cache_duration = timedelta(minutes=15)  # Cache for 15 minutes
        
        # Mock data for demonstration
        self.mock_rates = self._generate_mock_rates()
        self.mock_volatility = self._generate_mock_volatility()
    
    def _generate_mock_rates(self) -> Dict[str, FXRate]:
        """Generate mock FX rates data"""
        base_rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 149.50,
            "CNY": 7.24,
            "CAD": 1.36,
            "AUD": 1.53,
            "CHF": 0.88,
            "HKD": 7.83,
            "SGD": 1.34,
            "KRW": 1320.0,
            "INR": 83.12,
            "MXN": 17.15,
            "BRL": 4.92,
            "RUB": 89.50,
            "ZAR": 18.75,
            "THB": 36.25,
            "MYR": 4.72,
            "IDR": 15625.0,
            "PHP": 56.50
        }
        
        rates = {}
        timestamp = datetime.utcnow()
        
        for base, base_value in base_rates.items():
            for quote, quote_value in base_rates.items():
                if base != quote:
                    rate = quote_value / base_value
                    change_24h = np.random.uniform(-0.02, 0.02)  # Random daily change
                    change_pct_24h = change_24h * 100
                    
                    rates[f"{base}-{quote}"] = FXRate(
                        base_currency=base,
                        quote_currency=quote,
                        rate=rate,
                        timestamp=timestamp,
                        source="Mock FX API",
                        bid=rate * 0.999,
                        ask=rate * 1.001,
                        high_24h=rate * (1 + abs(change_24h)),
                        low_24h=rate * (1 - abs(change_24h)),
                        change_24h=change_24h,
                        change_pct_24h=change_pct_24h
                    )
        
        return rates
    
    def _generate_mock_volatility(self) -> Dict[str, VolatilityAnalysis]:
        """Generate mock volatility data"""
        volatility_data = {}
        
        # Generate volatility for major currency pairs
        major_pairs = ["USD-EUR", "USD-GBP", "USD-JPY", "USD-CNY", "EUR-GBP", "EUR-JPY", "GBP-JPY"]
        
        for pair in major_pairs:
            volatility_30d = np.random.uniform(0.05, 0.15)  # 5-15% monthly volatility
            volatility_90d = np.random.uniform(0.08, 0.20)  # 8-20% quarterly volatility
            volatility_1y = np.random.uniform(0.10, 0.25)   # 10-25% annual volatility
            
            # Determine trend
            trend = np.random.choice(["increasing", "decreasing", "stable"], p=[0.3, 0.3, 0.4])
            
            # Determine risk level
            if volatility_1y < 0.12:
                risk_level = "low"
            elif volatility_1y < 0.20:
                risk_level = "medium"
            else:
                risk_level = "high"
            
            # Recommend hedging for high volatility pairs
            recommended_hedge = risk_level in ["medium", "high"]
            
            volatility_data[pair] = VolatilityAnalysis(
                currency_pair=pair,
                volatility_30d=volatility_30d,
                volatility_90d=volatility_90d,
                volatility_1y=volatility_1y,
                trend=trend,
                risk_level=risk_level,
                recommended_hedge=recommended_hedge
            )
        
        return volatility_data
    
    async def get_fx_rate(
        self,
        base_currency: str,
        quote_currency: str,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get current FX rate for a currency pair
        
        Args:
            base_currency: Base currency code (e.g., 'USD', 'EUR')
            quote_currency: Quote currency code (e.g., 'EUR', 'JPY')
            amount: Optional amount to convert
        """
        pair_key = f"{base_currency}-{quote_currency}"
        
        # Get rate from mock data
        fx_rate = self.mock_rates.get(pair_key)
        
        if not fx_rate:
            raise ValueError(f"FX rate not available for {base_currency}-{quote_currency}")
        
        # Calculate converted amount if provided
        converted_amount = None
        if amount:
            converted_amount = amount * fx_rate.rate
        
        return {
            "base_currency": base_currency,
            "quote_currency": quote_currency,
            "rate": fx_rate.rate,
            "bid": fx_rate.bid,
            "ask": fx_rate.ask,
            "timestamp": fx_rate.timestamp.isoformat(),
            "source": fx_rate.source,
            "high_24h": fx_rate.high_24h,
            "low_24h": fx_rate.low_24h,
            "change_24h": fx_rate.change_24h,
            "change_pct_24h": fx_rate.change_pct_24h,
            "converted_amount": converted_amount,
            "amount": amount
        }
    
    async def get_multiple_rates(
        self,
        base_currency: str,
        quote_currencies: List[str]
    ) -> Dict[str, Any]:
        """
        Get FX rates for multiple quote currencies
        
        Args:
            base_currency: Base currency code
            quote_currencies: List of quote currency codes
        """
        rates = {}
        
        for quote_currency in quote_currencies:
            try:
                rate_data = await self.get_fx_rate(base_currency, quote_currency)
                rates[quote_currency] = {
                    "rate": rate_data["rate"],
                    "change_pct_24h": rate_data["change_pct_24h"],
                    "timestamp": rate_data["timestamp"]
                }
            except Exception as e:
                rates[quote_currency] = {"error": str(e)}
        
        return {
            "base_currency": base_currency,
            "rates": rates,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def analyze_volatility(
        self,
        base_currency: str,
        quote_currency: str,
        period_days: int = 30
    ) -> VolatilityAnalysis:
        """
        Analyze volatility for a currency pair
        
        Args:
            base_currency: Base currency code
            quote_currency: Quote currency code
            period_days: Analysis period in days
        """
        pair_key = f"{base_currency}-{quote_currency}"
        
        # Get volatility data
        volatility = self.mock_volatility.get(pair_key)
        
        if not volatility:
            # Generate volatility for unknown pairs
            volatility_30d = np.random.uniform(0.05, 0.15)
            volatility_90d = np.random.uniform(0.08, 0.20)
            volatility_1y = np.random.uniform(0.10, 0.25)
            
            trend = np.random.choice(["increasing", "decreasing", "stable"], p=[0.3, 0.3, 0.4])
            risk_level = "medium" if volatility_1y < 0.20 else "high"
            recommended_hedge = risk_level in ["medium", "high"]
            
            volatility = VolatilityAnalysis(
                currency_pair=pair_key,
                volatility_30d=volatility_30d,
                volatility_90d=volatility_90d,
                volatility_1y=volatility_1y,
                trend=trend,
                risk_level=risk_level,
                recommended_hedge=recommended_hedge
            )
        
        return volatility
    
    async def get_hedge_recommendations(
        self,
        base_currency: str,
        quote_currency: str,
        exposure_amount: float,
        timeframe_months: int = 3
    ) -> List[HedgeRecommendation]:
        """
        Get hedging recommendations for currency exposure
        
        Args:
            base_currency: Base currency code
            quote_currency: Quote currency code
            exposure_amount: Amount of currency exposure
            timeframe_months: Hedging timeframe in months
        """
        pair_key = f"{base_currency}-{quote_currency}"
        
        # Get volatility analysis
        volatility = await self.analyze_volatility(base_currency, quote_currency)
        
        recommendations = []
        
        # Get current rate
        rate_data = await self.get_fx_rate(base_currency, quote_currency)
        current_rate = rate_data["rate"]
        
        # Generate recommendations based on risk level
        if volatility.risk_level == "high":
            # High volatility - recommend multiple hedging strategies
            recommendations.append(HedgeRecommendation(
                currency_pair=pair_key,
                hedge_type="forward",
                hedge_percentage=0.75,
                reasoning="High volatility justifies significant forward contract protection",
                estimated_cost=exposure_amount * 0.02,  # 2% cost
                risk_reduction=0.85,
                timeframe=f"{timeframe_months} months"
            ))
            
            recommendations.append(HedgeRecommendation(
                currency_pair=pair_key,
                hedge_type="option",
                hedge_percentage=0.25,
                reasoning="Options provide flexibility while limiting downside",
                estimated_cost=exposure_amount * 0.03,  # 3% premium
                risk_reduction=0.70,
                timeframe=f"{timeframe_months} months"
            ))
            
        elif volatility.risk_level == "medium":
            # Medium volatility - recommend moderate hedging
            recommendations.append(HedgeRecommendation(
                currency_pair=pair_key,
                hedge_type="forward",
                hedge_percentage=0.50,
                reasoning="Moderate volatility suggests partial hedging",
                estimated_cost=exposure_amount * 0.015,  # 1.5% cost
                risk_reduction=0.60,
                timeframe=f"{timeframe_months} months"
            ))
            
        else:
            # Low volatility - minimal hedging needed
            recommendations.append(HedgeRecommendation(
                currency_pair=pair_key,
                hedge_type="forward",
                hedge_percentage=0.25,
                reasoning="Low volatility - minimal hedging recommended",
                estimated_cost=exposure_amount * 0.01,  # 1% cost
                risk_reduction=0.40,
                timeframe=f"{timeframe_months} months"
            ))
        
        return recommendations
    
    async def get_historical_rates(
        self,
        base_currency: str,
        quote_currency: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get historical FX rates for a period
        
        Args:
            base_currency: Base currency code
            quote_currency: Quote currency code
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        # Parse dates
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Generate mock historical data
        current_rate = self.mock_rates.get(f"{base_currency}-{quote_currency}")
        
        if not current_rate:
            raise ValueError(f"FX rate not available for {base_currency}-{quote_currency}")
        
        historical_data = []
        current_date = start_dt
        
        while current_date <= end_dt:
            # Generate rate with some random variation
            days_diff = (current_date - start_dt).days
            trend_factor = 1 + (days_diff * 0.0001)  # Slight upward trend
            random_factor = np.random.uniform(0.98, 1.02)  # Random variation
            
            rate = current_rate.rate * trend_factor * random_factor
            
            historical_data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "rate": rate,
                "open": rate * np.random.uniform(0.995, 1.005),
                "high": rate * np.random.uniform(1.005, 1.015),
                "low": rate * np.random.uniform(0.985, 0.995),
                "close": rate,
                "volume": np.random.randint(1000000, 5000000)
            })
            
            current_date += timedelta(days=1)
        
        return {
            "base_currency": base_currency,
            "quote_currency": quote_currency,
            "period": {
                "start": start_date,
                "end": end_date,
                "days": (end_dt - start_dt).days + 1
            },
            "data": historical_data,
            "statistics": self._calculate_statistics(historical_data)
        }
    
    def _calculate_statistics(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for historical data"""
        if not historical_data:
            return {}
        
        rates = [entry["rate"] for entry in historical_data]
        
        return {
            "min_rate": min(rates),
            "max_rate": max(rates),
            "avg_rate": sum(rates) / len(rates),
            "volatility": np.std(rates),
            "total_return": (rates[-1] - rates[0]) / rates[0] * 100,
            "data_points": len(rates)
        }
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """
        Get FX market overview with major currency pairs
        """
        major_pairs = [
            ("USD", "EUR"),
            ("USD", "GBP"),
            ("USD", "JPY"),
            ("USD", "CNY"),
            ("EUR", "GBP"),
            ("EUR", "JPY"),
            ("GBP", "JPY"),
            ("USD", "CAD"),
            ("USD", "AUD"),
            ("USD", "CHF")
        ]
        
        overview_data = []
        
        for base, quote in major_pairs:
            try:
                rate_data = await self.get_fx_rate(base, quote)
                volatility = await self.analyze_volatility(base, quote)
                
                overview_data.append({
                    "pair": f"{base}/{quote}",
                    "rate": rate_data["rate"],
                    "change_pct_24h": rate_data["change_pct_24h"],
                    "volatility": volatility.volatility_30d,
                    "risk_level": volatility.risk_level,
                    "trend": volatility.trend,
                    "recommended_hedge": volatility.recommended_hedge
                })
            except Exception as e:
                continue
        
        # Calculate market sentiment
        positive_changes = sum(1 for item in overview_data if item["change_pct_24h"] > 0)
        total_pairs = len(overview_data)
        market_sentiment = "bullish" if positive_changes > total_pairs * 0.6 else "bearish" if positive_changes < total_pairs * 0.4 else "neutral"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "market_sentiment": market_sentiment,
            "major_pairs": overview_data,
            "summary": {
                "total_pairs": total_pairs,
                "positive_changes": positive_changes,
                "negative_changes": total_pairs - positive_changes,
                "avg_volatility": sum(item["volatility"] for item in overview_data) / total_pairs if overview_data else 0
            }
        }
    
    async def calculate_forward_rate(
        self,
        base_currency: str,
        quote_currency: str,
        forward_months: int
    ) -> Dict[str, Any]:
        """
        Calculate forward FX rate based on interest rate differential
        
        Args:
            base_currency: Base currency code
            quote_currency: Quote currency code
            forward_months: Forward period in months
        """
        # Get current spot rate
        spot_data = await self.get_fx_rate(base_currency, quote_currency)
        spot_rate = spot_data["rate"]
        
        # Mock interest rates (in real implementation, these would come from market data)
        interest_rates = {
            "USD": 0.053,  # 5.3%
            "EUR": 0.038,  # 3.8%
            "GBP": 0.052,  # 5.2%
            "JPY": 0.001,  # 0.1%
            "CNY": 0.028,  # 2.8%
            "CAD": 0.048,  # 4.8%
            "AUD": 0.043,  # 4.3%
            "CHF": 0.018,  # 1.8%
            "HKD": 0.058,  # 5.8%
            "SGD": 0.036,  # 3.6%
            "KRW": 0.034,  # 3.4%
            "INR": 0.068,  # 6.8%
            "MXN": 0.112,  # 11.2%
            "BRL": 0.109,  # 10.9%
            "RUB": 0.160,  # 16.0%
            "ZAR": 0.084,  # 8.4%
            "THB": 0.025,  # 2.5%
            "MYR": 0.030,  # 3.0%
            "IDR": 0.065,  # 6.5%
            "PHP": 0.065   # 6.5%
        }
        
        base_rate = interest_rates.get(base_currency, 0.05)
        quote_rate = interest_rates.get(quote_currency, 0.05)
        
        # Calculate forward rate using interest rate parity
        # Forward Rate = Spot Rate * (1 + quote_rate * time) / (1 + base_rate * time)
        time_years = forward_months / 12
        forward_rate = spot_rate * (1 + quote_rate * time_years) / (1 + base_rate * time_years)
        
        # Calculate forward points
        forward_points = (forward_rate - spot_rate) * 10000  # In pips
        
        # Calculate annualized forward premium/discount
        forward_premium = ((forward_rate - spot_rate) / spot_rate) / time_years * 100
        
        return {
            "base_currency": base_currency,
            "quote_currency": quote_currency,
            "spot_rate": spot_rate,
            "forward_rate": forward_rate,
            "forward_months": forward_months,
            "forward_points": forward_points,
            "forward_premium_pct": forward_premium,
            "base_interest_rate": base_rate,
            "quote_interest_rate": quote_rate,
            "calculation_date": datetime.utcnow().isoformat()
        }


# Helper function to get FX rates service
def get_fx_rates_service(db: Session) -> FXRatesService:
    """Get FX rates service instance"""
    return FXRatesService(db)

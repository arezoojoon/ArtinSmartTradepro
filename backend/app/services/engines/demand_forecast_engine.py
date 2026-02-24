"""
Demand Forecast Engine — Deterministic seasonal and trend analysis (Phase 5).
NO LLM. Audit-safe.

Predicts market demand, risk of stockouts, and optimal market entry windows based on:
1. Historical trade volumes (YoY, MoM growth).
2. Seasonal indices (identifying peak months).
3. Cultural/Event catalysts (e.g., Ramadan, Back-to-school).
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DemandForecastEngine:
    def __init__(self):
        # In a real system, these would connect to a timeseries DB or feature store
        pass

    async def assess(self, product_key: str, hs_code: str, target_country: str) -> Dict[str, Any]:
        """
        Assess market demand, predict stockouts, and recommend optimal timing.
        """
        logger.info(f"[DemandEngine] Running forecast for {product_key} (HS:{hs_code}) in {target_country}")

        # 1. Base Demand Trend (from historical data)
        trend_data = self._get_historical_trend(hs_code, target_country)
        
        # 2. Seasonality & Peak Detection
        seasonality = self._get_seasonality_index(hs_code, target_country)
        
        # 3. Cultural/Event Catalysts
        catalysts = self._get_demand_catalysts(hs_code, target_country)

        # 4. Stockout Prediction Model
        current_month = datetime.now().month
        stockout_prediction = self._predict_stockout(seasonality, current_month)

        # 5. Optimal Profit Timing (Integration hook for Arbitrage Engine)
        best_profit_month = self._calculate_optimal_entry(seasonality, trend_data)

        # Calculate a 0-100 score indicating current market readiness
        readiness_score = self._calculate_readiness_score(trend_data['yoy_growth'], stockout_prediction['risk_level'])

        return {
            "market_readiness_score": readiness_score,
            "best_profit_month": best_profit_month,
            "forecast": {
                "trend": trend_data,
                "seasonality_peaks": seasonality['peak_months'],
                "stockout_risk": stockout_prediction,
                "catalysts": catalysts
            },
            "explainability": [
                f"Trend Analysis: YoY growth is {trend_data['yoy_growth']}% indicating {trend_data['direction']} demand.",
                f"Seasonality: Peak demand historically observed in {', '.join(seasonality['peak_months'])}.",
                f"Stockout Alert: {stockout_prediction['reason']}",
                f"Timing Strategy: Best execution window is {best_profit_month} to maximize margins."
            ]
        }

    def _get_historical_trend(self, hs_code: str, country: str) -> Dict[str, Any]:
        """Simulates fetching YoY/MoM growth from TradeMap/Comtrade."""
        # STUB: In production, fetch this from the database
        yoy = 12.5 # Positive growth
        direction = "expanding" if yoy > 0 else "contracting"
        return {"yoy_growth": yoy, "mom_growth": 3.2, "direction": direction}

    def _get_seasonality_index(self, hs_code: str, country: str) -> Dict[str, Any]:
        """Simulates finding peak months based on product & region."""
        # STUB logic
        is_agri = hs_code.startswith("10") or hs_code.startswith("09")
        is_consumer = hs_code.startswith("19") or hs_code.startswith("61")

        if is_agri:
            return {"peak_months": ["September", "October", "November"], "index_variance": 0.45}
        elif is_consumer and country in ["AE", "SA", "QA"]:
            return {"peak_months": ["February", "March", "November"], "index_variance": 0.30} # Pre-Ramadan / Winter
        
        return {"peak_months": ["June", "July", "August"], "index_variance": 0.15}

    def _get_demand_catalysts(self, hs_code: str, country: str) -> List[str]:
        """Identifies specific events that shock demand."""
        catalysts = []
        if country in ["AE", "SA", "EG", "TR"]:
            catalysts.append("Pre-Ramadan Stockpiling (Expect 25% surge 45 days prior)")
        if hs_code.startswith("10"):
             catalysts.append("Global harvest yield reports (Weather dependent)")
        return catalysts

    def _predict_stockout(self, seasonality: Dict[str, Any], current_month: int) -> Dict[str, Any]:
        """
        Calculates the risk of buyers running out of stock.
        If we are 1-2 months *before* a peak season, stockout risk is HIGH (best time to sell).
        """
        # Map month names to integers for simple logic
        month_map = {"January":1, "February":2, "March":3, "April":4, "May":5, "June":6, 
                     "July":7, "August":8, "September":9, "October":10, "November":11, "December":12}
        
        peak_integers = [month_map.get(m, 0) for m in seasonality['peak_months']]
        
        # Check if current month is 1 or 2 months prior to any peak
        is_pre_peak = any((p - current_month) in [1, 2] or (p - current_month) in [-10, -11] for p in peak_integers)

        if is_pre_peak:
            return {
                "risk_level": "High", 
                "score": 85, 
                "reason": "Approaching peak seasonal demand. Buyers are actively securing inventory now to prevent stockouts."
            }
        elif current_month in peak_integers:
            return {
                "risk_level": "Medium", 
                "score": 50, 
                "reason": "Currently in peak season. Spot shortages possible, but bulk contracts likely fulfilled."
            }
        else:
            return {
                "risk_level": "Low", 
                "score": 15, 
                "reason": "Off-peak period. Inventory levels generally stable."
            }

    def _calculate_optimal_entry(self, seasonality: Dict[str, Any], trend: Dict[str, Any]) -> str:
        """Determines the best month to execute the trade."""
        if seasonality['peak_months']:
            # The best time to start the trade (ship) is usually 1-2 months before the peak
            # For simplicity in this STUB, we return the first peak month
            first_peak = seasonality['peak_months'][0]
            return f"Mid-{first_peak} (Plan shipment 45 days prior)"
        return "Immediate Entry (No strong seasonality detected)"

    def _calculate_readiness_score(self, yoy_growth: float, stockout_risk: str) -> float:
        """Composite score defining how hungry the market is right now."""
        score = 50 # Base
        if yoy_growth > 5:
            score += 20
        elif yoy_growth < 0:
            score -= 20
            
        if stockout_risk == "High":
            score += 30
        elif stockout_risk == "Low":
            score -= 10
            
        return max(0.0, min(100.0, score))

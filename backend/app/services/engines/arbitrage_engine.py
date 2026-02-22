"""
Arbitrage Engine — Deterministic profit calculation.
NO LLM. NO hallucination. Audit-safe math.

Input: product, origin (FOB), destination (CIF), quantities
Output: Profit Probability Score, net margin, breakeven analysis
"""
from app.integrations.fx_client import FXClient
from app.integrations.freight_client import FreightClient
from app.integrations.un_comtrade_client import UNComtradeClient
from app.integrations.political_risk_client import PoliticalRiskClient
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

fx = FXClient()
freight = FreightClient()
comtrade = UNComtradeClient()
risk_client = PoliticalRiskClient()


class ArbitrageEngine:
    """
    Deterministic arbitrage calculator.
    Every number is traceable. No AI guessing.
    """

    @staticmethod
    async def calculate(
        db,
        tenant_id,
        product_hs: str,
        origin_country: str,
        destination_country: str,
        buy_price_per_kg: float,
        sell_price_per_kg: float,
        quantity_kg: float,
        buy_currency: str = "USD",
        sell_currency: str = "USD",
    ) -> dict:
        """
        Full arbitrage calculation with cost breakdown.
        Returns: profit, margin, risk-adjusted margin, probability score.
        Persists to ArbitrageResult table.
        """
        from app.models.brain import ArbitrageResult
        
        # V3 Strict: Insufficient Data Verification
        try:
            # 1. FX conversion
            buy_rate = await fx.get_rate(buy_currency, "USD") if buy_currency != "USD" else 1.0
            sell_rate = await fx.get_rate(sell_currency, "USD") if sell_currency != "USD" else 1.0

            buy_usd = buy_price_per_kg * buy_rate
            sell_usd = sell_price_per_kg * sell_rate

            # 2. Freight cost
            freight_data = await freight.get_rate(origin_country, destination_country)
            # Estimate: 20ft container ≈ 20,000 kg
            containers_needed = max(1, quantity_kg / 20000)
            total_freight = freight_data["total_cost_usd"] * containers_needed
            freight_per_kg = total_freight / quantity_kg

            # 3. Tariff
            tariff_data = await comtrade.get_tariff_rate(origin_country, destination_country, product_hs)
            tariff_rate = tariff_data["applied_rate"] / 100.0
            tariff_per_kg = sell_usd * tariff_rate

        except ValueError as e:
            # INTERCEPT: If data is missing, we DO NOT GUESS.
            logger.warning(f"Arbitrage Insufficient Data: {str(e)}")
            return {
                "status": "insufficient_data",
                "message": "Data insufficient for reliable calculation.",
                "missing_fields": ["fx_rate" if "FX" in str(e) else "freight_rate" if "freight" in str(e) else "tariff_rate"],
                "suggested_next_steps": [f"Configure API Key for {str(e)}", "Use known routes/pairs for testing."]
            }

        # 4. Total landed cost
        total_cost_per_kg = buy_usd + freight_per_kg + tariff_per_kg

        # 5. Insurance (0.5% of cargo value)
        insurance_per_kg = buy_usd * 0.005

        # 6. Total with insurance
        landed_cost_per_kg = total_cost_per_kg + insurance_per_kg

        # 7. Gross profit per kg
        gross_profit_per_kg = sell_usd - landed_cost_per_kg

        # 8. Gross margin
        gross_margin = (gross_profit_per_kg / sell_usd) if sell_usd > 0 else 0

        # 9. Total profit
        total_revenue = sell_usd * quantity_kg
        total_cost = landed_cost_per_kg * quantity_kg
        total_profit = total_revenue - total_cost

        # 10. Risk adjustment
        dest_risk = await risk_client.get_country_risk(destination_country)
        fx_volatility = await fx.get_volatility(sell_currency, "USD")

        risk_factor = 1.0 - (dest_risk["risk_score"] * 0.3 + fx_volatility * 0.2)
        risk_adjusted_margin = gross_margin * risk_factor

        # 11. Profit Probability Score (0-100)
        if gross_margin <= 0:
            profit_probability = max(5, int(gross_margin * 100 + 20))
        elif gross_margin < 0.05:
            profit_probability = 30 + int(gross_margin * 400)
        elif gross_margin < 0.15:
            profit_probability = 50 + int(gross_margin * 200)
        else:
            profit_probability = min(95, 70 + int(gross_margin * 100))

        # Adjust by risk
        profit_probability = max(5, min(95, int(profit_probability * risk_factor)))

        result = {
            "product_hs": product_hs,
            "origin": origin_country,
            "destination": destination_country,
            "quantity_kg": quantity_kg,

            # Prices
            "buy_price_usd_per_kg": round(buy_usd, 4),
            "sell_price_usd_per_kg": round(sell_usd, 4),

            # Cost breakdown
            "cost_breakdown": {
                "product_cost": round(buy_usd, 4),
                "freight_per_kg": round(freight_per_kg, 4),
                "tariff_per_kg": round(tariff_per_kg, 4),
                "insurance_per_kg": round(insurance_per_kg, 4),
                "landed_cost_per_kg": round(landed_cost_per_kg, 4),
            },

            # Freight details
            "freight": {
                "total_cost": round(total_freight, 2),
                "containers": round(containers_needed, 1),
                "transit_days": freight_data["transit_days"],
            },

            # Tariff details
            "tariff": {
                "applied_rate_pct": tariff_data["applied_rate"],
                "preferential_available": tariff_data["preferential_available"],
            },

            # Profitability
            "gross_profit_per_kg": round(gross_profit_per_kg, 4),
            "gross_margin_pct": round(gross_margin * 100, 2),
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_profit, 2),

            # Risk-adjusted
            "risk_score": dest_risk["risk_score"],
            "fx_volatility": fx_volatility,
            "risk_factor": round(risk_factor, 3),
            "risk_adjusted_margin_pct": round(risk_adjusted_margin * 100, 2),

            # Final score
            "profit_probability_score": profit_probability,
            "recommendation": ArbitrageEngine._get_recommendation(profit_probability, gross_margin),
            "payment_terms": dest_risk["recommended_payment_terms"],
        }

        # PERSISTENCE
        try:
            record = ArbitrageResult(
                tenant_id=tenant_id,
                product_hs=product_hs,
                origin_country=origin_country,
                destination_country=destination_country,
                buy_price=buy_usd,
                sell_price=sell_usd,
                margin_net=total_profit,
                roi_percentage=gross_margin * 100,
                breakdown=result
            )
            db.add(record)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save ArbitrageResult: {e}")

        logger.info(f"Arbitrage calc: {origin_country}→{destination_country} HS:{product_hs} margin:{gross_margin:.2%} prob:{profit_probability}")
        return result

    @staticmethod
    def _get_recommendation(probability: int, margin: float) -> str:
        if probability >= 75 and margin > 0.10:
            return "STRONG BUY — High margin, low risk"
        elif probability >= 60 and margin > 0.05:
            return "BUY — Favorable trade opportunity"
        elif probability >= 40:
            return "HOLD — Monitor pricing and risk factors"
        elif probability >= 20:
            return "CAUTION — Low margin, elevated risk"
        else:
            return "AVOID — Negative or near-zero margin"

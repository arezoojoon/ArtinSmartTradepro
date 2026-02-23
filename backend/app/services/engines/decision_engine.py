"""
Decision Intelligence Layer — One-click trade decisions.
Combines all engines into a unified trade recommendation.
Includes 3 scenarios: optimistic, pessimistic, realistic.
"""
from app.services.brain_arbitrage_engine import ArbitrageEngine as BrainArbitrageEngine
from app.services.engines.risk_engine import RiskEngine
from app.services.engines.demand_forecast_engine import DemandForecastEngine
from app.services.engines.cultural_engine import CulturalNegotiationEngine
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    One-click trade decision: combines arbitrage, risk, demand, and cultural analysis.
    Returns best buy/sell country, timing, net profit, confidence, and 3 scenarios.
    """

    @staticmethod
    async def analyze_opportunity(
        db,
        tenant_id,
        product_hs: str,
        product_name: str,
        origin_country: str,
        destination_country: str,
        buy_price_per_kg: float,
        sell_price_per_kg: float,
        quantity_kg: float,
        buy_currency: str = "USD",
        sell_currency: str = "USD",
        trader_country: str = "IR",
    ) -> dict:
        """
        Complete trade opportunity analysis.
        One call → full intelligence picture.
        """
        # 1. Arbitrage (financial analysis)
        from app.schemas.brain import ArbitrageInput
        
        input_data = ArbitrageInput(
            product_key=product_hs, # Using HS as product key for lookup
            hs_code=product_hs,
            origin_country=origin_country,
            destination_country=destination_country,
            buy_market=origin_country,
            sell_market=destination_country,
            buy_price=buy_price_per_kg,
            buy_currency=buy_currency,
            sell_price=sell_price_per_kg,
            sell_currency=sell_currency,
            # freight_cost and others will be auto-calculated
        )
        
        arb_engine = BrainArbitrageEngine(db)
        arb_output = await arb_engine.run_analysis(
            tenant_id=tenant_id,
            input_data=input_data
        )
        
        # Bridge to legacy-style dict for rest of DecisionEngine
        if arb_output.status == "success" and arb_output.financials:
            f = arb_output.financials
            arbitrage = {
                "buy_price_usd_per_kg": f.buy_price_usd,
                "sell_price_usd_per_kg": f.sell_price_usd,
                "cost_breakdown": {
                    "product_cost": f.buy_price_usd,
                    "freight_per_kg": f.total_freight_cost,
                    "tariff_per_kg": f.tariff_cost_usd,
                    "insurance_per_kg": f.buy_price_usd * 0.005, # Insurance logic from old engine
                    "landed_cost_per_kg": f.total_cost_usd + (f.buy_price_usd * 0.005),
                },
                "freight": {
                    "total_cost": f.total_freight_cost * quantity_kg,
                    "containers": round(quantity_kg / 20000, 1), # Logic from old engine
                    "transit_days": 15, # Mock
                },
                "tariff": {
                    "applied_rate_pct": f.tariff_pct,
                    "preferential_available": False,
                },
                "total_profit": f.total_profit_usd * quantity_kg, # Adjust to total if needed
                "total_revenue": f.total_revenue_usd * quantity_kg,
                "gross_margin_pct": f.estimated_margin_pct,
                "risk_adjusted_margin_pct": f.estimated_margin_pct, # Will be adjusted below
                "profit_probability_score": 70, # Initial
                "origin": origin_country,
                "destination": destination_country,
                "recommendation": arb_output.opportunity_card.next_actions[0] if arb_output.opportunity_card.next_actions else "Monitor"
            }
        else:
            # Fallback for insufficient data
            raise ValueError(f"Arbitrage analysis failed: {arb_output.status}")

        # 2. Risk assessment
        risk = await RiskEngine.assess(
            db=db,
            tenant_id=tenant_id,
            destination_country=destination_country,
            origin_country=origin_country,
            commodity=product_name,
            sell_currency=sell_currency,
        )

        # 3. Demand forecast
        demand = await DemandForecastEngine.forecast(
            db=db,
            tenant_id=tenant_id,
            commodity=product_name,
            target_market=destination_country,
        )

        # 4. Cultural strategy
        cultural = await CulturalNegotiationEngine.get_strategy(
            db=db,
            tenant_id=tenant_id,
            counterpart_country=destination_country,
            your_country=trader_country,
            product_category=product_name,
            deal_size_usd=sell_price_per_kg * quantity_kg,
        )

        # 5. Generate 3 scenarios
        scenarios = DecisionEngine._generate_scenarios(arbitrage, risk)

        # 6. Overall decision confidence
        confidence = DecisionEngine._calculate_confidence(arbitrage, risk, demand)

        # 7. Build verdict
        verdict = DecisionEngine._build_verdict(arbitrage, risk, demand, confidence)

        result = {
            "verdict": verdict,
            "confidence_score": confidence,

            "financials": {
                "buy_price_usd_per_kg": arbitrage["buy_price_usd_per_kg"],
                "sell_price_usd_per_kg": arbitrage["sell_price_usd_per_kg"],
                "landed_cost_per_kg": arbitrage["cost_breakdown"]["landed_cost_per_kg"],
                "gross_margin_pct": arbitrage["gross_margin_pct"],
                "risk_adjusted_margin_pct": arbitrage["risk_adjusted_margin_pct"],
                "total_profit": arbitrage["total_profit"],
                "total_revenue": arbitrage["total_revenue"],
                "profit_probability_score": arbitrage["profit_probability_score"],
            },

            "cost_breakdown": arbitrage["cost_breakdown"],
            "freight": arbitrage["freight"],
            "tariff": arbitrage["tariff"],

            "risk": {
                "composite_score": risk["composite_risk_score"],
                "level": risk["risk_level"],
                "factors": risk["factors"],
                "alerts": risk["alerts"],
                "sanctions": risk["sanctions"],
                "payment_terms": risk["payment_terms"],
            },

            "timing": {
                "best_entry_month": demand["best_entry_month"],
                "best_entry_reason": demand["best_entry_reason"],
                "peak_month": demand["peak_month"],
                "peak_demand_index": demand["peak_demand_index"],
                "cultural_events": demand["cultural_events"],
            },

            "negotiation": {
                "approach": cultural.get("negotiation_approach", ""),
                "payment_suggestion": cultural.get("payment_terms_suggestion", ""),
                "communication_style": cultural.get("communication_style", ""),
                "red_flags": cultural.get("red_flags", []),
                "power_moves": cultural.get("power_moves", []),
                "timeline": cultural.get("timeline_expectation", ""),
            },

            "scenarios": scenarios,

            "recommendation": arbitrage["recommendation"],
        }

        logger.info(f"Decision analysis: {origin_country}→{destination_country} HS:{product_hs} verdict={verdict['decision']} confidence={confidence:.0%}")
        return result

    @staticmethod
    def _generate_scenarios(arbitrage: dict, risk: dict) -> dict:
        """3 scenarios: optimistic, realistic, pessimistic."""
        base_profit = arbitrage["total_profit"]
        risk_factor = risk["composite_risk_score"]

        return {
            "optimistic": {
                "label": "Best Case",
                "profit": round(base_profit * 1.25, 2),
                "margin_pct": round(arbitrage["gross_margin_pct"] * 1.20, 2),
                "probability": round(max(10, 30 - risk_factor * 40), 0),
                "assumptions": "Favorable FX, below-average freight, no delays",
            },
            "realistic": {
                "label": "Expected Case",
                "profit": round(base_profit, 2),
                "margin_pct": arbitrage["risk_adjusted_margin_pct"],
                "probability": round(max(20, 50 - risk_factor * 20), 0),
                "assumptions": "Current rates, average conditions",
            },
            "pessimistic": {
                "label": "Worst Case",
                "profit": round(base_profit * (0.6 - risk_factor * 0.3), 2),
                "margin_pct": round(arbitrage["gross_margin_pct"] * (0.5 - risk_factor * 0.2), 2),
                "probability": round(min(40, 20 + risk_factor * 30), 0),
                "assumptions": "Adverse FX, freight surge, payment delays",
            },
        }

    @staticmethod
    def _calculate_confidence(arbitrage: dict, risk: dict, demand: dict) -> float:
        """Overall confidence in the decision (0.0 - 1.0)."""
        arb_score = arbitrage["profit_probability_score"] / 100.0
        risk_score = 1.0 - risk["composite_risk_score"]
        demand_strength = demand["seasonality_strength"]

        confidence = (arb_score * 0.5 + risk_score * 0.35 + min(1.0, demand_strength) * 0.15)
        return round(max(0.05, min(0.95, confidence)), 2)

    @staticmethod
    def _build_verdict(arbitrage: dict, risk: dict, demand: dict, confidence: float) -> dict:
        """Final trade verdict."""
        prob = arbitrage["profit_probability_score"]
        risk_level = risk["risk_level"]

        if prob >= 70 and risk_level in ("LOW", "MODERATE"):
            decision = "GO"
            emoji = "✅"
            summary = "Strong opportunity. Favorable margin and manageable risk."
        elif prob >= 50:
            decision = "CONDITIONAL GO"
            emoji = "🟡"
            summary = "Viable opportunity. Monitor risk factors closely."
        elif prob >= 30:
            decision = "PROCEED WITH CAUTION"
            emoji = "🟠"
            summary = "Marginal opportunity. Requires risk mitigation."
        else:
            decision = "DO NOT PROCEED"
            emoji = "🔴"
            summary = "Unfavorable. Margin too thin or risk too high."

        return {
            "decision": decision,
            "emoji": emoji,
            "summary": summary,
            "best_buy_country": arbitrage["origin"],
            "best_sell_country": arbitrage["destination"],
            "best_entry_month": demand["best_entry_month"],
            "confidence": confidence,
        }

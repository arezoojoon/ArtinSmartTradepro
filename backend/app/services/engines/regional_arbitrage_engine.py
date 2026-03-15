"""
Regional Arbitrage Finder Engine
AI-powered opportunity scanner that detects price gaps across neighboring markets.
Uses Gemini AI for wholesale price intelligence and margin analysis.
"""
from typing import List, Optional
from pydantic import BaseModel
import json
import logging

logger = logging.getLogger(__name__)


class ArbitrageOpportunity(BaseModel):
    product: str
    buy_market: str
    buy_price_usd_per_kg: float
    sell_market: str
    sell_price_usd_per_kg: float
    estimated_margin_pct: float
    estimated_profit_per_ton_usd: float
    demand_level: str         # "high", "medium", "low"
    supply_level: str         # "surplus", "balanced", "deficit"
    confidence: float
    reasoning: str
    recommended_action: str
    risk_factors: List[str]


class RegionalArbitrageResult(BaseModel):
    product: str
    hs_code: str
    markets_scanned: List[str]
    opportunities: List[ArbitrageOpportunity]
    market_summary: str
    scan_confidence: float
    disclaimer: str


class RegionalArbitrageEngine:
    """
    Scans multiple regional markets for price arbitrage opportunities.
    """

    # Default GCC + regional markets
    DEFAULT_MARKETS = ["AE", "OM", "QA", "KW", "BH", "SA", "IR", "TR", "IN", "PK"]

    @staticmethod
    async def scan(
        product: str,
        hs_code: str = "",
        markets: Optional[List[str]] = None,
        min_margin_pct: float = 5.0,
    ) -> RegionalArbitrageResult:
        """
        Scan regional markets for arbitrage opportunities on a specific product.
        """
        from app.services.gemini_service import _get_model, _extract_json
        import asyncio

        target_markets = markets or RegionalArbitrageEngine.DEFAULT_MARKETS
        markets_str = ", ".join(target_markets)

        model = _get_model()
        prompt = f"""You are an expert B2B commodity trade analyst specializing in the Middle East, Central Asia, and South Asia markets.

Analyze the current wholesale/B2B market conditions for the following product across multiple countries and identify arbitrage opportunities.

Product: {product}
HS Code: {hs_code or "Not specified"}
Markets to scan: {markets_str}

For each pair of markets where a meaningful price difference exists, identify the arbitrage opportunity.

Respond in this exact JSON format:
{{
    "opportunities": [
        {{
            "buy_market": "Country ISO code where price is lower",
            "buy_price_usd_per_kg": 0.0,
            "sell_market": "Country ISO code where price is higher",
            "sell_price_usd_per_kg": 0.0,
            "estimated_margin_pct": 0.0,
            "estimated_profit_per_ton_usd": 0.0,
            "demand_level": "high/medium/low",
            "supply_level": "surplus/balanced/deficit",
            "confidence": 0.0,
            "reasoning": "1-2 sentences explaining WHY this opportunity exists",
            "recommended_action": "Specific next step for the trader",
            "risk_factors": ["risk1", "risk2"]
        }}
    ],
    "market_summary": "2-3 sentence overview of the current market landscape for this product in the region",
    "scan_confidence": 0.0
}}

Rules:
- Only include opportunities with estimated margin > {min_margin_pct}%
- Sort by estimated_margin_pct descending (best first)
- Maximum 5 opportunities
- Prices must be realistic B2B wholesale prices in USD/kg
- Consider seasonality, trade restrictions, and logistics feasibility
- confidence per opportunity should be 0.0-1.0
- Be specific with reasoning — reference real trade dynamics (e.g., "Dubai re-export hub", "Oman has lower import duties")
"""
        try:
            response = await asyncio.to_thread(model.generate_content, prompt)
            ai_data = _extract_json(response.text)
        except Exception as e:
            logger.error(f"Gemini regional arbitrage scan failed: {e}")
            return RegionalArbitrageResult(
                product=product,
                hs_code=hs_code,
                markets_scanned=target_markets,
                opportunities=[],
                market_summary=f"AI scan failed: {str(e)}. Please try again.",
                scan_confidence=0.0,
                disclaimer="Scan could not be completed."
            )

        # Parse opportunities
        raw_opps = ai_data.get("opportunities", [])
        opportunities: List[ArbitrageOpportunity] = []

        for opp in raw_opps:
            try:
                opportunities.append(ArbitrageOpportunity(
                    product=product,
                    buy_market=opp.get("buy_market", "??"),
                    buy_price_usd_per_kg=float(opp.get("buy_price_usd_per_kg", 0)),
                    sell_market=opp.get("sell_market", "??"),
                    sell_price_usd_per_kg=float(opp.get("sell_price_usd_per_kg", 0)),
                    estimated_margin_pct=float(opp.get("estimated_margin_pct", 0)),
                    estimated_profit_per_ton_usd=float(opp.get("estimated_profit_per_ton_usd", 0)),
                    demand_level=opp.get("demand_level", "medium"),
                    supply_level=opp.get("supply_level", "balanced"),
                    confidence=float(opp.get("confidence", 0.5)),
                    reasoning=opp.get("reasoning", ""),
                    recommended_action=opp.get("recommended_action", "Investigate further"),
                    risk_factors=opp.get("risk_factors", []),
                ))
            except Exception as e:
                logger.warning(f"Skipping malformed opportunity: {e}")
                continue

        # Sort by margin descending
        opportunities.sort(key=lambda x: x.estimated_margin_pct, reverse=True)

        return RegionalArbitrageResult(
            product=product,
            hs_code=hs_code,
            markets_scanned=target_markets,
            opportunities=opportunities[:5],
            market_summary=ai_data.get("market_summary", "No summary available."),
            scan_confidence=float(ai_data.get("scan_confidence", 0.6)),
            disclaimer="AI-generated analysis based on general trade intelligence. Prices are indicative wholesale estimates. Always verify with actual market quotes before making trade decisions.",
        )

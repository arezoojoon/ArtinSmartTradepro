"""
Landed Cost Calculator Engine
Computes the full cost breakdown for importing/exporting goods:
freight, tariffs, insurance, warehousing, port charges, and final profit/loss.
Uses Gemini AI for intelligent cost estimation when live data is unavailable.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import json
import logging

logger = logging.getLogger(__name__)


class CostLineItem(BaseModel):
    category: str          # e.g. "Freight", "Customs Duty", "Insurance"
    description: str
    amount_usd: float
    percentage_of_total: float = 0.0
    source: str            # "user_input", "ai_estimate", "calculation"
    notes: Optional[str] = None


class LandedCostBreakdown(BaseModel):
    product_name: str
    hs_code: str
    origin_country: str
    destination_country: str
    quantity_kg: float
    unit_price_usd: float
    currency: str

    # Cost breakdown
    product_cost_usd: float
    cost_items: List[CostLineItem]
    total_additional_costs_usd: float
    total_landed_cost_usd: float
    landed_cost_per_kg_usd: float

    # Profit analysis
    suggested_sell_price_per_kg: float
    estimated_profit_usd: float
    estimated_margin_pct: float

    # Meta
    confidence: float
    assumptions: List[str]
    ai_notes: str


class LandedCostEngine:
    """
    Computes a full landed-cost breakdown using Gemini AI for intelligent estimation.
    """

    @staticmethod
    async def calculate(
        product_name: str,
        hs_code: str,
        origin_country: str,
        destination_country: str,
        unit_price: float,
        quantity_kg: float,
        currency: str = "USD",
        sell_price_per_kg: Optional[float] = None,
    ) -> LandedCostBreakdown:
        """
        Calculate the full landed cost for a trade deal.
        Uses Gemini AI to estimate freight, tariffs, insurance, and other costs.
        """
        from app.services.gemini_service import GeminiService, _get_model, _extract_json

        product_cost_usd = unit_price * quantity_kg

        # Ask Gemini for a comprehensive cost estimate
        model = _get_model()
        prompt = f"""You are an expert international trade cost analyst. Calculate the FULL landed cost breakdown for the following shipment.

Product: {product_name}
HS Code: {hs_code}
Origin: {origin_country}
Destination: {destination_country}
Quantity: {quantity_kg} kg
Unit Price: {unit_price} {currency}/kg
Total Product Cost: {product_cost_usd} {currency}

You MUST provide realistic cost estimates based on current trade routes and typical rates. 
Consider: Sea freight (most common for bulk), customs duties based on the HS code, cargo insurance, 
port handling charges, warehousing, documentation fees, and any relevant taxes.

Respond in this exact JSON format:
{{
    "freight": {{
        "method": "Sea Freight / Air Freight",
        "cost_usd": 0.0,
        "description": "Brief description of the freight route and method",
        "transit_days": 0
    }},
    "customs_duty": {{
        "tariff_rate_pct": 0.0,
        "duty_amount_usd": 0.0,
        "hs_classification_note": "Brief note on HS classification"
    }},
    "insurance": {{
        "rate_pct": 0.0,
        "cost_usd": 0.0,
        "coverage_type": "CIF / All Risk"
    }},
    "port_handling": {{
        "origin_charges_usd": 0.0,
        "destination_charges_usd": 0.0,
        "total_usd": 0.0
    }},
    "warehousing": {{
        "estimated_days": 0,
        "cost_per_day_usd": 0.0,
        "total_usd": 0.0
    }},
    "documentation_fees_usd": 0.0,
    "other_taxes": {{
        "vat_pct": 0.0,
        "vat_amount_usd": 0.0,
        "other_charges_usd": 0.0
    }},
    "suggested_sell_price_per_kg": 0.0,
    "market_notes": "Brief note on market conditions and pricing strategy",
    "confidence": 0.0
}}

Rules:
- All amounts must be in USD
- Be realistic based on actual trade routes between {origin_country} and {destination_country}
- customs_duty tariff_rate should be based on HS code {hs_code}
- insurance is typically 0.2-0.5% of CIF value
- confidence should reflect how certain you are (0.0-1.0)
"""
        try:
            import asyncio
            response = await asyncio.to_thread(model.generate_content, prompt)
            ai_data = _extract_json(response.text)
        except Exception as e:
            logger.error(f"Gemini landed cost estimation failed: {e}")
            # Fallback to rough estimates
            ai_data = LandedCostEngine._fallback_estimates(
                product_cost_usd, quantity_kg, origin_country, destination_country
            )

        # Build cost line items from AI response
        cost_items: List[CostLineItem] = []
        total_additional = 0.0

        # 1. Freight
        freight = ai_data.get("freight", {})
        freight_cost = float(freight.get("cost_usd", 0))
        cost_items.append(CostLineItem(
            category="🚢 Freight",
            description=freight.get("description", f"Shipping {origin_country} → {destination_country}"),
            amount_usd=freight_cost,
            source="ai_estimate",
            notes=f"Method: {freight.get('method', 'Sea')} | Transit: {freight.get('transit_days', '~')} days"
        ))
        total_additional += freight_cost

        # 2. Customs Duty
        customs = ai_data.get("customs_duty", {})
        duty_amount = float(customs.get("duty_amount_usd", 0))
        tariff_rate = float(customs.get("tariff_rate_pct", 0))
        cost_items.append(CostLineItem(
            category="🏛️ Customs Duty",
            description=f"Import duty at {tariff_rate}% (HS {hs_code})",
            amount_usd=duty_amount,
            source="ai_estimate",
            notes=customs.get("hs_classification_note", "")
        ))
        total_additional += duty_amount

        # 3. Insurance
        insurance = ai_data.get("insurance", {})
        insurance_cost = float(insurance.get("cost_usd", 0))
        cost_items.append(CostLineItem(
            category="🛡️ Insurance",
            description=f"Cargo insurance ({insurance.get('coverage_type', 'CIF')})",
            amount_usd=insurance_cost,
            source="ai_estimate",
            notes=f"Rate: {insurance.get('rate_pct', 0.3)}%"
        ))
        total_additional += insurance_cost

        # 4. Port Handling
        port = ai_data.get("port_handling", {})
        port_total = float(port.get("total_usd", 0))
        cost_items.append(CostLineItem(
            category="⚓ Port Handling",
            description="Origin + destination port charges",
            amount_usd=port_total,
            source="ai_estimate",
            notes=f"Origin: ${port.get('origin_charges_usd', 0):.0f} | Dest: ${port.get('destination_charges_usd', 0):.0f}"
        ))
        total_additional += port_total

        # 5. Warehousing
        warehouse = ai_data.get("warehousing", {})
        warehouse_cost = float(warehouse.get("total_usd", 0))
        cost_items.append(CostLineItem(
            category="📦 Warehousing",
            description=f"Storage for ~{warehouse.get('estimated_days', 7)} days",
            amount_usd=warehouse_cost,
            source="ai_estimate"
        ))
        total_additional += warehouse_cost

        # 6. Documentation
        doc_fees = float(ai_data.get("documentation_fees_usd", 0))
        cost_items.append(CostLineItem(
            category="📄 Documentation",
            description="BL, CO, phytosanitary, customs clearance fees",
            amount_usd=doc_fees,
            source="ai_estimate"
        ))
        total_additional += doc_fees

        # 7. VAT / Other Taxes
        taxes = ai_data.get("other_taxes", {})
        vat_amount = float(taxes.get("vat_amount_usd", 0))
        other_charges = float(taxes.get("other_charges_usd", 0))
        tax_total = vat_amount + other_charges
        if tax_total > 0:
            cost_items.append(CostLineItem(
                category="💰 Taxes & VAT",
                description=f"VAT {taxes.get('vat_pct', 0)}% + other levies",
                amount_usd=tax_total,
                source="ai_estimate"
            ))
            total_additional += tax_total

        # Calculate totals
        total_landed = product_cost_usd + total_additional
        landed_per_kg = total_landed / quantity_kg if quantity_kg > 0 else 0

        # Set percentages
        for item in cost_items:
            item.percentage_of_total = (item.amount_usd / total_landed * 100) if total_landed > 0 else 0

        # Profit analysis
        suggested_sell = float(ai_data.get("suggested_sell_price_per_kg", landed_per_kg * 1.2))
        effective_sell = sell_price_per_kg if sell_price_per_kg else suggested_sell
        estimated_revenue = effective_sell * quantity_kg
        estimated_profit = estimated_revenue - total_landed
        estimated_margin = (estimated_profit / total_landed * 100) if total_landed > 0 else 0

        confidence = float(ai_data.get("confidence", 0.6))
        ai_notes = ai_data.get("market_notes", "AI-generated estimates. Verify with your freight forwarder and customs broker.")

        assumptions = [
            f"All costs normalized to USD",
            f"Freight method: {freight.get('method', 'Sea Freight')}",
            f"Customs tariff rate: {tariff_rate}% for HS {hs_code}",
            f"Insurance rate: {insurance.get('rate_pct', 0.3)}% of CIF value",
            "AI-estimated costs should be verified with actual quotes",
        ]

        return LandedCostBreakdown(
            product_name=product_name,
            hs_code=hs_code,
            origin_country=origin_country,
            destination_country=destination_country,
            quantity_kg=quantity_kg,
            unit_price_usd=unit_price,
            currency=currency,
            product_cost_usd=product_cost_usd,
            cost_items=cost_items,
            total_additional_costs_usd=total_additional,
            total_landed_cost_usd=total_landed,
            landed_cost_per_kg_usd=landed_per_kg,
            suggested_sell_price_per_kg=effective_sell,
            estimated_profit_usd=estimated_profit,
            estimated_margin_pct=estimated_margin,
            confidence=confidence,
            assumptions=assumptions,
            ai_notes=ai_notes,
        )

    @staticmethod
    def _fallback_estimates(product_cost: float, qty_kg: float, origin: str, dest: str) -> dict:
        """Rough fallback estimates if Gemini fails."""
        freight_est = qty_kg * 0.08  # ~$80/ton sea freight
        duty_est = product_cost * 0.05  # 5% avg tariff
        insurance_est = product_cost * 0.003
        return {
            "freight": {"cost_usd": freight_est, "method": "Sea Freight", "description": f"{origin} → {dest}", "transit_days": 25},
            "customs_duty": {"tariff_rate_pct": 5.0, "duty_amount_usd": duty_est, "hs_classification_note": "Fallback estimate"},
            "insurance": {"rate_pct": 0.3, "cost_usd": insurance_est, "coverage_type": "CIF"},
            "port_handling": {"origin_charges_usd": 200, "destination_charges_usd": 300, "total_usd": 500},
            "warehousing": {"estimated_days": 7, "cost_per_day_usd": 50, "total_usd": 350},
            "documentation_fees_usd": 250,
            "other_taxes": {"vat_pct": 5, "vat_amount_usd": product_cost * 0.05, "other_charges_usd": 0},
            "suggested_sell_price_per_kg": (product_cost / qty_kg) * 1.25 if qty_kg > 0 else 0,
            "market_notes": "Fallback estimates used. Verify with actual quotes.",
            "confidence": 0.3,
        }

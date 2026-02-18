"""
Cultural Negotiation Engine — Gemini-powered (LLM is appropriate here).
Strategy recommendations based on counterpart's culture and nationality.

This is the ONE engine where LLM is correct:
- Human behavior is nuanced
- Cultural norms require contextual reasoning
- No financial numbers to hallucinate
"""
from app.services.gemini_service import GeminiService
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CulturalNegotiationEngine:
    """
    Gemini-powered cultural negotiation advisor.
    Provides: payment term suggestions, negotiation strategy,
    communication style, contract type recommendations.
    """

    @staticmethod
    async def get_strategy(
        db,
        tenant_id,
        counterpart_country: str,
        your_country: str = "IR",
        product_category: str = "FMCG",
        deal_size_usd: float = 50000,
        relationship_stage: str = "new",  # new, established, long_term
    ) -> dict:
        """
        Cultural negotiation strategy based on nationality.
        Uses Gemini for nuanced cultural understanding.
        Persists to CulturalStrategy table.
        """
        from app.services.gemini_service import _get_model, _extract_json
        from app.models.brain import CulturalStrategy

        model = _get_model("gemini-2.5-flash")

        prompt = f"""You are an expert international trade negotiation consultant with 20 years of experience.

Provide cultural negotiation guidance for this trade scenario:
- Your trader is from: {your_country}
- Counterpart is from: {counterpart_country}
- Product category: {product_category}
- Deal size: ${deal_size_usd:,.0f}
- Relationship stage: {relationship_stage}

Respond in this exact JSON format:
{{
    "greeting_protocol": "How to properly greet and address the counterpart",
    "communication_style": "direct/indirect/formal — with specific guidance",
    "negotiation_approach": "Step-by-step negotiation strategy",
    "price_discussion": "How to approach pricing — when to bring it up, how to counter",
    "payment_terms_suggestion": "Recommended payment structure for this culture",
    "contract_type": "Recommended contract format",
    "red_flags": ["Things to absolutely avoid"],
    "power_moves": ["Cultural leverage points that build trust"],
    "timeline_expectation": "How long deals typically take with this culture",
    "follow_up_style": "How to follow up without being pushy or too passive",
    "gift_protocol": "Business gift customs (if applicable)",
    "dining_etiquette": "If a business meal is expected, key rules",
    "confidence": 0.0-1.0,
    "disclaimer": "Cultural generalization. Individual behavior may vary."
}}

Rules:
- Be specific to the countries involved, not generic
- Include real cultural nuances, not textbook platitudes
- Consider the deal size — larger deals have different protocols
- Consider the relationship stage — new contacts need more formal approach"""

        try:
            response = model.generate_content(prompt)
            result = _extract_json(response.text)
            
            # PERSISTENCE
            try:
                record = CulturalStrategy(
                    tenant_id=tenant_id,
                    target_country=counterpart_country,
                    deal_context=f"{product_category} / ${deal_size_usd}",
                    strategy_summary=result.get("negotiation_approach", "")[:255],
                    do_and_donts=result.get("red_flags", []),
                    negotiation_tactics=result
                )
                db.add(record)
                db.commit()
            except Exception as e:
                logger.error(f"Failed to save CulturalStrategy: {e}")
                
            logger.info(f"Cultural strategy: {your_country}→{counterpart_country} for {product_category}")
            return result
        except Exception as e:
            logger.error(f"Cultural negotiation engine error: {e}")
            return {
                "error": str(e),
                "fallback": "Use formal communication. Start with Letter of Credit. Allow 2-4 weeks for response.",
                "confidence": 0.3,
                "disclaimer": "Fallback recommendation. AI service temporarily unavailable."
            }
        except Exception as e:
            logger.error(f"Cultural negotiation engine error: {e}")
            return {
                "error": str(e),
                "fallback": "Use formal communication. Start with Letter of Credit. Allow 2-4 weeks for response.",
                "confidence": 0.3,
                "disclaimer": "Fallback recommendation. AI service temporarily unavailable."
            }

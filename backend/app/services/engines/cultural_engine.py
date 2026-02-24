"""
Cultural & Negotiation Engine — Phase 5 Strategic Enhancement.
Generates an AI-driven "Deal Closer" playbook based on the counterparty's nationality and business culture.
Includes specific objection handling and walk-away parameters.
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CulturalEngine:
    def __init__(self, gemini_service=None):
        self.gemini = gemini_service

    async def generate_playbook(self, country: str, deal_type: str, product: str) -> Dict[str, Any]:
        """
        Generates a comprehensive negotiation strategy based on cultural norms.
        deal_type: "sourcing" (buying) or "sales" (selling)
        """
        logger.info(f"[CulturalEngine] Generating playbook for {country} - {deal_type} of {product}")

        playbook = self._get_base_cultural_profile(country, deal_type)
        
        # Add dynamic objection handling based on the deal type
        objection_handling = self._generate_objection_handling(country, deal_type)
        
        # Calculate strict walk-away points based on risk profiles
        walk_away_points = self._determine_walk_away(country, deal_type)

        return {
            "country": country,
            "deal_context": deal_type,
            "strategic_playbook": playbook,
            "objection_handling": objection_handling,
            "walk_away_points": walk_away_points,
            "explainability": [
                f"Strategy adapted for {country}'s standard business etiquette.",
                "Objection handling tailored to typical regional price sensitivity.",
                "Walk-away thresholds set to mitigate local compliance and payment risks."
            ]
        }

    def _get_base_cultural_profile(self, country: str, deal_type: str) -> Dict[str, Any]:
        """Returns the core negotiation strategy based on the country's business culture."""
        country_code = country.upper()
        
        # Group 1: Relationship-Driven, High Context (e.g., Middle East, LatAm)
        if country_code in ["AE", "SA", "TR", "EG", "BR", "MX"]:
            return {
                "communication_style": "High-context. Trust and personal relationships are paramount. Expect small talk before business.",
                "preferred_channel": "WhatsApp voice notes and face-to-face meetings (or video calls). Emails are often ignored.",
                "decision_speed": "Slow initially while building trust, then execution can be very fast.",
                "negotiation_tactic": "Start with a higher margin buffer. Haggling is expected and seen as part of the relationship building." if deal_type == "sales" else "Do not accept the first offer. Build rapport to unlock 'special' partner pricing.",
                "payment_norms": "Open Account (OA) after trust is established. Letters of Credit (LC) for first large deals."
            }
            
        # Group 2: Direct, Low Context, Efficiency-Driven (e.g., Germany, USA, UK)
        elif country_code in ["DE", "US", "GB", "NL", "SE"]:
            return {
                "communication_style": "Direct, explicit, and low-context. Time is money. Get straight to the point.",
                "preferred_channel": "Formal emails with clear bullet points. Scheduled Teams/Zoom calls.",
                "decision_speed": "Fast and logical, strictly based on ROI and SLAs.",
                "negotiation_tactic": "Present your best or near-best price early. Provide data-backed ROI. Excessive haggling may be viewed as unprofessional." if deal_type == "sales" else "Ask for volume discounts directly. They respect strict adherence to timelines and specs over relationships.",
                "payment_norms": "Strict adherence to Net 30/60. Late payments incur strict penalties."
            }
            
        # Group 3: Consensus-Driven, Detail-Oriented (e.g., Japan, China, South Korea)
        elif country_code in ["JP", "CN", "KR", "SG"]:
            return {
                "communication_style": "Indirect, highly respectful. Harmony (face-saving) is critical. Never force a 'No'.",
                "preferred_channel": "WeChat/Line (China) or formal emails (Japan). Always respect hierarchy in communications.",
                "decision_speed": "Very slow. Consensus must be reached among multiple stakeholders.",
                "negotiation_tactic": "Focus on long-term partnership value rather than short-term price wins. Be patient." if deal_type == "sales" else "Specify quality standards rigorously in writing. Expect intense price negotiations in China, but strict quality adherence in Japan.",
                "payment_norms": "TT Advance is common in China sourcing. Letters of Credit are standard."
            }
            
        # Default Profile
        return {
            "communication_style": "Standard professional business etiquette.",
            "preferred_channel": "Email followed by scheduled calls.",
            "decision_speed": "Moderate.",
            "negotiation_tactic": "Maintain a 10-15% negotiation buffer.",
            "payment_norms": "Standard commercial terms (LC or TT)."
        }

    def _generate_objection_handling(self, country: str, deal_type: str) -> List[Dict[str, str]]:
        """Provides specific scripts for common objections in that region."""
        country_code = country.upper()
        objections = []

        if deal_type == "sales":
            if country_code in ["AE", "SA", "TR", "EG"]:
                objections.append({
                    "objection": "Your price is too high compared to my other supplier.",
                    "response_strategy": "Do not immediately drop the price. Emphasize reliability and premium service.",
                    "script": "I understand price is important, my friend. However, with us, you are buying peace of mind. We guarantee zero delays at Jebel Ali, which saves you demurrage costs. Let's look at the total landed cost."
                })
            elif country_code in ["DE", "US", "GB"]:
                objections.append({
                    "objection": "We don't have the budget for this right now.",
                    "response_strategy": "Pivot to ROI and total cost of ownership (TCO) with hard data.",
                    "script": "I appreciate the budget constraints. However, our product increases yield by 4%, meaning the premium pays for itself within the first quarter. I can send the calculation matrix."
                })
            elif country_code in ["JP", "CN", "KR"]:
                objections.append({
                    "objection": "We need to discuss this internally before making a decision.",
                    "response_strategy": "Respect the consensus process. Provide supporting materials for internal circulation.",
                    "script": "Of course, I completely understand. Let me prepare a detailed comparison document that your team can review. Shall I include our quality certifications and reference clients in your region?"
                })
            elif country_code in ["BR", "MX"]:
                objections.append({
                    "objection": "We found a cheaper local alternative.",
                    "response_strategy": "Highlight international quality standards and export compliance advantages.",
                    "script": "I respect your local options. However, our product meets EU/FDA standards, which opens re-export possibilities for you. Plus, our supply chain consistency means no production stoppages during local shortages."
                })
        else: # sourcing
            if country_code in ["CN", "IN", "VN"]:
                objections.append({
                    "objection": "We cannot meet your target price at this MOQ.",
                    "response_strategy": "Offer a phased volume commitment rather than dropping the request.",
                    "script": "If we commit to a 12-month blanket order with quarterly call-offs, can we lock in this target price for the first shipment?"
                })
            elif country_code in ["TR", "EG"]:
                objections.append({
                    "objection": "Raw material costs have increased, we need to raise prices.",
                    "response_strategy": "Request transparency on cost breakdown and propose a shared-risk formula.",
                    "script": "We understand the market situation. Could you share the cost breakdown so we can identify where we can optimize together? We are open to a price adjustment formula tied to the commodity index."
                })

        # Generic fallback objection
        if not objections:
            objections.append({
                "objection": "We need better payment terms.",
                "response_strategy": "Trade terms for price, or utilize export credit insurance.",
                "script": "We can extend the payment terms to 60 days, but we will need to adjust the FOB price by +2% to cover the financing costs."
            })
            
        return objections

    def _determine_walk_away(self, country: str, deal_type: str) -> List[str]:
        """Hard red-lines where the trader should abort the deal."""
        walk_aways = []
        country_code = country.upper()
        
        # High Risk / Liquidity issues
        if country_code in ["EG", "NG", "AR", "LB", "PK"]:
            if deal_type == "sales":
                walk_aways.append("WALK AWAY IF: Buyer refuses to provide a confirmed Letter of Credit from a top-tier international bank. Local currency devaluation risk is too high.")
                
        # Scammer/Quality Risk profiles
        if deal_type == "sourcing" and country_code in ["CN", "VN", "TR"]:
            walk_aways.append("WALK AWAY IF: Supplier refuses third-party SGS/Intertek inspection prior to container loading.")
            walk_aways.append("WALK AWAY IF: Bank account name does not exactly match the registered company name on the commercial invoice.")
            
        # Generic strict rules
        if deal_type == "sales":
            walk_aways.append("WALK AWAY IF: The negotiated margin drops below the AI-calculated Risk-Adjusted Penalty Threshold.")
        
        if deal_type == "sourcing":
            walk_aways.append("WALK AWAY IF: Supplier cannot provide at least 2 verifiable trade references from the past 12 months.")
            
        return walk_aways


# Keep backward compatibility alias
CulturalNegotiationEngine = CulturalEngine

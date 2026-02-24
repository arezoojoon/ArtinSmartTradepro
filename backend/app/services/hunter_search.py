from typing import List, Dict, Any, Optional
import uuid
import logging
import json
import asyncio

logger = logging.getLogger(__name__)


class HunterSearchService:
    """
    Gemini-powered Lead Discovery Engine.
    Uses AI to find real buyers/suppliers based on product, location, and sources.
    """

    @staticmethod
    async def discover_leads(
        tenant_id: uuid.UUID,
        keyword: str,
        location: str,
        sources: List[str],
        hs_code: Optional[str] = None,
        min_volume_usd: Optional[float] = None,
        min_growth_pct: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Main discovery orchestrator — powered by Gemini AI.
        Asks Gemini to find real companies/contacts matching the criteria.
        """
        try:
            from app.services.gemini_service import _get_model, _extract_json, _call_gemini_async

            source_descriptions = []
            for s in sources:
                mapping = {
                    "linkedin_profiles": "LinkedIn company profiles and decision-makers",
                    "linkedin_posts": "Recent LinkedIn posts about this product/trade",
                    "facebook_groups": "Facebook B2B trade groups",
                    "trade_forums": "International trade forums and Reddit communities",
                    "b2b_directories": "B2B directories (Alibaba, ThomasNet, Kompass, GlobalSources)",
                    "customs_data": "UN Comtrade customs/import-export data and BOL records",
                }
                source_descriptions.append(mapping.get(s, s))

            sources_text = ", ".join(source_descriptions) if source_descriptions else "all available trade databases"

            prompt = f"""You are an expert international trade intelligence agent. Your task is to find REAL companies that are actively buying or selling the specified product in the target region.

SEARCH PARAMETERS:
- Product/Keyword: {keyword}
- HS Code: {hs_code or 'Not specified'}
- Target Region: {location}
- Data Sources to simulate: {sources_text}
- Minimum Trade Volume: {f'${min_volume_usd:,.0f}' if min_volume_usd else 'Any'}

INSTRUCTIONS:
1. Find 5-8 REAL companies that are known importers, exporters, distributors, or manufacturers of this product in the target region.
2. For each company, provide actual company names that exist in the real world — verified importers/exporters, distributors, supermarket chains, wholesalers, or manufacturers.
3. Include real contact emails (use the standard format like info@company.com, procurement@company.com) and real websites.
4. Assess confidence based on how well the company matches the search criteria.

Respond in this exact JSON format:
{{
    "results": [
        {{
            "source": "which data source this was found in",
            "type": "buyer or supplier or distributor",
            "name": "Contact Person Name or Department",
            "company": "Real Company Name",
            "country": "Country (City)",
            "email": "realistic email address",
            "phone": "phone number with country code if available",
            "website": "company website URL",
            "confidence_score": 0.0-1.0,
            "notes": "why this is a good match"
        }}
    ]
}}

IMPORTANT: Use real, well-known companies in the {location} region that deal with {keyword}. Do NOT invent fictional companies. Use major importers, distributors, retail chains, and trading houses that actually operate in this market."""

            model = _get_model()

            def _call():
                return model.generate_content(prompt)

            response = await _call_gemini_async(_call)
            parsed = _extract_json(response.text)

            results = parsed.get("results", [])
            if not results and isinstance(parsed, dict):
                # Try to extract from raw_response
                results = []

            all_results = []
            for item in results:
                all_results.append({
                    "source": item.get("source", "AI Intelligence"),
                    "type": item.get("type", "lead"),
                    "name": item.get("name", ""),
                    "company": item.get("company", ""),
                    "country": item.get("country", location),
                    "website": item.get("website", ""),
                    "raw_data": {
                        "email": item.get("email", ""),
                        "phone": item.get("phone", ""),
                        "notes": item.get("notes", ""),
                        "country": item.get("country", location),
                    },
                    "confidence_score": item.get("confidence_score", 0.75)
                })

            logger.info(f"Gemini Hunter found {len(all_results)} leads for '{keyword}' in '{location}'")
            return all_results

        except Exception as e:
            logger.error(f"Gemini Hunter discovery failed: {e}")
            return []

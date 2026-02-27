"""
Gemini AI Service — Unified client for trade intelligence, vision, and voice.
Uses key rotation across 3 API keys for rate limit management.
Thread-safe: key rotation uses a Lock, calls wrapped in asyncio.to_thread.
"""
import google.generativeai as genai
from app.config import get_settings
from typing import Optional, Dict, List, Callable, Any
import json
import re
import threading
import asyncio

settings = get_settings()

# API Key Rotation (thread-safe)
_api_keys = [k for k in [settings.GEMINI_API_KEY_1, settings.GEMINI_API_KEY_2, settings.GEMINI_API_KEY_3] if k]
_key_index = 0
_key_lock = threading.Lock()

def _get_model(model_name: str = "gemini-2.5-flash") -> genai.GenerativeModel:
    """Get a Gemini model with rotated API key (thread-safe)."""
    global _key_index
    if not _api_keys:
        raise ValueError("No Gemini API keys configured")
    
    with _key_lock:
        key = _api_keys[_key_index % len(_api_keys)]
        _key_index += 1
    
    genai.configure(api_key=key)
    return genai.GenerativeModel(model_name)


async def _call_gemini_async(sync_fn: Callable[..., Any], *args, **kwargs) -> Any:
    """Run a blocking Gemini call in a thread pool to avoid blocking the event loop."""
    return await asyncio.to_thread(sync_fn, *args, **kwargs)

def _extract_json(text: str) -> dict:
    """
    Extract JSON from Gemini response with robust parsing and security.
    Handles multiple response formats and prevents parsing crashes.
    """
    # Security: Limit input size to prevent DoS
    if len(text) > 100000:  # 100KB limit
        text = text[:100000]
    
    # Try direct JSON parse first
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    
    # Try extracting from code blocks (```json ... ```)
    code_block_patterns = [
        r'```json\s*\n?(.*?)\n?```',  # ```json ... ```
        r'```\s*\n?(.*?)\n?```',      # ``` ... ```
        r'`{[^`]*}`',               # `{...}` inline
    ]
    
    for pattern in code_block_patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                parsed = json.loads(match.strip())
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
    
    # Try finding JSON object boundaries with regex (more robust)
    json_patterns = [
        r'\{[\s\S]*\}',  # Find any JSON object
        r'\{[^{}]*\}',   # Simple nested objects
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                # Validate JSON structure before parsing
                if match.count('{') == match.count('}'):  # Balanced braces
                    parsed = json.loads(match)
                    if isinstance(parsed, dict):
                        return parsed
            except json.JSONDecodeError:
                continue
    
    # Last resort: try to extract key-value pairs manually
    try:
        # Look for key: value patterns
        kv_pattern = r'"([^"]+)"\s*:\s*([^,}\]]+)'
        matches = re.findall(kv_pattern, text)
        if matches and len(matches) > 2:  # At least 3 key-value pairs
            result = {}
            for key, value in matches:
                # Try to parse the value
                try:
                    if value.strip().startswith('"') and value.strip().endswith('"'):
                        result[key] = value.strip()[1:-1]  # Remove quotes
                    elif value.strip().lower() in ['true', 'false']:
                        result[key] = value.strip().lower() == 'true'
                    elif value.strip().isdigit():
                        result[key] = int(value.strip())
                    else:
                        result[key] = value.strip()
                except:
                    result[key] = value.strip()
            return result
    except:
        pass
    
    # Ultimate fallback: return structured error
    return {
        "error": "JSON_PARSE_FAILED",
        "raw_response": text[:1000],  # Limit raw response size
        "suggestion": "AI response format was invalid. Please try again.",
        "fallback_data": {
            "status": "failed",
            "reason": "Invalid JSON format from AI"
        }
    }


class GeminiService:
    
    @staticmethod
    def analyze_seasonal(product: str, region: str = "global") -> dict:
        """
        Seasonal trade intelligence.
        "Which season is best to sell cocoa-based products in Europe?"
        """
        model = _get_model()
        prompt = f"""You are an expert international trade analyst. Analyze the seasonal demand for the following product.

Product: {product}
Target Region: {region}

Respond in this exact JSON format:
{{
    "product": "{product}",
    "region": "{region}",
    "best_season": "Q1/Q2/Q3/Q4",
    "peak_months": ["month1", "month2", "month3"],
    "demand_score": 0.0-1.0,
    "reasoning": "2-3 sentences explaining why",
    "competing_products": ["product1", "product2"],
    "recommended_action": "specific actionable advice",
    "confidence": 0.0-1.0,
    "disclaimer": "AI-suggested analysis based on general trade patterns. Verify with current market data."
}}"""
        
        response = model.generate_content(prompt)
        return _extract_json(response.text)
    
    @staticmethod
    def analyze_market(product: str, season: str = "Q4", context_data: Optional[str] = None) -> dict:
        """
        Market intelligence.
        "Which country is best for product X in Q4?"
        """
        model = _get_model()
        prompt = f"""You are an expert international trade analyst. Identify the best markets for the following product in a specific season.
        
Context Data (Real-time):
{context_data or "No real-time data available."}

Product: {product}
Season: {season}

Respond in this exact JSON format:
{{
    "product": "{product}",
    "season": "{season}",
    "top_markets": [
        {{
            "country": "Country Name",
            "demand_score": 0.0-1.0,
            "import_volume_estimate": "high/medium/low",
            "key_buyers": "description of typical buyer types",
            "entry_barriers": "low/medium/high",
            "notes": "specific insight"
        }}
    ],
    "recommended_market": "Country Name",
    "reasoning": "2-3 sentences",
    "confidence": 0.0-1.0,
    "disclaimer": "AI-suggested analysis. Verify with official trade statistics."
}}"""
        
        response = model.generate_content(prompt)
        return _extract_json(response.text)
    
    @staticmethod
    def analyze_brand(brand_name: str) -> dict:
        """
        Brand & supply chain intelligence.
        For any brand: raw materials, suppliers, distributors, agencies.
        """
        model = _get_model()
        prompt = f"""You are an expert in global supply chains and brand intelligence. Analyze the following brand.

Brand: {brand_name}

Respond in this exact JSON format:
{{
    "brand": "{brand_name}",
    "parent_company": "Company Name",
    "headquarters": "Country",
    "product_categories": ["category1", "category2"],
    "raw_materials": [
        {{
            "material": "Material Name",
            "typical_source_countries": ["Country1", "Country2"],
            "estimated_price_range": "$X - $Y per unit"
        }}
    ],
    "official_distributors": [
        {{
            "company": "Distributor Name",
            "region": "Region/Country",
            "website": "URL if known",
            "contact_type": "official/authorized"
        }}
    ],
    "manufacturing_locations": ["Country1", "Country2"],
    "key_competitors": ["Brand1", "Brand2"],
    "market_position": "description",
    "confidence": 0.0-1.0,
    "disclaimer": "AI-generated intelligence. Company details should be verified independently."
}}"""
        
        response = model.generate_content(prompt)
        return _extract_json(response.text)
    
    @staticmethod
    def analyze_shipping(product: str, origin: str, destination: str) -> dict:
        """
        Shipping cost estimation and compliance.
        """
        model = _get_model()
        prompt = f"""You are an expert in international logistics and trade compliance. Estimate shipping details for:

Product: {product}
Origin Country: {origin}
Destination Country: {destination}

Respond in this exact JSON format:
{{
    "product": "{product}",
    "origin": "{origin}",
    "destination": "{destination}",
    "shipping_methods": [
        {{
            "method": "Sea Freight / Air Freight / Road",
            "estimated_cost_per_kg": "$X - $Y",
            "transit_time": "X-Y days",
            "recommended_for": "description"
        }}
    ],
    "import_duties": {{
        "estimated_tariff_rate": "X%",
        "hs_code_suggestion": "XXXX.XX",
        "notes": "any special conditions"
    }},
    "required_documents": ["Document1", "Document2"],
    "restrictions": ["any known restrictions"],
    "official_reference": "link to official customs authority if known",
    "confidence": 0.0-1.0,
    "disclaimer": "Estimates based on general trade data. Verify with licensed customs broker."
}}"""
        
        response = model.generate_content(prompt)
        return _extract_json(response.text)
    
    @staticmethod
    def scan_business_card(image_bytes: bytes) -> dict:
        """
        Vision: Extract contact info from business card image.
        """
        model = _get_model("gemini-2.5-flash")
        
        prompt = """Extract all contact information from this business card image.

Respond in this exact JSON format:
{
    "name": "Full Name",
    "company": "Company Name",
    "position": "Job Title",
    "phone": "Phone Number",
    "email": "Email Address",
    "website": "Website URL",
    "linkedin": "LinkedIn URL if visible",
    "address": "Physical Address if visible",
    "confidence": 0.0-1.0
}"""
        
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        return _extract_json(response.text)

    @staticmethod
    def scan_business_card_enhanced(image_bytes: bytes) -> dict:
        """
        Enhanced Vision: Extract contact info with per-field confidence.
        Used by D2 async vision pipeline.
        """
        model = _get_model("gemini-2.5-flash")

        prompt = """Extract all contact information from this business card image.
Analyze each field carefully and rate your confidence for each extraction.

Respond in this exact JSON format:
{
    "name": "Full Name",
    "company": "Company Name",
    "position": "Job Title",
    "phone": "Phone Number (with country code if visible)",
    "email": "Email Address",
    "website": "Website URL",
    "linkedin": "LinkedIn URL if visible",
    "address": "Physical Address if visible",
    "confidence": 0.0-1.0,
    "field_confidence": {
        "name": 0.0-1.0,
        "company": 0.0-1.0,
        "phone": 0.0-1.0,
        "email": 0.0-1.0
    }
}

Rules:
- If a field is not visible, set it to empty string and confidence to 0.0
- confidence is the overall confidence across all fields
- field_confidence rates each key field individually
- Always include country code for phone if visible on card"""

        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        return _extract_json(response.text)
    
    @staticmethod
    def generate_insights(data_summary: str) -> dict:
        """
        AI Brain: Generate insights from stored data.
        """
        model = _get_model()
        prompt = f"""You are an AI trade advisor. Based on the following data summary, generate actionable insights.

Data Summary:
{data_summary}

Respond in this exact JSON format:
{{
    "insights": [
        {{
            "type": "opportunity/risk/recommendation",
            "title": "Short title",
            "description": "2-3 sentences",
            "priority": "high/medium/low",
            "suggested_action": "Specific next step"
        }}
    ],
    "overall_assessment": "Brief market assessment",
    "confidence": 0.0-1.0,
    "disclaimer": "AI-generated insights. Business decisions should consider multiple data sources."
}}"""
        
        response = model.generate_content(prompt)
        return _extract_json(response.text)

    @staticmethod
    def analyze_audio(audio_file) -> dict:
        """
        Voice Intelligence: Analyze uploaded audio for transcript, sentiment, intent, and action items.
        Uses Gemini File Upload API for audio processing.
        """
        import tempfile
        import os
        import time
        
        model = _get_model("gemini-2.5-flash")
        
        # Save to temp file for upload
        suffix = ".wav"
        if hasattr(audio_file, 'filename') and audio_file.filename:
            ext = os.path.splitext(audio_file.filename)[1]
            if ext in ['.mp3', '.m4a', '.wav', '.ogg', '.webm']:
                suffix = ext
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = audio_file.file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        start_time = time.time()
        
        try:
            # Upload to Gemini
            uploaded = genai.upload_file(path=tmp_path)
            
            prompt = """You are analyzing a sales/business phone call or voice note.
Listen carefully and provide a structured analysis.

Respond in this exact JSON format:
{
    "transcript": "Full verbatim transcript of the audio",
    "sentiment": "POSITIVE or NEUTRAL or NEGATIVE",
    "intent": "Primary intent (e.g. Purchase Inquiry, Follow-up, Complaint, Negotiation, Information Request)",
    "action_items": ["Specific action item 1", "Specific action item 2"],
    "key_topics": ["Topic 1", "Topic 2"],
    "urgency": "high/medium/low",
    "confidence": 0.0-1.0,
    "disclaimer": "AI-generated analysis. Verify critical details before acting."
}"""
            
            response = model.generate_content([prompt, uploaded])
            processing_time = time.time() - start_time
            
            result = _extract_json(response.text)
            result["processing_time_seconds"] = round(processing_time, 2)
            return result
            
        finally:
            # Cleanup temp file
            try:
                os.unlink(tmp_path)
            except:
                pass


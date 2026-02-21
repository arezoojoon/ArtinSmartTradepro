"""
Hunter Phase 4 Enrichment Engine
Adapter interface + web_basic enrichment provider
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import re
import httpx
import asyncio
from datetime import datetime

from ..models.hunter_phase4 import HunterLead, HunterLeadIdentity, HunterEvidence
from ..services.hunter_repository import HunterRepository

@dataclass
class EnrichmentResult:
    """Result from enrichment provider"""
    updates: Dict[str, Any]  # Field updates for lead
    identities: List[Dict[str, str]]  # New identities to add
    evidence: List[Dict[str, Any]]  # New evidence items

class EnrichmentProvider(ABC):
    """Abstract base class for enrichment providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def enrich(self, lead: HunterLead, repo: HunterRepository) -> EnrichmentResult:
        """
        Enrich a lead with additional data
        
        Args:
            lead: The lead to enrich
            repo: Repository for database operations
            
        Returns:
            EnrichmentResult with updates, identities, and evidence
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get provider name"""
        pass

class WebBasicProvider(EnrichmentProvider):
    """
    Basic web enrichment provider
    Extracts emails, phones, company info from website HTML
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.timeout = config.get('timeout', 10)
        self.max_size = config.get('max_size', 5 * 1024 * 1024)  # 5MB
        self.user_agent = config.get('user_agent', 'ArtinHunter/1.0')
        self.rate_limit_delay = config.get('rate_limit_delay', 5)  # seconds
    
    def get_name(self) -> str:
        return "web_basic"
    
    async def enrich(self, lead: HunterLead, repo: HunterRepository) -> EnrichmentResult:
        """Enrich lead by scraping their website"""
        if not lead.website:
            return EnrichmentResult(updates={}, identities=[], evidence=[])
        
        # Normalize URL
        website_url = self._normalize_url(lead.website)
        if not website_url:
            return EnrichmentResult(updates={}, identities=[], evidence=[])
        
        try:
            # Rate limiting - check Redis for last request to this domain
            domain = urlparse(website_url).netloc
            # TODO: Implement Redis rate limiting
            # For now, just add a delay
            await asyncio.sleep(self.rate_limit_delay)
            
            # Fetch HTML
            html_content = await self._fetch_html(website_url)
            if not html_content:
                return EnrichmentResult(updates={}, identities=[], evidence=[])
            
            # Extract data
            result = EnrichmentResult(updates={}, identities=[], evidence=[])
            
            # Extract emails
            emails = self._extract_emails(html_content)
            for email in emails:
                result.identities.append({"type": "email", "value": email})
                result.evidence.append({
                    "field_name": "email",
                    "source_name": "web_scrape",
                    "source_url": website_url,
                    "confidence": 0.7,
                    "snippet": email,
                    "collected_at": datetime.utcnow()
                })
            
            # Extract phones
            phones = self._extract_phones(html_content)
            for phone in phones:
                result.identities.append({"type": "phone", "value": phone})
                result.evidence.append({
                    "field_name": "phone",
                    "source_name": "web_scrape",
                    "source_url": website_url,
                    "confidence": 0.6,
                    "snippet": phone,
                    "collected_at": datetime.utcnow()
                })
            
            # Extract social links
            social_links = self._extract_social_links(html_content, website_url)
            for social_type, url in social_links.items():
                result.identities.append({"type": social_type, "value": url})
                result.evidence.append({
                    "field_name": social_type,
                    "source_name": "web_scrape",
                    "source_url": website_url,
                    "confidence": 0.8,
                    "snippet": url,
                    "collected_at": datetime.utcnow()
                })
            
            # Extract company name hints (store as evidence only, don't override primary_name)
            company_hints = self._extract_company_hints(html_content)
            for hint in company_hints:
                result.evidence.append({
                    "field_name": "company_name_hint",
                    "source_name": "web_scrape",
                    "source_url": website_url,
                    "confidence": 0.5,
                    "snippet": hint,
                    "collected_at": datetime.utcnow()
                })
            
            # Extract industry hints
            industry_hints = self._extract_industry_hints(html_content)
            for hint in industry_hints:
                result.evidence.append({
                    "field_name": "industry_hint",
                    "source_name": "web_scrape",
                    "source_url": website_url,
                    "confidence": 0.4,
                    "snippet": hint,
                    "collected_at": datetime.utcnow()
                })
            
            return result
            
        except Exception as e:
            # Log error but don't crash
            print(f"WebBasicProvider error for {website_url}: {str(e)}")
            return EnrichmentResult(updates={}, identities=[], evidence=[])
    
    def _normalize_url(self, url: str) -> Optional[str]:
        """Normalize and validate URL"""
        if not url:
            return None
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return None
            return url
        except Exception:
            return None
    
    async def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL"""
        try:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()
                
                # Check content length
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.max_size:
                    return None
                
                content = response.text
                if len(content.encode('utf-8')) > self.max_size:
                    return None
                
                return content
                
        except Exception as e:
            print(f"Failed to fetch {url}: {str(e)}")
            return None
    
    def _extract_emails(self, html: str) -> List[str]:
        """Extract email addresses from HTML"""
        # Common email regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, html, re.IGNORECASE)
        
        # Filter out common false positives
        false_positives = {
            'example.com', 'test.com', 'domain.com', 'email.com',
            'yourcompany.com', 'company.com', 'sample.com'
        }
        
        filtered_emails = []
        for email in emails:
            domain = email.split('@')[1].lower()
            if domain not in false_positives and not domain.startswith('www.'):
                filtered_emails.append(email.lower())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_emails = []
        for email in filtered_emails:
            if email not in seen:
                seen.add(email)
                unique_emails.append(email)
        
        return unique_emails[:5]  # Limit to 5 emails
    
    def _extract_phones(self, html: str) -> List[str]:
        """Extract phone numbers from HTML"""
        # Basic phone patterns (US and international)
        patterns = [
            r'\+?1?-?\s*\(?([0-9]{3})\)?\s*[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',  # US format
            r'\+?([0-9]{1,3})\s*[-.\s]?([0-9]{1,4})\s*[-.\s]?([0-9]{1,4})\s*[-.\s]?([0-9]{1,9})',  # International
        ]
        
        phones = []
        for pattern in patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                if isinstance(match, tuple):
                    phone = ''.join(match)
                else:
                    phone = match
                
                # Basic normalization
                phone = re.sub(r'[^\d+]', '', phone)
                if len(phone) >= 10:  # Minimum length for a phone number
                    # Add + if missing and starts with country code
                    if not phone.startswith('+') and len(phone) >= 11:
                        phone = '+' + phone
                    phones.append(phone)
        
        # Remove duplicates
        seen = set()
        unique_phones = []
        for phone in phones:
            if phone not in seen:
                seen.add(phone)
                unique_phones.append(phone)
        
        return unique_phones[:3]  # Limit to 3 phone numbers
    
    def _extract_social_links(self, html: str, base_url: str) -> Dict[str, str]:
        """Extract social media links"""
        social_patterns = {
            'linkedin': r'linkedin\.com/(?:company|in)/[a-zA-Z0-9-]+',
            'instagram': r'instagram\.com/[a-zA-Z0-9_.-]+',
            'twitter': r'twitter\.com/[a-zA-Z0-9_]+',
            'facebook': r'facebook\.com/[a-zA-Z0-9.]+',
        }
        
        social_links = {}
        
        for social_type, pattern in social_patterns.items():
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                # Reconstruct full URL
                if social_type == 'linkedin':
                    url = f"https://www.linkedin.com/{match}"
                else:
                    url = f"https://www.{social_type}.com/{match}"
                
                social_links[social_type] = url
                break  # Take first match only
        
        return social_links
    
    def _extract_company_name_hints(self, html: str) -> List[str]:
        """Extract potential company names from title/meta tags"""
        hints = []
        
        # Extract from title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            # Remove common suffixes
            title = re.sub(r'\s*[-|]\s*(home|about|contact|welcome).*$', '', title, flags=re.IGNORECASE)
            if len(title) > 3 and len(title) < 100:
                hints.append(title)
        
        # Extract from meta tags
        meta_patterns = [
            r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+name=["\']author["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+name=["\']organization["\'][^>]+content=["\']([^"\']+)["\']',
        ]
        
        for pattern in meta_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if len(match) > 3 and len(match) < 100:
                    hints.append(match.strip())
        
        return hints[:3]  # Limit to 3 hints
    
    def _extract_industry_hints(self, html: str) -> List[str]:
        """Extract industry keywords from content"""
        industry_keywords = [
            'technology', 'software', 'manufacturing', 'retail', 'healthcare',
            'finance', 'banking', 'insurance', 'consulting', 'education',
            'construction', 'real estate', 'logistics', 'transportation',
            'agriculture', 'food', 'beverage', 'automotive', 'aerospace',
            'pharmaceutical', 'biotechnology', 'telecommunications',
            'energy', 'utilities', 'mining', 'chemical', 'textile'
        ]
        
        found_keywords = []
        html_lower = html.lower()
        
        for keyword in industry_keywords:
            # Look for keyword in common contexts
            patterns = [
                rf'\b{keyword}\s+(company|corporation|inc|llc|ltd|gmbh)',
                rf'\b(we|our|company)\s+(are|is|specialize\s+in)\s+{keyword}',
                rf'\b{keyword}\s+(industry|sector|business|solutions)',
            ]
            
            for pattern in patterns:
                if re.search(pattern, html_lower):
                    found_keywords.append(keyword.title())
                    break
        
        return found_keywords[:2]  # Limit to 2 industry hints
class AIInferenceProvider(EnrichmentProvider):
    """
    Advanced AI enrichment provider using Gemini LLM.
    Infers decision makers and deep intelligence from scraped text.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_text_len = config.get('max_text_len', 10000)
    
    def get_name(self) -> str:
        return "ai_inference"
    
    async def enrich(self, lead: HunterLead, repo: HunterRepository) -> EnrichmentResult:
        from .gemini_service import GeminiService
        
        # 1. Gather existing evidence text
        evidence_texts = [e.snippet for e in lead.evidence if e.snippet]
        combined_text = "\n---\n".join(evidence_texts)
        
        if len(combined_text) < 50:
             # Not enough data to infer
             return EnrichmentResult(updates={}, identities=[], evidence=[])
             
        current_data = {
            "name": lead.primary_name,
            "website": lead.website,
            "country": lead.country,
            "industry": lead.industry
        }
        
        try:
            inference = await GeminiService.infer_lead_details_async(combined_text, current_data)
            
            result = EnrichmentResult(updates={}, identities=[], evidence=[])
            
            # Decision Maker Updates
            dm = inference.get("decision_maker", {})
            if dm.get("name") and dm.get("name") != "Full Name":
                result.updates["primary_name"] = dm["name"]
                result.updates["industry"] = inference.get("company_profile", {}).get("industry", lead.industry)
            
            # Identities
            for identity in inference.get("identities", []):
                if identity.get("value") and identity["value"] != "extracted value":
                    result.identities.append({
                        "type": identity["type"],
                        "value": identity["value"]
                    })
            
            # Evidence Panel
            for ev in inference.get("evidence_panel", []):
                result.evidence.append({
                    "field_name": ev.get("field", "ai_inference"),
                    "source_name": "ai_inference",
                    "confidence": 0.85,
                    "snippet": ev.get("snippet"),
                    "collected_at": datetime.utcnow(),
                    "raw": inference
                })
                
            return result
            
        except Exception as e:
            logger.error(f"AIInferenceProvider failed: {e}")
            return EnrichmentResult(updates={}, identities=[], evidence=[])

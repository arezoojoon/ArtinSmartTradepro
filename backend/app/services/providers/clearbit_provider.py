"""
Clearbit Provider (Skeleton)
Disabled by default - requires CLEARBIT_API_KEY
"""
from typing import Dict, Any
from ..hunter_enrichment import EnrichmentProvider, EnrichmentResult
from ..hunter_provider_registry import NotConfiguredProviderError, DisabledProviderError
from ...models.hunter_phase4 import HunterLead
from ...services.hunter_repository import HunterRepository
import httpx

class ClearbitProvider(EnrichmentProvider):
    """
    Clearbit API provider for company enrichment
    NOTE: Disabled by default, requires CLEARBIT_API_KEY
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key', '')
        self.timeout = config.get('timeout', 15)
        
        # Check if properly configured
        if not self.api_key:
            raise NotConfiguredProviderError("Clearbit provider requires CLEARBIT_API_KEY")
    
    def get_name(self) -> str:
        return "clearbit"
    
    async def enrich(self, lead: HunterLead, repo: HunterRepository) -> EnrichmentResult:
        """Enrich lead using Clearbit API"""
        # This is a skeleton - actual implementation would call Clearbit API
        # For now, return empty result to show it's properly configured but not implemented
        
        # Example of what would be implemented:
        # 1. Use domain from lead.website to call Clearbit's Company API
        # 2. Extract company info, employee count, industry, etc.
        # 3. Return structured data as EnrichmentResult
        
        return EnrichmentResult(
            updates={},
            identities=[],
            evidence=[{
                "field_name": "clearbit_status",
                "source_name": "clearbit",
                "source_url": None,
                "confidence": 1.0,
                "snippet": "Provider configured but not implemented",
                "collected_at": datetime.utcnow()
            }]
        )

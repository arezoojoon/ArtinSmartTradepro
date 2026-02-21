"""
Hunter Phase 4 Provider Registry
Config-driven provider enable/disable system
"""
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import os
from dataclasses import dataclass

from .hunter_enrichment import EnrichmentProvider, EnrichmentResult
from ..models.hunter_phase4 import HunterLead
from ..services.hunter_repository import HunterRepository

@dataclass
class ProviderConfig:
    """Configuration for an enrichment provider"""
    name: str
    enabled: bool
    config: Dict[str, Any]
    description: str

class ProviderRegistry:
    """Registry for managing enrichment providers"""
    
    def __init__(self):
        self._providers: Dict[str, EnrichmentProvider] = {}
        self._configs: Dict[str, ProviderConfig] = {}
        self._load_default_configs()
    
    def _load_default_configs(self):
        """Load default provider configurations from environment"""
        # Web Basic Provider (always enabled)
        self._configs["web_basic"] = ProviderConfig(
            name="web_basic",
            enabled=os.getenv("HUNTER_PROVIDER_WEB_BASIC_ENABLED", "true").lower() == "true",
            config={
                "timeout": int(os.getenv("HUNTER_WEB_BASIC_TIMEOUT", "10")),
                "max_size": int(os.getenv("HUNTER_WEB_BASIC_MAX_SIZE", str(5 * 1024 * 1024))),
                "user_agent": os.getenv("HUNTER_WEB_BASIC_USER_AGENT", "ArtinHunter/1.0"),
                "rate_limit_delay": int(os.getenv("HUNTER_WEB_BASIC_RATE_DELAY", "5"))
            },
            description="Basic web scraping for emails, phones, and social links"
        )
        
        # Clearbit Provider (disabled by default)
        self._configs["clearbit"] = ProviderConfig(
            name="clearbit",
            enabled=os.getenv("HUNTER_PROVIDER_CLEARBIT_ENABLED", "false").lower() == "true",
            config={
                "api_key": os.getenv("CLEARBIT_API_KEY", ""),
                "timeout": int(os.getenv("HUNTER_CLEARBIT_TIMEOUT", "15"))
            },
            description="Clearbit API for company enrichment"
        )
        
        # ImportYeti Provider (disabled by default)
        self._configs["importyeti"] = ProviderConfig(
            name="importyeti",
            enabled=os.getenv("HUNTER_PROVIDER_IMPORTYETI_ENABLED", "false").lower() == "true",
            config={
                "api_key": os.getenv("IMPORTYETI_API_KEY", ""),
                "timeout": int(os.getenv("HUNTER_IMPORTYETI_TIMEOUT", "20"))
            },
            description="ImportYeti API for import/export data"
        )
    
    def register_provider(self, provider: EnrichmentProvider):
        """Register a provider instance"""
        self._providers[provider.get_name()] = provider
    
    def get_provider(self, name: str) -> Optional[EnrichmentProvider]:
        """Get a provider by name if enabled"""
        config = self._configs.get(name)
        if not config or not config.enabled:
            return None
        
        # Lazy load provider if not already loaded
        if name not in self._providers:
            provider = self._create_provider(name)
            if provider:
                self.register_provider(provider)
        
        return self._providers.get(name)
    
    def _create_provider(self, name: str) -> Optional[EnrichmentProvider]:
        """Create provider instance based on name"""
        if name == "web_basic":
            from .hunter_enrichment import WebBasicProvider
            return WebBasicProvider(self._configs[name].config)
        
        elif name == "clearbit":
            from .providers.clearbit_provider import ClearbitProvider
            return ClearbitProvider(self._configs[name].config)
        
        elif name == "importyeti":
            from .providers.importyeti_provider import ImportYetiProvider
            return ImportYetiProvider(self._configs[name].config)
        
        return None
    
    def list_providers(self) -> List[ProviderConfig]:
        """List all provider configurations"""
        return list(self._configs.values())
    
    def get_provider_config(self, name: str) -> Optional[ProviderConfig]:
        """Get configuration for a specific provider"""
        return self._configs.get(name)
    
    def enable_provider(self, name: str) -> bool:
        """Enable a provider"""
        config = self._configs.get(name)
        if config:
            config.enabled = True
            return True
        return False
    
    def disable_provider(self, name: str) -> bool:
        """Disable a provider"""
        config = self._configs.get(name)
        if config:
            config.enabled = False
            # Remove cached provider
            if name in self._providers:
                del self._providers[name]
            return True
        return False

# Global registry instance
registry = ProviderRegistry()

class DisabledProviderError(Exception):
    """Raised when trying to use a disabled provider"""
    pass

class NotConfiguredProviderError(Exception):
    """Raised when provider is enabled but not properly configured"""
    pass

from typing import List, Dict, Any, Optional
import abc
from dataclasses import dataclass, field

@dataclass
class ScraperResult:
    """Standardized result from any scraper."""
    company_name: str = ""
    contact_name: str = ""
    email: str = ""
    phone: str = ""
    country: str = ""
    city: str = ""
    website: str = ""
    brand_name: str = ""
    product_name: str = ""
    price: str = ""
    source: str = ""
    score: int = 0
    raw_data: Dict[str, Any] = field(default_factory=dict)


class BaseScraper(abc.ABC):
    @abc.abstractmethod
    async def scrape(
        self,
        keyword: str,
        location: str = "",
        credentials: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> List[ScraperResult]:
        """
        Execute the scraping strategy.
        
        Args:
            keyword: Search term (product, company, person)
            location: Target country/city
            credentials: Source-specific auth credentials
        """
        pass


class ScraperFactory:
    @staticmethod
    def get_scraper(source: str) -> BaseScraper:
        from app.services.scraper.strategies import (
            GoogleMapsScraper,
            LinkedInScraper,
            TelegramScraper,
            DiscordScraper,
            TradeMapScraper,
            FacebookScraper,
            WebScraper,
        )
        
        strategies = {
            "google_maps": GoogleMapsScraper,
            "linkedin": LinkedInScraper,
            "telegram": TelegramScraper,
            "discord": DiscordScraper,
            "trademap": TradeMapScraper,
            "facebook": FacebookScraper,
            "web": WebScraper,
            # Legacy aliases
            "maps": GoogleMapsScraper,
            "linkedin_serp": LinkedInScraper,
            "social": FacebookScraper,
        }
        
        scraper_class = strategies.get(source)
        if not scraper_class:
            raise ValueError(f"Unknown scraper source: {source}")
            
        return scraper_class()

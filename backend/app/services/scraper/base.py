from typing import List, Dict, Any
import abc

class BaseScraper(abc.ABC):
    @abc.abstractmethod
    async def scrape(self, keyword: str, location: str) -> List[Dict[str, Any]]:
        """
        Execute the scraping strategy.
        """
        pass

class ScraperFactory:
    @staticmethod
    def get_scraper(source: str) -> BaseScraper:
        # Import strategies lazily to avoid circular imports
        from app.services.scraper.strategies import (
            GoogleMapsScraper,
            LinkedInSERPScraper,
            TradeMapScraper,
            SocialMediaScraper,
            WebsiteScraper,
            ReviewScraper,
            IntentScraper,
            CompetitorScraper,
            PDFScraper,
            ReverseImageScraper
        )
        
        strategies = {
            "maps": GoogleMapsScraper,
            "linkedin_serp": LinkedInSERPScraper,
            "trademap": TradeMapScraper,
            "social": SocialMediaScraper,
            "website": WebsiteScraper,
            "reviews": ReviewScraper,
            "intent": IntentScraper,
            "competitors": CompetitorScraper,
            "pdfs": PDFScraper,
            "reverse_image": ReverseImageScraper
        }
        
        scraper_class = strategies.get(source)
        if not scraper_class:
            raise ValueError(f"Unknown scraper source: {source}")
            
        return scraper_class()

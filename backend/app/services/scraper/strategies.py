from typing import List, Dict, Any
from app.services.scraper.base import BaseScraper
import asyncio

class MockScraper(BaseScraper):
    async def scrape(self, keyword: str, location: str) -> List[Dict[str, Any]]:
        # Simulate network delay
        await asyncio.sleep(2)
        return [
            {"name": f"Mock Lead {i}", "source": self.__class__.__name__, "keyword": keyword}
            for i in range(1, 4)
        ]

class GoogleMapsScraper(MockScraper): pass
class LinkedInSERPScraper(MockScraper): pass
class TradeMapScraper(MockScraper): pass
class SocialMediaScraper(MockScraper): pass
class WebsiteScraper(MockScraper): pass
class ReviewScraper(MockScraper): pass
class IntentScraper(MockScraper): pass
class CompetitorScraper(MockScraper): pass
class PDFScraper(MockScraper): pass
class ReverseImageScraper(MockScraper): pass

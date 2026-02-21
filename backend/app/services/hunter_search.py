from typing import List, Dict, Any, Optional
import uuid
import logging
from app.integrations.un_comtrade_client import UNComtradeClient
from app.integrations.trademap import TradeMapClient
from app.services.scraper.base import ScraperFactory

logger = logging.getLogger(__name__)

class HunterSearchService:
    """
    Advanced Lead Discovery Engine.
    Filters by HS Code, Volume, and Growth.
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
        Main discovery orchestrator.
        1. Query Trade APIs for high-potential countries/segments.
        2. Run Scrapers for specific companies in those segments.
        3. Apply filters.
        """
        all_results = []
        
        # 1. Trade Intelligence (UN Comtrade / TradeMap)
        if hs_code and ("un_comtrade" in sources or "trademap" in sources):
            try:
                un_client = UNComtradeClient()
                # Get trade flows for the HS code
                trade_flows = await un_client.get_trade_flows(hs_code)
                
                # Filter importers by volume if requested
                importers = trade_flows.get("top_importers", [])
                for imp in importers:
                    # Simulation: If user provided a specific location, only look at that
                    if location != "Global" and location.upper() not in imp["country"].upper():
                        continue
                        
                    if min_volume_usd and imp["value_usd"] < min_volume_usd:
                        continue
                    
                    # Growth threshold check (requires bilateral or specific growth data)
                    # For now, UNComtrade mock returns growth in share or bilateral trades
                    
                    all_results.append({
                        "source": "un_comtrade",
                        "type": "trade_data",
                        "name": f"Market: {imp['country']}",
                        "country": imp["country"],
                        "raw_data": imp,
                        "confidence_score": 0.9
                    })

                # If TradeMap is selected, get specific companies
                if "trademap" in sources:
                    tm_client = TradeMapClient()
                    tm_companies = await tm_client.get_companies(keyword, location)
                    for comp in tm_companies:
                        all_results.append({
                            "source": "trademap",
                            "type": "company",
                            "name": comp["name"],
                            "company": comp["name"],
                            "country": comp["country"],
                            "website": comp.get("website"),
                            "raw_data": comp,
                            "confidence_score": 0.8
                        })
            except Exception as e:
                logger.error(f"Trade Intelligence failed: {e}")

        # 2. Scraper Discovery (Maps, LinkedIn, etc.)
        scraper_sources = [s for s in sources if s not in ("un_comtrade", "trademap", "freight")]
        for src in scraper_sources:
            try:
                scraper = ScraperFactory.get_scraper(src)
                scraped_data = await scraper.scrape(keyword, location)
                for item in scraped_data:
                    all_results.append({
                        "source": src,
                        "type": "lead",
                        "name": item.get("name") or item.get("title"),
                        "company": item.get("company") or item.get("name"),
                        "country": location,
                        "website": item.get("website"),
                        "raw_data": item,
                        "confidence_score": 0.7
                    })
            except Exception as e:
                logger.error(f"Scraper {src} failed: {e}")

        return all_results

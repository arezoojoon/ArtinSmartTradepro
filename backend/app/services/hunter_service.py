from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid
import datetime
import logging

from app.models.hunter import HunterRun, HunterResult, TradeSignal
from app.models.ai_job import AIJob
from app.models.crm import CRMContact, CRMCompany
from app.services.scraper.base import ScraperFactory
from app.integrations.uncomtrade import UNComtradeClient
from app.integrations.trademap import TradeMapClient
from app.integrations.freight import FreightClient
from app.integrations.fx import RXClient
from app.integrations.weather import WeatherClient
from app.integrations.political import PoliticalRiskClient

logger = logging.getLogger(__name__)

class HunterService:
    """
    Orchestrates data collection from Scrapers (Leads) and Official APIs (Signals).
    """

    @staticmethod
    def _get_integration_client(source: str):
        if source == "un_comtrade": return UNComtradeClient()
        if source == "trademap": return TradeMapClient()
        if source == "freight": return FreightClient()
        if source == "fx": return RXClient()
        if source == "weather": return WeatherClient()
        if source == "political": return PoliticalRiskClient()
        return None

    @staticmethod
    async def run_hunter_job(
        db: Session,
        job_id: uuid.UUID,
        tenant_id: uuid.UUID,
        keyword: str,
        location: str,
        sources: List[str]
    ):
        """
        Async worker function to execute a Hunter Job.
        1. Create HunterRun record.
        2. Iterate sources.
        3. Fetch data (Scraper or API).
        4. Save results.
        5. Update Job status.
        """
        logger.info(f"Starting Hunter Job {job_id} for tenant {tenant_id}")
        
        # 1. Create Run Record
        run = HunterRun(
            tenant_id=tenant_id,
            job_id=job_id,
            target_keyword=keyword,
            target_location=location,
            sources=sources,
            status="processing"
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        total_leads = 0
        
        try:
            # Initialize Clients
            from app.integrations.uncomtrade import UNComtradeClient
            from app.integrations.trademap import TradeMapClient
            from app.integrations.freight import FreightClient
            from app.integrations.fx import FXClient
            from app.integrations.political import PoliticalRiskClient

            results = []
            
            # 1. Trade Data (UN Comtrade / TradeMap)
            if "un_comtrade" in sources or "trademap" in sources:
                try:
                    # Mock HS Code lookup for keyword
                    hs_code = "1006.30" if "rice" in keyword.lower() else "8517.12"
                    
                    if "un_comtrade" in sources:
                        un_client = UNComtradeClient()
                        trade_data = await un_client.get_top_importers(hs_code)
                        for item in trade_data:
                            results.append({
                                "source": "un_comtrade",
                                "type": "trade_flow",
                                "title": f"Top Importer: {item['country']}",
                                "company": "N/A",
                                "country": item['country'],
                                "details": item
                            })

                    if "trademap" in sources:
                        tm_client = TradeMapClient()
                        companies = await tm_client.get_companies(keyword, location)
                        for comp in companies:
                            results.append({
                                "source": "trademap",
                                "type": "company",
                                "title": comp["name"],
                                "company": comp["name"],
                                "country": comp["country"],
                                "website": comp.get("website"),
                                "details": comp
                            })
                except Exception as e:
                    logger.error(f"Trade Data Error: {e}")

            # 2. Logistics & Risk (Freight, FX, Political)
            if "freight" in sources:
                try:
                    f_client = FreightClient()
                    # Mock route based on location
                    origin = "Shanghai, China"
                    dest = location if location != "Global" else "Hamburg, Germany"
                    rates = await f_client.get_rates(origin, dest)
                    results.append({
                        "source": "freight",
                        "type": "logistics",
                        "title": f"Freight: {origin} -> {dest}",
                        "details": rates
                    })
                except Exception as e:
                    logger.error(f"Freight Error: {e}")

            if "political_risk" in sources:
                try:
                    pr_client = PoliticalRiskClient()
                    target = location if location != "Global" else "Iran"
                    risk = await pr_client.get_risk_score(target)
                    results.append({
                        "source": "political_risk",
                        "type": "risk",
                        "title": f"Risk Score: {target}",
                        "details": risk
                    })
                except Exception as e:
                    logger.error(f"Risk Error: {e}")

            # 3. Existing Scraper Logic
            for source in sources:
                # Skip if already handled above
                if source in ("un_comtrade", "trademap", "freight", "political_risk", "fx"):
                    continue

                try:
                    scraper = ScraperFactory.get_scraper(source)
                    scraped_data = await scraper.scrape(keyword, location)
                    for item in scraped_data:
                         results.append({
                            "source": source,
                            "type": "lead",
                            "title": item.get("title") or item.get("name"),
                            "company": item.get("company"),
                            "details": item
                         })
                except Exception as scraper_err:
                    logger.error(f"Scraper {source} failed: {scraper_err}")

            # Persist Results
            for item in results:
                res = HunterResult(
                    run_id=run.id,
                    tenant_id=tenant_id,
                    source=item.get("source", "unknown"),
                    type=item.get("type", "lead"),
                    name=item.get("title") or item.get("name"),
                    company=item.get("company"),
                    email=item.get("details", {}).get("email"),
                    phone=item.get("details", {}).get("phone"),
                    website=item.get("details", {}).get("website"),
                    country=item.get("details", {}).get("country"),
                    raw_data=item.get("details", item),
                    confidence_score=0.85
                )
                db.add(res)
                total_leads += 1
            
            # Update Run
            run.status = "completed"
            run.leads_found = total_leads
            run.completed_at = datetime.datetime.utcnow()
            
            # Update AIJob
            job = db.query(AIJob).get(job_id)
            if job:
                job.status = "completed"
                job.completed_at = datetime.datetime.utcnow()
            
            db.commit()
            logger.info(f"Hunter Job {job_id} completed. Found {total_leads} items.")

        except Exception as e:
            logger.error(f"Hunter Job {job_id} failed: {e}")
            run.status = "failed"
            job = db.query(AIJob).get(job_id)
            if job:
                job.status = "failed"
                job.error_message = str(e)
            db.commit()

    @staticmethod
    def import_result_to_crm(db: Session, result_id: uuid.UUID, user_id: uuid.UUID) -> CRMContact:
        """
        Convert a HunterResult into a CRMContact/Company
        """
        result = db.query(HunterResult).get(result_id)
        if not result:
            raise ValueError("Result not found")
        
        if result.is_imported:
            raise ValueError("Already imported")

        # 1. Create/Find Company
        company_id = None
        if result.company:
            # Check exist
            existing = db.query(CRMCompany).filter(
                CRMCompany.tenant_id == result.tenant_id,
                CRMCompany.name == result.company
            ).first()
            if existing:
                company_id = existing.id
            else:
                new_comp = CRMCompany(
                    tenant_id=result.tenant_id,
                    name=result.company,
                    website=result.website,
                    owner_id=user_id,
                    source=f"Hunter: {result.source}"
                )
                db.add(new_comp)
                db.flush()
                company_id = new_comp.id
        
        # 2. Create Contact
        contact = CRMContact(
            tenant_id=result.tenant_id,
            company_id=company_id,
            first_name=result.name.split(" ")[0] if result.name else "Unknown",
            last_name=" ".join(result.name.split(" ")[1:]) if result.name and " " in result.name else "",
            email=result.email,
            phone=result.phone,
            owner_id=user_id,
            source=f"Hunter: {result.source}",
            lead_score=int(result.confidence_score * 100) if result.confidence_score else 50
        )
        db.add(contact)
        
        # 3. Mark imported
        result.is_imported = True
        db.commit()
        db.refresh(contact)
        return contact

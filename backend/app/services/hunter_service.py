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
            for source in sources:
                # A) Check if it's an Official API integration
                api_client = HunterService._get_integration_client(source)
                if api_client:
                    # Fetch Macro Data
                    data = await api_client.fetch_data() # Arguments would need mapping in real scenario
                    # Save as TradeSignal (Global or Tenant scoped?)
                    # For this implementation, we save as HunterResult type="trade_data"
                    for item in data:
                        res = HunterResult(
                            run_id=run.id,
                            tenant_id=tenant_id,
                            source=source,
                            type="trade_data",
                            raw_data=item,
                            confidence_score=1.0
                        )
                        db.add(res)
                    total_leads += len(data)

                # B) Otherwise, treat as Scraper (Leads)
                else:
                    try:
                        scraper = ScraperFactory.get_scraper(source)
                        results = await scraper.scrape(keyword, location)
                        snythesized_results = []
                        
                        for item in results:
                            # Normalize scraper output to HunterResult
                            res = HunterResult(
                                run_id=run.id,
                                tenant_id=tenant_id,
                                source=source,
                                type="lead", # Simplification
                                name=item.get("title") or item.get("name"),
                                company=item.get("company"),
                                email=item.get("email"),
                                phone=item.get("phone"),
                                website=item.get("website"),
                                address=item.get("address"),
                                raw_data=item,
                                confidence_score=0.8 # Mock score
                            )
                            db.add(res)
                            snythesized_results.append(res)
                        total_leads += len(results)
                    except Exception as scraper_err:
                        logger.error(f"Scraper {source} failed: {scraper_err}")
            
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

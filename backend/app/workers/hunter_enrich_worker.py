"""
Hunter Phase 4 Enrichment Worker
Processes enrichment jobs from the queue
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.services.hunter_repository import HunterRepository
from app.services.hunter_enrichment import WebBasicProvider, EnrichmentResult
from app.models.hunter_phase4 import HunterEnrichmentJob
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HunterEnrichmentWorker:
    """Worker for processing Hunter enrichment jobs"""
    
    def __init__(self):
        self.providers = {
            "web_basic": WebBasicProvider({
                "timeout": 10,
                "max_size": 5 * 1024 * 1024,
                "user_agent": "ArtinHunter/1.0",
                "rate_limit_delay": 5
            })
        }
    
    async def run_worker(self, db_session: Session):
        """Run the worker - process pending jobs"""
        repo = HunterRepository(db_session)
        
        while True:
            try:
                # Get pending jobs
                jobs = repo.get_pending_enrichment_jobs(limit=5)
                
                if not jobs:
                    # No jobs, wait before checking again
                    await asyncio.sleep(10)
                    continue
                
                logger.info(f"Found {len(jobs)} enrichment jobs to process")
                
                for job in jobs:
                    await self.process_job(db_session, repo, job)
                
                # Small delay between batches
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
                await asyncio.sleep(30)  # Wait longer on error
    
    async def process_job(self, db_session: Session, repo: HunterRepository, job: HunterEnrichmentJob):
        """Process a single enrichment job"""
        logger.info(f"Processing job {job.id} for lead {job.lead_id} with provider {job.provider}")
        
        # Update job status to running
        repo.update_job_status(job.tenant_id, job.id, "running")
        
        try:
            # Get the provider
            provider = self.providers.get(job.provider)
            if not provider:
                raise ValueError(f"Provider '{job.provider}' not found")
            
            # Get the lead
            lead = repo.get_lead_with_details(job.tenant_id, job.lead_id)
            if not lead:
                raise ValueError(f"Lead {job.lead_id} not found")
            
            # Run enrichment
            result = await provider.enrich(lead, repo)
            
            # Apply results
            evidence_added = 0
            
            # Add identities
            for identity in result.identities:
                repo.attach_identity(
                    tenant_id=job.tenant_id,
                    lead_id=job.lead_id,
                    type=identity["type"],
                    value=identity["value"]
                )
            
            # Add evidence
            for evidence_item in result.evidence:
                repo.attach_evidence(
                    tenant_id=job.tenant_id,
                    lead_id=job.lead_id,
                    field_name=evidence_item["field_name"],
                    source_name=evidence_item["source_name"],
                    source_url=evidence_item.get("source_url"),
                    confidence=evidence_item["confidence"],
                    snippet=evidence_item.get("snippet"),
                    collected_at=evidence_item["collected_at"],
                    raw=evidence_item.get("raw")
                )
                evidence_added += 1
            
            # Update lead status if evidence was added
            if evidence_added > 0:
                repo.update_lead_status(job.tenant_id, job.lead_id, "enriched")
            
            # Mark job as done
            repo.update_job_status(job.tenant_id, job.id, "done")
            
            logger.info(f"Job {job.id} completed successfully. Added {evidence_added} evidence items")
            
        except Exception as e:
            logger.error(f"Job {job.id} failed: {str(e)}")
            
            # Update job status to failed
            repo.update_job_status(
                job.tenant_id, 
                job.id, 
                "failed", 
                error={"message": str(e), "type": type(e).__name__}
            )

async def main():
    """Main worker entry point"""
    logger.info("Starting Hunter Enrichment Worker")
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        worker = HunterEnrichmentWorker()
        await worker.run_worker(db)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())

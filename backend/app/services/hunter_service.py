from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
import uuid
import datetime
import logging

from app.models.hunter import HunterRun, HunterResult, TradeSignal
from app.models.ai_job import AIJob
from app.models.crm import CRMContact, CRMCompany

logger = logging.getLogger(__name__)

class HunterService:
    """
    Orchestrates lead discovery via Gemini AI and imports results to CRM.
    """

    @staticmethod
    async def run_hunter_job(
        job_id: uuid.UUID,
        tenant_id: uuid.UUID,
        keyword: str,
        location: str,
        sources: List[str],
        hs_code: Optional[str] = None,
        min_volume_usd: Optional[float] = None,
        min_growth_pct: Optional[float] = None
    ):
        """
        Async worker function to execute a Hunter Job.
        """
        from app.db.session import AsyncSessionLocal as async_session_maker
        from app.services.hunter_search import HunterSearchService
        
        async with async_session_maker() as db:
            try:
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
                await db.commit()
                await db.refresh(run)

                # 2. Advanced Discovery
                results = await HunterSearchService.discover_leads(
                    tenant_id=tenant_id,
                    keyword=keyword,
                    location=location,
                    sources=sources,
                    hs_code=hs_code,
                    min_volume_usd=min_volume_usd,
                    min_growth_pct=min_growth_pct
                )

                total_leads = 0
                
                try:
                    # Persist Results
        
                    from app.services.hunter_scoring import HunterScoringEngine
                    from app.services.hunter_repository import HunterRepository
                    from app.services.hunter_enrichment import AIInferenceProvider
                    
                    repo = HunterRepository(db)
                    scorer = HunterScoringEngine(repo)
                    enricher = AIInferenceProvider({"max_text_len": 10000})

                    # Persist & Process Results
                    for item in results:
                        # Simulation of real-time scoring for the 'vaghei' requirement
                        # In Phase 4, scoring usually happens on HunterLead, but we'll apply it to Results too.
                        
                        score_val = 0.8 # Default
                        if hs_code and item.get("source") == "un_comtrade":
                             score_val = 0.95 # Direct matching data
                        elif item.get("website") or item.get("raw_data", {}).get("email"):
                             score_val = 0.85
                             
                        res = HunterResult(
                            run_id=run.id,
                            tenant_id=tenant_id,
                            source=item.get("source", "unknown"),
                            type=item.get("type", "lead"),
                            name=item.get("name"),
                            company=item.get("company"),
                            email=item.get("raw_data", {}).get("email"),
                            phone=item.get("raw_data", {}).get("phone"),
                            website=item.get("website") or item.get("raw_data", {}).get("website"),
                            country=item.get("country") or item.get("raw_data", {}).get("country"),
                            raw_data={
                                **item.get("raw_data", {}),
                                "scoring_version": "3.0",
                                "market_hs_code": hs_code
                            },
                            confidence_score=score_val
                        )
                        db.add(res)
                        total_leads += 1
                    
                    # Update Run
                    run.status = "completed"
                    run.leads_found = total_leads
                    run.completed_at = datetime.datetime.utcnow()
                    
                    # Update AIJob
                    job = (await db.execute(select(AIJob).where(AIJob.id == job_id))).scalar_one_or_none()
                    if job:
                        job.status = "completed"
                        job.completed_at = datetime.datetime.utcnow()
                    
                    await db.commit()
                    logger.info(f"Hunter Job {job_id} completed. Found {total_leads} items.")
        
                except Exception as e:
                    logger.error(f"Hunter Job {job_id} failed logic: {e}")
                    run.status = "failed"
                    job = (await db.execute(select(AIJob).where(AIJob.id == job_id))).scalar_one_or_none()
                    if job:
                        job.status = "failed"
                        job.error_message = str(e)
                    await db.commit()

            except Exception as e:
                logger.error(f"Hunter Job {job_id} totally failed: {e}")
                # Try to clean up or rollback
                try:
                    await db.rollback()
                except:
                    pass

    @staticmethod
    async def import_result_to_crm(db: AsyncSession, result_id: uuid.UUID, user_id: uuid.UUID, tenant_id: uuid.UUID) -> CRMContact:
        """
        Convert a HunterResult into a CRMContact/Company with Deduplication & IDOR protection.
        """
        res = await db.execute(select(HunterResult).where(HunterResult.id == result_id))
        result = res.scalar_one_or_none()
        
        if not result:
            raise ValueError("Result not found")
        
        if str(result.tenant_id) != str(tenant_id):
             raise ValueError("Unauthorized: result belongs to another tenant")

        if result.is_imported:
             pass 

        # 1. Company Deduplication (Domain > Name)
        company_id = None
        if result.company:
            query = select(CRMCompany).where(CRMCompany.tenant_id == tenant_id)
            existing_company = None
            
            if result.website:
                domain_part = result.website.replace("https://", "").replace("http://", "").split("/")[0]
                c_res = await db.execute(query.where(CRMCompany.website.ilike(f"%{domain_part}%")))
                existing_company = c_res.scalar_one_or_none()
            
            if not existing_company:
                c_res = await db.execute(query.where(CRMCompany.name.ilike(result.company)))
                existing_company = c_res.scalar_one_or_none()
            
            if existing_company:
                company_id = existing_company.id
            else:
                new_comp = CRMCompany(
                    tenant_id=tenant_id,
                    name=result.company,
                    website=result.website,
                    industry="Import/Export",
                )
                db.add(new_comp)
                await db.flush()
                company_id = new_comp.id
        
        # 2. Contact Deduplication (Email > Phone)
        query = select(CRMContact).where(CRMContact.tenant_id == tenant_id)
        existing_contact = None
        
        if result.email:
            ct_res = await db.execute(query.where(CRMContact.email == result.email))
            existing_contact = ct_res.scalar_one_or_none()
        
        if not existing_contact and result.phone:
            ct_res = await db.execute(query.where(CRMContact.phone == result.phone))
            existing_contact = ct_res.scalar_one_or_none()

        if existing_contact:
            if not result.is_imported:
                result.is_imported = True
                await db.commit()
            return existing_contact

        # 3. Create New Contact
        contact = CRMContact(
            tenant_id=tenant_id,
            company_id=company_id,
            first_name=result.name.split(" ")[0] if result.name else "Unknown",
            last_name=" ".join(result.name.split(" ")[1:]) if result.name and " " in result.name else "",
            email=result.email,
            phone=result.phone,
        )
        
        db.add(contact)
        result.is_imported = True
        
        # 4. Create Review Task
        from app.models.crm import CRMTask
        task = CRMTask(
            tenant_id=tenant_id,
            author_id=user_id,
            assigned_to_id=user_id,
            contact_id=contact.id,
            company_id=company_id,
            title=f"Review & Qualification: {result.name}",
            description=f"Newly imported lead from Hunter ({result.source}). Initial score: {result.confidence_score}. Please verify and start outreach.",
            priority="high" if result.confidence_score > 0.8 else "medium",
            due_date=datetime.datetime.utcnow() + datetime.timedelta(days=1)
        )
        db.add(task)

        # 5. Auto Follow-Up: Send WhatsApp with nationality detection + Gemini language
        try:
            from app.services.lead_auto_followup import auto_followup_on_import
            await db.commit()
            await db.refresh(contact)
            
            # Get the keyword from the hunter run for context
            run_res = await db.execute(select(HunterResult).where(HunterResult.id == result_id))
            result_obj = run_res.scalar_one_or_none()
            product_keyword = ""
            if result_obj and result_obj.raw_data:
                product_keyword = result_obj.raw_data.get("market_hs_code", "") or ""
            
            await auto_followup_on_import(
                db=db,
                contact=contact,
                tenant_id=tenant_id,
                product_keyword=product_keyword,
            )
        except Exception as followup_err:
            logger.warning(f"Auto follow-up after import failed (non-blocking): {followup_err}")
            # Non-blocking: contact is already created, followup failure shouldn't break import
            try:
                await db.commit()
            except Exception:
                pass

        await db.refresh(contact)
        return contact

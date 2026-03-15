from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.api.deps import get_current_user
from app.core.rbac import require_permissions
from app.models.user import User
from app.models.ai_job import AIJob
from app.models.hunter import HunterRun, HunterResult
from app.models.competitor import Competitor, CompetitorProduct, CompetitorPriceObservation, MarketShareSnapshot
from app.services.hunter_service import HunterService
from app.services.competitor_service import CompetitorService
from app.workers.tasks import run_hunter_job, track_competitor_job
from pydantic import BaseModel, Field
import uuid

router = APIRouter()

class ScrapeRequest(BaseModel):
    keyword: str
    location: Optional[str] = None
    sources: List[str] = Field(..., description="List of sources (google_maps, linkedin, telegram, discord, trademap, facebook, web)")
    hs_code: Optional[str] = None
    min_volume_usd: Optional[float] = None
    min_growth_pct: Optional[float] = None
    credentials: Optional[dict] = Field(None, description="Per-source credentials: {source_id: {field: value}}")
    hunt_type: Optional[str] = Field("buyer", description="Type of hunt: buyer or supplier")

class ImportRequest(BaseModel):
    result_id: str

@router.post("/start", dependencies=[Depends(require_permissions(["hunter.write"]))])
async def start_hunt(
    request: ScrapeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Start a new Hunter Job (Async).
    """
    job = AIJob(
        tenant_id=current_user.current_tenant_id,
        job_type="hunter",
        status="pending",
        credit_cost=5.0
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Dispatch to Celery worker (survives server restarts)
    run_hunter_job.delay(
        job_id=str(job.id),
        tenant_id=str(current_user.current_tenant_id),
        keyword=request.keyword,
        location=request.location,
        sources=request.sources,
        hs_code=request.hs_code,
        min_volume_usd=request.min_volume_usd,
        min_growth_pct=request.min_growth_pct,
    )
    
    return {
        "status": "success",
        "job_id": str(job.id),
        "message": "Hunter Job Started",
        "active_sources": request.sources
    }

@router.post("/scrape-now", dependencies=[Depends(require_permissions(["hunter.write"]))])
async def scrape_now(
    request: ScrapeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Inline scraping — runs scrapers directly and returns results immediately.
    No Celery needed. Results are saved to DB and returned to frontend.
    """
    import datetime
    from app.services.scraper.base import ScraperFactory
    
    tenant_id = current_user.current_tenant_id
    
    # Create a job record
    job = AIJob(
        tenant_id=tenant_id,
        job_type="hunter_inline",
        status="running",
        credit_cost=2.0
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Create hunter run
    run = HunterRun(
        tenant_id=tenant_id,
        job_id=job.id,
        target_keyword=request.keyword,
        target_location=request.location or "",
        sources=request.sources,
        status="processing"
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    
    all_leads = []
    errors = []
    
    for source_id in request.sources:
        try:
            scraper = ScraperFactory.get_scraper(source_id)
            source_creds = (request.credentials or {}).get(source_id, {})
            results = await scraper.scrape(
                keyword=request.keyword,
                location=request.location or "",
                credentials=source_creds if source_creds else None,
            )
            
            for r in results:
                # Save to DB
                hunter_result = HunterResult(
                    run_id=run.id,
                    tenant_id=tenant_id,
                    source=r.source or source_id,
                    type=request.hunt_type or "buyer",
                    name=r.contact_name,
                    company=r.company_name,
                    email=r.email,
                    phone=r.phone,
                    website=r.website,
                    country=r.country,
                    raw_data={
                        "brand_name": r.brand_name,
                        "product_name": r.product_name,
                        "price": r.price,
                        "city": r.city,
                        "company_name": r.company_name,
                        "contact_name": r.contact_name,
                        "email": r.email,
                        "phone": r.phone,
                        "website": r.website,
                        "country": r.country,
                        "source": r.source,
                        "score": r.score,
                    },
                    confidence_score=r.score / 100.0 if r.score else 0.5,
                )
                db.add(hunter_result)
                
                all_leads.append({
                    "company_name": r.company_name,
                    "contact_name": r.contact_name,
                    "email": r.email,
                    "phone": r.phone,
                    "country": r.country,
                    "source": r.source or source_id,
                    "brand_name": r.brand_name,
                    "product_name": r.product_name,
                    "price": r.price,
                    "website": r.website,
                    "score": r.score,
                })
        except Exception as e:
            errors.append({"source": source_id, "error": str(e)})
    
    # Update run and job status
    run.status = "completed"
    run.leads_found = len(all_leads)
    run.completed_at = datetime.datetime.utcnow()
    job.status = "completed"
    job.completed_at = datetime.datetime.utcnow()
    
    await db.commit()
    
    return {
        "status": "success",
        "total_leads": len(all_leads),
        "results": all_leads,
        "errors": errors,
        "job_id": str(job.id),
    }

@router.get("/search", dependencies=[Depends(require_permissions(["hunter.read"]))])
async def search_leads(
    type: str = "buyer",
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all hunter results for the current tenant, optionally filtered by type.
    Returns empty list if no results found.
    """
    tenant_id = current_user.current_tenant_id
    if not tenant_id:
        return {"results": [], "total": 0}
    
    # Get all runs for this tenant
    runs_result = await db.execute(
        select(HunterRun).where(HunterRun.tenant_id == tenant_id).order_by(HunterRun.created_at.desc())
    )
    runs = runs_result.scalars().all()
    
    if not runs:
        return {"results": [], "total": 0}
    
    # Get all results from those runs
    run_ids = [run.id for run in runs]
    results_query = select(HunterResult).where(HunterResult.run_id.in_(run_ids))
    results_result = await db.execute(results_query)
    all_results = results_result.scalars().all()
    
    # Map to response format
    leads = []
    for r in all_results[:limit]:
        raw = r.raw_data if hasattr(r, 'raw_data') and r.raw_data else {}
        leads.append({
            "id": str(r.id),
            "company_name": getattr(r, 'company_name', '') or raw.get('company_name', 'Unknown'),
            "contact_name": getattr(r, 'contact_name', '') or raw.get('contact_name', ''),
            "email": getattr(r, 'email', '') or raw.get('email', ''),
            "phone": getattr(r, 'phone', '') or raw.get('phone', ''),
            "country": getattr(r, 'country', '') or raw.get('country', ''),
            "source": getattr(r, 'source', '') or raw.get('source', ''),
            "status": getattr(r, 'status', 'new') or 'new',
            "score": getattr(r, 'lead_score', 0) or raw.get('score', 0),
            "brand_name": raw.get('brand_name', ''),
            "product_name": raw.get('product_name', ''),
            "price": raw.get('price', ''),
            "website": raw.get('website', ''),
            "created_at": str(r.created_at) if hasattr(r, 'created_at') else '',
        })
    
    return {"results": leads, "total": len(leads)}

@router.get("/status/{job_id}", dependencies=[Depends(require_permissions(["hunter.read"]))])
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(AIJob).where(AIJob.id == job_id, AIJob.tenant_id == current_user.current_tenant_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    res_run = await db.execute(select(HunterRun).where(HunterRun.job_id == job_id))
    run = res_run.scalar_one_or_none()
    
    return {
        "job_status": job.status,
        "leads_found": run.leads_found if run else 0,
        "completed_at": job.completed_at
    }

@router.get("/results/{job_id}", dependencies=[Depends(require_permissions(["hunter.read"]))])
async def get_job_results(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(HunterRun).where(HunterRun.job_id == job_id, HunterRun.tenant_id == current_user.current_tenant_id))
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    res_results = await db.execute(select(HunterResult).where(HunterResult.run_id == run.id))
    results = res_results.scalars().all()
    return results

@router.post("/import-to-crm", dependencies=[Depends(require_permissions(["hunter.write"]))])
async def import_lead(
    req: ImportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        contact = await HunterService.import_result_to_crm(
            db, 
            uuid.UUID(req.result_id), 
            current_user.id,
            current_user.current_tenant_id
        )
        return {"status": "success", "contact_id": str(contact.id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Competitor Intelligence (Hunter v2) ---

class CompetitorCreate(BaseModel):
    name: str
    website: Optional[str] = None
    country: Optional[str] = None
    industry_tags: List[str] = []

@router.post("/competitors", dependencies=[Depends(require_permissions(["hunter.write"]))])
async def create_competitor(
    comp: CompetitorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_comp = Competitor(
        tenant_id=current_user.current_tenant_id,
        name=comp.name,
        website=comp.website,
        country=comp.country,
        industry_tags=comp.industry_tags
    )
    db.add(new_comp)
    await db.commit()
    await db.refresh(new_comp)
    return new_comp

@router.get("/competitors", dependencies=[Depends(require_permissions(["hunter.read"]))])
async def get_competitors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Competitor).where(Competitor.tenant_id == current_user.current_tenant_id))
    return res.scalars().all()

@router.post("/competitors/{id}/track", dependencies=[Depends(require_permissions(["hunter.write"]))])
async def track_competitor(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Dispatch to Celery worker
    track_competitor_job.delay(
        competitor_id=id,
        tenant_id=str(current_user.current_tenant_id),
    )
    return {"status": "queued", "message": "Competitor tracking started."}

@router.get("/competitors/{id}/products", dependencies=[Depends(require_permissions(["hunter.read"]))])
async def get_competitor_products(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(CompetitorProduct).where(
        CompetitorProduct.competitor_id == uuid.UUID(id),
        CompetitorProduct.tenant_id == current_user.current_tenant_id
    ))
    return res.scalars().all()

@router.get("/market-share/analyze", dependencies=[Depends(require_permissions(["hunter.read"]))])
async def analyze_market_share(
    competitor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    snapshot = await CompetitorService.analyze_market_share(db, uuid.UUID(competitor_id), current_user.current_tenant_id)
    return snapshot

@router.get("/price-decision", dependencies=[Depends(require_permissions(["hunter.read"]))])
async def get_price_decision(
    my_price: float,
    keyword: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    decision = await CompetitorService.compare_prices(db, my_price, keyword)
    return decision

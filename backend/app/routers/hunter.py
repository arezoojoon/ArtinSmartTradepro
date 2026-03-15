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

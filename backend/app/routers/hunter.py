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
from pydantic import BaseModel, Field
import uuid
import asyncio

router = APIRouter()

class ScrapeRequest(BaseModel):
    keyword: str
    location: str
    sources: List[str] = Field(..., description="List of sources (maps, un_comtrade, freight, etc.)")

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

    # Detach from request context
    asyncio.create_task(
        HunterService.run_hunter_job(
            job_id=job.id,
            tenant_id=current_user.current_tenant_id,
            keyword=request.keyword,
            location=request.location,
            sources=request.sources
        )
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
    asyncio.create_task(
        CompetitorService.track_competitor_job(
            competitor_id=uuid.UUID(id),
            tenant_id=current_user.current_tenant_id
        )
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

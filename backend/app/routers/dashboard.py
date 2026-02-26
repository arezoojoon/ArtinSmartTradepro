"""
Dashboard Router — /main (web command center), /mobile, /web endpoints.
Uses async DB session and modern auth imports.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any
import datetime
import logging

from app.db.session import get_db
from app.models.user import User
from app.models.crm import CRMCompany, CRMPipeline, CRMDeal
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

# Graceful optional model imports
try:
    from app.models.billing import Wallet, WalletTransaction
except ImportError:
    Wallet = WalletTransaction = None

try:
    from app.models.crm import CRMInvoice
except ImportError:
    CRMInvoice = None

try:
    from app.models.brain import BrainEngineRun
except ImportError:
    BrainEngineRun = None

try:
    from app.models.hunter_phase4 import HunterLead
except ImportError:
    HunterLead = None

try:
    from app.models.phase5 import AssetArbitrageHistory
except ImportError:
    AssetArbitrageHistory = None

router = APIRouter()


# ─── Helper ────────────────────────────────────────────────────────────
def _tenant_id(user: User):
    tid = getattr(user, "current_tenant_id", None) or getattr(user, "tenant_id", None)
    if not tid:
        raise HTTPException(status_code=400, detail="No tenant context found")
    return tid


# ═══════════════════════════════════════════════════════════════════════
# GET /dashboard/main — Web Command Center (frontend GlobalCommandCenter)
# ═══════════════════════════════════════════════════════════════════════
@router.get("/main")
async def get_main_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Aggregated endpoint consumed by the web Global Command Center.
    Returns kpi_summary, margin_overview, risk_heatmap.
    """
    tenant_id = _tenant_id(current_user)
    now = datetime.datetime.utcnow()

    # ── KPI: total pipeline value ──
    total_pipeline_value = 0.0
    try:
        result = await db.execute(
            select(func.coalesce(func.sum(CRMDeal.value), 0))
            .where(CRMDeal.tenant_id == tenant_id, CRMDeal.status == "open")
        )
        total_pipeline_value = float(result.scalar_one())
    except Exception as e:
        logger.warning(f"pipeline value query: {e}")

    # ── KPI: active leads ──
    active_leads = 0
    if HunterLead is not None:
        try:
            result = await db.execute(
                select(func.count(HunterLead.id))
                .where(HunterLead.tenant_id == tenant_id, HunterLead.status == "qualified")
            )
            active_leads = result.scalar_one()
        except Exception as e:
            logger.warning(f"active leads query: {e}")

    # ── Margin overview from arbitrage history ──
    margin_overview = []
    weighted_margin = None
    if AssetArbitrageHistory is not None:
        try:
            result = await db.execute(
                select(AssetArbitrageHistory)
                .where(
                    AssetArbitrageHistory.tenant_id == tenant_id,
                    AssetArbitrageHistory.created_at >= now - datetime.timedelta(days=30),
                )
                .order_by(AssetArbitrageHistory.created_at.desc())
                .limit(10)
            )
            records = result.scalars().all()
            margins_pct = []
            for rec in records:
                est = float(rec.estimated_margin_pct) if rec.estimated_margin_pct else 0
                rea = float(rec.realized_margin_pct) if rec.realized_margin_pct else None
                margin_overview.append({
                    "product_key": getattr(rec, "product_key", "Unknown"),
                    "buy_market": getattr(rec, "buy_market", "N/A"),
                    "sell_market": getattr(rec, "sell_market", "N/A"),
                    "estimated_margin_pct": est,
                    "realized_margin_pct": rea,
                    "status": getattr(rec, "status", "pending"),
                })
                margins_pct.append(est)
            if margins_pct:
                weighted_margin = sum(margins_pct) / len(margins_pct)
        except Exception as e:
            logger.warning(f"margin overview query: {e}")

    # ── Risk heatmap ──
    risk_heatmap = []
    high_risk_count = 0
    if BrainEngineRun is not None:
        try:
            result = await db.execute(
                select(BrainEngineRun)
                .where(
                    BrainEngineRun.tenant_id == tenant_id,
                    BrainEngineRun.engine_type == "risk",
                    BrainEngineRun.status == "success",
                )
                .order_by(BrainEngineRun.created_at.desc())
                .limit(20)
            )
            for run in result.scalars().all():
                payload = getattr(run, "output_payload", None) or getattr(run, "result_json", None) or {}
                risk_level = payload.get("overall_risk_level", payload.get("risk_level", "low"))
                risk_heatmap.append({
                    "country": payload.get("country", "Unknown"),
                    "risk_type": payload.get("primary_risk", payload.get("category", "General")),
                    "risk_level": risk_level,
                    "risk_score": int(payload.get("risk_score", 50)),
                    "description": payload.get("recommendation", payload.get("description", "")),
                })
                if risk_level in ("high", "critical"):
                    high_risk_count += 1
        except Exception as e:
            logger.warning(f"risk heatmap query: {e}")

    # ── Cash flow health ──
    cash_flow_health = "unknown"
    if CRMInvoice is not None:
        try:
            result = await db.execute(
                select(func.coalesce(func.sum(CRMInvoice.amount), 0))
                .where(CRMInvoice.tenant_id == tenant_id, CRMInvoice.status == "overdue")
            )
            overdue = float(result.scalar_one())
            cash_flow_health = "negative" if overdue > 10000 else "positive"
        except Exception as e:
            logger.warning(f"cash flow query: {e}")
            cash_flow_health = "positive"
    else:
        cash_flow_health = "positive"

    return {
        "kpi_summary": {
            "total_pipeline_value": total_pipeline_value,
            "active_leads": active_leads,
            "high_risk_countries": high_risk_count,
            "cash_flow_health": cash_flow_health,
            "weighted_margin": weighted_margin,
        },
        "margin_overview": margin_overview,
        "risk_heatmap": risk_heatmap,
    }


# ═══════════════════════════════════════════════════════════════════════
# GET /dashboard/mobile — Mobile Control Tower
# ═══════════════════════════════════════════════════════════════════════
@router.get("/mobile")
async def get_mobile_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    tenant_id = _tenant_id(current_user)
    now = datetime.datetime.utcnow()

    liquidity = {
        "balance": 0, "currency": "USD",
        "pending_in": 0, "pending_out": 0, "dso": 0,
        "source": "Wallet Service",
        "timestamp": now.isoformat(),
    }
    opportunities = []
    risks = []
    leads = []

    # Opportunities from Brain
    if BrainEngineRun is not None:
        try:
            result = await db.execute(
                select(BrainEngineRun).where(
                    BrainEngineRun.tenant_id == tenant_id,
                    BrainEngineRun.engine_type == "arbitrage",
                    BrainEngineRun.status == "success",
                    BrainEngineRun.created_at >= now - datetime.timedelta(days=1),
                ).order_by(BrainEngineRun.created_at.desc()).limit(3)
            )
            for run in result.scalars().all():
                opp = (run.output_payload or {}).get("opportunity_card", {})
                opportunities.append({
                    "id": str(run.id),
                    "title": f"{opp.get('product', 'Unknown')} Arbitrage",
                    "description": f"Buy: {opp.get('buy_market')} @ ${opp.get('buy_price', 0)}, Sell: {opp.get('sell_market')} @ ${opp.get('sell_price', 0)}",
                    "source": "Brain Arbitrage Engine",
                    "timestamp": run.created_at.isoformat(),
                    "confidence": opp.get("confidence", 0.8),
                    "isInsufficientData": False,
                })
        except Exception as e:
            logger.warning(f"mobile opportunities: {e}")

    # Leads from Hunter
    if HunterLead is not None:
        try:
            result = await db.execute(
                select(HunterLead).where(
                    HunterLead.tenant_id == tenant_id,
                    HunterLead.status == "qualified",
                    HunterLead.created_at >= now - datetime.timedelta(days=7),
                ).order_by(HunterLead.score_total.desc()).limit(3)
            )
            for lead in result.scalars().all():
                leads.append({
                    "id": str(lead.id),
                    "title": lead.primary_name,
                    "description": f"{lead.country} - Score: {lead.score_total}",
                    "source": "Hunter Lead Generation",
                    "timestamp": lead.created_at.isoformat(),
                    "confidence": min(lead.score_total / 100, 1.0),
                    "isInsufficientData": False,
                })
        except Exception as e:
            logger.warning(f"mobile leads: {e}")

    return {
        "liquidity": liquidity,
        "opportunities": opportunities,
        "risks": risks,
        "shocks": [],
        "leads": leads,
    }


# ═══════════════════════════════════════════════════════════════════════
# GET /dashboard/web — Full Web Dashboard
# ═══════════════════════════════════════════════════════════════════════
@router.get("/web")
async def get_web_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    tenant_id = _tenant_id(current_user)
    now = datetime.datetime.utcnow()

    # 1. Pipeline
    pipeline_list = []
    try:
        result = await db.execute(
            select(CRMPipeline)
            .where(CRMPipeline.tenant_id == tenant_id)
            .order_by(CRMPipeline.is_default.desc())
            .limit(1)
        )
        pipeline = result.scalar_one_or_none()
        if pipeline and pipeline.stages:
            for stage in pipeline.stages:
                sid = stage.get("id")
                dr = await db.execute(
                    select(func.count(CRMDeal.id), func.coalesce(func.sum(CRMDeal.value), 0))
                    .where(CRMDeal.tenant_id == tenant_id, CRMDeal.pipeline_id == pipeline.id,
                           CRMDeal.stage_id == sid, CRMDeal.status == "open")
                )
                cnt, val = dr.one()
                pipeline_list.append({"name": stage.get("name"), "count": cnt, "value": float(val)})
    except Exception as e:
        logger.warning(f"web pipeline: {e}")
    if not pipeline_list:
        pipeline_list = [
            {"name": "Qualification", "count": 0, "value": 0.0},
            {"name": "Proposal", "count": 0, "value": 0.0},
            {"name": "Negotiation", "count": 0, "value": 0.0},
            {"name": "Closed Won", "count": 0, "value": 0.0},
        ]

    # 2. Margin matrix
    margin_matrix = []
    if AssetArbitrageHistory is not None:
        try:
            result = await db.execute(
                select(AssetArbitrageHistory)
                .where(AssetArbitrageHistory.tenant_id == tenant_id,
                       AssetArbitrageHistory.created_at >= now - datetime.timedelta(days=30))
                .order_by(AssetArbitrageHistory.created_at.desc()).limit(10)
            )
            for rec in result.scalars().all():
                margin_matrix.append({
                    "product": getattr(rec, "product_key", "Unknown"),
                    "origin": getattr(rec, "buy_market", "N/A"),
                    "destination": getattr(rec, "sell_market", "N/A"),
                    "net_margin": float(rec.estimated_margin_pct) if rec.estimated_margin_pct else 0,
                    "roi": float(rec.realized_margin_pct) if rec.realized_margin_pct else 0,
                })
        except Exception as e:
            logger.warning(f"web margin: {e}")

    # 3. Cash flow trends (simplified — 6 month buckets)
    cash_flow = []
    for i in range(5, -1, -1):
        ps = now - datetime.timedelta(days=30 * i)
        cash_flow.append({"period": ps.strftime("%b"), "cash_in": 0.0, "cash_out": 0.0})

    # 4. Risk heatmap
    risk_heatmap = []
    if BrainEngineRun is not None:
        try:
            result = await db.execute(
                select(BrainEngineRun).where(
                    BrainEngineRun.tenant_id == tenant_id,
                    BrainEngineRun.engine_type == "risk",
                    BrainEngineRun.status == "success",
                ).order_by(BrainEngineRun.created_at.desc()).limit(10)
            )
            for run in result.scalars().all():
                r = getattr(run, "result_json", None) or getattr(run, "output_payload", None) or {}
                risk_heatmap.append({
                    "country": r.get("country", "Unknown"),
                    "category": r.get("primary_risk", "General"),
                    "score": int(r.get("risk_score", 50)),
                })
        except Exception as e:
            logger.warning(f"web risk: {e}")

    # 5. Performance snapshots
    performance = []
    try:
        result = await db.execute(
            select(CRMCompany)
            .where(CRMCompany.tenant_id == tenant_id, CRMCompany.risk_score.isnot(None))
            .order_by(CRMCompany.risk_score.desc()).limit(5)
        )
        for c in result.scalars().all():
            tags = getattr(c, "tags_json", []) or []
            ct = "buyer" if "buyer" in tags else "supplier" if "supplier" in tags else "other"
            performance.append({"id": str(c.id), "name": c.name, "type": ct, "score": float(c.risk_score or 80)})
    except Exception as e:
        logger.warning(f"web performance: {e}")

    return {
        "pipeline": pipeline_list,
        "margin_matrix": margin_matrix,
        "cash_flow": cash_flow,
        "risk_heatmap": risk_heatmap,
        "performance": performance,
    }

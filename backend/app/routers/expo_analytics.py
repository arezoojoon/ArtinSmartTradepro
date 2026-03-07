"""
Expo Analytics Router — ported from Expo app_fastapi.py
Provides lead analytics stats, funnel data, product heatmap, lead quality distribution.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.database import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.models.lead import Lead
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats")
def get_analytics_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Basic analytics KPIs for the Acquisition dashboard."""
    tid = current_user.current_tenant_id or current_user.tenant_id
    try:
        total = db.query(func.count(Lead.id)).filter(Lead.tenant_id == tid).scalar() or 0

        rows = (
            db.query(Lead.status, func.count(Lead.id))
            .filter(Lead.tenant_id == tid)
            .group_by(Lead.status)
            .all()
        )
        status_counts = {r[0]: r[1] for r in rows}

        closed_won = status_counts.get("closed_won", 0)
        conversion = round((closed_won / total * 100), 1) if total > 0 else 0

        return {
            "total_leads": total,
            "new_leads": status_counts.get("new", 0),
            "qualified_leads": status_counts.get("qualified", 0),
            "viewing_scheduled": status_counts.get("viewing_scheduled", 0),
            "closed_won": closed_won,
            "closed_lost": status_counts.get("closed_lost", 0),
            "conversion_rate": conversion,
            "avg_deal_value": 0,
        }
    except Exception as e:
        logger.error(f"Analytics stats error: {e}")
        return {"total_leads": 0, "conversion_rate": 0}


@router.get("/funnel")
def get_funnel_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """AIDA funnel data: Attention → Interest → Desire → Action."""
    tid = current_user.current_tenant_id or current_user.tenant_id
    try:
        rows = (
            db.query(Lead.aida_stage, func.count(Lead.id))
            .filter(Lead.tenant_id == tid, Lead.aida_stage.isnot(None))
            .group_by(Lead.aida_stage)
            .all()
        )
        stage_counts = {r[0]: r[1] for r in rows}
        return {
            "attention": stage_counts.get("Attention", 0),
            "interest": stage_counts.get("Interest", 0),
            "desire": stage_counts.get("Desire", 0),
            "action": stage_counts.get("Action", 0),
        }
    except Exception as e:
        logger.error(f"Funnel data error: {e}")
        return {"attention": 0, "interest": 0, "desire": 0, "action": 0}


@router.get("/lead-quality")
def get_lead_quality_distribution(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Lead Quality Distribution (Hot / Warm / Cold) for donut chart."""
    tid = current_user.current_tenant_id or current_user.tenant_id
    try:
        rows = (
            db.query(Lead.lead_quality, func.count(Lead.id))
            .filter(Lead.tenant_id == tid, Lead.lead_quality.isnot(None))
            .group_by(Lead.lead_quality)
            .all()
        )
        quality = {r[0]: r[1] for r in rows}
        return {
            "hot": quality.get("hot", 0),
            "warm": quality.get("warm", 0),
            "cold": quality.get("cold", 0),
        }
    except Exception as e:
        logger.error(f"Lead quality error: {e}")
        return {"hot": 0, "warm": 0, "cold": 0}

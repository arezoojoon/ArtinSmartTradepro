"""
Control Tower API — Pillar 2: Money-Making Engine
Actionable dashboard with smart alerts and one-click actions.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, update
from app.db.session import get_db
from app.core.tenant import get_tenant_context, TenantContext
from app.services.control_tower import ControlTowerService
from app.models.ai_approval import AIApprovalQueue, ApprovalStatus, AIActionLog
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Schemas ---
class AlertResponse(BaseModel):
    id: str
    type: str
    severity: str
    title_fa: str = ""
    title_en: str = ""
    description_fa: str = ""
    description_en: str = ""
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    suggested_action: Optional[str] = None
    action_label_fa: Optional[str] = None
    action_label_en: Optional[str] = None
    action_payload: Optional[dict] = None
    ai_confidence: Optional[float] = None
    created_at: Optional[str] = None


class KPISummary(BaseModel):
    active_shipments: int = 0
    pending_approvals: int = 0
    active_deals: int = 0
    total_contacts: int = 0
    last_updated: str = ""


class ApprovalItem(BaseModel):
    id: str
    category: str
    title: str
    description: Optional[str] = None
    ai_payload: Optional[dict] = None
    ai_confidence: float = 0.0
    ai_reasoning: Optional[str] = None
    source_type: Optional[str] = None
    source_preview: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    created_at: Optional[str] = None
    expires_at: Optional[str] = None


class ApprovalAction(BaseModel):
    action: str  # approve | reject
    note: Optional[str] = None


class ExecuteAlertAction(BaseModel):
    alert_id: str
    action_payload: dict


# --- Control Tower Endpoints ---
@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    limit: int = Query(20, ge=1, le=50),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Get all active Control Tower alerts — sorted by priority."""
    alerts = await ControlTowerService.get_dashboard_alerts(db, ctx.tenant_id, limit)
    return alerts


@router.get("/kpi")
async def get_kpi(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Get real-time KPI summary for the Control Tower dashboard."""
    return await ControlTowerService.get_kpi_summary(db, ctx.tenant_id)


# --- AI Approval Queue Endpoints ---
@router.get("/approvals", response_model=List[ApprovalItem])
async def list_approvals(
    status: Optional[str] = Query(None, description="Filter by status: pending|approved|rejected"),
    limit: int = Query(20, ge=1, le=100),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """List AI approval queue items."""
    query = select(AIApprovalQueue).where(
        AIApprovalQueue.tenant_id == ctx.tenant_id
    )
    if status:
        query = query.where(AIApprovalQueue.status == status)
    query = query.order_by(desc(AIApprovalQueue.created_at)).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    return [
        ApprovalItem(
            id=str(item.id),
            category=item.category or "",
            title=item.title or "",
            description=item.description,
            ai_payload=item.ai_payload,
            ai_confidence=item.ai_confidence or 0.0,
            ai_reasoning=item.ai_reasoning,
            source_type=item.source_type,
            source_preview=item.source_preview,
            status=item.status or "pending",
            priority=item.priority or "medium",
            created_at=item.created_at.isoformat() if item.created_at else None,
            expires_at=item.expires_at.isoformat() if item.expires_at else None,
        )
        for item in items
    ]


@router.get("/approvals/{approval_id}")
async def get_approval(
    approval_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific approval item with full details."""
    result = await db.execute(
        select(AIApprovalQueue).where(
            AIApprovalQueue.id == approval_id,
            AIApprovalQueue.tenant_id == ctx.tenant_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Approval item not found")

    return {
        "id": str(item.id),
        "category": item.category,
        "title": item.title,
        "description": item.description,
        "ai_payload": item.ai_payload,
        "ai_confidence": item.ai_confidence,
        "ai_reasoning": item.ai_reasoning,
        "source_type": item.source_type,
        "source_preview": item.source_preview,
        "status": item.status,
        "priority": item.priority,
        "reviewed_by": str(item.reviewed_by) if item.reviewed_by else None,
        "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
        "review_note": item.review_note,
        "executed": item.executed,
        "execution_result": item.execution_result,
        "execution_error": item.execution_error,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "expires_at": item.expires_at.isoformat() if item.expires_at else None,
    }


@router.post("/approvals/{approval_id}/review")
async def review_approval(
    approval_id: uuid.UUID,
    body: ApprovalAction,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Approve or reject an AI action — Human-in-the-Loop.
    This is the core of Pillar 4: Guardrails.
    """
    result = await db.execute(
        select(AIApprovalQueue).where(
            AIApprovalQueue.id == approval_id,
            AIApprovalQueue.tenant_id == ctx.tenant_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Approval item not found")

    if item.status != ApprovalStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Item already {item.status}")

    now = datetime.utcnow()

    if body.action == "approve":
        item.status = ApprovalStatus.APPROVED.value
        item.reviewed_at = now
        item.reviewed_by = ctx.user_id
        item.review_note = body.note

        # Log the approval
        log = AIActionLog(
            tenant_id=ctx.tenant_id,
            approval_id=item.id,
            action_type=item.category,
            description=f"Approved: {item.title}",
            payload=item.ai_payload,
            was_auto_approved=False,
            confidence=item.ai_confidence or 0.0,
        )
        db.add(log)

    elif body.action == "reject":
        item.status = ApprovalStatus.REJECTED.value
        item.reviewed_at = now
        item.reviewed_by = ctx.user_id
        item.review_note = body.note

        log = AIActionLog(
            tenant_id=ctx.tenant_id,
            approval_id=item.id,
            action_type=item.category,
            description=f"Rejected: {item.title}",
            payload=item.ai_payload,
            was_auto_approved=False,
            confidence=item.ai_confidence or 0.0,
        )
        db.add(log)
    else:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")

    await db.commit()

    return {
        "id": str(item.id),
        "status": item.status,
        "reviewed_at": now.isoformat(),
        "message": f"Action {body.action}d successfully",
    }


@router.get("/approvals/stats/summary")
async def approval_stats(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Get approval queue statistics."""
    stats = {}
    for status in ["pending", "approved", "rejected", "expired"]:
        q = await db.execute(
            select(func.count(AIApprovalQueue.id)).where(
                AIApprovalQueue.tenant_id == ctx.tenant_id,
                AIApprovalQueue.status == status,
            )
        )
        stats[status] = q.scalar() or 0

    stats["total"] = sum(stats.values())
    return stats

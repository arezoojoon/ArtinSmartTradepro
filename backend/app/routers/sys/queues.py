"""
/sys/queues — DLQ inspection and retry for messages + hunter jobs.
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.phase6 import SystemAdmin
from app.services.sys_admin_auth import get_current_sys_admin

router = APIRouter()


@router.get("/dlq", summary="List DLQ Messages")
def list_dlq(
    queue_type: Optional[str] = Query(None, description="messages | hunter"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: SystemAdmin = Depends(get_current_sys_admin),
):
    """
    Returns dead-letter queue items.
    Reads from app.models.communication and app.models.hunter_phase4.
    """
    results = []

    # Message DLQ
    if not queue_type or queue_type == "messages":
        try:
            from app.models.communication import OutboundMessage
            q = db.query(OutboundMessage).filter(
                OutboundMessage.status == "failed"
            ).order_by(OutboundMessage.created_at.desc())
            total_msg = q.count()
            for m in q.offset(offset).limit(limit).all():
                results.append({
                    "id": str(m.id),
                    "queue_type": "messages",
                    "status": m.status,
                    "error": getattr(m, "error_message", None),
                    "retry_count": getattr(m, "retry_count", 0),
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                })
        except Exception:
            pass  # Model may not exist yet in older versions

    # Hunter job DLQ
    if not queue_type or queue_type == "hunter":
        try:
            from app.models.hunter_phase4 import HunterJob
            q = db.query(HunterJob).filter(
                HunterJob.status == "failed"
            ).order_by(HunterJob.created_at.desc())
            for j in q.offset(offset).limit(limit).all():
                results.append({
                    "id": str(j.id),
                    "queue_type": "hunter",
                    "status": j.status,
                    "error": getattr(j, "error_message", None),
                    "retry_count": getattr(j, "retry_count", 0),
                    "created_at": j.created_at.isoformat() if j.created_at else None,
                })
        except Exception:
            pass

    return {"total": len(results), "items": results}


class RetryRequest(BaseModel):
    item_id: UUID
    queue_type: str  # "messages" | "hunter"


@router.post("/dlq/retry", summary="Retry DLQ Item")
def retry_dlq_item(
    body: RetryRequest,
    db: Session = Depends(get_db),
    admin: SystemAdmin = Depends(get_current_sys_admin),
):
    """
    Resets a DLQ item to 'pending' so it will be retried by the worker.
    """
    if body.queue_type == "messages":
        try:
            from app.models.communication import OutboundMessage
            item = db.query(OutboundMessage).filter(OutboundMessage.id == body.item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail="Message not found")
            item.status = "pending"
            item.retry_count = 0
            db.commit()
            return {"status": "retrying", "id": str(body.item_id), "queue_type": "messages"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif body.queue_type == "hunter":
        try:
            from app.models.hunter_phase4 import HunterJob
            item = db.query(HunterJob).filter(HunterJob.id == body.item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail="Hunter job not found")
            item.status = "pending"
            db.commit()
            return {"status": "retrying", "id": str(body.item_id), "queue_type": "hunter"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=400, detail="Invalid queue_type. Use 'messages' or 'hunter'")

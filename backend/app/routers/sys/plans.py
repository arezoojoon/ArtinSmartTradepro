"""
/sys/plans — CRUD for SysPlan (Phase 6 JSONB plans).
"""
from uuid import UUID
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.phase6 import SystemAdmin, SysPlan
from app.services.sys_admin_auth import get_current_sys_admin, write_sys_audit

router = APIRouter()


class PlanUpsertRequest(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    monthly_price_usd: Optional[float] = None
    features: dict[str, Any] = {}
    limits: dict[str, Any] = {}


@router.get("", summary="List Plans")
def list_plans(db: Session = Depends(get_db), admin: SystemAdmin = Depends(get_current_sys_admin)):
    plans = db.query(SysPlan).filter(SysPlan.is_active == True).order_by(SysPlan.monthly_price_usd).all()
    return [
        {
            "id": str(p.id),
            "code": p.code,
            "name": p.name,
            "monthly_price_usd": float(p.monthly_price_usd) if p.monthly_price_usd else None,
            "features": p.features,
            "limits": p.limits,
        }
        for p in plans
    ]


@router.post("", summary="Create or Update Plan")
def upsert_plan(
    body: PlanUpsertRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: SystemAdmin = Depends(get_current_sys_admin),
):
    existing = db.query(SysPlan).filter(SysPlan.code == body.code).first()
    if existing:
        before = {"code": existing.code, "name": existing.name, "limits": existing.limits}
        existing.name = body.name
        existing.description = body.description
        existing.monthly_price_usd = body.monthly_price_usd
        existing.features = body.features
        existing.limits = body.limits
        db.commit()
        write_sys_audit(db, action="plan_update", resource_type="plan",
                        actor_sys_admin_id=admin.id, resource_id=str(existing.id),
                        before_state=before,
                        after_state={"code": existing.code, "limits": existing.limits})
        return {"id": str(existing.id), "code": existing.code, "action": "updated"}
    else:
        plan = SysPlan(**body.model_dump())
        db.add(plan)
        db.commit()
        write_sys_audit(db, action="plan_create", resource_type="plan",
                        actor_sys_admin_id=admin.id, resource_id=str(plan.id),
                        after_state={"code": plan.code})
        return {"id": str(plan.id), "code": plan.code, "action": "created"}


@router.get("/{plan_id}", summary="Get Plan Detail")
def get_plan(plan_id: UUID, db: Session = Depends(get_db), admin: SystemAdmin = Depends(get_current_sys_admin)):
    plan = db.query(SysPlan).filter(SysPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"id": str(plan.id), "code": plan.code, "name": plan.name,
            "monthly_price_usd": float(plan.monthly_price_usd) if plan.monthly_price_usd else None,
            "features": plan.features, "limits": plan.limits}


@router.delete("/{plan_id}", summary="Deactivate Plan")
def deactivate_plan(
    plan_id: UUID, request: Request,
    db: Session = Depends(get_db), admin: SystemAdmin = Depends(get_current_sys_admin),
):
    plan = db.query(SysPlan).filter(SysPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    before = {"is_active": plan.is_active}
    plan.is_active = False
    db.commit()
    write_sys_audit(db, action="plan_deactivate", resource_type="plan",
                    actor_sys_admin_id=admin.id, resource_id=str(plan.id),
                    before_state=before, after_state={"is_active": False})
    return {"status": "deactivated", "plan_id": str(plan_id)}

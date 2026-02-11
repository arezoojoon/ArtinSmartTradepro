"""
CRM Follow-Up Router — Automated Follow-Up Rules.
Phase C4.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.database import get_db
from app.models.user import User
from app.models.followup import CRMFollowUpRule, CRMFollowUpExecution
from app.middleware.auth import get_current_active_user
from app.middleware.plan_gate import require_feature
from app.constants import Feature
from app.services.followup_service import FollowUpService
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
import datetime

router = APIRouter()

class FollowUpRuleCreate(BaseModel):
    name: str
    template_body: str
    delay_minutes: int = 1440
    max_attempts: int = 1
    trigger_event: str = "no_reply"
    channel: str = "whatsapp"

class FollowUpRuleRead(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    template_body: str
    delay_minutes: int
    max_attempts: int
    trigger_event: str
    channel: str
    is_active: bool
    created_at: datetime.datetime
    
    class Config:
        from_attributes = True

class FollowUpExecutionRead(BaseModel):
    id: UUID
    rule_id: Optional[UUID]
    contact_id: UUID
    status: str
    scheduled_at: datetime.datetime
    sent_at: Optional[datetime.datetime]
    attempt: int
    error: Optional[str]

    class Config:
        from_attributes = True

@router.post("/rules", response_model=FollowUpRuleRead)
@require_feature(Feature.FOLLOW_UP)
def create_rule(
    rule_in: FollowUpRuleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return FollowUpService.create_rule(
        db=db,
        tenant_id=current_user.tenant_id,
        name=rule_in.name,
        template=rule_in.template_body,
        delay_minutes=rule_in.delay_minutes
    )

@router.get("/rules", response_model=List[FollowUpRuleRead])
@require_feature(Feature.FOLLOW_UP)
def list_rules(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.execute(
        select(CRMFollowUpRule)
        .where(CRMFollowUpRule.tenant_id == current_user.tenant_id)
        .order_by(desc(CRMFollowUpRule.created_at))
    ).scalars().all()

@router.post("/rules/{rule_id}/toggle")
@require_feature(Feature.FOLLOW_UP)
def toggle_rule(
    rule_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    rule = db.execute(
        select(CRMFollowUpRule)
        .where(CRMFollowUpRule.id == rule_id)
        .where(CRMFollowUpRule.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    rule.is_active = not rule.is_active
    db.commit()
    return {"status": "updated", "is_active": rule.is_active}

@router.get("/executions", response_model=List[FollowUpExecutionRead])
@require_feature(Feature.FOLLOW_UP)
def list_executions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.execute(
        select(CRMFollowUpExecution)
        .where(CRMFollowUpExecution.tenant_id == current_user.tenant_id)
        .order_by(desc(CRMFollowUpExecution.scheduled_at))
        .limit(50) 
    ).scalars().all()

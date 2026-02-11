"""
Campaigns Router — Create, manage, and run outbound campaigns.
All endpoints gated to CAMPAIGNS feature.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.campaign import CRMCampaign, CRMCampaignSegment, CRMCampaignMessage, CampaignStatus
from app.models.crm import CRMContact
from app.middleware.auth import get_current_active_user
from app.middleware.plan_gate import require_feature
from app.constants import Feature
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    channel: Optional[str] = "whatsapp"
    template_body: Optional[str] = None

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    template_body: Optional[str] = None
    status: Optional[str] = None

class SegmentCreate(BaseModel):
    filter_json: Optional[dict] = {}

class AddContactsRequest(BaseModel):
    contact_ids: List[UUID]


# ─── Campaigns CRUD ──────────────────────────────────────────────────

@router.get("/")
@require_feature(Feature.CAMPAIGNS)
async def list_campaigns(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all campaigns for the tenant."""
    query = db.query(CRMCampaign).filter(
        CRMCampaign.tenant_id == current_user.tenant_id
    )
    if status:
        query = query.filter(CRMCampaign.status == status)
    total = query.count()
    campaigns = query.order_by(CRMCampaign.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "campaigns": campaigns}


@router.post("/")
@require_feature(Feature.CAMPAIGNS)
async def create_campaign(
    data: CampaignCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new campaign (starts as DRAFT)."""
    campaign = CRMCampaign(
        tenant_id=current_user.tenant_id,
        name=data.name,
        channel=data.channel,
        template_body=data.template_body,
        status=CampaignStatus.DRAFT,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("/{campaign_id}")
@require_feature(Feature.CAMPAIGNS)
async def get_campaign(
    campaign_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get campaign details with stats."""
    campaign = db.query(CRMCampaign).filter(
        CRMCampaign.id == campaign_id,
        CRMCampaign.tenant_id == current_user.tenant_id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.put("/{campaign_id}")
@require_feature(Feature.CAMPAIGNS)
async def update_campaign(
    campaign_id: UUID,
    data: CampaignUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update campaign (name, template, status)."""
    campaign = db.query(CRMCampaign).filter(
        CRMCampaign.id == campaign_id,
        CRMCampaign.tenant_id == current_user.tenant_id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(campaign, field, value)

    db.commit()
    db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}")
@require_feature(Feature.CAMPAIGNS)
async def delete_campaign(
    campaign_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a campaign (only DRAFT campaigns)."""
    campaign = db.query(CRMCampaign).filter(
        CRMCampaign.id == campaign_id,
        CRMCampaign.tenant_id == current_user.tenant_id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status != CampaignStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft campaigns can be deleted")

    db.delete(campaign)
    db.commit()
    return {"detail": "Campaign deleted"}


# ─── Campaign Contacts ───────────────────────────────────────────────

@router.post("/{campaign_id}/contacts")
@require_feature(Feature.CAMPAIGNS)
async def add_contacts_to_campaign(
    campaign_id: UUID,
    data: AddContactsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Add contacts to a campaign."""
    campaign = db.query(CRMCampaign).filter(
        CRMCampaign.id == campaign_id,
        CRMCampaign.tenant_id == current_user.tenant_id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    added = 0
    for contact_id in data.contact_ids:
        # Check contact belongs to tenant
        contact = db.query(CRMContact).filter(
            CRMContact.id == contact_id,
            CRMContact.tenant_id == current_user.tenant_id,
        ).first()
        if not contact:
            continue

        # Skip duplicates
        existing = db.query(CRMCampaignMessage).filter(
            CRMCampaignMessage.campaign_id == campaign_id,
            CRMCampaignMessage.contact_id == contact_id,
        ).first()
        if existing:
            continue

        msg = CRMCampaignMessage(
            campaign_id=campaign_id,
            contact_id=contact_id,
            status="pending",
        )
        db.add(msg)
        added += 1

    campaign.total_contacts = (campaign.total_contacts or 0) + added
    db.commit()
    return {"detail": f"{added} contacts added to campaign", "total": campaign.total_contacts}


@router.get("/{campaign_id}/messages")
@require_feature(Feature.CAMPAIGNS)
async def list_campaign_messages(
    campaign_id: UUID,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List messages in a campaign."""
    campaign = db.query(CRMCampaign).filter(
        CRMCampaign.id == campaign_id,
        CRMCampaign.tenant_id == current_user.tenant_id,
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    query = db.query(CRMCampaignMessage).filter(
        CRMCampaignMessage.campaign_id == campaign_id
    )
    if status:
        query = query.filter(CRMCampaignMessage.status == status)

    total = query.count()
    messages = query.offset(skip).limit(limit).all()
    return {"total": total, "messages": messages}

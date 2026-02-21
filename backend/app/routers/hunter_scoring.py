"""
Hunter Phase 4 Scoring API Endpoints
Endpoints for scoring leads and managing scoring profiles
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from ..database import get_db
from ..services.hunter_repository import HunterRepository
from ..services.hunter_scoring import HunterScoringEngine
from ..schemas.hunter import ScoringProfileResponse, ScoringProfileCreate, ScoringProfileUpdate
from ..core.auth import get_current_user, get_current_tenant
from ..models.user import User
from ..models.tenant import Tenant

router = APIRouter(prefix="/hunter", tags=["hunter"])

@router.post("/leads/{lead_id}/score")
def score_lead(
    lead_id: UUID,
    profile_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Score a lead using default or specified scoring profile"""
    repo = HunterRepository(db)
    
    # Check if lead exists
    lead = repo.get_lead_with_details(current_tenant.id, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get scoring profile
    profile_weights = None
    if profile_id:
        # Get specific profile
        profiles = repo.get_scoring_profiles(current_tenant.id)
        profile = next((p for p in profiles if p.id == profile_id), None)
        if not profile:
            raise HTTPException(status_code=404, detail="Scoring profile not found")
        profile_weights = profile.weights
    
    # Score the lead
    scoring_engine = HunterScoringEngine(repo)
    result = scoring_engine.score_lead(current_tenant.id, lead_id, profile_weights)
    
    # Update lead with score
    repo.update_lead_score(current_tenant.id, lead_id, result.total_score, result.breakdown)
    
    return {
        "lead_id": lead_id,
        "total_score": result.total_score,
        "max_score": result.max_score,
        "score_percentage": result.breakdown["score_percentage"],
        "signals": result.breakdown["signals"],
        "risk_flags": result.risk_flags,
        "breakdown": result.breakdown
    }

@router.get("/scoring/profiles", response_model=List[ScoringProfileResponse])
def list_scoring_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """List all scoring profiles for tenant"""
    repo = HunterRepository(db)
    profiles = repo.get_scoring_profiles(current_tenant.id)
    return [ScoringProfileResponse.from_orm(profile) for profile in profiles]

@router.post("/scoring/profiles", response_model=ScoringProfileResponse)
def create_scoring_profile(
    request: ScoringProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Create a new scoring profile"""
    repo = HunterRepository(db)
    
    # Validate weights structure
    required_keys = ["priority_countries", "risk_countries", "free_email_domains"]
    for key in required_keys:
        if key not in request.weights:
            raise HTTPException(status_code=400, detail=f"Missing required weight key: {key}")
    
    profile = repo.create_scoring_profile(
        tenant_id=current_tenant.id,
        name=request.name,
        weights=request.weights,
        is_default=request.is_default
    )
    
    return ScoringProfileResponse.from_orm(profile)

@router.get("/scoring/profiles/{profile_id}", response_model=ScoringProfileResponse)
def get_scoring_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get a specific scoring profile"""
    repo = HunterRepository(db)
    profiles = repo.get_scoring_profiles(current_tenant.id)
    profile = next((p for p in profiles if p.id == profile_id), None)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Scoring profile not found")
    
    return ScoringProfileResponse.from_orm(profile)

@router.patch("/scoring/profiles/{profile_id}", response_model=ScoringProfileResponse)
def update_scoring_profile(
    profile_id: UUID,
    request: ScoringProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Update a scoring profile"""
    repo = HunterRepository(db)
    
    # Get existing profile
    profiles = repo.get_scoring_profiles(current_tenant.id)
    profile = next((p for p in profiles if p.id == profile_id), None)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Scoring profile not found")
    
    # Update fields
    if request.name is not None:
        profile.name = request.name
    
    if request.weights is not None:
        # Validate weights structure
        required_keys = ["priority_countries", "risk_countries", "free_email_domains"]
        for key in required_keys:
            if key not in request.weights:
                raise HTTPException(status_code=400, detail=f"Missing required weight key: {key}")
        profile.weights = request.weights
    
    if request.is_default is not None:
        if request.is_default:
            # Unset other defaults
            repo.db.query(HunterScoringProfile).filter(
                HunterScoringProfile.tenant_id == current_tenant.id,
                HunterScoringProfile.is_default == True
            ).update({"is_default": False})
        profile.is_default = request.is_default
    
    repo.db.commit()
    repo.db.refresh(profile)
    
    return ScoringProfileResponse.from_orm(profile)

@router.post("/scoring/profiles/{profile_id}/set-default")
def set_default_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Set a scoring profile as default"""
    repo = HunterRepository(db)
    
    # Get existing profile
    profiles = repo.get_scoring_profiles(current_tenant.id)
    profile = next((p for p in profiles if p.id == profile_id), None)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Scoring profile not found")
    
    # Unset other defaults and set this one
    repo.db.query(HunterScoringProfile).filter(
        HunterScoringProfile.tenant_id == current_tenant.id,
        HunterScoringProfile.is_default == True
    ).update({"is_default": False})
    
    profile.is_default = True
    repo.db.commit()
    
    return {"message": f"Profile '{profile.name}' set as default"}

"""
Hunter Phase 4 Pydantic Schemas
Lead Intake API request/response models
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

# Enums matching database
class LeadStatus(str, Enum):
    NEW = "new"
    ENRICHED = "enriched"
    QUALIFIED = "qualified"
    REJECTED = "rejected"
    PUSHED_TO_CRM = "pushed_to_crm"

class IdentityType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    DOMAIN = "domain"
    LINKEDIN = "linkedin"
    ADDRESS = "address"
    OTHER = "other"

class EnrichmentStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

# Request Schemas
class ManualLeadRequest(BaseModel):
    primary_name: str = Field(..., min_length=1, max_length=255)
    country: str = Field(..., min_length=2, max_length=2)
    website: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)
    identities: Optional[List[Dict[str, str]]] = Field(default_factory=list)
    
    @validator('identities')
    def validate_identities(cls, v):
        if v:
            for identity in v:
                if 'type' not in identity or 'value' not in identity:
                    raise ValueError("Each identity must have 'type' and 'value'")
                if identity['type'] not in [t.value for t in IdentityType]:
                    raise ValueError(f"Identity type must be one of: {[t.value for t in IdentityType]}")
        return v

class IdentityCreate(BaseModel):
    type: IdentityType
    value: str = Field(..., min_length=1, max_length=500)

class ManualLeadWithIdentitiesRequest(BaseModel):
    primary_name: str = Field(..., min_length=1, max_length=255)
    country: str = Field(..., min_length=2, max_length=2)
    website: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)
    identities: Optional[List[IdentityCreate]] = Field(default_factory=list)

# Response Schemas
class IdentityResponse(BaseModel):
    id: UUID
    type: IdentityType
    value: str
    normalized_value: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class EvidenceResponse(BaseModel):
    id: UUID
    field_name: str
    source_name: str
    source_url: Optional[str]
    collected_at: datetime
    confidence: float
    snippet: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class LeadResponse(BaseModel):
    id: UUID
    primary_name: str
    country: str
    city: Optional[str]
    website: Optional[str]
    industry: Optional[str]
    source_hint: Optional[str]
    status: LeadStatus
    score_total: int
    score_breakdown: Dict[str, Any]
    created_at: datetime
    identities: List[IdentityResponse] = []
    evidence: List[EvidenceResponse] = []
    
    class Config:
        from_attributes = True

class LeadDetailResponse(LeadResponse):
    """Lead with grouped evidence for detail view"""
    evidence_by_field: Dict[str, List[EvidenceResponse]] = {}

class EnrichmentJobResponse(BaseModel):
    id: UUID
    provider: str
    status: EnrichmentStatus
    attempts: int
    scheduled_for: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True

# CSV Import
class CSVImportSummary(BaseModel):
    created: int = 0
    updated: int = 0
    skipped: int = 0
    duplicates: int = 0
    errors: List[str] = []

class TradeDataQueryRequest(BaseModel):
    hs_code: str = Field(..., min_length=4, max_length=10)
    importer_country: str = Field(..., min_length=2, max_length=2)
    min_volume: Optional[int] = Field(None, ge=0)

# Search/Filter
class LeadSearchRequest(BaseModel):
    status: Optional[LeadStatus] = None
    q: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    min_score: Optional[int] = Field(None, ge=0)
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)

# Scoring
class ScoringProfileResponse(BaseModel):
    id: UUID
    name: str
    weights: Dict[str, Any]
    is_default: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ScoringProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    weights: Dict[str, Any] = Field(..., min_items=1)
    is_default: bool = False

class ScoringProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    weights: Optional[Dict[str, Any]] = Field(None, min_items=1)
    is_default: Optional[bool] = None

# Qualification
class QualificationRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)

class RejectionRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)

# Push to CRM
class PushToCRMRequest(BaseModel):
    create_company: bool = True
    create_contact: bool = True
    create_task: bool = True
    task_due_days: int = Field(1, ge=0, le=30)

# Evidence Summary
class EvidenceSummaryResponse(BaseModel):
    lead_id: UUID
    field_counts: Dict[str, int]
    top_sources: Dict[str, List[str]]
    total_evidence: int
    last_collected: Optional[datetime]

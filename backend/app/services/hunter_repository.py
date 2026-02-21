"""
Hunter Phase 4 Repository Functions
Leads + Evidence + Enrichment Jobs + RLS
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime
import re

from ..models.hunter_phase4 import (
    HunterLead, HunterLeadIdentity, HunterEvidence, 
    HunterEnrichmentJob, HunterScoringProfile,
    hunter_lead_status_enum, hunter_identity_type_enum, hunter_enrichment_status_enum
)

def normalize_email(email: str) -> str:
    """Normalize email address for deduplication"""
    return email.lower().strip()

def normalize_phone(phone: str) -> str:
    """Normalize phone number for deduplication"""
    # Remove all non-numeric characters
    digits = re.sub(r'[^\d]', '', phone)
    # Basic E.164 format check
    if len(digits) >= 10:
        # If starts with country code, keep it, otherwise assume US
        if len(digits) == 10:
            digits = '1' + digits
        return '+' + digits
    return phone

def normalize_domain(domain: str) -> str:
    """Normalize domain for deduplication"""
    domain = domain.lower().strip()
    # Remove protocol and www
    domain = re.sub(r'^https?://', '', domain)
    domain = re.sub(r'^www\.', '', domain)
    # Remove trailing slash
    domain = domain.rstrip('/')
    return domain

class HunterRepository:
    """Repository for Hunter Phase 4 operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_lead(
        self, 
        tenant_id: UUID,
        primary_name: str,
        country: str,
        city: Optional[str] = None,
        website: Optional[str] = None,
        industry: Optional[str] = None,
        source_hint: Optional[str] = None
    ) -> HunterLead:
        """Create a new lead with basic evidence"""
        lead = HunterLead(
            tenant_id=tenant_id,
            primary_name=primary_name,
            country=country,
            city=city,
            website=website,
            industry=industry,
            source_hint=source_hint or "manual"
        )
        self.db.add(lead)
        self.db.flush()  # Get the ID
        
        # Add evidence for provided fields
        now = datetime.utcnow()
        
        if primary_name:
            self.attach_evidence(
                tenant_id=tenant_id,
                lead_id=lead.id,
                field_name="primary_name",
                source_name="manual",
                confidence=1.0,
                snippet=primary_name,
                collected_at=now
            )
        
        if country:
            self.attach_evidence(
                tenant_id=tenant_id,
                lead_id=lead.id,
                field_name="country",
                source_name="manual",
                confidence=1.0,
                snippet=country,
                collected_at=now
            )
        
        if city:
            self.attach_evidence(
                tenant_id=tenant_id,
                lead_id=lead.id,
                field_name="city",
                source_name="manual",
                confidence=1.0,
                snippet=city,
                collected_at=now
            )
        
        if website:
            self.attach_evidence(
                tenant_id=tenant_id,
                lead_id=lead.id,
                field_name="website",
                source_name="manual",
                confidence=1.0,
                snippet=website,
                collected_at=now
            )
            # Also add domain identity
            self.attach_identity(
                tenant_id=tenant_id,
                lead_id=lead.id,
                type="domain",
                value=website
            )
        
        if industry:
            self.attach_evidence(
                tenant_id=tenant_id,
                lead_id=lead.id,
                field_name="industry",
                source_name="manual",
                confidence=1.0,
                snippet=industry,
                collected_at=now
            )
        
        self.db.commit()
        return lead
    
    def attach_identity(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        type: str,  # email, phone, domain, linkedin, address, other
        value: str
    ) -> HunterLeadIdentity:
        """Attach identity to lead with normalization"""
        # Normalize based on type
        if type == "email":
            normalized = normalize_email(value)
        elif type == "phone":
            normalized = normalize_phone(value)
        elif type == "domain":
            normalized = normalize_domain(value)
        else:
            normalized = value.lower().strip()
        
        # Check if already exists
        existing = self.db.query(HunterLeadIdentity).filter(
            and_(
                HunterLeadIdentity.tenant_id == tenant_id,
                HunterLeadIdentity.type == type,
                HunterLeadIdentity.normalized_value == normalized
            )
        ).first()
        
        if existing:
            return existing
        
        identity = HunterLeadIdentity(
            tenant_id=tenant_id,
            lead_id=lead_id,
            type=type,
            value=value,
            normalized_value=normalized
        )
        self.db.add(identity)
        self.db.commit()
        return identity
    
    def attach_evidence(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        field_name: str,
        source_name: str,
        confidence: float,
        snippet: Optional[str] = None,
        source_url: Optional[str] = None,
        collected_at: Optional[datetime] = None,
        raw: Optional[Dict[str, Any]] = None
    ) -> HunterEvidence:
        """Attach evidence to lead"""
        if collected_at is None:
            collected_at = datetime.utcnow()
        
        evidence = HunterEvidence(
            tenant_id=tenant_id,
            lead_id=lead_id,
            field_name=field_name,
            source_name=source_name,
            source_url=source_url,
            collected_at=collected_at,
            confidence=confidence,
            snippet=snippet,
            raw=raw
        )
        self.db.add(evidence)
        self.db.commit()
        return evidence
    
    def enqueue_enrichment_job(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        provider: str,
        scheduled_for: Optional[datetime] = None
    ) -> HunterEnrichmentJob:
        """Enqueue enrichment job for lead"""
        if scheduled_for is None:
            scheduled_for = datetime.utcnow()
        
        job = HunterEnrichmentJob(
            tenant_id=tenant_id,
            lead_id=lead_id,
            provider=provider,
            status="queued",
            scheduled_for=scheduled_for
        )
        self.db.add(job)
        self.db.commit()
        return job
    
    def search_leads(
        self,
        tenant_id: UUID,
        query: Optional[str] = None,
        status: Optional[str] = None,
        country: Optional[str] = None,
        min_score: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[HunterLead]:
        """Search leads with filters"""
        filters = [HunterLead.tenant_id == tenant_id]
        
        if query:
            filters.append(
                or_(
                    HunterLead.primary_name.ilike(f"%{query}%"),
                    HunterLead.website.ilike(f"%{query}%"),
                    # Search identities
                    HunterLead.identities.any(
                        HunterLeadIdentity.value.ilike(f"%{query}%")
                    )
                )
            )
        
        if status:
            filters.append(HunterLead.status == status)
        
        if country:
            filters.append(HunterLead.country == country)
        
        if min_score is not None:
            filters.append(HunterLead.score_total >= min_score)
        
        return self.db.query(HunterLead).filter(
            and_(*filters)
        ).offset(offset).limit(limit).all()
    
    def get_lead_with_details(self, tenant_id: UUID, lead_id: UUID) -> Optional[HunterLead]:
        """Get lead with all related data"""
        lead = self.db.query(HunterLead).filter(
            and_(
                HunterLead.tenant_id == tenant_id,
                HunterLead.id == lead_id
            )
        ).first()
        return lead
    
    def group_evidence_by_field(self, evidence_list: List[HunterEvidence]) -> Dict[str, List[HunterEvidence]]:
        """Group evidence by field_name for display"""
        grouped = {}
        for evidence in evidence_list:
            if evidence.field_name not in grouped:
                grouped[evidence.field_name] = []
            grouped[evidence.field_name].append(evidence)
        return grouped
    
    def update_lead_status(self, tenant_id: UUID, lead_id: UUID, status: str) -> bool:
        """Update lead status"""
        lead = self.db.query(HunterLead).filter(
            and_(
                HunterLead.tenant_id == tenant_id,
                HunterLead.id == lead_id
            )
        ).first()
        
        if not lead:
            return False
        
        lead.status = status
        self.db.commit()
        return True
    
    def update_lead_score(self, tenant_id: UUID, lead_id: UUID, score_total: int, score_breakdown: Dict[str, Any]) -> bool:
        """Update lead score and breakdown"""
        lead = self.db.query(HunterLead).filter(
            and_(
                HunterLead.tenant_id == tenant_id,
                HunterLead.id == lead_id
            )
        ).first()
        
        if not lead:
            return False
        
        lead.score_total = score_total
        lead.score_breakdown = score_breakdown
        self.db.commit()
        return True
    
    def get_pending_enrichment_jobs(self, limit: int = 10) -> List[HunterEnrichmentJob]:
        """Get pending enrichment jobs for worker"""
        return self.db.query(HunterEnrichmentJob).filter(
            and_(
                HunterEnrichmentJob.status == "queued",
                HunterEnrichmentJob.scheduled_for <= datetime.utcnow()
            )
        ).order_by(HunterEnrichmentJob.scheduled_for).limit(limit).all()
    
    def update_job_status(
        self, 
        tenant_id: UUID, 
        job_id: UUID, 
        status: str, 
        error: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update enrichment job status"""
        job = self.db.query(HunterEnrichmentJob).filter(
            and_(
                HunterEnrichmentJob.tenant_id == tenant_id,
                HunterEnrichmentJob.id == job_id
            )
        ).first()
        
        if not job:
            return False
        
        job.status = status
        if status == "running":
            job.started_at = datetime.utcnow()
            job.attempts += 1
        elif status in ["done", "failed"]:
            job.finished_at = datetime.utcnow()
            if error:
                job.error = error
        
        self.db.commit()
        return True
    
    def create_scoring_profile(
        self,
        tenant_id: UUID,
        name: str,
        weights: Dict[str, Any],
        is_default: bool = False
    ) -> HunterScoringProfile:
        """Create scoring profile"""
        # If setting as default, unset other defaults
        if is_default:
            self.db.query(HunterScoringProfile).filter(
                and_(
                    HunterScoringProfile.tenant_id == tenant_id,
                    HunterScoringProfile.is_default == True
                )
            ).update({"is_default": False})
        
        profile = HunterScoringProfile(
            tenant_id=tenant_id,
            name=name,
            weights=weights,
            is_default=is_default
        )
        self.db.add(profile)
        self.db.commit()
        return profile
    
    def get_default_scoring_profile(self, tenant_id: UUID) -> Optional[HunterScoringProfile]:
        """Get default scoring profile for tenant"""
        return self.db.query(HunterScoringProfile).filter(
            and_(
                HunterScoringProfile.tenant_id == tenant_id,
                HunterScoringProfile.is_default == True
            )
        ).first()
    
    def get_scoring_profiles(self, tenant_id: UUID) -> List[HunterScoringProfile]:
        """Get all scoring profiles for tenant"""
        return self.db.query(HunterScoringProfile).filter(
            HunterScoringProfile.tenant_id == tenant_id
        ).all()

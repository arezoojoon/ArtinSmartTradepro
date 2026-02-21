"""
Hunter Phase 4 Guardrails Implementation
Anti-fake + evidence requirements + API contract validation
"""
from typing import Dict, List, Any, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from ..models.hunter_phase4 import HunterLead, HunterEvidence
from ..services.hunter_repository import HunterRepository

class HunterGuardrails:
    """
    Guardrails to prevent fake reporting and ensure evidence requirements
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = HunterRepository(db)
    
    def validate_lead_response(self, tenant_id: UUID, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate lead response to ensure no fake data and proper evidence references
        
        Args:
            tenant_id: Tenant ID for RLS
            lead_data: Lead data to validate
            
        Returns:
            Validated lead data with evidence requirements enforced
        """
        validated_data = lead_data.copy()
        
        # Get actual lead from database
        lead = self.repo.get_lead_with_details(tenant_id, UUID(lead_data['id']))
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Validate each field has proper evidence
        validated_fields = {}
        
        # Check required fields
        required_fields = ['primary_name', 'country']
        for field in required_fields:
            field_value = getattr(lead, field, None)
            if not field_value:
                validated_data[field] = None
                validated_data[f"{field}_evidence"] = "NO_EVIDENCE"
                validated_data[f"{field}_reason"] = f"Field '{field}' has no evidence"
            else:
                # Check if field has evidence
                field_evidence = [
                    e for e in lead.evidence 
                    if e.field_name == field
                ]
                if field_evidence:
                    validated_data[f"{field}_evidence"] = "HAS_EVIDENCE"
                    validated_data[f"{field}_top_source"] = field_evidence[0].source_name
                else:
                    validated_data[f"{field}_evidence"] = "NO_EVIDENCE"
                    validated_data[f"{field}_reason"] = f"Field '{field}' has no evidence"
        
        # Validate optional fields
        optional_fields = ['website', 'city', 'industry']
        for field in optional_fields:
            field_value = getattr(lead, field, None)
            if field_value:
                field_evidence = [
                    e for e in lead.evidence 
                    if e.field_name == field
                ]
                if field_evidence:
                    validated_data[f"{field}_evidence"] = "HAS_EVIDENCE"
                    validated_data[f"{field}_top_source"] = field_evidence[0].source_name
                else:
                    validated_data[f"{field}_evidence"] = "NO_EVIDENCE"
                    validated_data[f"{field}_reason"] = f"Field '{field}' has no evidence"
            else:
                validated_data[field] = None
                validated_data[f"{field}_evidence"] = "NO_DATA"
        
        # Validate identities
        if lead.identities:
            validated_identities = []
            for identity in lead.identities:
                # Check if identity has supporting evidence
                identity_evidence = [
                    e for e in lead.evidence 
                    if e.field_name == identity.type
                ]
                validated_identities.append({
                    **identity.__dict__,
                    "has_evidence": len(identity_evidence) > 0,
                    "evidence_count": len(identity_evidence),
                    "top_source": identity_evidence[0].source_name if identity_evidence else None
                })
            validated_data['identities'] = validated_identities
        else:
            validated_data['identities'] = []
        
        # Validate score breakdown
        if lead.score_total > 0:
            if not lead.score_breakdown:
                validated_data['score_evidence'] = "NO_EVIDENCE"
                validated_data['score_reason'] = "Score has no breakdown evidence"
            else:
                validated_data['score_evidence'] = "HAS_EVIDENCE"
                validated_data['score_breakdown'] = lead.score_breakdown
        else:
            validated_data['score_total'] = 0
            validated_data['score_evidence'] = "NO_DATA"
            validated_data['score_reason'] = "No score calculated"
        
        return validated_data
    
    def enforce_enrichment_evidence_requirement(self, tenant_id: UUID, lead_id: UUID) -> bool:
        """
        Enforce that 'enriched' status can only be set if evidence was added
        
        Args:
            tenant_id: Tenant ID for RLS
            lead_id: Lead ID to check
            
        Returns:
            True if requirement is met
        """
        lead = self.repo.get_lead_with_details(tenant_id, lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Count evidence added after creation
        creation_time = lead.created_at
        evidence_count = len([
            e for e in lead.evidence 
            if e.collected_at > creation_time
        ])
        
        return evidence_count >= 1
    
    def validate_evidence_summary(self, tenant_id: UUID, lead_id: UUID) -> Dict[str, Any]:
        """
        Generate evidence summary with counts and top sources
        
        Args:
            tenant_id: Tenant ID for RLS
            lead_id: Lead ID to summarize
            
        Returns:
            Evidence summary data
        """
        lead = self.repo.get_lead_with_details(tenant_id, lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Calculate field counts
        field_counts = {}
        top_sources = {}
        total_evidence = len(lead.evidence)
        last_collected = None
        
        for evidence in lead.evidence:
            # Count by field
            if evidence.field_name not in field_counts:
                field_counts[evidence.field_name] = 0
            field_counts[evidence.field_name] += 1
            
            # Track top sources per field
            if evidence.field_name not in top_sources:
                top_sources[evidence.field_name] = []
            if evidence.source_name not in top_sources[evidence.field_name]:
                top_sources[evidence.field_name].append(evidence.source_name)
            
            # Track last collected
            if last_collected is None or evidence.collected_at > last_collected:
                last_collected = evidence.collected_at
        
        return {
            "lead_id": str(lead_id),
            "field_counts": field_counts,
            "top_sources": top_sources,
            "total_evidence": total_evidence,
            "last_collected": last_collected,
            "evidence_by_field": self._group_evidence_by_field(lead.evidence),
            "identity_count": len(lead.identities),
            "has_website": bool(lead.website),
            "has_email": any(i.type == 'email' for i in lead.identities),
            "has_phone": any(i.type == 'phone' for i in lead.identities),
            "enrichment_possible": bool(lead.website) and lead.status == 'new'
        }
    
    def _group_evidence_by_field(self, evidence_list: List[HunterEvidence]) -> Dict[str, List[Dict[str, Any]]]:
        """Group evidence by field for display"""
        grouped = {}
        for evidence in evidence_list:
            if evidence.field_name not in grouped:
                grouped[evidence.field_name] = []
            grouped[evidence.field_name].append({
                "id": str(evidence.id),
                "source_name": evidence.source_name,
                "source_url": evidence.source_url,
                "collected_at": evidence.collected_at.isoformat(),
                "confidence": evidence.confidence,
                "snippet": evidence.snippet,
                "created_at": evidence.created_at.isoformat()
            })
        return grouped
    
    def check_data_quality(self, tenant_id: UUID, lead_id: UUID) -> Dict[str, Any]:
        """
        Check data quality metrics for a lead
        
        Args:
            tenant_id: Tenant ID for RLS
            lead_id: Lead ID to check
            
        Returns:
            Data quality metrics
        """
        lead = self.repo.get_lead_with_details(tenant_id, lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Calculate quality metrics
        metrics = {
            "completeness_score": 0,
            "freshness_score": 0,
            "confidence_score": 0,
            "source_diversity": 0,
            "risk_flags": []
        }
        
        # Completeness (0-30)
        completeness = 0
        if lead.primary_name: completeness += 10
        if lead.country: completeness += 10
        if lead.website: completeness += 5
        if lead.city: completeness += 5
        metrics["completeness_score"] = completeness
        
        # Freshness (0-20)
        if lead.evidence:
            latest = max(e.collected_at for e in lead.evidence)
            days_old = (datetime.utcnow() - latest).days
            if days_old <= 30:
                metrics["freshness_score"] = 20
            elif days_old <= 90:
                metrics["freshness_score"] = 10
            elif days_old <= 180:
                metrics["freshness_score"] = 5
        
        # Confidence (0-30)
        if lead.evidence:
            avg_confidence = sum(e.confidence for e in lead.evidence) / len(lead.evidence)
            metrics["confidence_score"] = int(avg_confidence * 30)
        
        # Source diversity (0-20)
        sources = set(e.source_name for e in lead.evidence)
        metrics["source_diversity"] = min(len(sources) * 4, 20)
        
        # Risk flags
        if not lead.website:
            metrics["risk_flags"].append("NO_WEBSITE")
        
        if not any(i.type == 'email' for i in lead.identities):
            metrics["risk_flags"].append("NO_EMAIL")
        
        if lead.country in ['IR', 'KP', 'SY', 'AF']:
            metrics["risk_flags"].append("HIGH_RISK_COUNTRY")
        
        # Check for free email domains
        free_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        for identity in lead.identities:
            if identity.type == 'email':
                domain = identity.value.split('@')[-1].lower()
                if domain in free_domains:
                    metrics["risk_flags"].append("FREE_EMAIL_DOMAIN")
                    break
        
        # Overall quality score (0-100)
        metrics["overall_score"] = (
            metrics["completeness_score"] +
            metrics["freshness_score"] +
            metrics["confidence_score"] +
            metrics["source_diversity"]
        )
        
        # Deduct points for risk flags
        metrics["overall_score"] = max(0, metrics["overall_score"] - len(metrics["risk_flags"]) * 5)
        
        return metrics

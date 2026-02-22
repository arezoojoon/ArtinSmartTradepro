"""
Hunter Phase 4 Qualification and CRM Integration
Qualification workflow + push to CRM functionality
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session
from ..models.hunter_phase4 import HunterLead, HunterEvidence, HunterLeadIdentity
from ..models.crm import CRMCompany, CRMContact, CRMTask, CRMNote
from ..models.audit import AuditLog
from ..services.hunter_repository import HunterRepository

class HunterQualificationService:
    """Service for lead qualification and CRM integration"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = HunterRepository(db)
    
    def qualify_lead(self, tenant_id: UUID, lead_id: UUID, reason: Optional[str] = None) -> bool:
        """
        Qualify a lead
        
        Args:
            tenant_id: Tenant ID for RLS
            lead_id: Lead ID to qualify
            reason: Optional qualification reason
            
        Returns:
            True if successful
        """
        lead = self.repo.get_lead_with_details(tenant_id, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        # Update lead status
        success = self.repo.update_lead_status(tenant_id, lead_id, "qualified")
        
        if success:
            # Log audit
            self._log_audit_action(
                tenant_id=tenant_id,
                action="hunter.qualify",
                resource_type="lead",
                resource_id=str(lead_id),
                details={"reason": reason, "lead_name": lead.primary_name}
            )
        
        return success
    
    def reject_lead(self, tenant_id: UUID, lead_id: UUID, reason: str) -> bool:
        """
        Reject a lead
        
        Args:
            tenant_id: Tenant ID for RLS
            lead_id: Lead ID to reject
            reason: Rejection reason (required)
            
        Returns:
            True if successful
        """
        if not reason:
            raise ValueError("Rejection reason is required")
        
        lead = self.repo.get_lead_with_details(tenant_id, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        # Update lead status
        success = self.repo.update_lead_status(tenant_id, lead_id, "rejected")
        
        if success:
            # Log audit
            self._log_audit_action(
                tenant_id=tenant_id,
                action="hunter.reject",
                resource_type="lead",
                resource_id=str(lead_id),
                details={"reason": reason, "lead_name": lead.primary_name}
            )
        
        return success
    
    def push_to_crm(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        create_company: bool = True,
        create_contact: bool = True,
        create_task: bool = True,
        task_due_days: int = 1
    ) -> Dict[str, Any]:
        """
        Push lead to CRM with evidence summary
        
        Args:
            tenant_id: Tenant ID for RLS
            lead_id: Lead ID to push
            create_company: Whether to create/match company
            create_contact: Whether to create contact
            create_task: Whether to create follow-up task
            task_due_days: Days until task is due
            
        Returns:
            Dictionary with created CRM objects
        """
        lead = self.repo.get_lead_with_details(tenant_id, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        if lead.status not in ["qualified", "enriched"]:
            raise ValueError(f"Lead must be qualified or enriched to push to CRM. Current status: {lead.status}")
        
        result = {
            "company": None,
            "contact": None,
            "task": None,
            "note": None,
            "evidence_summary": self._create_evidence_summary(lead.evidence)
        }
        
        try:
            # Create or match company
            if create_company:
                result["company"] = self._create_or_match_company(tenant_id, lead)
            
            # Create contact
            if create_contact:
                result["contact"] = self._create_contact(tenant_id, lead, result["company"])
            
            # Create CRM note with evidence summary
            result["note"] = self._create_evidence_note(tenant_id, lead, result["company"], result["contact"])
            
            # Create follow-up task
            if create_task:
                result["task"] = self._create_follow_up_task(tenant_id, lead, result["company"], result["contact"], task_due_days)
            
            # Update lead status
            self.repo.update_lead_status(tenant_id, lead_id, "pushed_to_crm")
            
            # Log audit
            self._log_audit_action(
                tenant_id=tenant_id,
                action="hunter.push_to_crm",
                resource_type="lead",
                resource_id=str(lead_id),
                details={
                    "lead_name": lead.primary_name,
                    "company_id": str(result["company"].id) if result["company"] else None,
                    "contact_id": str(result["contact"].id) if result["contact"] else None,
                    "task_id": str(result["task"].id) if result["task"] else None
                }
            )
            
            return result
            
        except Exception as e:
            # Log error but don't crash
            self._log_audit_action(
                tenant_id=tenant_id,
                action="hunter.push_to_crm.error",
                resource_type="lead",
                resource_id=str(lead_id),
                details={"error": str(e), "lead_name": lead.primary_name}
            )
            raise
    
    def _create_or_match_company(self, tenant_id: UUID, lead: HunterLead) -> CRMCompany:
        """Create or match CRM company"""
        # Try to match existing company by website domain or name
        company = None
        
        if lead.website:
            # Extract domain from website
            domain = self._extract_domain(lead.website)
            if domain:
                company = self.db.query(CRMCompany).filter(
                    CRMCompany.tenant_id == tenant_id,
                    CRMCompany.website.ilike(f"%{domain}%")
                ).first()
        
        if not company and lead.primary_name:
            # Try to match by name
            company = self.db.query(CRMCompany).filter(
                CRMCompany.tenant_id == tenant_id,
                CRMCompany.name.ilike(f"%{lead.primary_name}%")
            ).first()
        
        if company:
            return company
        
        # Create new company
        company = CRMCompany(
            tenant_id=tenant_id,
            name=lead.primary_name,
            website=lead.website,
            country=lead.country,
            city=lead.city,
            industry=lead.industry,
            source="hunter"
        )
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        
        return company
    
    def _create_contact(self, tenant_id: UUID, lead: HunterLead, company: Optional[CRMCompany]) -> Optional[CRMContact]:
        """Create CRM contact from lead identities"""
        # Get email and phone identities
        email_identity = None
        phone_identity = None
        
        for identity in lead.identities:
            if identity.type == "email" and not email_identity:
                email_identity = identity
            elif identity.type == "phone" and not phone_identity:
                phone_identity = identity
        
        if not email_identity and not phone_identity:
            return None  # No contact info
        
        # Check if contact already exists
        contact = None
        if email_identity:
            contact = self.db.query(CRMContact).filter(
                CRMContact.tenant_id == tenant_id,
                CRMContact.email == email_identity.value
            ).first()
        
        if contact:
            return contact
        
        # Create new contact
        contact = CRMContact(
            tenant_id=tenant_id,
            first_name=lead.primary_name.split()[0] if lead.primary_name else "",
            last_name=" ".join(lead.primary_name.split()[1:]) if len(lead.primary_name.split()) > 1 else "",
            email=email_identity.value if email_identity else None,
            phone=phone_identity.value if phone_identity else None,
            company_id=company.id if company else None,
            source="hunter"
        )
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        
        return contact
    
    def _create_evidence_summary(self, evidence_list: List[HunterEvidence]) -> Dict[str, Any]:
        """Create summary of evidence for CRM note"""
        summary = {
            "total_evidence": len(evidence_list),
            "fields": {},
            "sources": set(),
            "latest_collection": None
        }
        
        # Group evidence by field
        for evidence in evidence_list:
            field_name = evidence.field_name
            if field_name not in summary["fields"]:
                summary["fields"][field_name] = []
            
            summary["fields"][field_name].append({
                "source": evidence.source_name,
                "url": evidence.source_url,
                "confidence": evidence.confidence,
                "snippet": evidence.snippet,
                "collected_at": evidence.collected_at.isoformat()
            })
            
            summary["sources"].add(evidence.source_name)
            
            if (summary["latest_collection"] is None or 
                evidence.collected_at > summary["latest_collection"]):
                summary["latest_collection"] = evidence.collected_at
        
        summary["sources"] = list(summary["sources"])
        return summary
    
    def _create_evidence_note(
        self,
        tenant_id: UUID,
        lead: HunterLead,
        company: Optional[CRMCompany],
        contact: Optional[CRMContact]
    ) -> CRMNote:
        """Create CRM note with evidence summary"""
        evidence_summary = self._create_evidence_summary(lead.evidence)
        
        # Format note content
        note_content = f"Hunter Lead: {lead.primary_name}\\n\\n"
        note_content += f"Country: {lead.country}\\n"
        if lead.city:
            note_content += f"City: {lead.city}\\n"
        if lead.website:
            note_content += f"Website: {lead.website}\\n"
        
        note_content += f"\\nEvidence Summary:\\n"
        note_content += f"- Total evidence items: {evidence_summary['total_evidence']}\\n"
        note_content += f"- Data sources: {', '.join(evidence_summary['sources'])}\\n"
        
        if evidence_summary['latest_collection']:
            note_content += f"- Latest data: {evidence_summary['latest_collection'].strftime('%Y-%m-%d')}\\n"
        
        note_content += "\\nField Details:\\n"
        for field_name, field_evidence in evidence_summary['fields'].items():
            note_content += f"\\n{field_name.title()}:\\n"
            for evidence in field_evidence[:3]:  # Limit to top 3 per field
                note_content += f"  - {evidence['source']}: {evidence['snippet'] or 'No snippet'}\\n"
        
        note = CRMNote(
            tenant_id=tenant_id,
            company_id=company.id if company else None,
            contact_id=contact.id if contact else None,
            content=note_content,
            source="hunter",
            created_by="system"
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        
        return note
    
    def _create_follow_up_task(
        self,
        tenant_id: UUID,
        lead: HunterLead,
        company: Optional[CRMCompany],
        contact: Optional[CRMContact],
        due_days: int
    ) -> CRMTask:
        """Create follow-up task"""
        due_date = datetime.utcnow() + timedelta(days=due_days)
        
        task = CRMTask(
            tenant_id=tenant_id,
            title=f"Follow up new lead: {lead.primary_name}",
            description=f"New qualified lead from Hunter. Country: {lead.country}. Score: {lead.score_total}.",
            status="pending",
            priority="medium" if lead.score_total >= 50 else "low",
            due_date=due_date,
            company_id=company.id if company else None,
            contact_id=contact.id if contact else None,
            assigned_to=None,  # Will be assigned to default user
            source="hunter"
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def _extract_domain(self, website: str) -> Optional[str]:
        """Extract domain from website URL"""
        if not website:
            return None
        
        # Remove protocol
        website = website.replace("https://", "").replace("http://", "")
        # Remove www
        website = website.replace("www.", "")
        # Remove path
        website = website.split("/")[0]
        
        return website
    
    def _log_audit_action(self, tenant_id: UUID, action: str, resource_type: str, resource_id: str, details: Dict[str, Any]):
        """Log audit action"""
        audit_log = AuditLog(
            tenant_id=tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address="system",
            user_agent="hunter-service"
        )
        self.db.add(audit_log)
        self.db.commit()

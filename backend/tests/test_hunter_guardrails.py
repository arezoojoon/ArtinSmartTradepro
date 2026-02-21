"""
Hunter Phase 4 Guardrails Tests
Test anti-fake, evidence requirements, and API contract validation
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.services.hunter_guardrails import HunterGuardrails
from app.services.hunter_repository import HunterRepository
from app.models.hunter_phase4 import HunterLead, HunterEvidence, HunterLeadIdentity
from app.models.user import User
from app.models.tenant import Tenant

client = TestClient(app)

class TestHunterGuardrails:
    """Test Hunter guardrails functionality"""
    
    @pytest.fixture
    def test_tenant(self, db_session: Session):
        """Create test tenant"""
        tenant = Tenant(
            id=uuid4(),
            name="Test Tenant",
            domain="test.example.com",
            settings={}
        )
        db_session.add(tenant)
        db_session.commit()
        return tenant
    
    @pytest.fixture
    def test_user(self, db_session: Session, test_tenant: Tenant):
        """Create test user"""
        user = User(
            id=uuid4(),
            email="test@example.com",
            current_tenant_id=test_tenant.id
        )
        db_session.add(user)
        db_session.commit()
        return user
    
    @pytest.fixture
    def test_lead(self, db_session: Session, test_tenant: Tenant):
        """Create test lead with evidence"""
        lead = HunterLead(
            id=uuid4(),
            tenant_id=test_tenant.id,
            primary_name="Test Company",
            country="US",
            website="https://testcompany.com",
            status="enriched"
        )
        db_session.add(lead)
        db_session.commit()
        
        # Add evidence
        repo = HunterRepository(db_session)
        repo.attach_evidence(
            test_tenant.id, lead.id, "primary_name", "manual", 1.0,
            snippet="Test Company", collected_at=datetime.utcnow()
        )
        repo.attach_evidence(
            test_tenant.id, lead.id, "website", "web_scrape", 0.8,
            snippet="https://testcompany.com", collected_at=datetime.utcnow()
        )
        repo.attach_identity(test_tenant.id, lead.id, "email", "contact@testcompany.com")
        
        return lead
    
    @pytest.fixture
    def guardrails(self, db_session: Session):
        """Create guardrails instance"""
        return HunterGuardrails(db_session)
    
    def test_validate_lead_response_complete_data(self, guardrails: HunterGuardrails, test_lead: HunterLead, test_tenant: Tenant):
        """Test validating lead with complete data"""
        lead_data = {
            "id": str(test_lead.id),
            "primary_name": test_lead.primary_name,
            "country": test_lead.country,
            "website": test_lead.website,
            "status": test_lead.status
        }
        
        result = guardrails.validate_lead_response(test_tenant.id, lead_data)
        
        assert result["primary_name_evidence"] == "HAS_EVIDENCE"
        assert result["primary_name_top_source"] == "manual"
        assert result["website_evidence"] == "HAS_EVIDENCE"
        assert result["website_top_source"] == "web_scrape"
        assert result["country_evidence"] == "HAS_EVIDENCE"
        assert result["country_top_source"] == "manual"
        
        # Check identities
        assert len(result["identities"]) == 1
        assert result["identities"][0]["has_evidence"] is True
        assert result["identities"][0]["type"] == "email"
    
    def test_validate_lead_response_missing_evidence(self, guardrails: HunterGuardrails, test_tenant: Tenant, db_session: Session):
        """Test validating lead with missing evidence"""
        # Create lead without evidence
        lead = HunterLead(
            id=uuid4(),
            tenant_id=test_tenant.id,
            primary_name="No Evidence Company",
            country="US"
        )
        db_session.add(lead)
        db_session.commit()
        
        lead_data = {
            "id": str(lead.id),
            "primary_name": lead.primary_name,
            "country": lead.country,
            "website": None,
            "status": lead.status
        }
        
        result = guardrails.validate_lead_response(test_tenant.id, lead_data)
        
        assert result["primary_name_evidence"] == "NO_EVIDENCE"
        assert result["primary_name_reason"] == "Field 'primary_name' has no evidence"
        assert result["website_evidence"] == "NO_DATA"
        assert result["website_reason"] == "Field 'website' has no evidence"
    
    def test_enrichment_evidence_requirement_met(self, guardrails: HunterGuardrails, test_lead: HunterLead, test_tenant: Tenant):
        """Test enrichment requirement when evidence exists"""
        # Lead already has evidence from creation, but check if there's newer evidence
        repo = HunterRepository(db_session)
        
        # Add new evidence after creation
        repo.attach_evidence(
            test_tenant.id, test_lead.id, "email", "web_scrape", 0.7,
            snippet="contact@testcompany.com", 
            collected_at=test_lead.created_at + timedelta(hours=1)
        )
        
        result = guardrails.enforce_enrichment_evidence_requirement(test_tenant.id, test_lead.id)
        assert result is True
    
    def test_enrichment_evidence_requirement_not_met(self, guardrails: HunterGuardrails, test_tenant: Tenant, db_session: Session):
        """Test enrichment requirement when no new evidence"""
        # Create lead without any evidence after creation
        lead = HunterLead(
            id=uuid4(),
            tenant_id=test_tenant.id,
            primary_name="No New Evidence",
            country="US"
        )
        db_session.add(lead)
        db_session.commit()
        
        result = guardrails.enforce_enrichment_evidence_requirement(test_tenant.id, lead.id)
        assert result is False
    
    def test_evidence_summary(self, guardrails: HunterGuardrails, test_lead: HunterLead, test_tenant: Tenant):
        """Test evidence summary generation"""
        summary = guardrails.validate_evidence_summary(test_tenant.id, test_lead.id)
        
        assert summary["lead_id"] == str(test_lead.id)
        assert summary["total_evidence"] == 2  # primary_name + website
        assert "primary_name" in summary["field_counts"]
        assert "website" in summary["field_counts"]
        assert summary["field_counts"]["primary_name"] == 1
        assert summary["field_counts"]["website"] == 1
        assert "manual" in summary["top_sources"]["primary_name"]
        assert "web_scrape" in summary["top_sources"]["website"]
        assert summary["identity_count"] == 1
        assert summary["has_website"] is True
        assert summary["has_email"] is True
        assert summary["has_phone"] is False
    
    def test_data_quality_high_quality(self, guardrails: HunterGuardrails, test_lead: HunterLead, test_tenant: Tenant):
        """Test data quality metrics for high-quality lead"""
        quality = guardrails.check_data_quality(test_tenant.id, test_lead.id)
        
        assert quality["completeness_score"] == 30  # name + country + website + city + industry
        assert quality["freshness_score"] == 20  # Recent evidence
        assert quality["confidence_score"] >= 20  # Average confidence
        assert quality["source_diversity"] >= 8  # 2 sources * 4
        assert len(quality["risk_flags"]) == 0  # No risk flags
        assert quality["overall_score"] >= 80
    
    def test_data_quality_low_quality(self, guardrails: HunterGuardrails, test_tenant: Tenant, db_session: Session):
        """Test data quality metrics for low-quality lead"""
        # Create low-quality lead
        lead = HunterLead(
            id=uuid4(),
            tenant_id=test_tenant.id,
            primary_name="Low Quality",
            country="IR",  # High risk country
            status="new"
        )
        db_session.add(lead)
        db_session.commit()
        
        # Add old, low-confidence evidence
        repo = HunterRepository(db_session)
        repo.attach_evidence(
            test_tenant.id, lead.id, "primary_name", "manual", 0.3,
            snippet="Low Quality", collected_at=datetime.utcnow() - timedelta(days=100)
        )
        repo.attach_identity(test_tenant.id, lead.id, "email", "contact@gmail.com")
        
        quality = guardrails.check_data_quality(test_tenant.id, lead.id)
        
        assert quality["completeness_score"] == 10  # Only name + country
        assert quality["freshness_score"] == 0  # Old evidence
        assert quality["confidence_score"] <= 10  # Low confidence
        assert quality["source_diversity"] == 4  # 1 source * 4
        assert "NO_WEBSITE" in quality["risk_flags"]
        assert "FREE_EMAIL_DOMAIN" in quality["risk_flags"]
        assert "HIGH_RISK_COUNTRY" in quality["risk_flags"]
        assert quality["overall_score"] <= 20

class TestGuardrailsAPI:
    """Test guardrails API endpoints"""
    
    @pytest.fixture
    def test_tenant(self, db_session: Session):
        """Create test tenant"""
        tenant = Tenant(
            id=uuid4(),
            name="Test Tenant",
            domain="test.example.com",
            settings={}
        )
        db_session.add(tenant)
        db_session.commit()
        return tenant
    
    @pytest.fixture
    def test_user(self, db_session: Session, test_tenant: Tenant):
        """Create test user"""
        user = User(
            id=uuid4(),
            email="test@example.com",
            current_tenant_id=test_tenant.id
        )
        db_session.add(user)
        db_session.commit()
        return user
    
    @pytest.fixture
    def test_lead(self, db_session: Session, test_tenant: Tenant):
        """Create test lead"""
        lead = HunterLead(
            id=uuid4(),
            tenant_id=test_tenant.id,
            primary_name="Test Company",
            country="US",
            website="https://testcompany.com"
        )
        db_session.add(lead)
        db_session.commit()
        
        # Add evidence
        repo = HunterRepository(db_session)
        repo.attach_evidence(
            test_tenant.id, lead.id, "primary_name", "manual", 1.0,
            snippet="Test Company", collected_at=datetime.utcnow()
        )
        
        return lead
    
    def test_get_evidence_summary(self, test_user: User, test_tenant: Tenant, test_lead: HunterLead):
        """Test evidence summary endpoint"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.get(f"/hunter/leads/{test_lead.id}/evidence/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert data["lead_id"] == str(test_lead.id)
        assert data["total_evidence"] == 1
        assert "primary_name" in data["field_counts"]
        assert data["identity_count"] == 0  # No identities in this test
        
        app.dependency_overrides.clear()
    
    def test_get_lead_quality(self, test_user: User, test_tenant: Tenant, test_lead: HunterLead):
        """Test lead quality endpoint"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.get(f"/hunter/leads/{test_lead.id}/quality")
        assert response.status_code == 200
        
        data = response.json()
        assert "completeness_score" in data
        assert "freshness_score" in data
        assert "confidence_score" in data
        assert "source_diversity" in data
        assert "risk_flags" in data
        assert "overall_score" in data
        
        app.dependency_overrides.clear()
    
    def test_validate_lead_data(self, test_user: User, test_tenant: Tenant, test_lead: HunterLead):
        """Test lead validation endpoint"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.get(f"/hunter/leads/{test_lead.id}/validate")
        assert response.status_code == 200
        
        data = response.json()
        assert data["primary_name_evidence"] == "HAS_EVIDENCE"
        assert data["country_evidence"] == "NO_EVIDENCE"  # No country evidence added
        assert data["website_evidence"] == "NO_DATA"  # No website evidence added
        
        app.dependency_overrides.clear()
    
    def test_validate_enrichment_eligibility(self, test_user: User, test_tenant: Tenant, test_lead: HunterLead):
        """Test enrichment eligibility validation"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.post(f"/hunter/leads/{test_lead.id}/enrich/validate")
        assert response.status_code == 200
        
        data = response.json()
        assert "lead_id" in data
        assert "meets_requirement" in data
        assert "message" in data
        
        # Should not meet requirement since no new evidence
        assert data["meets_requirement"] is False
        
        app.dependency_overrides.clear()
    
    def test_health_check(self, test_user: User, test_tenant: Tenant):
        """Test evidence health check endpoint"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.get("/hunter/health/evidence")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_leads" in data
        assert "total_evidence" in data
        assert "avg_evidence_per_lead" in data
        assert "source_distribution" in data
        assert "field_distribution" in data
        assert "avg_confidence" in data
        assert "recent_evidence_count" in data
        
        app.dependency_overrides.clear()
    
    def test_validate_nonexistent_lead(self, test_user: User, test_tenant: Tenant):
        """Test validation with non-existent lead"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        fake_id = uuid4()
        response = client.get(f"/hunter/leads/{fake_id}/validate")
        assert response.status_code == 404
        
        app.dependency_overrides.clear()

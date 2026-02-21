"""
Hunter Phase 4 Qualification Tests
Test qualification workflow and CRM integration
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.services.hunter_qualification import HunterQualificationService
from app.services.hunter_repository import HunterRepository
from app.models.hunter_phase4 import HunterLead, HunterLeadIdentity, HunterEvidence
from app.models.crm import CRMCompany, CRMContact, CRMTask, CRMNote
from app.models.user import User
from app.models.tenant import Tenant

client = TestClient(app)

class TestHunterQualificationService:
    """Test Hunter qualification service"""
    
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
    def test_lead(self, db_session: Session, test_tenant: Tenant):
        """Create test lead"""
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
        return lead
    
    @pytest.fixture
    def service(self, db_session: Session):
        """Create qualification service"""
        return HunterQualificationService(db_session)
    
    def test_qualify_lead(self, service: HunterQualificationService, test_lead: HunterLead, test_tenant: Tenant):
        """Test qualifying a lead"""
        success = service.qualify_lead(test_tenant.id, test_lead.id, "Good fit for our services")
        
        assert success is True
        
        # Check lead status updated
        updated_lead = service.repo.get_lead_with_details(test_tenant.id, test_lead.id)
        assert updated_lead.status == "qualified"
    
    def test_reject_lead(self, service: HunterQualificationService, test_lead: HunterLead, test_tenant: Tenant):
        """Test rejecting a lead"""
        success = service.reject_lead(test_tenant.id, test_lead.id, "Not in our target market")
        
        assert success is True
        
        # Check lead status updated
        updated_lead = service.repo.get_lead_with_details(test_tenant.id, test_lead.id)
        assert updated_lead.status == "rejected"
    
    def test_reject_lead_no_reason(self, service: HunterQualificationService, test_lead: HunterLead, test_tenant: Tenant):
        """Test rejecting lead without reason should fail"""
        with pytest.raises(ValueError, match="Rejection reason is required"):
            service.reject_lead(test_tenant.id, test_lead.id, "")
    
    def test_push_to_crm_new_company_contact(self, service: HunterQualificationService, test_lead: HunterLead, test_tenant: Tenant, db_session: Session):
        """Test pushing lead to CRM creates new company and contact"""
        # Add identities to lead
        service.repo.attach_identity(test_tenant.id, test_lead.id, "email", "contact@testcompany.com")
        service.repo.attach_identity(test_tenant.id, test_lead.id, "phone", "+1-555-123-4567")
        
        # Add evidence
        service.repo.attach_evidence(
            test_tenant.id, test_lead.id, "website", "manual", 1.0,
            snippet="https://testcompany.com", collected_at=datetime.utcnow()
        )
        
        # Push to CRM
        result = service.push_to_crm(test_tenant.id, test_lead.id)
        
        # Check results
        assert result["company"] is not None
        assert result["company"].name == "Test Company"
        assert result["company"].website == "https://testcompany.com"
        
        assert result["contact"] is not None
        assert result["contact"].email == "contact@testcompany.com"
        assert result["contact"].phone == "+1-555-123-4567"
        
        assert result["task"] is not None
        assert "Follow up new lead" in result["task"].title
        
        assert result["note"] is not None
        assert "Hunter Lead" in result["note"].content
        
        # Check lead status updated
        updated_lead = service.repo.get_lead_with_details(test_tenant.id, test_lead.id)
        assert updated_lead.status == "pushed_to_crm"
    
    def test_push_to_crm_existing_company(self, service: HunterQualificationService, test_lead: HunterLead, test_tenant: Tenant, db_session: Session):
        """Test pushing lead matches existing company"""
        # Create existing company
        existing_company = CRMCompany(
            tenant_id=test_tenant.id,
            name="Test Company",
            website="https://testcompany.com",
            country="US"
        )
        db_session.add(existing_company)
        db_session.commit()
        
        # Push lead to CRM
        result = service.push_to_crm(test_tenant.id, test_lead.id)
        
        # Should use existing company
        assert result["company"].id == existing_company.id
        assert result["company"].name == "Test Company"
    
    def test_push_to_crm_no_contact_info(self, service: HunterQualificationService, test_lead: HunterLead, test_tenant: Tenant):
        """Test pushing lead without contact info"""
        # Lead has no identities
        
        result = service.push_to_crm(test_tenant.id, test_lead.id, create_contact=True)
        
        # Should create company but no contact
        assert result["company"] is not None
        assert result["contact"] is None
    
    def test_push_to_crm_wrong_status(self, service: HunterQualificationService, test_lead: HunterLead, test_tenant: Tenant):
        """Test pushing lead with wrong status should fail"""
        # Set lead to new status
        service.repo.update_lead_status(test_tenant.id, test_lead.id, "new")
        
        with pytest.raises(ValueError, match="must be qualified or enriched"):
            service.push_to_crm(test_tenant.id, test_lead.id)
    
    def test_idempotent_push(self, service: HunterQualificationService, test_lead: HunterLead, test_tenant: Tenant, db_session: Session):
        """Test pushing same lead twice is idempotent"""
        # Add email identity
        service.repo.attach_identity(test_tenant.id, test_lead.id, "email", "contact@testcompany.com")
        
        # First push
        result1 = service.push_to_crm(test_tenant.id, test_lead.id)
        
        # Second push
        result2 = service.push_to_crm(test_tenant.id, test_lead.id)
        
        # Should reuse same company and contact
        assert result1["company"].id == result2["company"].id
        assert result1["contact"].id == result2["contact"].id
    
    def test_evidence_summary(self, service: HunterQualificationService, test_lead: HunterLead, test_tenant: Tenant):
        """Test evidence summary creation"""
        # Add evidence
        service.repo.attach_evidence(
            test_tenant.id, test_lead.id, "website", "manual", 1.0,
            snippet="https://testcompany.com", collected_at=datetime.utcnow()
        )
        service.repo.attach_evidence(
            test_tenant.id, test_lead.id, "email", "web_scrape", 0.8,
            snippet="contact@testcompany.com", collected_at=datetime.utcnow()
        )
        
        summary = service._create_evidence_summary(test_lead.evidence)
        
        assert summary["total_evidence"] == 2
        assert "website" in summary["fields"]
        assert "email" in summary["fields"]
        assert "manual" in summary["sources"]
        assert "web_scrape" in summary["sources"]
        assert len(summary["fields"]["website"]) == 1
        assert len(summary["fields"]["email"]) == 1

class TestQualificationAPI:
    """Test qualification API endpoints"""
    
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
            website="https://testcompany.com",
            status="enriched"
        )
        db_session.add(lead)
        db_session.commit()
        return lead
    
    def test_qualify_lead_api(self, test_user: User, test_tenant: Tenant, test_lead: HunterLead):
        """Test qualifying lead via API"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        request_data = {"reason": "Good fit for our services"}
        response = client.post(f"/hunter/leads/{test_lead.id}/qualify", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "qualified successfully" in data["message"]
        assert str(test_lead.id) in data["lead_id"]
        
        app.dependency_overrides.clear()
    
    def test_reject_lead_api(self, test_user: User, test_tenant: Tenant, test_lead: HunterLead):
        """Test rejecting lead via API"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        request_data = {"reason": "Not in our target market"}
        response = client.post(f"/hunter/leads/{test_lead.id}/reject", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "rejected successfully" in data["message"]
        
        app.dependency_overrides.clear()
    
    def test_reject_lead_no_reason_api(self, test_user: User, test_tenant: Tenant, test_lead: HunterLead):
        """Test rejecting lead without reason via API"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        request_data = {"reason": ""}
        response = client.post(f"/hunter/leads/{test_lead.id}/reject", json=request_data)
        
        assert response.status_code == 400
        
        app.dependency_overrides.clear()
    
    def test_push_to_crm_api(self, test_user: User, test_tenant: Tenant, test_lead: HunterLead, db_session: Session):
        """Test pushing lead to CRM via API"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        # Add email identity
        repo = HunterRepository(db_session)
        repo.attach_identity(test_tenant.id, test_lead.id, "email", "contact@testcompany.com")
        
        request_data = {
            "create_company": True,
            "create_contact": True,
            "create_task": True,
            "task_due_days": 3
        }
        response = client.post(f"/hunter/leads/{test_lead.id}/push-to-crm", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "pushed to CRM successfully" in data["message"]
        assert data["company_id"] is not None
        assert data["contact_id"] is not None
        assert data["task_id"] is not None
        assert data["note_id"] is not None
        assert "evidence_summary" in data
        
        app.dependency_overrides.clear()
    
    def test_get_crm_status_api(self, test_user: User, test_tenant: Tenant, test_lead: HunterLead):
        """Test getting CRM status via API"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.get(f"/hunter/leads/{test_lead.id}/crm-status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["lead_id"] == str(test_lead.id)
        assert data["lead_status"] == test_lead.status
        assert data["crm_company"] is None  # No CRM objects yet
        assert data["can_push"] is True  # Lead is enriched and not pushed
        
        app.dependency_overrides.clear()
    
    def test_get_crm_status_nonexistent_lead(self, test_user: User, test_tenant: Tenant):
        """Test getting CRM status for non-existent lead"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        fake_id = uuid4()
        response = client.get(f"/hunter/leads/{fake_id}/crm-status")
        
        assert response.status_code == 404
        assert "Lead not found" in response.json()["detail"]
        
        app.dependency_overrides.clear()

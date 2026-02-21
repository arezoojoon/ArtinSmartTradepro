"""
Hunter Phase 4 Tests
Test manual lead creation, CSV import, and search functionality
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4
import io
import csv

from app.main import app
from app.services.hunter_repository import HunterRepository
from app.models.user import User
from app.models.tenant import Tenant

client = TestClient(app)

class TestHunterPhase4:
    """Test Hunter Phase 4 functionality"""
    
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
    
    def test_create_manual_lead_success(self, db_session: Session, test_user: User, test_tenant: Tenant):
        """Test successful manual lead creation"""
        # Mock authentication
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        request_data = {
            "primary_name": "Test Company",
            "country": "US",
            "website": "https://testcompany.com",
            "city": "New York",
            "industry": "Technology",
            "identities": [
                {"type": "email", "value": "contact@testcompany.com"},
                {"type": "phone", "value": "+1-555-0123"}
            ]
        }
        
        response = client.post("/hunter/leads/manual", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["primary_name"] == "Test Company"
        assert data["country"] == "US"
        assert data["website"] == "https://testcompany.com"
        assert data["status"] == "new"
        assert len(data["identities"]) == 3  # email, phone, domain (from website)
        
        # Clean up
        app.dependency_overrides.clear()
    
    def test_create_manual_lead_validation_error(self, test_user: User, test_tenant: Tenant):
        """Test manual lead creation with invalid data"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        # Missing required field
        request_data = {
            "country": "US"
        }
        
        response = client.post("/hunter/leads/manual", json=request_data)
        assert response.status_code == 422
        
        app.dependency_overrides.clear()
    
    def test_csv_import_success(self, db_session: Session, test_user: User, test_tenant: Tenant):
        """Test successful CSV import"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        # Create test CSV content
        csv_content = io.StringIO()
        writer = csv.writer(csv_content)
        writer.writerow(['name', 'country', 'website', 'email', 'phone', 'city', 'industry'])
        writer.writerow(['Company A', 'US', 'https://companya.com', 'info@companya.com', '+1-555-0101', 'Boston', 'Software'])
        writer.writerow(['Company B', 'CA', 'https://companyb.ca', 'hello@companyb.ca', '+1-555-0102', 'Toronto', 'Manufacturing'])
        
        csv_file = io.BytesIO(csv_content.getvalue().encode('utf-8'))
        
        response = client.post(
            "/hunter/leads/import/csv",
            files={"file": ("test.csv", csv_file, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["created"] == 2
        assert data["errors"] == []
        
        app.dependency_overrides.clear()
    
    def test_csv_import_missing_columns(self, test_user: User, test_tenant: Tenant):
        """Test CSV import with missing required columns"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        # CSV missing 'country' column
        csv_content = io.StringIO()
        writer = csv.writer(csv_content)
        writer.writerow(['name', 'website'])
        writer.writerow(['Company A', 'https://companya.com'])
        
        csv_file = io.BytesIO(csv_content.getvalue().encode('utf-8'))
        
        response = client.post(
            "/hunter/leads/import/csv",
            files={"file": ("test.csv", csv_file, "text/csv")}
        )
        
        assert response.status_code == 400
        assert "missing required columns" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_csv_import_invalid_file_type(self, test_user: User, test_tenant: Tenant):
        """Test CSV import with invalid file type"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        txt_file = io.BytesIO(b"This is not a CSV file")
        
        response = client.post(
            "/hunter/leads/import/csv",
            files={"file": ("test.txt", txt_file, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "must be a CSV" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_search_leads(self, db_session: Session, test_user: User, test_tenant: Tenant):
        """Test lead search functionality"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        repo = HunterRepository(db_session)
        
        # Create test leads
        lead1 = repo.create_lead(
            tenant_id=test_tenant.id,
            primary_name="Alpha Corporation",
            country="US",
            city="New York",
            industry="Technology"
        )
        
        lead2 = repo.create_lead(
            tenant_id=test_tenant.id,
            primary_name="Beta Industries",
            country="CA",
            city="Toronto",
            industry="Manufacturing"
        )
        
        # Test search by name
        response = client.get("/hunter/leads?q=Alpha")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["primary_name"] == "Alpha Corporation"
        
        # Test search by country
        response = client.get("/hunter/leads?country=US")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["country"] == "US"
        
        # Test search with no filters
        response = client.get("/hunter/leads")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        app.dependency_overrides.clear()
    
    def test_get_lead_detail(self, db_session: Session, test_user: User, test_tenant: Tenant):
        """Test getting lead detail with grouped evidence"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        repo = HunterRepository(db_session)
        
        lead = repo.create_lead(
            tenant_id=test_tenant.id,
            primary_name="Test Company",
            country="US",
            website="https://testcompany.com"
        )
        
        # Add some evidence
        repo.attach_evidence(
            tenant_id=test_tenant.id,
            lead_id=lead.id,
            field_name="website",
            source_name="manual",
            confidence=1.0,
            snippet="https://testcompany.com"
        )
        
        response = client.get(f"/hunter/leads/{lead.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["primary_name"] == "Test Company"
        assert "evidence_by_field" in data
        assert "website" in data["evidence_by_field"]
        assert len(data["evidence_by_field"]["website"]) == 1
        
        app.dependency_overrides.clear()
    
    def test_get_lead_detail_not_found(self, test_user: User, test_tenant: Tenant):
        """Test getting non-existent lead"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        fake_id = uuid4()
        response = client.get(f"/hunter/leads/{fake_id}")
        assert response.status_code == 404
        assert "Lead not found" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_trade_query_stub(self, test_user: User, test_tenant: Tenant):
        """Test trade query endpoint returns 501"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        request_data = {
            "hs_code": "870323",
            "importer_country": "US",
            "min_volume": 1000
        }
        
        response = client.post("/hunter/query/trade", json=request_data)
        assert response.status_code == 501
        assert "not configured" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_evidence_summary(self, db_session: Session, test_user: User, test_tenant: Tenant):
        """Test evidence summary endpoint"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        repo = HunterRepository(db_session)
        
        lead = repo.create_lead(
            tenant_id=test_tenant.id,
            primary_name="Test Company",
            country="US"
        )
        
        # Add multiple evidence items
        repo.attach_evidence(
            tenant_id=test_tenant.id,
            lead_id=lead.id,
            field_name="website",
            source_name="manual",
            confidence=1.0,
            snippet="https://testcompany.com"
        )
        
        repo.attach_evidence(
            tenant_id=test_tenant.id,
            lead_id=lead.id,
            field_name="email",
            source_name="web_scrape",
            confidence=0.8,
            snippet="contact@testcompany.com"
        )
        
        response = client.get(f"/hunter/leads/{lead.id}/evidence/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["lead_id"] == str(lead.id)
        assert data["total_evidence"] == 2
        assert data["field_counts"]["website"] == 1
        assert data["field_counts"]["email"] == 1
        assert "manual" in data["top_sources"]["website"]
        assert "web_scrape" in data["top_sources"]["email"]
        
        app.dependency_overrides.clear()

"""
Hunter Phase 4 Enrichment Tests
Test web_basic provider and worker functionality
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4
import asyncio

from app.main import app
from app.services.hunter_enrichment import WebBasicProvider, EnrichmentResult
from app.services.hunter_repository import HunterRepository
from app.models.hunter_phase4 import HunterLead, HunterEnrichmentJob
from app.models.user import User
from app.models.tenant import Tenant

client = TestClient(app)

class TestWebBasicProvider:
    """Test WebBasic enrichment provider"""
    
    @pytest.fixture
    def provider(self):
        """Create provider instance"""
        config = {
            "timeout": 5,
            "max_size": 1024 * 1024,
            "user_agent": "TestHunter/1.0",
            "rate_limit_delay": 0  # No delay for tests
        }
        return WebBasicProvider(config)
    
    @pytest.fixture
    def test_lead(self, db_session: Session, test_tenant: Tenant):
        """Create test lead"""
        lead = HunterLead(
            id=uuid4(),
            tenant_id=test_tenant.id,
            primary_name="Test Company",
            country="US",
            website="https://example.com"
        )
        db_session.add(lead)
        db_session.commit()
        return lead
    
    def test_normalize_url(self, provider):
        """Test URL normalization"""
        # Add protocol
        assert provider._normalize_url("example.com") == "https://example.com"
        assert provider._normalize_url("www.example.com") == "https://www.example.com"
        
        # Keep existing protocol
        assert provider._normalize_url("https://example.com") == "https://example.com"
        assert provider._normalize_url("http://example.com") == "http://example.com"
        
        # Invalid URLs
        assert provider._normalize_url("") is None
        assert provider._normalize_url("not-a-url") is None
    
    def test_extract_emails(self, provider):
        """Test email extraction"""
        html = """
        <html>
        <body>
        <p>Contact us at contact@example.com or sales@example.org</p>
        <p>Support: support@example.com</p>
        <p>Ignore: test@domain.com, example@test.com</p>
        </body>
        </html>
        """
        
        emails = provider._extract_emails(html)
        assert len(emails) == 3
        assert "contact@example.com" in emails
        assert "sales@example.org" in emails
        assert "support@example.com" in emails
        # Should filter out false positives
        assert "test@domain.com" not in emails
        assert "example@test.com" not in emails
    
    def test_extract_phones(self, provider):
        """Test phone extraction"""
        html = """
        <html>
        <body>
        <p>Call us at (555) 123-4567 or +1-555-987-6543</p>
        <p>Mobile: 555.555.5555</p>
        <p>International: +44 20 7946 0958</p>
        </body>
        </html>
        """
        
        phones = provider._extract_phones(html)
        assert len(phones) >= 3
        assert any("5551234567" in phone for phone in phones)
        assert any("15559876543" in phone for phone in phones)
        assert any("442079460958" in phone for phone in phones)
    
    def test_extract_social_links(self, provider):
        """Test social link extraction"""
        html = """
        <html>
        <body>
        <a href="https://www.linkedin.com/company/test-company">LinkedIn</a>
        <a href="https://www.instagram.com/testcompany">Instagram</a>
        <a href="https://twitter.com/testcompany">Twitter</a>
        </body>
        </html>
        """
        
        social_links = provider._extract_social_links(html, "https://example.com")
        assert "linkedin" in social_links
        assert "instagram" in social_links
        assert "twitter" in social_links
        assert "test-company" in social_links["linkedin"]
        assert "testcompany" in social_links["instagram"]
    
    def test_extract_company_hints(self, provider):
        """Test company name hint extraction"""
        html = """
        <html>
        <head>
        <title>Acme Corporation - Home</title>
        <meta property="og:site_name" content="Acme Inc">
        <meta name="author" content="Acme Company LLC">
        </head>
        <body>
        <h1>Welcome to Acme</h1>
        </body>
        </html>
        """
        
        hints = provider._extract_company_name_hints(html)
        assert len(hints) >= 2
        assert "Acme Corporation" in hints
        assert "Acme Inc" in hints
        assert "Acme Company LLC" in hints
    
    def test_extract_industry_hints(self, provider):
        """Test industry keyword extraction"""
        html = """
        <html>
        <body>
        <p>We are a technology company specializing in software solutions.</p>
        <p>Our manufacturing business serves the automotive industry.</p>
        <p>We provide consulting services to healthcare organizations.</p>
        </body>
        </html>
        """
        
        hints = provider._extract_industry_hints(html)
        assert len(hints) >= 2
        assert "Technology" in hints
        assert "Software" in hints
        assert "Manufacturing" in hints
        assert "Automotive" in hints
    
    @pytest.mark.asyncio
    async def test_enrich_with_website(self, provider, test_lead, db_session: Session):
        """Test enrichment with valid website"""
        # Mock HTML content
        mock_html = """
        <html>
        <head><title>Test Company</title></head>
        <body>
        <p>Contact: contact@testcompany.com</p>
        <p>Phone: (555) 123-4567</p>
        <a href="https://www.linkedin.com/company/testcompany">LinkedIn</a>
        </body>
        </html>
        """
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.text = mock_html
            mock_response.raise_for_status = MagicMock()
            mock_response.headers = {}
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            repo = HunterRepository(db_session)
            result = await provider.enrich(test_lead, repo)
            
            assert isinstance(result, EnrichmentResult)
            assert len(result.identities) >= 2  # email and phone
            assert len(result.evidence) >= 2
            
            # Check email identity
            email_identities = [i for i in result.identities if i["type"] == "email"]
            assert len(email_identities) == 1
            assert email_identities[0]["value"] == "contact@testcompany.com"
            
            # Check phone identity
            phone_identities = [i for i in result.identities if i["type"] == "phone"]
            assert len(phone_identities) == 1
            assert "5551234567" in phone_identities[0]["value"]
    
    @pytest.mark.asyncio
    async def test_enrich_no_website(self, provider, db_session: Session, test_tenant: Tenant):
        """Test enrichment with no website"""
        lead = HunterLead(
            id=uuid4(),
            tenant_id=test_tenant.id,
            primary_name="Test Company",
            country="US",
            website=None
        )
        
        repo = HunterRepository(db_session)
        result = await provider.enrich(lead, repo)
        
        assert result.updates == {}
        assert result.identities == []
        assert result.evidence == []
    
    @pytest.mark.asyncio
    async def test_enrich_fetch_error(self, provider, test_lead, db_session: Session):
        """Test enrichment when website fetch fails"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Network error")
            
            repo = HunterRepository(db_session)
            result = await provider.enrich(test_lead, repo)
            
            # Should return empty result on error
            assert result.updates == {}
            assert result.identities == []
            assert result.evidence == []

class TestEnrichmentAPI:
    """Test enrichment API endpoints"""
    
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
            website="https://example.com"
        )
        db_session.add(lead)
        db_session.commit()
        return lead
    
    def test_enqueue_enrichment_success(self, test_user: User, test_tenant: Tenant, test_lead: HunterLead):
        """Test successful enrichment job enqueue"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.post(f"/hunter/leads/{test_lead.id}/enrich")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "queued"
        assert data["provider"] == "web_basic"
        assert "job_id" in data
        
        app.dependency_overrides.clear()
    
    def test_enqueue_enrichment_invalid_provider(self, test_user: User, test_tenant: Tenant, test_lead: HunterLead):
        """Test enrichment with invalid provider"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.post(f"/hunter/leads/{test_lead.id}/enrich?provider=invalid_provider")
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_enqueue_enrichment_lead_not_found(self, test_user: User, test_tenant: Tenant):
        """Test enrichment for non-existent lead"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        fake_id = uuid4()
        response = client.post(f"/hunter/leads/{fake_id}/enrich")
        assert response.status_code == 404
        assert "Lead not found" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_get_enrichment_jobs(self, test_user: User, test_tenant: Tenant, test_lead: HunterLead, db_session: Session):
        """Test getting enrichment jobs for a lead"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        # Create a job
        repo = HunterRepository(db_session)
        job = repo.enqueue_enrichment_job(
            tenant_id=test_tenant.id,
            lead_id=test_lead.id,
            provider="web_basic"
        )
        
        response = client.get(f"/hunter/leads/{test_lead.id}/enrichment/jobs")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["provider"] == "web_basic"
        assert data[0]["status"] == "queued"
        
        app.dependency_overrides.clear()
    
    def test_get_enrichment_job_status(self, test_user: User, test_tenant: Tenant, test_lead: HunterLead, db_session: Session):
        """Test getting specific enrichment job status"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        # Create a job
        repo = HunterRepository(db_session)
        job = repo.enqueue_enrichment_job(
            tenant_id=test_tenant.id,
            lead_id=test_lead.id,
            provider="web_basic"
        )
        
        response = client.get(f"/hunter/enrichment/jobs/{job.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["provider"] == "web_basic"
        assert data["status"] == "queued"
        assert data["attempts"] == 0
        
        app.dependency_overrides.clear()
    
    def test_get_enrichment_job_not_found(self, test_user: User, test_tenant: Tenant):
        """Test getting non-existent enrichment job"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        fake_id = uuid4()
        response = client.get(f"/hunter/enrichment/jobs/{fake_id}")
        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]
        
        app.dependency_overrides.clear()

"""
Hunter Phase 4 Scoring Tests
Test scoring engine and API endpoints
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.services.hunter_scoring import HunterScoringEngine, ScoringSignal
from app.services.hunter_repository import HunterRepository
from app.models.hunter_phase4 import HunterLead, HunterLeadIdentity, HunterEvidence, HunterScoringProfile
from app.models.user import User
from app.models.tenant import Tenant

client = TestClient(app)

class TestHunterScoringEngine:
    """Test Hunter scoring engine"""
    
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
            website="https://testcompany.com"
        )
        db_session.add(lead)
        db_session.commit()
        return lead
    
    @pytest.fixture
    def repo(self, db_session: Session):
        """Create repository instance"""
        return HunterRepository(db_session)
    
    def test_score_lead_complete_data(self, repo: HunterRepository, test_lead: HunterLead, test_tenant: Tenant):
        """Test scoring lead with complete data"""
        # Add identities
        repo.attach_identity(test_tenant.id, test_lead.id, "email", "contact@testcompany.com")
        repo.attach_identity(test_tenant.id, test_lead.id, "phone", "+1-555-123-4567")
        
        # Add recent evidence
        repo.attach_evidence(
            test_tenant.id, test_lead.id, "website", "manual", 1.0,
            snippet="https://testcompany.com", collected_at=datetime.utcnow()
        )
        repo.attach_evidence(
            test_tenant.id, test_lead.id, "email", "web_scrape", 0.8,
            snippet="contact@testcompany.com", collected_at=datetime.utcnow()
        )
        
        # Score the lead
        engine = HunterScoringEngine(repo)
        result = engine.score_lead(test_tenant.id, test_lead.id)
        
        assert result.total_score > 0
        assert result.max_score == 70  # 30 + 20 + 10 + 10
        assert len(result.signals) == 4
        
        # Check identity completeness signal
        identity_signal = next(s for s in result.signals if s.name == "Identity Completeness")
        assert identity_signal.score == 30  # Has website, email, phone
        assert "Has website/domain" in identity_signal.explanation
        assert "Has email" in identity_signal.explanation
        assert "Has phone" in identity_signal.explanation
        
        # Check country priority signal
        country_signal = next(s for s in result.signals if s.name == "Country Priority")
        assert country_signal.score == 20  # US is in default priority list
        assert "priority list" in country_signal.explanation
    
    def test_score_lead_minimal_data(self, repo: HunterRepository, test_tenant: Tenant):
        """Test scoring lead with minimal data"""
        # Create lead with minimal info
        lead = repo.create_lead(
            tenant_id=test_tenant.id,
            primary_name="Minimal Company",
            country="XX"  # Non-priority country
        )
        
        engine = HunterScoringEngine(repo)
        result = engine.score_lead(test_tenant.id, lead.id)
        
        assert result.total_score == 0  # No identities, no priority country
        assert len(result.signals) == 4
        
        # Check identity completeness signal
        identity_signal = next(s for s in result.signals if s.name == "Identity Completeness")
        assert identity_signal.score == 0
        assert "No identity data" in identity_signal.explanation
    
    def test_score_lead_b2b_keywords(self, repo: HunterRepository, test_lead: HunterLead, test_tenant: Tenant):
        """Test scoring with B2B keywords in evidence"""
        # Add company name hint with B2B keywords
        repo.attach_evidence(
            test_tenant.id, test_lead.id, "company_name_hint", "web_scrape", 0.5,
            snippet="Test Company Wholesale Distributor", collected_at=datetime.utcnow()
        )
        
        engine = HunterScoringEngine(repo)
        result = engine.score_lead(test_tenant.id, test_lead.id)
        
        # Check company type hint signal
        company_signal = next(s for s in result.signals if s.name == "Company Type Hint")
        assert company_signal.score > 0
        assert "wholesale" in company_signal.explanation.lower()
        assert "distributor" in company_signal.explanation.lower()
    
    def test_score_lead_data_freshness(self, repo: HunterRepository, test_lead: HunterLead, test_tenant: Tenant):
        """Test data freshness scoring"""
        # Add old evidence
        old_date = datetime.utcnow() - timedelta(days=100)
        repo.attach_evidence(
            test_tenant.id, test_lead.id, "website", "manual", 1.0,
            snippet="https://testcompany.com", collected_at=old_date
        )
        
        engine = HunterScoringEngine(repo)
        result = engine.score_lead(test_tenant.id, test_lead.id)
        
        # Check data freshness signal
        freshness_signal = next(s for s in result.signals if s.name == "Data Freshness")
        assert freshness_signal.score == 0  # Data is stale
        assert "stale" in freshness_signal.explanation.lower()
        
        # Add recent evidence
        recent_date = datetime.utcnow() - timedelta(days=15)
        repo.attach_evidence(
            test_tenant.id, test_lead.id, "email", "web_scrape", 0.8,
            snippet="contact@testcompany.com", collected_at=recent_date
        )
        
        result = engine.score_lead(test_tenant.id, test_lead.id)
        freshness_signal = next(s for s in result.signals if s.name == "Data Freshness")
        assert freshness_signal.score == 10  # Data is recent
        assert "recent" in freshness_signal.explanation.lower()
    
    def test_risk_flags(self, repo: HunterRepository, test_tenant: Tenant):
        """Test risk flag calculation"""
        # Create lead with risk factors
        lead = repo.create_lead(
            tenant_id=test_tenant.id,
            primary_name="Risk Company",
            country="IR"  # High risk country
        )
        
        # Add free email
        repo.attach_identity(test_tenant.id, lead.id, "email", "contact@gmail.com")
        
        # Add old evidence
        old_date = datetime.utcnow() - timedelta(days=200)
        repo.attach_evidence(
            test_tenant.id, lead.id, "website", "manual", 1.0,
            snippet="https://riskcompany.com", collected_at=old_date
        )
        
        engine = HunterScoringEngine(repo)
        result = engine.score_lead(test_tenant.id, lead.id)
        
        assert len(result.risk_flags) >= 3
        assert any("High risk country: IR" in flag for flag in result.risk_flags)
        assert any("Uses free email domain: gmail.com" in flag for flag in result.risk_flags)
        assert any("Data is over 6 months old" in flag for flag in result.risk_flags)
    
    def test_custom_scoring_profile(self, repo: HunterRepository, test_lead: HunterLead, test_tenant: Tenant):
        """Test scoring with custom profile"""
        # Create custom profile
        custom_weights = {
            "priority_countries": ["DE", "FR"],  # Different priority countries
            "risk_countries": ["XX", "YY"],
            "free_email_domains": ["test.com"]
        }
        
        engine = HunterScoringEngine(repo)
        result = engine.score_lead(test_tenant.id, test_lead.id, custom_weights)
        
        # Check country priority signal (US should not be priority now)
        country_signal = next(s for s in result.signals if s.name == "Country Priority")
        assert country_signal.score == 0  # US not in custom priority list
        assert "not in priority list" in country_signal.explanation

class TestScoringAPI:
    """Test scoring API endpoints"""
    
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
        return lead
    
    def test_score_lead_api(self, test_user: User, test_tenant: Tenant, test_lead: HunterLead):
        """Test scoring lead via API"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.post(f"/hunter/leads/{test_lead.id}/score")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_score" in data
        assert "max_score" in data
        assert "signals" in data
        assert "risk_flags" in data
        assert "breakdown" in data
        assert len(data["signals"]) == 4
        
        app.dependency_overrides.clear()
    
    def test_score_nonexistent_lead(self, test_user: User, test_tenant: Tenant):
        """Test scoring non-existent lead"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        fake_id = uuid4()
        response = client.post(f"/hunter/leads/{fake_id}/score")
        assert response.status_code == 404
        assert "Lead not found" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_create_scoring_profile(self, test_user: User, test_tenant: Tenant):
        """Test creating scoring profile"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        profile_data = {
            "name": "Custom Profile",
            "weights": {
                "priority_countries": ["US", "CA"],
                "risk_countries": ["IR", "KP"],
                "free_email_domains": ["gmail.com", "yahoo.com"]
            },
            "is_default": False
        }
        
        response = client.post("/hunter/scoring/profiles", json=profile_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Custom Profile"
        assert data["is_default"] is False
        assert "priority_countries" in data["weights"]
        
        app.dependency_overrides.clear()
    
    def test_create_scoring_profile_invalid_weights(self, test_user: User, test_tenant: Tenant):
        """Test creating scoring profile with invalid weights"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        # Missing required key
        profile_data = {
            "name": "Invalid Profile",
            "weights": {
                "priority_countries": ["US"],
                # Missing risk_countries and free_email_domains
            },
            "is_default": False
        }
        
        response = client.post("/hunter/scoring/profiles", json=profile_data)
        assert response.status_code == 400
        assert "Missing required weight key" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_list_scoring_profiles(self, test_user: User, test_tenant: Tenant, db_session: Session):
        """Test listing scoring profiles"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        # Create a profile first
        repo = HunterRepository(db_session)
        repo.create_scoring_profile(
            tenant_id=test_tenant.id,
            name="Test Profile",
            weights={
                "priority_countries": ["US"],
                "risk_countries": ["IR"],
                "free_email_domains": ["gmail.com"]
            }
        )
        
        response = client.get("/hunter/scoring/profiles")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        assert any(p["name"] == "Test Profile" for p in data)
        
        app.dependency_overrides.clear()
    
    def test_set_default_profile(self, test_user: User, test_tenant: Tenant, db_session: Session):
        """Test setting default scoring profile"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        # Create a profile
        repo = HunterRepository(db_session)
        profile = repo.create_scoring_profile(
            tenant_id=test_tenant.id,
            name="Default Profile",
            weights={
                "priority_countries": ["US"],
                "risk_countries": ["IR"],
                "free_email_domains": ["gmail.com"]
            }
        )
        
        response = client.post(f"/hunter/scoring/profiles/{profile.id}/set-default")
        assert response.status_code == 200
        assert "set as default" in response.json()["message"]
        
        app.dependency_overrides.clear()

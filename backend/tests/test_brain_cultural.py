"""
Phase 5 Cultural Strategy Engine Tests
Tests for LLM-based cultural strategy with guardrails
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.tenant import Tenant
from app.models.brain_assets import CulturalProfile
from app.services.brain_cultural_engine import CulturalStrategyEngine
from app.schemas.brain import CulturalInput, PaymentTerms

client = TestClient(app)

class TestCulturalStrategyEngine:
    """Test cultural strategy engine with LLM guardrails"""
    
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
    def cultural_engine(self, db_session: Session):
        """Create cultural strategy engine instance"""
        return CulturalStrategyEngine(db_session)
    
    @pytest.fixture
    def sample_cultural_profile(self, db_session: Session, test_tenant: Tenant):
        """Create sample cultural profile"""
        profile = CulturalProfile(
            tenant_id=test_tenant.id,
            country="US",
            negotiation_style={
                "approach": "Direct and results-oriented",
                "pace": "Fast-paced",
                "communication": "Explicit and straightforward"
            },
            do_dont={
                "do": ["Be punctual and prepared", "Use data to support arguments"],
                "don't": ["Be overly emotional", "Make promises you can't keep"]
            },
            typical_terms={
                "payment_terms": ["Net 30", "Net 60"],
                "contract_formality": "High",
                "relationship_focus": "Transactional"
            }
        )
        db_session.add(profile)
        db_session.commit()
        return profile
    
    def test_cultural_analysis_success(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Test successful cultural analysis"""
        input_data = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Looking to establish long-term partnership for electronic components",
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        assert len(result.templates) > 0
        assert len(result.negotiation_tips) > 0
        assert len(result.objection_handling) > 0
        assert len(result.referenced_profile_ids) == 1
        assert result.referenced_profile_ids[0] == sample_cultural_profile.id
        
        # Check templates structure
        for template in result.templates:
            assert template.template_type in ["negotiation", "email", "whatsapp"]
            assert template.content is not None
            assert template.language == "en"
            assert template.referenced_profile_id == sample_cultural_profile.id
    
    def test_cultural_analysis_no_profile(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant):
        """Test cultural analysis with no cultural profile"""
        input_data = CulturalInput(
            destination_country="XX",  # Non-existent country
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Test deal context",
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "insufficient_data"
        assert len(result.templates) == 0
        assert len(result.negotiation_tips) == 0
        assert len(result.objection_handling) == 0
        assert len(result.referenced_profile_ids) == 0
        
        # Check explainability
        assert result.explainability.confidence == 0.0
        assert "No cultural profile found" in str(result.explainability.missing_fields)
    
    def test_cultural_analysis_missing_fields(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant):
        """Test cultural analysis with missing required fields"""
        input_data = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            # Missing payment_terms_target, deal_context, language
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "insufficient_data"
        assert len(result.explainability.missing_fields) > 0
    
    def test_cultural_analysis_invalid_language(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant):
        """Test cultural analysis with invalid language"""
        input_data = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Test deal context",
            language="invalid_lang"  # Invalid language
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "insufficient_data"
        assert "Invalid language" in str(result.explainability.missing_fields)
    
    def test_cultural_analysis_long_context(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Test cultural analysis with deal context too long"""
        input_data = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="x" * 600,  # Too long (> 500 chars)
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "insufficient_data"
        assert "deal_context must be 500 characters or less" in str(result.explainability.missing_fields)
    
    def test_template_generation_types(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Test generation of different template types"""
        input_data = CulturalInput(
            destination_country="US",
            buyer_type="Distributor",
            payment_terms_target=PaymentTerms.TT,
            deal_context="Partnership opportunity for distribution network",
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Check that different template types are generated
        template_types = [template.template_type for template in result.templates]
        expected_types = ["negotiation", "email", "whatsapp"]
        
        for expected_type in expected_types:
            assert expected_type in template_types
    
    def test_negotiation_tips_generation(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Test negotiation tips generation"""
        input_data = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Test deal context",
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        assert len(result.negotiation_tips) > 0
        
        # Check that tips are based on cultural profile
        tips_text = " ".join(result.negotiation_tips).lower()
        assert any(keyword in tips_text for keyword in ["punctual", "data", "prepared", "direct"])
    
    def test_objection_handling_generation(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Test objection handling strategies generation"""
        input_data = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Test deal context",
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        assert len(result.objection_handling) > 0
        
        # Check that strategies are practical
        strategies_text = " ".join(result.objection_handling).lower()
        assert any(keyword in strategies_text for keyword in ["listen", "data", "respectful", "alternative"])
    
    def test_explainability_structure(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Test explainability bundle structure"""
        input_data = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Test deal context",
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        explainability = result.explainability
        
        # Check required fields
        assert "data_used" in explainability
        assert "assumptions" in explainability
        assert "confidence" in explainability
        assert "confidence_rationale" in explainability
        assert "action_plan" in explainability
        assert "limitations" in explainability
        assert "computation_method" in explainability
        
        # Check data sources
        assert len(explainability.data_used) >= 3  # Input + profile + LLM
        assert any(ds.source_name == "user_input" for ds in explainability.data_used)
        assert any(ds.source_name == "cultural_profiles" for ds in explainability.data_used)
        assert any(ds.source_name == "gemini_llm" for ds in explainability.data_used)
        
        # Check confidence
        assert 0.0 <= explainability.confidence <= 1.0
        assert explainability.confidence >= 0.4  # Should have some confidence with profile
        
        # Check computation method
        assert "llm" in explainability.computation_method.lower()
        assert "guardrails" in explainability.computation_method.lower()
    
    def test_confidence_calculation(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Test confidence score calculation"""
        input_data = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Test deal context",
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        confidence = result.explainability.confidence
        
        # With complete profile and templates, confidence should be reasonable
        assert confidence >= 0.6
        assert confidence <= 0.8  # Capped for LLM-based content
    
    def test_llm_guardrails(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Test LLM guardrails are enforced"""
        input_data = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Test deal context",
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Check that templates reference the cultural profile
        for template in result.templates:
            assert template.referenced_profile_id == sample_cultural_profile.id
        
        # Check that explainability mentions guardrails
        assert "guardrails" in result.explainability.computation_method.lower()
    
    def test_incomplete_cultural_profile(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, db_session: Session):
        """Test handling of incomplete cultural profile"""
        # Create incomplete profile
        incomplete_profile = CulturalProfile(
            tenant_id=test_tenant.id,
            country="IN",
            negotiation_style=None,  # Missing
            do_dont={"do": ["Build relationships"]},  # Partial
            typical_terms=None  # Missing
        )
        db_session.add(incomplete_profile)
        db_session.commit()
        
        input_data = CulturalInput(
            destination_country="IN",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Test deal context",
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should still generate templates but with lower confidence
        assert len(result.templates) > 0
        assert result.explainability.confidence < 0.7  # Lower due to incomplete profile
        
        # Should mention limitations
        limitations_text = " ".join(result.explainability.limitations).lower()
        assert "limited" in limitations_text

class TestCulturalAPI:
    """Test cultural strategy engine API endpoints"""
    
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
    
    def test_cultural_api_success(self, test_user: User, test_tenant: Tenant):
        """Test successful cultural API call"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "destination_country": "US",
            "buyer_type": "B2B",
            "payment_terms_target": "LC",
            "deal_context": "Looking for partnership opportunities",
            "language": "en"
        }
        
        response = client.post("/brain/cultural/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "templates" in data
        assert "negotiation_tips" in data
        assert "objection_handling" in data
        assert "referenced_profile_ids" in data
        assert "explainability" in data
        
        # Check templates structure
        templates = data["templates"]
        assert isinstance(templates, list)
        
        if templates:  # If templates were generated
            template = templates[0]
            assert "template_type" in template
            assert "content" in template
            assert "language" in template
            assert "referenced_profile_id" in template
        
        app.dependency_overrides.clear()
    
    def test_cultural_api_missing_fields(self, test_user: User, test_tenant: Tenant):
        """Test cultural API with missing fields"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "destination_country": "US",
            "buyer_type": "B2B"
            # Missing required fields
        }
        
        response = client.post("/brain/cultural/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"
        assert "explainability" in data
        assert len(data["explainability"]["missing_fields"]) > 0
        
        app.dependency_overrides.clear()
    
    def test_cultural_api_no_profile(self, test_user: User, test_tenant: Tenant):
        """Test cultural API with no cultural profile"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "destination_country": "XX",  # Non-existent country
            "buyer_type": "B2B",
            "payment_terms_target": "LC",
            "deal_context": "Test deal",
            "language": "en"
        }
        
        response = client.post("/brain/cultural/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"
        assert len(data["templates"]) == 0
        assert len(data["referenced_profile_ids"]) == 0
        
        # Should suggest creating profile
        action_plan = data["explainability"]["action_plan"]
        assert any("cultural profile" in step.lower() for step in action_plan)
        
        app.dependency_overrides.clear()
    
    def test_cultural_api_invalid_language(self, test_user: User, test_tenant: Tenant):
        """Test cultural API with invalid language"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "destination_country": "US",
            "buyer_type": "B2B",
            "payment_terms_target": "LC",
            "deal_context": "Test deal",
            "language": "invalid_lang"
        }
        
        response = client.post("/brain/cultural/run", json=input_data)
        # Should return 422 for validation error
        assert response.status_code == 422
        
        app.dependency_overrides.clear()
    
    def test_cultural_run_persistence(self, test_user: User, test_tenant: Tenant):
        """Test that cultural runs are persisted"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "destination_country": "US",
            "buyer_type": "B2B",
            "payment_terms_target": "LC",
            "deal_context": "Test deal context",
            "language": "en"
        }
        
        # Run analysis
        response = client.post("/brain/cultural/run", json=input_data)
        assert response.status_code == 200
        
        # Check run was saved
        runs_response = client.get("/brain/runs?engine_type=cultural")
        assert runs_response.status_code == 200
        
        runs_data = runs_response.json()
        assert len(runs_data["runs"]) > 0
        
        # Find our run
        our_run = None
        for run in runs_data["runs"]:
            if run["input_payload"]["destination_country"] == "US":
                our_run = run
                break
        
        assert our_run is not None
        assert our_run["engine_type"] == "cultural"
        assert our_run["status"] in ["success", "insufficient_data"]
        assert "explainability" in our_run
        assert "templates" in our_run["output_payload"]
        
        app.dependency_overrides.clear()

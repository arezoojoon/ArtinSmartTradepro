"""
Phase 5 Golden Tests - Cultural Strategy Engine
Anti-fake validation with LLM guardrails and cultural profiles
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

class TestCulturalGolden:
    """Golden tests for cultural strategy engine with LLM guardrails"""
    
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
    
    def test_golden_case_1_successful_cultural_analysis(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Golden case 1: Successful cultural analysis with valid profile"""
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
        
        # Explainability must reference cultural profile
        assert any("cultural_profiles" in ds.dataset for ds in result.explainability.data_used)
        assert any("gemini_llm" in ds.source_name for ds in result.explainability.data_used)
        
        # Confidence should be reasonable with cultural profile
        assert result.explainability.confidence >= 0.6
        
        # Action plan must be non-empty
        assert len(result.explainability.action_plan) > 0
        
        # No missing fields for success case
        assert len(result.explainability.missing_fields) == 0
    
    def test_golden_case_2_no_cultural_profile(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant):
        """Golden case 2: No cultural profile available"""
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
        
        # Must list missing cultural profile
        assert "No cultural profile found" in str(result.explainability.missing_fields)
        
        # Confidence must be 0 for insufficient data
        assert result.explainability.confidence == 0.0
        
        # Action plan must suggest creating profile
        assert any("cultural profile" in step.lower() for step in result.explainability.action_plan)
    
    def test_golden_case_3_llm_guardrails_validation(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Golden case 3: LLM guardrails validation"""
        input_data = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Test deal context",
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Templates must reference the cultural profile
        for template in result.templates:
            assert template.referenced_profile_id == sample_cultural_profile.id
        
        # Explainability must mention guardrails
        assert "guardrails" in result.explainability.computation_method.lower()
        
        # Templates should not contain hallucinated cultural facts
        for template in result.templates:
            content = template.content.lower()
            # Should not contain external cultural facts not in profile
            assert "external" not in content
            assert "market" not in content or "market" in ["marketplace", "marketing"]  # Allow business context
        
        # Negotiation tips should be based on profile data
        tips_text = " ".join(result.negotiation_tips).lower()
        assert any(keyword in tips_text for keyword in ["punctual", "data", "prepared", "direct"])
        
        # No numeric facts should be invented
        for template in result.templates:
            content = template.content
            # Should not contain invented statistics
            assert not any(word in content for word in ["%", "percent", "billion", "million", "trillion"])
    
    def test_golden_case_4_template_generation_types(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Golden case 4: Template generation types validation"""
        input_data = CulturalInput(
            destination_country="US",
            buyer_type="Distributor",
            payment_terms_target=PaymentTerms.TT,
            deal_context="Partnership opportunity for distribution network",
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should generate different template types
        template_types = [template.template_type for template in result.templates]
        expected_types = ["negotiation", "email", "whatsapp"]
        
        for expected_type in expected_types:
            assert expected_type in template_types
        
        # Each template type should have content
        for template in result.templates:
            assert len(template.content) > 0
            assert template.language == "en"
            assert template.referenced_profile_id == sample_cultural_profile.id
    
    def test_golden_case_5_language_validation(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Golden case 5: Language validation"""
        # Test with valid language
        valid_input = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Test deal context",
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, valid_input)
        assert result.status == "success"
        
        # Templates should be in specified language
        for template in result.templates:
            assert template.language == "en"
        
        # Test with invalid language
        invalid_input = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Test deal context",
            language="invalid_lang"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, invalid_input)
        assert result.status == "insufficient_data"
        assert "Invalid language" in str(result.explainability.missing_fields)
    
    def test_golden_case_6_context_length_validation(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Golden case 6: Deal context length validation"""
        # Test with valid context length
        valid_input = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Test deal context",
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, valid_input)
        assert result.status == "success"
        
        # Test with context too long
        long_input = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="x" * 600,  # Too long (> 500 chars)
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, long_input)
        assert result.status == "insufficient_data"
        assert "deal_context must be 500 characters or less" in str(result.explainability.missing_fields)
    
    def test_golden_case_7_explainability_structure_validation(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Golden case 7: Explainability structure validation"""
        input_data = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Test deal context",
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Validate explainability structure
        explainability = result.explainability
        
        # Required fields must exist
        assert hasattr(explainability, 'data_used')
        assert hasattr(explainability, 'assumptions')
        assert hasattr(explainability, 'confidence')
        assert hasattr(explainability, 'confidence_rationale')
        assert hasattr(explainability, 'action_plan')
        assert hasattr(explainability, 'limitations')
        assert hasattr(explainability, 'computation_method')
        assert hasattr(explainability, 'missing_fields')
        
        # Data validation
        assert isinstance(explainability.data_used, list)
        assert isinstance(explainability.assumptions, list)
        assert isinstance(explainability.confidence, (int, float))
        assert 0.0 <= explainability.confidence <= 1.0
        assert isinstance(explainability.confidence_rationale, str)
        assert isinstance(explainability.action_plan, list)
        assert isinstance(explainability.limitations, list)
        assert isinstance(explainability.computation_method, str)
        assert isinstance(explainability.missing_fields, list)
        
        # Content validation
        assert len(explainability.data_used) >= 3  # Input + profile + LLM
        assert len(explainability.assumptions) > 0
        assert len(explainability.action_plan) > 0
        assert len(explainability.limitations) > 0
        assert len(explainability.computation_method) > 0
    
    def test_golden_case_8_llm_data_source_tracking(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Golden case 8: LLM data source tracking"""
        input_data = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Test deal context",
            language="en"
        )
        
        result = cultural_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Must track LLM data source
        llm_sources = [ds for ds in result.explainability.data_used if ds.source_name == "gemini_llm"]
        assert len(llm_sources) > 0
        
        # LLM source should have lower confidence
        for llm_source in llm_sources:
            assert llm_source.confidence is not None
            assert llm_source.confidence <= 0.6  # LLM confidence should be lower
        
        # Must track cultural profile source
        profile_sources = [ds for ds in result.explainability.data_used if ds.source_name == "cultural_profiles"]
        assert len(profile_sources) > 0
        
        # Profile source should have higher confidence
        for profile_source in profile_sources:
            assert profile_source.confidence is not None
            assert profile_source.confidence >= 0.7
    
    def test_golden_case_9_deterministic_template_generation(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, sample_cultural_profile):
        """Golden case 9: Deterministic template generation"""
        input_data = CulturalInput(
            destination_country="US",
            buyer_type="B2B",
            payment_terms_target=PaymentTerms.LC,
            deal_context="Test deal context",
            language="en"
        )
        
        # Run the same input multiple times
        results = []
        for _ in range(3):
            result = cultural_engine.run_analysis(test_tenant.id, input_data)
            results.append(result)
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result.status == first_result.status
            assert len(result.templates) == len(first_result.templates)
            assert len(result.referenced_profile_ids) == len(first_result.referenced_profile_ids)
            assert result.explainability.confidence == first_result.explainability.confidence
            
            # Individual templates should be identical
            for i, template in enumerate(result.templates):
                first_template = first_result.templates[i]
                assert template.template_type == first_template.template_type
                assert template.content == first_template.content
                assert template.language == first_template.language
                assert template.referenced_profile_id == first_template.referenced_profile_id
    
    def test_golden_case_10_incomplete_cultural_profile(self, cultural_engine: CulturalStrategyEngine, test_tenant: Tenant, db_session: Session):
        """Golden case 10: Incomplete cultural profile handling"""
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
        assert "negotiation style" in limitations_text

class TestCulturalAPIGolden:
    """Golden tests for cultural strategy API endpoints"""
    
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
    
    def test_api_golden_case_1_successful_analysis(self, test_user: User, test_tenant: Tenant):
        """API golden case 1: Successful cultural analysis"""
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
        
        # Should have templates
        templates = data["templates"]
        assert isinstance(templates, list)
        
        if templates:  # If templates were generated
            template = templates[0]
            assert "template_type" in template
            assert "content" in template
            assert "language" in template
            assert "referenced_profile_id" in template
        
        # Validate explainability
        explainability = data["explainability"]
        assert "data_used" in explainability
        assert "confidence" in explainability
        assert len(explainability["data_used"]) >= 3
        assert explainability["confidence"] >= 0.6
        
        app.dependency_overrides.clear()
    
    def test_api_golden_case_2_invalid_language(self, test_user: User, test_tenant: Tenant):
        """API golden case 2: Invalid language validation"""
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
    
    def test_api_golden_case_3_no_profile(self, test_user: User, test_tenant: Tenant):
        """API golden case 3: No cultural profile"""
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
    
    def test_api_golden_case_4_run_persistence(self, test_user: User, test_tenant: Tenant):
        """API golden case 4: Run persistence validation"""
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
        
        # Check that run was saved
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
        
        # Validate persisted explainability
        persisted_explainability = our_run["explainability"]
        assert "data_used" in persisted_explainability
        assert "confidence" in persisted_explainability
        assert persisted_explainability["confidence"] >= 0
        
        app.dependency_overrides.clear()

"""
Phase 5 Risk Engine Tests
Tests for rule-based risk analysis and risk register output
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.tenant import Tenant
from app.models.brain_assets import (
    AssetSupplierReliability, AssetBuyerPaymentBehavior, RiskSeverity
)
from app.services.brain_risk_engine import RiskEngine
from app.schemas.brain import RiskInput, PaymentTerms

client = TestClient(app)

class TestRiskEngine:
    """Test risk engine rule-based analysis"""
    
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
    def risk_engine(self, db_session: Session):
        """Create risk engine instance"""
        return RiskEngine(db_session)
    
    @pytest.fixture
    def sample_supplier_data(self, db_session: Session, test_tenant: Tenant):
        """Create sample supplier reliability data"""
        supplier = AssetSupplierReliability(
            tenant_id=test_tenant.id,
            supplier_name="Test Supplier Co",
            supplier_country="CN",
            identifiers={"website": "testsupplier.com"},
            on_time_rate=0.85,
            defect_rate=0.02,
            dispute_count=1,
            avg_lead_time_days=30,
            reliability_score=75,
            evidence={"source": "manual"}
        )
        db_session.add(supplier)
        db_session.commit()
        return supplier
    
    @pytest.fixture
    def sample_buyer_data(self, db_session: Session, test_tenant: Tenant):
        """Create sample buyer payment behavior data"""
        buyer = AssetBuyerPaymentBehavior(
            tenant_id=test_tenant.id,
            buyer_country="US",
            buyer_name="Test Buyer Inc",
            segment="Distributor",
            avg_payment_delay_days=45,
            default_rate=0.03,
            preferred_terms="LC",
            payment_risk_score=60,
            evidence={"source": "historical"}
        )
        db_session.add(buyer)
        db_session.commit()
        return buyer
    
    def test_political_risk_high_risk_country(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Test political risk for high-risk destination country"""
        input_data = RiskInput(
            product_key="123456",
            origin_country="US",
            destination_country="IR",  # High risk country
            incoterms="FOB",
            payment_terms=PaymentTerms.LC
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        assert len(result.risk_register) > 0
        
        # Should have political risk for high-risk country
        political_risks = [r for r in result.risk_register if r.type == "political"]
        assert len(political_risks) > 0
        
        high_risk = [r for r in political_risks if r.severity == RiskSeverity.HIGH]
        assert len(high_risk) > 0
        
        # Check reason mentions Iran
        assert any("IR" in risk.reason for risk in high_risk)
        
        # Check mitigation steps
        assert any("alternative" in step.lower() for risk in high_risk for step in risk.mitigation_steps)
    
    def test_political_risk_sanctions_country(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Test political risk for sanctions country"""
        input_data = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="RU",  # Sanctions country
            incoterms="CIF",
            payment_terms=PaymentTerms.TT
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should have sanctions risk
        sanctions_risks = [r for r in result.risk_register if r.type == "political" and "sanctions" in r.reason.lower()]
        assert len(sanctions_risks) > 0
        
        # Should be high severity
        assert all(risk.severity == RiskSeverity.HIGH for risk in sanctions_risks)
    
    def test_payment_risk_open_account(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Test payment risk for open account terms"""
        input_data = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="US",
            incoterms="FOB",
            payment_terms=PaymentTerms.OA  # High risk payment terms
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should have payment risk for OA terms
        payment_risks = [r for r in result.risk_register if r.type == "payment"]
        assert len(payment_risks) > 0
        
        oa_risks = [r for r in payment_risks if "OA" in r.reason]
        assert len(oa_risks) > 0
        
        # Should be high severity
        assert all(risk.severity == RiskSeverity.HIGH for risk in oa_risks)
        
        # Check mitigation steps
        assert any("LC" in step for risk in oa_risks for step in risk.mitigation_steps)
    
    def test_payment_risk_telegraphic_transfer(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Test payment risk for TT terms"""
        input_data = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="US",
            incoterms="FOB",
            payment_terms=PaymentTerms.TT
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should have payment risk for TT terms
        payment_risks = [r for r in result.risk_register if r.type == "payment"]
        tt_risks = [r for r in payment_risks if "TT" in r.reason]
        assert len(tt_risks) > 0
        
        # Should be medium severity
        assert all(risk.severity == RiskSeverity.MEDIUM for risk in tt_risks)
    
    def test_payment_risk_buyer_behavior(self, risk_engine: RiskEngine, test_tenant: Tenant, sample_buyer_data):
        """Test payment risk based on buyer behavior data"""
        input_data = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="US",  # Has sample buyer data
            incoterms="FOB",
            payment_terms=PaymentTerms.LC
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should have payment risks based on buyer behavior
        payment_risks = [r for r in result.risk_register if r.type == "payment"]
        behavior_risks = [r for r in payment_risks if "payment delay" in r.reason.lower() or "default rate" in r.reason.lower()]
        
        # Should detect high payment delay (45 days > 30 threshold)
        delay_risks = [r for r in behavior_risks if "payment delay" in r.reason.lower()]
        assert len(delay_risks) > 0
        
        # Should be medium severity for delay
        assert all(risk.severity == RiskSeverity.MEDIUM for risk in delay_risks)
    
    def test_supplier_risk_low_reliability(self, risk_engine: RiskEngine, test_tenant: Tenant, sample_supplier_data):
        """Test supplier risk for low reliability score"""
        # Update supplier to have low reliability
        sample_supplier_data.reliability_score = 45
        risk_engine.db.commit()
        
        input_data = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="US",
            incoterms="FOB",
            payment_terms=PaymentTerms.LC,
            supplier_id="Test Supplier Co"  # Matches sample supplier
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should have supplier risk
        supplier_risks = [r for r in result.risk_register if r.type == "supplier"]
        assert len(supplier_risks) > 0
        
        # Should detect low reliability score
        reliability_risks = [r for r in supplier_risks if "reliability score" in r.reason]
        assert len(reliability_risks) > 0
        
        # Should be high severity for low reliability
        assert all(risk.severity == RiskSeverity.HIGH for risk in reliability_risks)
    
    def test_supplier_risk_unknown_supplier(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Test supplier risk for unknown supplier"""
        input_data = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="US",
            incoterms="FOB",
            payment_terms=PaymentTerms.LC,
            supplier_id="Unknown Supplier Inc"  # Not in database
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should have supplier risk for unknown supplier
        supplier_risks = [r for r in result.risk_register if r.type == "supplier"]
        unknown_risks = [r for r in supplier_risks if "unknown supplier" in r.reason.lower()]
        assert len(unknown_risks) > 0
        
        # Should be medium severity
        assert all(risk.severity == RiskSeverity.MEDIUM for risk in unknown_risks)
    
    def test_route_risk_risky_tags(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Test route risk for risky route tags"""
        input_data = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="US",
            incoterms="FOB",
            payment_terms=PaymentTerms.LC,
            route_tags=["RedSea", "Suez_Canal"]  # Risky routes
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should have route risks
        route_risks = [r for r in result.risk_register if r.type == "route"]
        assert len(route_risks) > 0
        
        # Should detect RedSea risk
        redsea_risks = [r for r in route_risks if "RedSea" in r.reason]
        assert len(redsea_risks) > 0
        
        # Should be high severity
        assert all(risk.severity == RiskSeverity.HIGH for risk in redsea_risks)
    
    def test_overall_risk_level_calculation(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Test overall risk level calculation"""
        input_data = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="IR",  # High political risk
            incoterms="FOB",
            payment_terms=PaymentTerms.OA,  # High payment risk
            route_tags=["RedSea"],  # High route risk
            supplier_id="Unknown Supplier"  # Medium supplier risk
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should have multiple high risks
        high_risks = [r for r in result.risk_register if r.severity == RiskSeverity.HIGH]
        assert len(high_risks) >= 2
        
        # Overall risk should be high
        assert result.overall_risk_level == RiskSeverity.HIGH
    
    def test_explainability_structure(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Test explainability bundle structure"""
        input_data = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="US",
            incoterms="FOB",
            payment_terms=PaymentTerms.LC
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
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
        assert len(explainability.data_used) >= 2  # Input + tenant config
        assert any(ds.source_name == "user_input" for ds in explainability.data_used)
        assert any(ds.source_name == "tenant_configuration" for ds in explainability.data_used)
        
        # Check assumptions
        assert len(explainability.assumptions) > 0
        assert "geopolitical" in " ".join(explainability.assumptions).lower()
        
        # Check confidence
        assert 0.0 <= explainability.confidence <= 1.0
        
        # Check action plan
        assert len(explainability.action_plan) > 0
        
        # Check computation method
        assert "rule-based" in explainability.computation_method.lower()
    
    def test_confidence_calculation(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Test confidence score calculation"""
        # Minimal input - lower confidence
        input_data = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="US",
            incoterms="FOB",
            payment_terms=PaymentTerms.LC
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        assert result.status == "success"
        base_confidence = result.explainability.confidence
        
        # With supplier and route data - higher confidence
        input_data.supplier_id = "Test Supplier"
        input_data.route_tags = ["RedSea"]
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        assert result.status == "success"
        assert result.explainability.confidence > base_confidence

class TestRiskAPI:
    """Test risk engine API endpoints"""
    
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
    
    def test_risk_api_success(self, test_user: User, test_tenant: Tenant):
        """Test successful risk API call"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            "origin_country": "CN",
            "destination_country": "US",
            "incoterms": "FOB",
            "payment_terms": "LC",
            "route_tags": ["RedSea"]
        }
        
        response = client.post("/brain/risk/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "risk_register" in data
        assert "overall_risk_level" in data
        assert "explainability" in data
        
        # Check risk register structure
        risk_register = data["risk_register"]
        assert isinstance(risk_register, list)
        
        if risk_register:  # If risks were identified
            risk = risk_register[0]
            assert "type" in risk
            assert "severity" in risk
            assert "reason" in risk
            assert "mitigation_steps" in risk
            assert isinstance(risk["mitigation_steps"], list)
        
        app.dependency_overrides.clear()
    
    def test_risk_api_missing_fields(self, test_user: User, test_tenant: Tenant):
        """Test risk API with missing fields"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            # Missing required fields
        }
        
        response = client.post("/brain/risk/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"
        assert "explainability" in data
        assert len(data["explainability"]["missing_fields"]) > 0
        
        app.dependency_overrides.clear()
    
    def test_risk_api_high_risk_scenario(self, test_user: User, test_tenant: Tenant):
        """Test risk API with high-risk scenario"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            "origin_country": "CN",
            "destination_country": "IR",  # High risk
            "incoterms": "FOB",
            "payment_terms": "OA",  # High risk
            "route_tags": ["RedSea"]  # High risk
        }
        
        response = client.post("/brain/risk/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["overall_risk_level"] == "high"
        
        # Should have multiple risks
        risk_register = data["risk_register"]
        high_risks = [r for r in risk_register if r["severity"] == "high"]
        assert len(high_risks) >= 2
        
        app.dependency_overrides.clear()
    
    def test_risk_run_persistence(self, test_user: User, test_tenant: Tenant):
        """Test that risk runs are persisted"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            "origin_country": "CN",
            "destination_country": "US",
            "incoterms": "FOB",
            "payment_terms": "LC"
        }
        
        # Run analysis
        response = client.post("/brain/risk/run", json=input_data)
        assert response.status_code == 200
        
        # Check run was saved
        runs_response = client.get("/brain/runs?engine_type=risk")
        assert runs_response.status_code == 200
        
        runs_data = runs_response.json()
        assert len(runs_data["runs"]) > 0
        
        # Find our run
        our_run = None
        for run in runs_data["runs"]:
            if run["input_payload"]["product_key"] == "123456":
                our_run = run
                break
        
        assert our_run is not None
        assert our_run["engine_type"] == "risk"
        assert our_run["status"] == "success"
        assert "explainability" in our_run
        assert "risk_register" in our_run["output_payload"]
        
        app.dependency_overrides.clear()

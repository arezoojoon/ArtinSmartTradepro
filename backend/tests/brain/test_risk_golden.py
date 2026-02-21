"""
Phase 5 Golden Tests - Risk Engine
Anti-fake validation with deterministic rule-based outputs
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.tenant import Tenant
from app.models.brain_assets import AssetSupplierReliability, AssetBuyerPaymentBehavior
from app.services.brain_risk_engine import RiskEngine
from app.schemas.brain import RiskInput, PaymentTerms

client = TestClient(app)

class TestRiskGolden:
    """Golden tests for risk engine with fixed inputs and expected outputs"""
    
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
    
    def test_golden_case_1_high_risk_country(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Golden case 1: High risk destination country"""
        input_data = RiskInput(
            product_key="123456",
            origin_country="US",
            destination_country="IR",  # High risk country
            incoterms="FOB",
            payment_terms=PaymentTerms.LC
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should have political risk for high-risk country
        political_risks = [r for r in result.risk_register if r.type == "political"]
        assert len(political_risks) > 0
        
        high_risk = [r for r in political_risks if r.severity.value == "high"]
        assert len(high_risk) > 0
        
        # Risk reason should mention Iran
        assert any("IR" in risk.reason for risk in high_risk)
        
        # Mitigation steps should be provided
        for risk in high_risk:
            assert len(risk.mitigation_steps) > 0
            assert any("alternative" in step.lower() for step in risk.mitigation_steps)
        
        # Explainability must reference tenant configuration
        assert any("tenant" in ds.source_name.lower() for ds in result.explainability.data_used)
        
        # Overall risk should be high
        assert result.overall_risk_level.value == "high"
    
    def test_golden_case_2_open_account_payment_risk(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Golden case 2: Open account payment terms risk"""
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
        oa_risks = [r for r in payment_risks if "OA" in r.reason]
        assert len(oa_risks) > 0
        
        # Should be high severity
        assert all(risk.severity.value == "high" for risk in oa_risks)
        
        # Mitigation steps should suggest LC
        for risk in oa_risks:
            assert any("LC" in step for step in risk.mitigation_steps)
        
        # Explainability must mention payment terms
        assert any("payment" in assumption.lower() for assumption in result.explainability.assumptions)
    
    def test_golden_case_3_supplier_reliability_risk(self, risk_engine: RiskEngine, test_tenant: Tenant, db_session: Session):
        """Golden case 3: Supplier reliability risk"""
        # Create low reliability supplier
        supplier = AssetSupplierReliability(
            tenant_id=test_tenant.id,
            supplier_name="Unreliable Supplier Co",
            supplier_country="CN",
            on_time_rate=0.6,  # Low on-time rate
            defect_rate=0.08,   # High defect rate
            dispute_count=5,    # High dispute count
            reliability_score=45,  # Low reliability score
            evidence={"source": "historical"}
        )
        db_session.add(supplier)
        db_session.commit()
        
        input_data = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="US",
            incoterms="FOB",
            payment_terms=PaymentTerms.LC,
            supplier_id="Unreliable Supplier Co"
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should have supplier risk
        supplier_risks = [r for r in result.risk_register if r.type == "supplier"]
        assert len(supplier_risks) > 0
        
        # Should detect low reliability score
        reliability_risks = [r for r in supplier_risks if "reliability score" in r.reason.lower()]
        assert len(reliability_risks) > 0
        
        # Should be high severity for low reliability
        assert all(risk.severity.value == "high" for risk in reliability_risks)
        
        # Explainability must reference supplier data
        assert any("supplier" in ds.dataset.lower() for ds in result.explainability.data_used)
    
    def test_golden_case_4_route_risk_choking_points(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Golden case 4: Route risk through chokepoints"""
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
        
        # Should be high severity for RedSea
        assert all(risk.severity.value == "high" for risk in redsea_risks)
        
        # Mitigation steps should suggest alternatives
        for risk in redsea_risks:
            assert any("alternative" in step.lower() for step in risk.mitigation_steps)
            assert any("insurance" in step.lower() for step in risk.mitigation_steps)
    
    def test_golden_case_5_buyer_payment_behavior_risk(self, risk_engine: RiskEngine, test_tenant: Tenant, db_session: Session):
        """Golden case 5: Buyer payment behavior risk"""
        # Create high-risk buyer behavior
        buyer = AssetBuyerPaymentBehavior(
            tenant_id=test_tenant.id,
            buyer_country="US",
            buyer_name="Slow Payer Inc",
            segment="Distributor",
            avg_payment_delay_days=60,  # High delay
            default_rate=0.08,           # High default rate
            preferred_terms="LC",
            payment_risk_score=75,        # High risk score
            evidence={"source": "historical"}
        )
        db_session.add(buyer)
        db_session.commit()
        
        input_data = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="US",
            incoterms="FOB",
            payment_terms=PaymentTerms.LC,
            buyer_country="US"
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should have payment risks based on buyer behavior
        payment_risks = [r for r in result.risk_register if r.type == "payment"]
        behavior_risks = [r for r in payment_risks if "payment delay" in r.reason.lower() or "default rate" in r.reason.lower()]
        assert len(behavior_risks) > 0
        
        # Should detect high payment delay
        delay_risks = [r for r in behavior_risks if "payment delay" in r.reason.lower()]
        assert len(delay_risks) > 0
        
        # Should be medium severity for delay
        assert all(risk.severity.value == "medium" for risk in delay_risks)
        
        # Explainability must reference buyer data
        assert any("buyer" in ds.dataset.lower() for ds in result.explainability.data_used)
    
    def test_golden_case_6_insufficient_data(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Golden case 6: Insufficient data scenario"""
        input_data = RiskInput(
            product_key="123456"
            # Missing required fields
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "insufficient_data"
        
        # Must list missing fields
        assert len(result.explainability.missing_fields) > 0
        assert "origin_country" in result.explainability.missing_fields
        assert "destination_country" in result.explainability.missing_fields
        assert "incoterms" in result.explainability.missing_fields
        assert "payment_terms" in result.explainability.missing_fields
        
        # Confidence must be 0
        assert result.explainability.confidence == 0.0
        
        # Action plan must suggest providing missing fields
        assert any("Provide missing field" in action for action in result.explainability.action_plan)
    
    def test_golden_case_7_explainability_structure_validation(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Golden case 7: Explainability structure validation"""
        input_data = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="US",
            incoterms="FOB",
            payment_terms=PaymentTerms.LC
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
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
        assert len(explainability.data_used) >= 2  # Input + tenant config
        assert len(explainability.assumptions) > 0
        assert len(explainability.action_plan) > 0
        assert len(explainability.limitations) > 0
        assert len(explainability.computation_method) > 0
    
    def test_golden_case_8_no_hallucinated_risk_data(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Golden case 8: No hallucinated risk data"""
        input_data = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="US",
            incoterms="FOB",
            payment_terms=PaymentTerms.LC
        )
        
        result = risk_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # All data_used entries must have valid sources
        for data_source in result.explainability.data_used:
            assert data_source.source_name in ["user_input", "tenant_configuration", "asset_supplier_reliability", "asset_buyer_payment_behavior"]
            assert data_source.dataset is not None
            assert data_source.coverage is not None
            assert data_source.confidence is None or 0.0 <= data_source.confidence <= 1.0
        
        # Risk register must be based on rules, not external data
        for risk in result.risk_register:
            assert risk.type in ["political", "payment", "supplier", "route"]
            assert risk.severity.value in ["low", "medium", "high"]
            assert len(risk.reason) > 0
            assert len(risk.mitigation_steps) > 0
            
            # No external market references
            assert "market" not in risk.reason.lower()
            assert "external" not in risk.reason.lower()
    
    def test_golden_case_9_deterministic_rule_application(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Golden case 9: Deterministic rule application"""
        input_data = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="IR",  # High risk
            incoterms="FOB",
            payment_terms=PaymentTerms.OA,  # High risk
            route_tags=["RedSea"]  # High risk
        )
        
        # Run the same input multiple times
        results = []
        for _ in range(3):
            result = risk_engine.run_analysis(test_tenant.id, input_data)
            results.append(result)
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result.status == first_result.status
            assert result.overall_risk_level == first_result.overall_risk_level
            assert len(result.risk_register) == len(first_result.risk_register)
            assert result.explainability.confidence == first_result.explainability.confidence
            
            # Individual risks should be identical
            for i, risk in enumerate(result.risk_register):
                first_risk = first_result.risk_register[i]
                assert risk.type == first_risk.type
                assert risk.severity == first_risk.severity
                assert risk.reason == first_risk.reason
                assert len(risk.mitigation_steps) == len(first_risk.mitigation_steps)
    
    def test_golden_case_10_overall_risk_calculation(self, risk_engine: RiskEngine, test_tenant: Tenant):
        """Golden case 10: Overall risk level calculation"""
        # Test with no risks
        low_risk_input = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="US",
            incoterms="FOB",
            payment_terms=PaymentTerms.LC
        )
        
        result = risk_engine.run_analysis(test_tenant.id, low_risk_input)
        assert result.status == "success"
        assert result.overall_risk_level.value in ["low", "medium"]
        
        # Test with one high risk
        one_high_risk_input = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="IR",  # High risk
            incoterms="FOB",
            payment_terms=PaymentTerms.LC
        )
        
        result = risk_engine.run_analysis(test_tenant.id, one_high_risk_input)
        assert result.status == "success"
        assert result.overall_risk_level.value == "high"
        
        # Test with multiple medium risks
        multiple_medium_risk_input = RiskInput(
            product_key="123456",
            origin_country="CN",
            destination_country="US",
            incoterms="FOB",
            payment_terms=PaymentTerms.TT  # Medium risk
        )
        
        result = risk_engine.run_analysis(test_tenant.id, multiple_medium_risk_input)
        assert result.status == "success"
        assert result.overall_risk_level.value in ["medium", "high"]

class TestRiskAPIGolden:
    """Golden tests for risk API endpoints"""
    
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
    
    def test_api_golden_case_1_high_risk_scenario(self, test_user: User, test_tenant: Tenant):
        """API golden case 1: High risk scenario"""
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
        assert "risk_register" in data
        assert "overall_risk_level" in data
        assert "explainability" in data
        
        # Should have high overall risk
        assert data["overall_risk_level"] == "high"
        
        # Should have multiple risks
        risk_register = data["risk_register"]
        assert len(risk_register) >= 2
        
        # Should have political risk
        political_risks = [r for r in risk_register if r["type"] == "political"]
        assert len(political_risks) > 0
        
        # Should have payment risk
        payment_risks = [r for r in risk_register if r["type"] == "payment"]
        assert len(payment_risks) > 0
        
        # Validate explainability
        explainability = data["explainability"]
        assert "data_used" in explainability
        assert "confidence" in explainability
        assert len(explainability["data_used"]) >= 2
        assert explainability["confidence"] > 0.3
        
        app.dependency_overrides.clear()
    
    def test_api_golden_case_2_insufficient_data(self, test_user: User, test_tenant: Tenant):
        """API golden case 2: Insufficient data handling"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456"
            # Missing required fields
        }
        
        response = client.post("/brain/risk/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"
        
        # Must have explainability with missing fields
        explainability = data["explainability"]
        assert "missing_fields" in explainability
        assert len(explainability["missing_fields"]) > 0
        assert explainability["confidence"] == 0.0
        
        # Must suggest next steps
        assert len(explainability["action_plan"]) > 0
        
        app.dependency_overrides.clear()
    
    def test_api_golden_case_3_run_persistence(self, test_user: User, test_tenant: Tenant):
        """API golden case 3: Run persistence validation"""
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
        
        # Check that run was persisted
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
        
        # Validate persisted risk register
        persisted_risk_register = our_run["output_payload"]["risk_register"]
        assert isinstance(persisted_risk_register, list)
        
        # Validate persisted explainability
        persisted_explainability = our_run["explainability"]
        assert "data_used" in persisted_explainability
        assert "confidence" in persisted_explainability
        assert persisted_explainability["confidence"] > 0
        
        app.dependency_overrides.clear()

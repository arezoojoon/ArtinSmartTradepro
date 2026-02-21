"""
Phase 5 Golden Tests - Arbitrage Engine
Anti-fake validation with deterministic outputs
"""
import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.tenant import Tenant
from app.models.brain_assets import AssetArbitrageHistory, ArbitrageOutcome
from app.services.brain_arbitrage_engine import ArbitrageEngine
from app.schemas.brain import ArbitrageInput

client = TestClient(app)

class TestArbitrageGolden:
    """Golden tests for arbitrage engine with fixed inputs and expected outputs"""
    
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
    def arbitrage_engine(self, db_session: Session):
        """Create arbitrage engine instance"""
        return ArbitrageEngine(db_session)
    
    def test_golden_case_1_high_margin_opportunity(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Golden case 1: High margin arbitrage opportunity"""
        # Fixed input data
        input_data = ArbitrageInput(
            product_key="123456",
            buy_market="CN",
            sell_market="US",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=150.0,
            sell_currency="USD",
            freight_cost=10.0,
            fx_rates={},
            fees=[{"amount": 5.0, "currency": "USD"}],
            target_margin_pct=20.0
        )
        
        # Expected deterministic output
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
        # Assertions for anti-fake validation
        assert result.status == "success"
        assert result.opportunity_card is not None
        
        # Margin calculation should be deterministic
        expected_margin = ((150.0 - (100.0 + 10.0 + 5.0)) / (100.0 + 10.0 + 5.0)) * 100
        assert abs(result.opportunity_card.estimated_margin_pct - expected_margin) < 0.01
        
        # Explainability must have data_used entries
        assert len(result.explainability.data_used) > 0
        assert any(ds.source_name == "user_input" for ds in result.explainability.data_used)
        
        # Confidence should be high with complete data
        assert result.explainability.confidence >= 0.7
        
        # Action plan must be non-empty
        assert len(result.explainability.action_plan) > 0
        
        # No missing fields for success case
        assert len(result.explainability.missing_fields) == 0
    
    def test_golden_case_2_insufficient_data(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Golden case 2: Insufficient data scenario"""
        # Fixed input with missing required fields
        input_data = ArbitrageInput(
            product_key="123456",
            buy_market="CN",
            # Missing sell_market, buy_price, buy_currency, sell_price, sell_currency
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
        # Must return insufficient_data
        assert result.status == "insufficient_data"
        
        # Explainability must list missing fields
        assert len(result.explainability.missing_fields) > 0
        assert "sell_market" in result.explainability.missing_fields
        assert "buy_price" in result.explainability.missing_fields
        
        # Confidence must be 0 for insufficient data
        assert result.explainability.confidence == 0.0
        
        # Action plan must suggest providing missing fields
        assert any("Provide missing field" in action for action in result.explainability.action_plan)
    
    def test_golden_case_3_fx_conversion(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Golden case 3: FX conversion scenario"""
        input_data = ArbitrageInput(
            product_key="123456",
            buy_market="CN",
            sell_market="EU",
            buy_price=100.0,
            buy_currency="CNY",
            sell_price=120.0,
            sell_currency="EUR",
            freight_cost=10.0,
            fx_rates={"CNY_USD": 0.14, "EUR_USD": 1.1}
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # FX conversion should be reflected in margin calculation
        # Buy: 100 CNY * 0.14 = 14 USD
        # Sell: 120 EUR * 1.1 = 132 USD
        # Total cost: 14 + 10 = 24 USD
        # Expected margin: (132 - 24) / 24 * 100 = 450%
        expected_margin = ((120.0 * 1.1) - (100.0 * 0.14 + 10.0)) / (100.0 * 0.14 + 10.0) * 100
        assert abs(result.opportunity_card.estimated_margin_pct - expected_margin) < 0.01
        
        # Explainability must mention FX rates
        assert any("fx" in assumption.lower() for assumption in result.explainability.assumptions)
        
        # Confidence should be higher with FX data
        assert result.explainability.confidence >= 0.5
    
    def test_golden_case_4_similar_deals_retrieval(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant, db_session: Session):
        """Golden case 4: Similar past deals retrieval"""
        # Create sample arbitrage history
        historical_deal = AssetArbitrageHistory(
            tenant_id=test_tenant.id,
            product_key="123456",
            buy_market="CN",
            sell_market="US",
            incoterms="FOB",
            buy_price=95.0,
            buy_currency="USD",
            sell_price=125.0,
            sell_currency="USD",
            estimated_margin_pct=25.0,
            realized_margin_pct=23.0,
            outcome=ArbitrageOutcome.WON,
            decision_reason="Good margin opportunity",
            data_used={"source": "historical"}
        )
        db_session.add(historical_deal)
        db_session.commit()
        
        input_data = ArbitrageInput(
            product_key="123456",  # Same as historical
            buy_market="CN",      # Same as historical
            sell_market="US",     # Same as historical
            buy_price=100.0,
            buy_currency="USD",
            sell_price=130.0,
            sell_currency="USD"
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should retrieve similar deals
        assert len(result.similar_deals) > 0
        
        # Similar deal should match our historical data
        similar_deal = result.similar_deals[0]
        assert similar_deal.product_key == "123456"
        assert similar_deal.buy_market == "CN"
        assert similar_deal.sell_market == "US"
        assert similar_deal.outcome == ArbitrageOutcome.WON
        
        # Explainability must mention similar deals
        assert any("similar" in ds.dataset.lower() for ds in result.explainability.data_used)
    
    def test_golden_case_5_confidence_calculation(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Golden case 5: Confidence calculation validation"""
        # Test with minimal data
        minimal_input = ArbitrageInput(
            product_key="123456",
            buy_market="CN",
            sell_market="US",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=120.0,
            sell_currency="USD"
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, minimal_input)
        
        assert result.status == "success"
        assert result.explainability.confidence == 0.3  # Base confidence
        
        # Test with freight cost
        freight_input = ArbitrageInput(
            product_key="123456",
            buy_market="CN",
            sell_market="US",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=120.0,
            sell_currency="USD",
            freight_cost=10.0
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, freight_input)
        assert result.explainability.confidence == 0.5  # Base + freight
        
        # Test with FX rates
        fx_input = ArbitrageInput(
            product_key="123456",
            buy_market="CN",
            sell_market="US",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=120.0,
            sell_currency="USD",
            freight_cost=10.0,
            fx_rates={"EUR_USD": 1.1}
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, fx_input)
        assert result.explainability.confidence == 0.7  # Base + freight + fx
    
    def test_golden_case_6_explainability_structure_validation(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Golden case 6: Explainability structure validation"""
        input_data = ArbitrageInput(
            product_key="123456",
            buy_market="CN",
            sell_market="US",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=120.0,
            sell_currency="USD",
            freight_cost=10.0
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
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
        assert len(explainability.data_used) > 0
        assert len(explainability.assumptions) > 0
        assert len(explainability.action_plan) > 0
        assert len(explainability.limitations) > 0
        assert len(explainability.computation_method) > 0
    
    def test_golden_case_7_no_hallucinated_data(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Golden case 7: No hallucinated data validation"""
        input_data = ArbitrageInput(
            product_key="123456",
            buy_market="CN",
            sell_market="US",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=120.0,
            sell_currency="USD"
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # All data_used entries must have valid sources
        for data_source in result.explainability.data_used:
            assert data_source.source_name in ["user_input", "asset_arbitrage_history"]
            assert data_source.dataset is not None
            assert data_source.coverage is not None
            assert data_source.confidence is None or 0.0 <= data_source.confidence <= 1.0
        
        # No external market data should be referenced
        datasets = [ds.dataset for ds in result.explainability.data_used]
        assert not any("external" in dataset.lower() for dataset in datasets)
        assert not any("market" in dataset.lower() for dataset in datasets)
        
        # Assumptions should be about missing data, not external factors
        for assumption in result.explainability.assumptions:
            assert "market" not in assumption.lower()
            assert "external" not in assumption.lower()
    
    def test_golden_case_8_deterministic_reproducibility(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Golden case 8: Deterministic reproducibility"""
        input_data = ArbitrageInput(
            product_key="123456",
            buy_market="CN",
            sell_market="US",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=120.0,
            sell_currency="USD",
            freight_cost=10.0
        )
        
        # Run the same input multiple times
        results = []
        for _ in range(3):
            result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
            results.append(result)
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result.status == first_result.status
            assert abs(result.opportunity_card.estimated_margin_pct - first_result.opportunity_card.estimated_margin_pct) < 0.001
            assert result.explainability.confidence == first_result.explainability.confidence
            assert len(result.explainability.data_used) == len(first_result.explainability.data_used)
            assert len(result.explainability.assumptions) == len(first_result.explainability.assumptions)
    
    def test_golden_case_9_target_margin_validation(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Golden case 9: Target margin validation"""
        input_data = ArbitrageInput(
            product_key="123456",
            buy_market="CN",
            sell_market="US",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=110.0,  # Low margin
            sell_currency="USD",
            freight_cost=10.0,
            target_margin_pct=20.0  # High target
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should identify that target margin is not met
        expected_margin = ((110.0 - (100.0 + 10.0)) / (100.0 + 10.0)) * 100  # 0%
        assert result.opportunity_card.estimated_margin_pct == expected_margin
        
        # Risk factors should mention below target margin
        assert any("below target" in risk.lower() for risk in result.opportunity_card.risk_factors)
        
        # Action plan should suggest improving margin
        assert any("negotiate" in action.lower() for action in result.explainability.action_plan)

class TestArbitrageAPIGolden:
    """Golden tests for arbitrage API endpoints"""
    
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
    
    def test_api_golden_case_1_complete_input(self, test_user: User, test_tenant: Tenant):
        """API golden case 1: Complete input validation"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        # Fixed complete input
        input_data = {
            "product_key": "123456",
            "buy_market": "CN",
            "sell_market": "US",
            "buy_price": 100.0,
            "buy_currency": "USD",
            "sell_price": 120.0,
            "sell_currency": "USD",
            "freight_cost": 10.0,
            "fees": [{"amount": 5.0, "currency": "USD"}],
            "target_margin_pct": 15.0
        }
        
        response = client.post("/brain/arbitrage/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "opportunity_card" in data
        assert "explainability" in data
        
        # Validate explainability structure
        explainability = data["explainability"]
        assert "data_used" in explainability
        assert "assumptions" in explainability
        assert "confidence" in explainability
        assert "action_plan" in explainability
        assert len(explainability["data_used"]) > 0
        assert explainability["confidence"] > 0.5
        
        app.dependency_overrides.clear()
    
    def test_api_golden_case_2_insufficient_data(self, test_user: User, test_tenant: Tenant):
        """API golden case 2: Insufficient data handling"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        # Incomplete input
        input_data = {
            "product_key": "123456"
            # Missing required fields
        }
        
        response = client.post("/brain/arbitrage/run", json=input_data)
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
            "buy_market": "CN",
            "sell_market": "US",
            "buy_price": 100.0,
            "buy_currency": "USD",
            "sell_price": 120.0,
            "sell_currency": "USD"
        }
        
        # Run analysis
        response = client.post("/brain/arbitrage/run", json=input_data)
        assert response.status_code == 200
        
        # Check that run was persisted
        runs_response = client.get("/brain/runs?engine_type=arbitrage")
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
        assert our_run["engine_type"] == "arbitrage"
        assert our_run["status"] == "success"
        assert "explainability" in our_run
        assert "opportunity_card" in our_run["output_payload"]
        
        # Validate persisted explainability
        persisted_explainability = our_run["explainability"]
        assert "data_used" in persisted_explainability
        assert "confidence" in persisted_explainability
        assert persisted_explainability["confidence"] > 0
        
        app.dependency_overrides.clear()

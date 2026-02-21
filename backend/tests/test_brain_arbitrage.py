"""
Phase 5 Arbitrage Engine Tests
Tests for deterministic arbitrage analysis and similar deals
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

class TestArbitrageEngine:
    """Test arbitrage engine deterministic calculations"""
    
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
    
    @pytest.fixture
    def sample_arbitrage_history(self, db_session: Session, test_tenant: Tenant):
        """Create sample arbitrage history records"""
        records = []
        
        # Create similar past deals
        for i in range(3):
            record = AssetArbitrageHistory(
                tenant_id=test_tenant.id,
                product_key="123456",
                buy_market="US",
                sell_market="EU",
                incoterms="FOB",
                buy_price=100.0 + i,
                buy_currency="USD",
                sell_price=120.0 + i,
                sell_currency="EUR",
                estimated_margin_pct=15.0 + i,
                realized_margin_pct=14.0 + i,
                outcome=ArbitrageOutcome.WON if i < 2 else ArbitrageOutcome.LOST,
                decision_reason=f"Test deal {i}",
                data_used={"source": "test"}
            )
            db_session.add(record)
            records.append(record)
        
        db_session.commit()
        return records
    
    def test_margin_calculation_basic(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Test basic margin calculation"""
        input_data = ArbitrageInput(
            product_key="123456",
            buy_market="US",
            sell_market="EU",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=120.0,
            sell_currency="EUR",
            freight_cost=10.0,
            fx_rates={"EUR_USD": 1.1}
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        assert result.opportunity_card is not None
        assert result.opportunity_card.estimated_margin_pct > 0
        
        # Check margin calculation: (120*1.1 - (100 + 10)) / (100 + 10) * 100
        # = (132 - 110) / 110 * 100 = 20%
        expected_margin = ((120.0 * 1.1) - (100.0 + 10.0)) / (100.0 + 10.0) * 100
        assert abs(result.opportunity_card.estimated_margin_pct - expected_margin) < 0.01
    
    def test_margin_calculation_no_fx(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Test margin calculation without FX rates"""
        input_data = ArbitrageInput(
            product_key="123456",
            buy_market="US",
            sell_market="EU",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=120.0,
            sell_currency="USD",  # Same currency
            freight_cost=10.0
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Check margin: (120 - (100 + 10)) / (100 + 10) * 100 = 9.09%
        expected_margin = (120.0 - (100.0 + 10.0)) / (100.0 + 10.0) * 100
        assert abs(result.opportunity_card.estimated_margin_pct - expected_margin) < 0.01
    
    def test_margin_calculation_with_fees(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Test margin calculation with additional fees"""
        input_data = ArbitrageInput(
            product_key="123456",
            buy_market="US",
            sell_market="EU",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=120.0,
            sell_currency="USD",
            freight_cost=10.0,
            fees=[
                {"amount": 5.0, "currency": "USD"},
                {"amount": 2.0, "currency": "USD"}
            ]
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Check margin: (120 - (100 + 10 + 5 + 2)) / (100 + 10 + 5 + 2) * 100 = 2.86%
        expected_margin = (120.0 - (100.0 + 10.0 + 5.0 + 2.0)) / (100.0 + 10.0 + 5.0 + 2.0) * 100
        assert abs(result.opportunity_card.estimated_margin_pct - expected_margin) < 0.01
    
    def test_confidence_calculation(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Test confidence score calculation"""
        # Minimal input - lowest confidence
        input_data = ArbitrageInput(
            product_key="123456",
            buy_market="US",
            sell_market="EU",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=120.0,
            sell_currency="USD"
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        assert result.status == "success"
        assert result.explainability.confidence == 0.3
        
        # With freight - higher confidence
        input_data.freight_cost = 10.0
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        assert result.explainability.confidence == 0.5
        
        # With FX rates - higher confidence
        input_data.fx_rates = {"EUR_USD": 1.1}
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        assert result.explainability.confidence == 0.7
        
        # With fees - highest confidence
        input_data.fees = [{"amount": 5.0, "currency": "USD"}]
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        assert result.explainability.confidence == 0.9
    
    def test_similar_deals_retrieval(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant, sample_arbitrage_history):
        """Test similar past deals retrieval"""
        input_data = ArbitrageInput(
            product_key="123456",  # Same as sample data
            buy_market="US",        # Same as sample data
            sell_market="EU",       # Same as sample data
            buy_price=100.0,
            buy_currency="USD",
            sell_price=120.0,
            sell_currency="USD"
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        assert len(result.similar_deals) == 3
        
        # Check deal properties
        for deal in result.similar_deals:
            assert deal.product_key == "123456"
            assert deal.buy_market == "US"
            assert deal.sell_market == "EU"
            assert deal.outcome in [ArbitrageOutcome.WON, ArbitrageOutcome.LOST]
            assert deal.estimated_margin_pct is not None
    
    def test_similar_deals_different_product(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant, sample_arbitrage_history):
        """Test similar deals with different product"""
        input_data = ArbitrageInput(
            product_key="789012",  # Different from sample data
            buy_market="US",
            sell_market="EU",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=120.0,
            sell_currency="USD"
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        assert len(result.similar_deals) == 0  # No similar deals
    
    def test_opportunity_card_high_margin(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Test opportunity card for high margin deal"""
        input_data = ArbitrageInput(
            product_key="123456",
            buy_market="US",
            sell_market="EU",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=150.0,  # High margin
            sell_currency="USD"
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        card = result.opportunity_card
        
        assert card.estimated_margin_pct > 30  # Should be high margin
        assert any("High margin" in driver for driver in card.key_drivers)
        assert "Request detailed quote from supplier" in card.next_actions
    
    def test_opportunity_card_low_margin(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Test opportunity card for low margin deal"""
        input_data = ArbitrageInput(
            product_key="123456",
            buy_market="US",
            sell_market="EU",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=105.0,  # Low margin
            sell_currency="USD"
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        card = result.opportunity_card
        
        assert card.estimated_margin_pct < 10  # Should be low margin
        assert any("Low margin" in driver for driver in card.key_drivers)
        assert "Negotiate better buy price" in card.next_actions
    
    def test_explainability_structure(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Test explainability bundle structure"""
        input_data = ArbitrageInput(
            product_key="123456",
            buy_market="US",
            sell_market="EU",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=120.0,
            sell_currency="USD",
            freight_cost=10.0
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
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
        assert len(explainability.data_used) >= 1
        assert any(ds.source_name == "user_input" for ds in explainability.data_used)
        
        # Check assumptions
        assert len(explainability.assumptions) > 0
        assert "Base currency set to USD" in explainability.assumptions
        
        # Check confidence
        assert 0.0 <= explainability.confidence <= 1.0
        assert "confidence" in explainability.confidence_rationale.lower()
        
        # Check action plan
        assert len(explainability.action_plan) > 0
    
    def test_target_margin_check(self, arbitrage_engine: ArbitrageEngine, test_tenant: Tenant):
        """Test target margin threshold"""
        input_data = ArbitrageInput(
            product_key="123456",
            buy_market="US",
            sell_market="EU",
            buy_price=100.0,
            buy_currency="USD",
            sell_price=120.0,
            sell_currency="USD",
            target_margin_pct=15.0  # Higher than actual margin
        )
        
        result = arbitrage_engine.run_analysis(test_tenant.id, input_data)
        
        assert result.status == "success"
        card = result.opportunity_card
        
        # Should mention below target margin
        assert any("Below target margin" in risk for risk in card.risk_factors)

class TestArbitrageAPI:
    """Test arbitrage engine API endpoints"""
    
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
    
    def test_arbitrage_api_success(self, test_user: User, test_tenant: Tenant):
        """Test successful arbitrage API call"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            "buy_market": "US",
            "sell_market": "EU",
            "buy_price": 100.0,
            "buy_currency": "USD",
            "sell_price": 120.0,
            "sell_currency": "USD",
            "freight_cost": 10.0
        }
        
        response = client.post("/brain/arbitrage/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "opportunity_card" in data
        assert "similar_deals" in data
        assert "explainability" in data
        
        # Check opportunity card
        card = data["opportunity_card"]
        assert "estimated_margin_pct" in card
        assert "key_drivers" in card
        assert "next_actions" in card
        assert card["estimated_margin_pct"] > 0
        
        app.dependency_overrides.clear()
    
    def test_arbitrage_api_missing_fields(self, test_user: User, test_tenant: Tenant):
        """Test arbitrage API with missing fields"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            # Missing required fields
        }
        
        response = client.post("/brain/arbitrage/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"
        assert "explainability" in data
        assert len(data["explainability"]["missing_fields"]) > 0
        
        app.dependency_overrides.clear()
    
    def test_arbitrage_api_invalid_currency(self, test_user: User, test_tenant: Tenant):
        """Test arbitrage API with invalid currency"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            "buy_market": "US",
            "sell_market": "EU",
            "buy_price": 100.0,
            "buy_currency": "INVALID",  # Invalid currency
            "sell_price": 120.0,
            "sell_currency": "USD"
        }
        
        response = client.post("/brain/arbitrage/run", json=input_data)
        assert response.status_code == 422  # Validation error
        
        app.dependency_overrides.clear()
    
    def test_arbitrage_run_persistence(self, test_user: User, test_tenant: Tenant):
        """Test that arbitrage runs are persisted"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            "buy_market": "US",
            "sell_market": "EU",
            "buy_price": 100.0,
            "buy_currency": "USD",
            "sell_price": 120.0,
            "sell_currency": "USD"
        }
        
        # Run analysis
        response = client.post("/brain/arbitrage/run", json=input_data)
        assert response.status_code == 200
        
        # Check run was saved
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
        
        app.dependency_overrides.clear()

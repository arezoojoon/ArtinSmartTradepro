"""
Phase 5 Brain API Tests
Tests for brain API contracts and deterministic validation
"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.tenant import Tenant

client = TestClient(app)

class TestBrainAPIContracts:
    """Test brain API contracts and validation"""
    
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
    
    def test_arbitrage_engine_missing_fields(self, test_user: User, test_tenant: Tenant):
        """Test arbitrage engine with missing required fields"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        # Missing required fields
        input_data = {
            "product_key": "123456",
            "buy_market": "US",
            # Missing sell_market, buy_price, buy_currency, sell_price, sell_currency
        }
        
        response = client.post("/brain/arbitrage/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"
        assert "explainability" in data
        assert data["explainability"]["missing_fields"] is not None
        assert len(data["explainability"]["missing_fields"]) > 0
        assert "sell_market" in data["explainability"]["missing_fields"]
        
        app.dependency_overrides.clear()
    
    def test_arbitrage_engine_invalid_numeric_fields(self, test_user: User, test_tenant: Tenant):
        """Test arbitrage engine with invalid numeric fields"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            "buy_market": "US",
            "sell_market": "EU",
            "buy_price": "invalid_price",  # Invalid numeric
            "buy_currency": "USD",
            "sell_price": 100.0,
            "sell_currency": "EUR"
        }
        
        response = client.post("/brain/arbitrage/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"
        assert "explainability" in data
        assert "buy_price" in str(data["explainability"]["missing_fields"])
        
        app.dependency_overrides.clear()
    
    def test_arbitrage_engine_valid_input_placeholder(self, test_user: User, test_tenant: Tenant):
        """Test arbitrage engine with valid input (returns insufficient_data until implemented)"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            "buy_market": "US",
            "sell_market": "EU",
            "buy_price": 100.0,
            "buy_currency": "USD",
            "sell_price": 120.0,
            "sell_currency": "EUR",
            "freight_cost": 10.0
        }
        
        response = client.post("/brain/arbitrage/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"  # Engine not implemented yet
        assert "explainability" in data
        assert "Engine implementation" in data["explainability"]["missing_fields"]
        
        app.dependency_overrides.clear()
    
    def test_risk_engine_missing_fields(self, test_user: User, test_tenant: Tenant):
        """Test risk engine with missing required fields"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            "origin_country": "US",
            # Missing destination_country, incoterms, payment_terms
        }
        
        response = client.post("/brain/risk/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"
        assert "explainability" in data
        assert len(data["explainability"]["missing_fields"]) > 0
        
        app.dependency_overrides.clear()
    
    def test_risk_engine_valid_input_placeholder(self, test_user: User, test_tenant: Tenant):
        """Test risk engine with valid input (returns insufficient_data until implemented)"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            "origin_country": "US",
            "destination_country": "EU",
            "hs_code": "123456",
            "incoterms": "FOB",
            "payment_terms": "LC",
            "route_tags": ["RedSea"]
        }
        
        response = client.post("/brain/risk/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"  # Engine not implemented yet
        assert "explainability" in data
        
        app.dependency_overrides.clear()
    
    def test_demand_engine_missing_fields(self, test_user: User, test_tenant: Tenant):
        """Test demand engine with missing required fields"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            # Missing country
        }
        
        response = client.post("/brain/demand/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"
        assert "explainability" in data
        assert "country" in data["explainability"]["missing_fields"]
        
        app.dependency_overrides.clear()
    
    def test_demand_engine_valid_input_placeholder(self, test_user: User, test_tenant: Tenant):
        """Test demand engine with valid input (returns insufficient_data until implemented)"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            "country": "US",
            "forecast_months": 6
        }
        
        response = client.post("/brain/demand/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"  # Engine not implemented yet
        assert "explainability" in data
        
        app.dependency_overrides.clear()
    
    def test_cultural_engine_missing_fields(self, test_user: User, test_tenant: Tenant):
        """Test cultural engine with missing required fields"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "destination_country": "US",
            "buyer_type": "B2B",
            # Missing payment_terms_target, deal_context, language
        }
        
        response = client.post("/brain/cultural/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"
        assert "explainability" in data
        assert len(data["explainability"]["missing_fields"]) > 0
        
        app.dependency_overrides.clear()
    
    def test_cultural_engine_invalid_language(self, test_user: User, test_tenant: Tenant):
        """Test cultural engine with invalid language"""
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
    
    def test_cultural_engine_valid_input_placeholder(self, test_user: User, test_tenant: Tenant):
        """Test cultural engine with valid input (returns insufficient_data until implemented)"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "destination_country": "US",
            "buyer_type": "B2B",
            "payment_terms_target": "LC",
            "deal_context": "Test deal context",
            "language": "en"
        }
        
        response = client.post("/brain/cultural/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"  # Engine not implemented yet
        assert "explainability" in data
        
        app.dependency_overrides.clear()
    
    def test_list_engine_runs(self, test_user: User, test_tenant: Tenant):
        """Test listing engine runs"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.get("/brain/runs")
        assert response.status_code == 200
        
        data = response.json()
        assert "runs" in data
        assert "total" in data
        assert isinstance(data["runs"], list)
        
        app.dependency_overrides.clear()
    
    def test_list_engine_runs_with_filter(self, test_user: User, test_tenant: Tenant):
        """Test listing engine runs with engine type filter"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.get("/brain/runs?engine_type=arbitrage")
        assert response.status_code == 200
        
        data = response.json()
        assert "runs" in data
        assert "total" in data
        
        app.dependency_overrides.clear()
    
    def test_list_engine_runs_invalid_engine_type(self, test_user: User, test_tenant: Tenant):
        """Test listing engine runs with invalid engine type"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.get("/brain/runs?engine_type=invalid_engine")
        assert response.status_code == 400
        
        data = response.json()
        assert "Invalid engine type" in data["detail"]
        
        app.dependency_overrides.clear()
    
    def test_get_engine_run_not_found(self, test_user: User, test_tenant: Tenant):
        """Test getting non-existent engine run"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        fake_id = uuid4()
        response = client.get(f"/brain/runs/{fake_id}")
        assert response.status_code == 404
        
        data = response.json()
        assert "Engine run not found" in data["detail"]
        
        app.dependency_overrides.clear()
    
    def test_list_data_sources(self, test_user: User, test_tenant: Tenant):
        """Test listing data sources"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.get("/brain/data-sources")
        assert response.status_code == 200
        
        data = response.json()
        assert "sources" in data
        assert "total" in data
        assert isinstance(data["sources"], list)
        
        app.dependency_overrides.clear()
    
    def test_list_data_sources_active_only(self, test_user: User, test_tenant: Tenant):
        """Test listing only active data sources"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        response = client.get("/brain/data-sources?active_only=true")
        assert response.status_code == 200
        
        data = response.json()
        assert "sources" in data
        assert "total" in data
        
        # Check that all returned sources are active
        for source in data["sources"]:
            assert source["is_active"] is True
        
        app.dependency_overrides.clear()

class TestBrainAPIExplainability:
    """Test explainability structure in brain API responses"""
    
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
    
    def test_explainability_structure_insufficient_data(self, test_user: User, test_tenant: Tenant):
        """Test explainability structure for insufficient data responses"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456"
            # Missing many required fields
        }
        
        response = client.post("/brain/arbitrage/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        explainability = data["explainability"]
        
        # Check required explainability fields
        assert "data_used" in explainability
        assert "assumptions" in explainability
        assert "confidence" in explainability
        assert "confidence_rationale" in explainability
        assert "action_plan" in explainability
        assert "limitations" in explainability
        assert "computation_method" in explainability
        assert "missing_fields" in explainability
        
        # Check values for insufficient data
        assert explainability["data_used"] == []
        assert explainability["confidence"] == 0.0
        assert "insufficient" in explainability["computation_method"].lower()
        assert len(explainability["missing_fields"]) > 0
        assert len(explainability["action_plan"]) > 0
        
        app.dependency_overrides.clear()
    
    def test_engine_run_persistence(self, test_user: User, test_tenant: Tenant):
        """Test that engine runs are persisted correctly"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456"
        }
        
        # Run engine
        response = client.post("/brain/arbitrage/run", json=input_data)
        assert response.status_code == 200
        
        # Check that run was saved
        runs_response = client.get("/brain/runs")
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
        assert our_run["status"] == "insufficient_data"
        assert "explainability" in our_run
        assert "created_at" in our_run
        
        app.dependency_overrides.clear()

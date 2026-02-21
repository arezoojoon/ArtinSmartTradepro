"""
Phase 5 Demand Forecast Engine Tests
Tests for time series forecasting and seasonality matrix integration
"""
import pytest
from uuid import uuid4
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.tenant import Tenant
from app.models.brain_assets import DemandTimeSeries, AssetSeasonalityMatrix
from app.services.brain_demand_engine import DemandForecastEngine
from app.schemas.brain import DemandInput

client = TestClient(app)

class TestDemandForecastEngine:
    """Test demand forecast engine deterministic calculations"""
    
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
    def demand_engine(self, db_session: Session):
        """Create demand forecast engine instance"""
        return DemandForecastEngine(db_session)
    
    @pytest.fixture
    def sample_historical_data(self, db_session: Session, test_tenant: Tenant):
        """Create sample historical demand data"""
        records = []
        base_date = date(2023, 1, 1)
        
        # Create 24 months of data
        for i in range(24):
            record_date = base_date + timedelta(days=30 * i)
            
            # Add seasonal pattern (higher in summer)
            base_demand = 100
            if record_date.month in [6, 7, 8]:  # Summer
                demand = base_demand * 1.5
            elif record_date.month in [12, 1, 2]:  # Winter
                demand = base_demand * 0.8
            else:
                demand = base_demand
            
            record = DemandTimeSeries(
                tenant_id=test_tenant.id,
                product_key="123456",
                country="US",
                date=record_date,
                demand_value=demand + (i % 10) - 5,  # Add some variation
                source_name="test_data",
                data_used={"source": "test"}
            )
            db_session.add(record)
            records.append(record)
        
        db_session.commit()
        return records
    
    @pytest.fixture
    def sample_seasonality_data(self, db_session: Session, test_tenant: Tenant):
        """Create sample seasonality matrix data"""
        records = []
        
        seasons = [
            ("SUMMER_2024", 1.5, 0.2, 0.1),
            ("WINTER_2024", 0.8, 0.15, 0.1),
            ("Q1_2024", 0.9, 0.1, 0.05),
            ("Q2_2024", 1.1, 0.1, 0.05),
            ("Q3_2024", 1.3, 0.15, 0.1),
            ("Q4_2024", 0.95, 0.1, 0.05)
        ]
        
        for season_key, demand_idx, price_idx, vol_idx in seasons:
            record = AssetSeasonalityMatrix(
                tenant_id=test_tenant.id,
                product_key="123456",
                country="US",
                season_key=season_key,
                demand_index=demand_idx,
                price_index=price_idx,
                volatility_index=vol_idx,
                data_used={"source": "seasonal_analysis"}
            )
            db_session.add(record)
            records.append(record)
        
        db_session.commit()
        return records
    
    def test_time_series_forecast(self, demand_engine: DemandForecastEngine, test_tenant: Tenant, sample_historical_data):
        """Test time series forecasting with sufficient data"""
        input_data = DemandInput(
            product_key="123456",
            country="US",
            forecast_months=6
        )
        
        result = demand_engine.run_forecast(test_tenant.id, input_data)
        
        assert result.status == "success"
        assert result.method_used == "seasonal_naive"
        assert len(result.forecast_points) == 6
        assert result.data_points_used >= 12
        
        # Check forecast points structure
        for point in result.forecast_points:
            assert point.demand_value > 0
            assert point.date > date.today()
            assert "confidence_interval" in point.__dict__
            assert "lower" in point.confidence_interval
            assert "upper" in point.confidence_interval
            assert point.confidence_interval["lower"] <= point.demand_value <= point.confidence_interval["upper"]
    
    def test_seasonality_forecast(self, demand_engine: DemandForecastEngine, test_tenant: Tenant, sample_seasonality_data):
        """Test seasonality matrix forecasting"""
        input_data = DemandInput(
            product_key="123456",
            country="US",
            forecast_months=6
        )
        
        result = demand_engine.run_forecast(test_tenant.id, input_data)
        
        assert result.status == "success"
        assert result.method_used == "seasonality_matrix"
        assert len(result.forecast_points) == 6
        
        # Check that seasonality indices are applied
        forecast_values = [point.demand_value for point in result.forecast_points]
        assert all(value > 0 for value in forecast_values)
        
        # Should have variation based on seasonality
        assert max(forecast_values) != min(forecast_values)
    
    def test_insufficient_data_no_historical(self, demand_engine: DemandForecastEngine, test_tenant: Tenant):
        """Test insufficient data when no historical data available"""
        input_data = DemandInput(
            product_key="999999",  # Non-existent product
            country="XX",          # Non-existent country
            forecast_months=6
        )
        
        result = demand_engine.run_forecast(test_tenant.id, input_data)
        
        assert result.status == "insufficient_data"
        assert len(result.forecast_points) == 0
        assert result.method_used == "none"
        assert result.data_points_used == 0
        
        # Check explainability
        assert result.explainability.confidence == 0.0
        assert len(result.explainability.missing_fields) > 0
        assert len(result.explainability.action_plan) > 0
    
    def test_insufficient_data_invalid_forecast_months(self, demand_engine: DemandForecastEngine, test_tenant: Tenant):
        """Test insufficient data with invalid forecast months"""
        input_data = DemandInput(
            product_key="123456",
            country="US",
            forecast_months=15  # Invalid (> 12)
        )
        
        result = demand_engine.run_forecast(test_tenant.id, input_data)
        
        assert result.status == "insufficient_data"
        assert "forecast_months" in str(result.explainability.missing_fields)
    
    def test_peak_window_identification(self, demand_engine: DemandForecastEngine, test_tenant: Tenant, sample_historical_data):
        """Test peak window identification"""
        input_data = DemandInput(
            product_key="123456",
            country="US",
            forecast_months=12  # Longer forecast to capture peaks
        )
        
        result = demand_engine.run_forecast(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # Should identify some peak windows (since historical data has seasonal pattern)
        if result.peak_windows:
            for window in result.peak_windows:
                assert window.start_date <= window.end_date
                assert window.demand_multiplier > 1.0
                assert window.start_date > date.today()
    
    def test_confidence_calculation(self, demand_engine: DemandForecastEngine, test_tenant: Tenant, sample_historical_data):
        """Test confidence score calculation"""
        input_data = DemandInput(
            product_key="123456",
            country="US",
            forecast_months=6
        )
        
        result = demand_engine.run_forecast(test_tenant.id, input_data)
        
        assert result.status == "success"
        assert 0.0 <= result.explainability.confidence <= 1.0
        
        # With 24 months of data, confidence should be reasonably high
        assert result.explainability.confidence >= 0.7
    
    def test_confidence_calculation_limited_data(self, demand_engine: DemandForecastEngine, test_tenant: Tenant):
        """Test confidence calculation with limited data"""
        # Create only 6 months of data
        base_date = date(2023, 1, 1)
        for i in range(6):
            record_date = base_date + timedelta(days=30 * i)
            record = DemandTimeSeries(
                tenant_id=test_tenant.id,
                product_key="LIMITED",
                country="US",
                date=record_date,
                demand_value=100.0,
                source_name="limited_data",
                data_used={"source": "test"}
            )
            demand_engine.db.add(record)
        demand_engine.db.commit()
        
        input_data = DemandInput(
            product_key="LIMITED",
            country="US",
            forecast_months=3
        )
        
        result = demand_engine.run_forecast(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # With limited data, confidence should be lower
        assert result.explainability.confidence < 0.7
    
    def test_explainability_structure(self, demand_engine: DemandForecastEngine, test_tenant: Tenant, sample_historical_data):
        """Test explainability bundle structure"""
        input_data = DemandInput(
            product_key="123456",
            country="US",
            forecast_months=6
        )
        
        result = demand_engine.run_forecast(test_tenant.id, input_data)
        
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
        assert len(explainability.data_used) >= 2  # Input + historical data
        assert any(ds.source_name == "user_input" for ds in explainability.data_used)
        assert any(ds.source_name == "demand_time_series" for ds in explainability.data_used)
        
        # Check assumptions
        assert len(explainability.assumptions) > 0
        assert "seasonal" in " ".join(explainability.assumptions).lower()
        
        # Check confidence
        assert 0.0 <= explainability.confidence <= 1.0
        assert "confidence" in explainability.confidence_rationale.lower()
        
        # Check action plan
        assert len(explainability.action_plan) > 0
        
        # Check limitations
        assert len(explainability.limitations) > 0
        assert "historical" in " ".join(explainability.limitations).lower()
    
    def test_season_key_generation(self, demand_engine: DemandForecastEngine):
        """Test season key generation for different dates"""
        # Test different months
        test_cases = [
            (date(2024, 3, 15), "RAMADAN_2024"),
            (date(2024, 7, 15), "SUMMER_2024"),
            (date(2024, 12, 15), "WINTER_2024"),
            (date(2024, 2, 15), "WINTER_2024"),
            (date(2024, 4, 15), "SUMMER_2024"),
            (date(2024, 9, 15), "AUTUMN_2024"),
            (date(2024, 1, 15), "WINTER_2024")
        ]
        
        for test_date, expected_season in test_cases:
            season_key = demand_engine._get_season_key(test_date)
            assert season_key == expected_season
    
    def test_add_months_utility(self, demand_engine: DemandForecastEngine):
        """Test month addition utility function"""
        # Test basic month addition
        start_date = date(2024, 1, 15)
        
        # Add 1 month
        result = demand_engine._add_months(start_date, 1)
        assert result == date(2024, 2, 15)
        
        # Add 12 months (year rollover)
        result = demand_engine._add_months(start_date, 12)
        assert result == date(2025, 1, 15)
        
        # Test month end handling (Jan 31 + 1 month = Feb 28/29)
        jan_31 = date(2024, 1, 31)
        result = demand_engine._add_months(jan_31, 1)
        assert result.year == 2024
        assert result.month == 2
        assert result.day <= 29  # Feb 28 or 29 depending on leap year

class TestDemandAPI:
    """Test demand forecast engine API endpoints"""
    
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
    
    def test_demand_api_success(self, test_user: User, test_tenant: Tenant):
        """Test successful demand API call"""
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
        assert data["status"] == "success"
        assert "forecast_points" in data
        assert "peak_windows" in data
        assert "method_used" in data
        assert "data_points_used" in data
        assert "explainability" in data
        
        # Check forecast points structure
        forecast_points = data["forecast_points"]
        assert isinstance(forecast_points, list)
        
        if forecast_points:  # If forecast was generated
            point = forecast_points[0]
            assert "date" in point
            assert "demand_value" in point
            assert "confidence_interval" in point
        
        app.dependency_overrides.clear()
    
    def test_demand_api_missing_fields(self, test_user: User, test_tenant: Tenant):
        """Test demand API with missing fields"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456"
            # Missing country
        }
        
        response = client.post("/brain/demand/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"
        assert "explainability" in data
        assert len(data["explainability"]["missing_fields"]) > 0
        
        app.dependency_overrides.clear()
    
    def test_demand_api_invalid_forecast_months(self, test_user: User, test_tenant: Tenant):
        """Test demand API with invalid forecast months"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            "country": "US",
            "forecast_months": 15  # Invalid (> 12)
        }
        
        response = client.post("/brain/demand/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"
        assert "forecast_months" in str(data["explainability"]["missing_fields"])
        
        app.dependency_overrides.clear()
    
    def test_demand_api_no_data_available(self, test_user: User, test_tenant: Tenant):
        """Test demand API with no historical data available"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "NONEXISTENT",
            "country": "XX",
            "forecast_months": 6
        }
        
        response = client.post("/brain/demand/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"
        assert data["data_points_used"] == 0
        assert data["method_used"] == "none"
        
        # Should suggest data collection
        action_plan = data["explainability"]["action_plan"]
        assert any("historical" in step.lower() for step in action_plan)
        
        app.dependency_overrides.clear()
    
    def test_demand_run_persistence(self, test_user: User, test_tenant: Tenant):
        """Test that demand runs are persisted"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            "country": "US",
            "forecast_months": 6
        }
        
        # Run forecast
        response = client.post("/brain/demand/run", json=input_data)
        assert response.status_code == 200
        
        # Check run was saved
        runs_response = client.get("/brain/runs?engine_type=demand")
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
        assert our_run["engine_type"] == "demand"
        assert our_run["status"] in ["success", "insufficient_data"]
        assert "explainability" in our_run
        assert "forecast_points" in our_run["output_payload"]
        
        app.dependency_overrides.clear()

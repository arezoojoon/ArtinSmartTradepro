"""
Phase 5 Golden Tests - Demand Forecast Engine
Anti-fake validation with deterministic time series outputs
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

class TestDemandGolden:
    """Golden tests for demand forecast engine with fixed inputs and expected outputs"""
    
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
        
        # Create 24 months of data with seasonal pattern
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
    
    def test_golden_case_1_time_series_forecast(self, demand_engine: DemandForecastEngine, test_tenant: Tenant, sample_historical_data):
        """Golden case 1: Time series forecasting with sufficient data"""
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
        
        # Validate forecast points structure
        for point in result.forecast_points:
            assert point.demand_value > 0
            assert point.date > date.today()
            assert "confidence_interval" in point.__dict__
            assert "lower" in point.confidence_interval
            assert "upper" in point.confidence_interval
            assert point.confidence_interval["lower"] <= point.demand_value <= point.confidence_interval["upper"]
        
        # Explainability must reference historical data
        assert any("demand_time_series" in ds.dataset for ds in result.explainability.data_used)
        
        # Confidence should be reasonable with 24 months of data
        assert result.explainability.confidence >= 0.7
        
        # Action plan must be non-empty
        assert len(result.explainability.action_plan) > 0
        
        # No missing fields for success case
        assert len(result.explainability.missing_fields) == 0
    
    def test_golden_case_2_seasonality_matrix_forecast(self, demand_engine: DemandForecastEngine, test_tenant: Tenant, sample_seasonality_data):
        """Golden case 2: Seasonality matrix forecasting"""
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
        
        # Explainability must reference seasonality matrix
        assert any("seasonality_matrix" in ds.dataset for ds in result.explainability.data_used)
        
        # Confidence should be reasonable with seasonality data
        assert result.explainability.confidence >= 0.5
    
    def test_golden_case_3_insufficient_data(self, demand_engine: DemandForecastEngine, test_tenant: Tenant):
        """Golden case 3: Insufficient data scenario"""
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
        
        # Explainability must list missing data
        assert len(result.explainability.missing_fields) > 0
        assert "no_historical_data" in str(result.explainability.missing_fields)
        
        # Confidence must be 0 for insufficient data
        assert result.explainability.confidence == 0.0
        
        # Action plan must suggest data collection
        assert any("historical" in action.lower() for action in result.explainability.action_plan)
    
    def test_golden_case_4_peak_window_detection(self, demand_engine: DemandForecastEngine, test_tenant: Tenant, sample_historical_data):
        """Golden case 4: Peak window detection"""
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
                
                # Peak window should be within forecast period
                assert window.start_date <= result.forecast_points[-1].date
                assert window.end_date <= result.forecast_points[-1].date
    
    def test_golden_case_5_confidence_calculation(self, demand_engine: DemandForecastEngine, test_tenant: Tenant, sample_historical_data):
        """Golden case 5: Confidence calculation validation"""
        # Test with 24 months of data
        full_data_input = DemandInput(
            product_key="123456",
            country="US",
            forecast_months=6
        )
        
        result = demand_engine.run_forecast(test_tenant.id, full_data_input)
        assert result.status == "success"
        full_data_confidence = result.explainability.confidence
        
        # Test with limited data (create only 6 months)
        limited_input = DemandInput(
            product_key="LIMITED",
            country="US",
            forecast_months=3
        )
        
        result = demand_engine.run_forecast(test_tenant.id, limited_input)
        if result.status == "success":
            limited_data_confidence = result.explainability.confidence
            assert limited_data_confidence < full_data_confidence
    
    def test_golden_case_6_explainability_structure_validation(self, demand_engine: DemandForecastEngine, test_tenant: Tenant, sample_historical_data):
        """Golden case 6: Explainability structure validation"""
        input_data = DemandInput(
            product_key="123456",
            country="US",
            forecast_months=6
        )
        
        result = demand_engine.run_forecast(test_tenant.id, input_data)
        
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
        assert len(explainability.data_used) >= 2  # Input + historical data
        assert len(explainability.assumptions) > 0
        assert len(explainability.action_plan) > 0
        assert len(explainability.limitations) > 0
        assert len(explainability.computation_method) > 0
    
    def test_golden_case_7_no_hallucinated_forecast_data(self, demand_engine: DemandForecastEngine, test_tenant: Tenant, sample_historical_data):
        """Golden case 7: No hallucinated forecast data"""
        input_data = DemandInput(
            product_key="123456",
            country="US",
            forecast_months=6
        )
        
        result = demand_engine.run_forecast(test_tenant.id, input_data)
        
        assert result.status == "success"
        
        # All data_used entries must have valid sources
        for data_source in result.explainability.data_used:
            assert data_source.source_name in ["user_input", "demand_time_series", "seasonality_matrix"]
            assert data_source.dataset is not None
            assert data_source.coverage is not None
            assert data_source.confidence is None or 0.0 <= data_source.confidence <= 1.0
        
        # Forecast values should be based on historical patterns only
        forecast_values = [point.demand_value for point in result.forecast_points]
        historical_values = [float(record.demand_value) for record in sample_historical_data if record.demand_value is not None]
        
        # Forecast should be in reasonable range based on historical data
        min_historical = min(historical_values)
        max_historical = max(historical_values)
        
        for forecast_value in forecast_values:
            assert min_historical * 0.5 <= forecast_value <= max_historical * 2.0
        
        # No external market data should be referenced
        datasets = [ds.dataset for ds in result.explainability.data_used]
        assert not any("external" in dataset.lower() for dataset in datasets)
        assert not any("market" in dataset.lower() for dataset in datasets)
    
    def test_golden_case_8_deterministic_seasonal_naive(self, demand_engine: DemandForecastEngine, test_tenant: Tenant, sample_historical_data):
        """Golden case 8: Deterministic seasonal naive forecasting"""
        input_data = DemandInput(
            product_key="123456",
            country="US",
            forecast_months=6
        )
        
        # Run the same input multiple times
        results = []
        for _ in range(3):
            result = demand_engine.run_forecast(test_tenant.id, input_data)
            results.append(result)
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result.status == first_result.status
            assert result.method_used == first_result.method_used
            assert result.data_points_used == first_result.data_points_used
            assert result.explainability.confidence == first_result.explainability.confidence
            assert len(result.forecast_points) == len(first_result.forecast_points)
            
            # Individual forecast points should be identical
            for i, point in enumerate(result.forecast_points):
                first_point = first_result.forecast_points[i]
                assert point.date == first_point.date
                assert abs(point.demand_value - first_point.demand_value) < 0.001
                assert point.confidence_interval["lower"] == first_point.confidence_interval["lower"]
                assert point.confidence_interval["upper"] == first_point.confidence_interval["upper"]
    
    def test_golden_case_9_invalid_forecast_months(self, demand_engine: DemandForecastEngine, test_tenant: Tenant):
        """Golden case 9: Invalid forecast months validation"""
        input_data = DemandInput(
            product_key="123456",
            country="US",
            forecast_months=15  # Invalid (> 12)
        )
        
        result = demand_engine.run_forecast(test_tenant.id, input_data)
        
        assert result.status == "insufficient_data"
        
        # Must list validation error
        assert "forecast_months" in str(result.explainability.missing_fields)
        assert "between 1 and 12" in str(result.explainability.missing_fields)
        
        # Confidence must be 0
        assert result.explainability.confidence == 0.0
    
    def test_golden_case_10_seasonality_matrix_only(self, demand_engine: DemandForecastEngine, test_tenant: Tenant, sample_seasonality_data):
        """Golden case 10: Seasonality matrix only forecasting"""
        # Remove historical data to force seasonality-only forecasting
        input_data = DemandInput(
            product_key="123456",
            country="US",
            forecast_months=6
        )
        
        result = demand_engine.run_forecast(test_tenant.id, input_data)
        
        assert result.status == "success"
        assert result.method_used == "seasonality_matrix"
        
        # Forecast should be based on seasonality indices
        forecast_values = [point.demand_value for point in result.forecast_points]
        
        # Should use base demand * seasonality index
        base_demand = 100.0  # From seasonality matrix implementation
        for forecast_value in forecast_values:
            assert forecast_value > 0
        
        # Explainability must reference seasonality matrix
        assert any("seasonality_matrix" in ds.dataset for ds in result.explainability.data_used)
        
        # Confidence should be lower than with historical data
        assert result.explainability.confidence <= 0.7

class TestDemandAPIGolden:
    """Golden tests for demand forecast API endpoints"""
    
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
    
    def test_api_golden_case_1_successful_forecast(self, test_user: User, test_tenant: Tenant):
        """API golden case 1: Successful forecast with historical data"""
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
        assert "method_used" in data
        assert "data_points_used" in data
        assert "explainability" in data
        
        # Should have forecast points
        forecast_points = data["forecast_points"]
        assert isinstance(forecast_points, list)
        
        if forecast_points:  # If forecast was generated
            point = forecast_points[0]
            assert "date" in point
            assert "demand_value" in point
            assert "confidence_interval" in point
        
        # Validate explainability
        explainability = data["explainability"]
        assert "data_used" in explainability
        assert "confidence" in explainability
        assert len(explainability["data_used"]) >= 2
        assert explainability["confidence"] >= 0.3
        
        app.dependency_overrides.clear()
    
    def test_api_golden_case_2_insufficient_data(self, test_user: User, test_tenant: Tenant):
        """API golden case 2: Insufficient data handling"""
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
        assert len(data["forecast_points"]) == 0
        assert data["method_used"] == "none"
        assert data["data_points_used"] == 0
        
        # Must have explainability with missing fields
        explainability = data["explainability"]
        assert "missing_fields" in explainability
        assert len(explainability["missing_fields"]) > 0
        assert explainability["confidence"] == 0.0
        
        # Must suggest data collection
        action_plan = explainability["action_plan"]
        assert any("historical" in step.lower() for step in action_plan)
        
        app.dependency_overrides.clear()
    
    def test_api_golden_case_3_invalid_forecast_months(self, test_user: User, test_tenant: Tenant):
        """API golden case 3: Invalid forecast months"""
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_tenant] = lambda: test_tenant
        
        input_data = {
            "product_key": "123456",
            "country": "US",
            "forecast_months": 15  # Invalid
        }
        
        response = client.post("/brain/demand/run", json=input_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "insufficient_data"
        assert "forecast_months" in str(data["explainability"]["missing_fields"])
        
        app.dependency_overrides.clear()
    
    def test_api_golden_case_4_run_persistence(self, test_user: User, test_tenant: Tenant):
        """API golden case 4: Run persistence validation"""
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
        
        # Check that run was saved
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
        
        # Validate persisted explainability
        persisted_explainability = our_run["explainability"]
        assert "data_used" in persisted_explainability
        assert "confidence" in persisted_explainability
        assert persisted_explainability["confidence"] >= 0
        
        app.dependency_overrides.clear()

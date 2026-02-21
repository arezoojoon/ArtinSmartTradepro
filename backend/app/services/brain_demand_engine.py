"""
Phase 5 Demand Forecast Engine v1
Time series forecasting with seasonality matrix integration
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from statistics import mean, median
import calendar

from ..models.brain_assets import DemandTimeSeries, AssetSeasonalityMatrix
from ..services.brain_assets_repository import BrainAssetRepository
from ..services.brain_registry import BrainEngineRegistry, BrainEngineValidator, make_data_used_item
from ..schemas.brain import (
    DemandInput, DemandOutput, ForecastPoint, PeakWindow, ExplainabilityBundle
)

class DemandForecastEngine:
    """
    Time series demand forecasting engine
    Uses historical data and seasonality matrix for deterministic forecasting
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = BrainAssetRepository(db)
        self.registry = BrainEngineRegistry(db)
        self.validator = BrainEngineValidator()
    
    def run_forecast(self, tenant_id: UUID, input_data: DemandInput) -> DemandOutput:
        """
        Run demand forecast analysis
        
        Args:
            tenant_id: Tenant ID for RLS
            input_data: Demand forecast input
            
        Returns:
            DemandOutput with forecast points and peak windows
        """
        try:
            # Validate input
            validation_result = self._validate_input(input_data)
            if not validation_result[0]:
                return self._create_insufficient_data_response(
                    tenant_id, input_data, validation_result[1]
                )
            
            # Get historical data
            historical_data = self._get_historical_data(tenant_id, input_data)
            
            # Get seasonality matrix
            seasonality_data = self._get_seasonality_data(tenant_id, input_data)
            
            # Choose forecasting method
            forecast_method, forecast_points = self._generate_forecast(
                historical_data, seasonality_data, input_data
            )
            
            # Identify peak windows
            peak_windows = self._identify_peak_windows(
                forecast_points, seasonality_data, input_data
            )
            
            # Create explainability bundle
            explainability = self._create_explainability_bundle(
                tenant_id, input_data, historical_data, seasonality_data, 
                forecast_method, forecast_points
            )
            
            # Save engine run
            output_payload = {
                "forecast_points": [point.dict() for point in forecast_points],
                "peak_windows": [window.dict() for window in peak_windows],
                "method_used": forecast_method,
                "data_points_used": len(historical_data)
            }
            
            self.registry.create_successful_run(
                tenant_id,
                "demand",
                input_data.dict(),
                output_payload,
                explainability
            )
            
            return DemandOutput(
                status="success",
                forecast_points=forecast_points,
                peak_windows=peak_windows,
                method_used=forecast_method,
                data_points_used=len(historical_data),
                explainability=explainability
            )
            
        except Exception as e:
            # Create failed run
            error_data = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.registry.create_failed_run(
                tenant_id,
                "demand",
                input_data.dict(),
                error_data
            )
            
            raise
    
    def _validate_input(self, input_data: DemandInput) -> Tuple[bool, List[str]]:
        """Validate demand forecast input data"""
        missing_fields = []
        
        # Check required fields
        required_fields = ['product_key', 'country']
        
        is_valid, missing = self.validator.validate_required_fields(
            input_data.dict(), required_fields
        )
        missing_fields.extend(missing)
        
        # Validate forecast_months
        if input_data.forecast_months < 1 or input_data.forecast_months > 12:
            missing_fields.append("forecast_months must be between 1 and 12")
        
        # Validate date range if provided
        if input_data.historical_start_date and input_data.historical_end_date:
            if input_data.historical_start_date >= input_data.historical_end_date:
                missing_fields.append("historical_start_date must be before historical_end_date")
        
        return (len(missing_fields) == 0), missing_fields
    
    def _get_historical_data(self, tenant_id: UUID, input_data: DemandInput) -> List[DemandTimeSeries]:
        """Get historical demand data"""
        return self.repo.get_demand_time_series(
            tenant_id,
            input_data.product_key,
            input_data.country,
            input_data.historical_start_date,
            input_data.historical_end_date
        )
    
    def _get_seasonality_data(self, tenant_id: UUID, input_data: DemandInput) -> List[AssetSeasonalityMatrix]:
        """Get seasonality matrix data"""
        return self.repo.get_seasonality_matrix(
            tenant_id,
            input_data.product_key,
            input_data.country
        )
    
    def _generate_forecast(
        self,
        historical_data: List[DemandTimeSeries],
        seasonality_data: List[AssetSeasonalityMatrix],
        input_data: DemandInput
    ) -> Tuple[str, List[ForecastPoint]]:
        """Generate forecast using appropriate method"""
        
        if len(historical_data) >= 12:
            # Use time series method
            return self._forecast_time_series(historical_data, input_data)
        elif seasonality_data:
            # Use seasonality matrix method
            return self._forecast_seasonality(seasonality_data, input_data)
        else:
            # Insufficient data
            raise ValueError("Insufficient data for forecasting")
    
    def _forecast_time_series(
        self, 
        historical_data: List[DemandTimeSeries], 
        input_data: DemandInput
    ) -> Tuple[str, List[ForecastPoint]]:
        """Generate forecast using time series method"""
        
        # Extract demand values
        demand_values = [
            float(point.demand_value) for point in historical_data 
            if point.demand_value is not None
        ]
        
        if len(demand_values) < 3:
            raise ValueError("Insufficient demand values for time series forecasting")
        
        # Simple seasonal naive forecast
        # Use same month from previous year as base
        forecast_points = []
        
        # Get the most recent date
        latest_date = max(point.date for point in historical_data)
        
        for i in range(input_data.forecast_months):
            forecast_date = self._add_months(latest_date, i + 1)
            
            # Find same month from previous year
            same_month_last_year = forecast_date.replace(year=forecast_date.year - 1)
            
            # Find closest historical data point
            closest_point = min(
                historical_data,
                key=lambda p: abs((p.date - same_month_last_year).days)
            )
            
            if closest_point.demand_value:
                # Apply simple trend adjustment (moving average growth)
                if len(demand_values) >= 3:
                    recent_avg = mean(demand_values[-3:])
                    older_avg = mean(demand_values[-6:-3]) if len(demand_values) >= 6 else mean(demand_values[:3])
                    trend_factor = recent_avg / older_avg if older_avg > 0 else 1.0
                else:
                    trend_factor = 1.0
                
                forecast_value = float(closest_point.demand_value) * trend_factor
                
                # Add some randomness for confidence interval (deterministic based on month)
                month_seed = forecast_date.month
                confidence_range = forecast_value * 0.1  # 10% confidence range
                lower_bound = forecast_value - confidence_range
                upper_bound = forecast_value + confidence_range
                
                forecast_points.append(ForecastPoint(
                    date=forecast_date,
                    demand_value=forecast_value,
                    confidence_interval={
                        "lower": max(0, lower_bound),
                        "upper": upper_bound
                    }
                ))
            else:
                # Use historical average if no specific value
                avg_demand = mean(demand_values)
                forecast_points.append(ForecastPoint(
                    date=forecast_date,
                    demand_value=avg_demand,
                    confidence_interval={
                        "lower": max(0, avg_demand * 0.9),
                        "upper": avg_demand * 1.1
                    }
                ))
        
        return "seasonal_naive", forecast_points
    
    def _forecast_seasonality(
        self, 
        seasonality_data: List[AssetSeasonalityMatrix], 
        input_data: DemandInput
    ) -> Tuple[str, List[ForecastPoint]]:
        """Generate forecast using seasonality matrix method"""
        
        # Calculate base demand from seasonality indices
        base_demand = 100.0  # Base demand level
        
        forecast_points = []
        current_date = date.today()
        
        for i in range(input_data.forecast_months):
            forecast_date = self._add_months(current_date, i + 1)
            
            # Find season key for this date
            season_key = self._get_season_key(forecast_date)
            
            # Find matching seasonality data
            matching_season = None
            for season in seasonality_data:
                if season.season_key == season_key:
                    matching_season = season
                    break
            
            if matching_season and matching_season.demand_index:
                # Apply demand index
                forecast_value = base_demand * float(matching_season.demand_index)
                
                # Add confidence based on volatility
                volatility = float(matching_season.volatility_index or 0.1)
                confidence_range = forecast_value * volatility
                
                forecast_points.append(ForecastPoint(
                    date=forecast_date,
                    demand_value=forecast_value,
                    confidence_interval={
                        "lower": max(0, forecast_value - confidence_range),
                        "upper": forecast_value + confidence_range
                    }
                ))
            else:
                # Use base demand if no seasonality data
                forecast_points.append(ForecastPoint(
                    date=forecast_date,
                    demand_value=base_demand,
                    confidence_interval={
                        "lower": base_demand * 0.8,
                        "upper": base_demand * 1.2
                    }
                ))
        
        return "seasonality_matrix", forecast_points
    
    def _identify_peak_windows(
        self,
        forecast_points: List[ForecastPoint],
        seasonality_data: List[AssetSeasonalityMatrix],
        input_data: DemandInput
    ) -> List[PeakWindow]:
        """Identify peak demand windows from forecast"""
        
        if len(forecast_points) < 2:
            return []
        
        # Calculate average demand
        avg_demand = mean(point.demand_value for point in forecast_points)
        
        # Find peak periods (demand > 1.2 * average)
        peak_threshold = avg_demand * 1.2
        
        peak_windows = []
        current_peak_start = None
        
        for i, point in enumerate(forecast_points):
            if point.demand_value > peak_threshold:
                if current_peak_start is None:
                    current_peak_start = point.date
            else:
                if current_peak_start is not None:
                    # End of peak window
                    peak_end = forecast_points[i-1].date if i > 0 else point.date
                    
                    # Calculate demand multiplier
                    peak_demands = [
                        p.demand_value for p in forecast_points 
                        if current_peak_start <= p.date <= peak_end
                    ]
                    peak_avg = mean(peak_demands) if peak_demands else avg_demand
                    demand_multiplier = peak_avg / avg_demand if avg_demand > 0 else 1.0
                    
                    peak_windows.append(PeakWindow(
                        start_date=current_peak_start,
                        end_date=peak_end,
                        demand_multiplier=demand_multiplier
                    ))
                    
                    current_peak_start = None
        
        # Handle case where peak extends to end of forecast
        if current_peak_start is not None:
            peak_end = forecast_points[-1].date
            peak_demands = [
                p.demand_value for p in forecast_points 
                if current_peak_start <= p.date <= peak_end
            ]
            peak_avg = mean(peak_demands) if peak_demands else avg_demand
            demand_multiplier = peak_avg / avg_demand if avg_demand > 0 else 1.0
            
            peak_windows.append(PeakWindow(
                start_date=current_peak_start,
                end_date=peak_end,
                demand_multiplier=demand_multiplier
            ))
        
        return peak_windows
    
    def _get_season_key(self, date_obj: date) -> str:
        """Generate season key for a given date"""
        year = date_obj.year
        
        # Check for specific seasons
        month = date_obj.month
        
        # Islamic seasons (approximate)
        if month in [3, 4, 5]:
            return f"RAMADAN_{year}"
        elif month in [6, 7, 8]:
            return f"SUMMER_{year}"
        elif month in [9, 10, 11]:
            return f"AUTUMN_{year}"
        elif month in [12, 1, 2]:
            return f"WINTER_{year}"
        else:
            return f"Q{((month - 1) // 3) + 1}_{year}"
    
    def _add_months(self, date_obj: date, months: int) -> date:
        """Add months to a date"""
        year = date_obj.year + (date_obj.month - 1 + months) // 12
        month = (date_obj.month - 1 + months) % 12 + 1
        
        # Handle day overflow (e.g., Jan 31 + 1 month = Feb 28/29)
        day = min(date_obj.day, calendar.monthrange(year, month)[1])
        
        return date(year, month, day)
    
    def _create_explainability_bundle(
        self,
        tenant_id: UUID,
        input_data: DemandInput,
        historical_data: List[DemandTimeSeries],
        seasonality_data: List[AssetSeasonalityMatrix],
        forecast_method: str,
        forecast_points: List[ForecastPoint]
    ) -> ExplainabilityBundle:
        """Create comprehensive explainability bundle"""
        
        # Data used
        data_used = []
        
        # Add input data source
        data_used.append(make_data_used_item(
            source_name="user_input",
            dataset="demand_forecast_input",
            coverage=f"{input_data.product_key} in {input_data.country}",
            confidence=1.0
        ))
        
        # Add historical data source if used
        if historical_data:
            data_used.append(make_data_used_item(
                source_name="demand_time_series",
                dataset="historical_demand_data",
                coverage=f"{len(historical_data)} data points from {historical_data[0].date} to {historical_data[-1].date}",
                record_count=len(historical_data),
                confidence=0.8
            ))
        
        # Add seasonality data source if used
        if seasonality_data:
            data_used.append(make_data_used_item(
                source_name="seasonality_matrix",
                dataset="seasonal_demand_patterns",
                coverage=f"{len(seasonality_data)} seasonal patterns",
                record_count=len(seasonality_data),
                confidence=0.7
            ))
        
        # Assumptions
        assumptions = []
        
        if forecast_method == "seasonal_naive":
            assumptions.append("Using seasonal naive forecasting method")
            assumptions.append("Assuming seasonal patterns repeat annually")
            assumptions.append("Trend adjustment based on recent 3-month average")
        elif forecast_method == "seasonality_matrix":
            assumptions.append("Using seasonality matrix for forecasting")
            assumptions.append("Base demand level set to 100 units")
            assumptions.append("Confidence intervals based on historical volatility")
        
        assumptions.append("No external market factors considered")
        assumptions.append("Forecast assumes stable market conditions")
        
        # Confidence calculation
        confidence = self._calculate_confidence(
            historical_data, seasonality_data, forecast_method
        )
        confidence_rationale = f"Base confidence 0.3 + data availability + method reliability = {confidence:.1f}"
        
        # Action plan
        action_plan = []
        
        if len(historical_data) < 12:
            action_plan.append("Collect more historical data for improved accuracy")
        
        if not seasonality_data:
            action_plan.append("Consider building seasonality matrix for better forecasts")
        
        action_plan.append("Monitor actual demand vs forecast regularly")
        action_plan.append("Update forecasting models with new data")
        
        if forecast_points:
            avg_forecast = mean(point.demand_value for point in forecast_points)
            action_plan.append(f"Plan for average demand of {avg_forecast:.1f} units")
        
        # Limitations
        limitations = [
            "Forecast based only on historical patterns",
            "Does not account for market shocks or external events",
            "Seasonal patterns may change over time",
            "Confidence intervals are estimates"
        ]
        
        if len(historical_data) < 12:
            limitations.append("Limited historical data may reduce accuracy")
        
        if not seasonality_data:
            limitations.append("No seasonality matrix available for enhanced forecasting")
        
        return ExplainabilityBundle(
            data_used=data_used,
            assumptions=assumptions,
            confidence=confidence,
            confidence_rationale=confidence_rationale,
            action_plan=action_plan,
            limitations=limitations,
            computation_method=f"Deterministic {forecast_method} forecasting",
            missing_fields=[]
        )
    
    def _calculate_confidence(
        self,
        historical_data: List[DemandTimeSeries],
        seasonality_data: List[AssetSeasonalityMatrix],
        forecast_method: str
    ) -> float:
        """Calculate confidence score based on data availability"""
        confidence = 0.3  # Base confidence
        
        # Add confidence for historical data
        if len(historical_data) >= 24:
            confidence += 0.4  # 2+ years of data
        elif len(historical_data) >= 12:
            confidence += 0.3  # 1+ year of data
        elif len(historical_data) >= 6:
            confidence += 0.2  # 6+ months of data
        elif len(historical_data) >= 3:
            confidence += 0.1  # 3+ months of data
        
        # Add confidence for seasonality data
        if seasonality_data:
            confidence += 0.2
        
        # Add confidence for method reliability
        if forecast_method == "seasonal_naive":
            confidence += 0.1
        elif forecast_method == "seasonality_matrix":
            confidence += 0.05
        
        return min(confidence, 0.9)
    
    def _create_insufficient_data_response(
        self,
        tenant_id: UUID,
        input_data: DemandInput,
        missing_fields: List[str]
    ) -> DemandOutput:
        """Create insufficient data response"""
        suggested_steps = [
            f"Provide missing field: {field}" for field in missing_fields
        ]
        
        if len(missing_fields) == 0:  # Input valid but no data available
            suggested_steps = [
                "Upload historical demand data",
                "Create seasonality matrix entries",
                "Ensure at least 3 months of historical data"
            ]
        
        # Create insufficient data run
        self.registry.create_insufficient_data_run(
            tenant_id,
            "demand",
            input_data.dict(),
            missing_fields or ["no_historical_data"],
            suggested_steps
        )
        
        return DemandOutput(
            status="insufficient_data",
            forecast_points=[],
            peak_windows=[],
            method_used="none",
            data_points_used=0,
            explainability=ExplainabilityBundle(
                data_used=[],
                assumptions=[f"Missing required data: {', '.join(missing_fields) if missing_fields else 'No historical data available'}"],
                confidence=0.0,
                confidence_rationale="Insufficient data for computation",
                action_plan=suggested_steps,
                limitations=["Insufficient data"],
                computation_method="None - insufficient data",
                missing_fields=missing_fields
            )
        )

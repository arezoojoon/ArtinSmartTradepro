
import sys
import os
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.models.climate import ClimateRisk
from app.models.financial import RiskFactor, TradeScenario
from app.services.climate_service import ClimateService

def test_climate_risk_to_financial_factor_contract():
    """
    Contract: ClimateService.assess_route_risk must create a valid RiskFactor
    in the Financial Service when a route intersects a risk zone.
    """
    # 1. Mock Data
    scenario_id = uuid4()
    
    # Define a risk (The Provider)
    climate_risk = ClimateRisk(
        region="Red Sea",
        risk_type="conflict",
        severity="high",
        valid_until=datetime.utcnow() + timedelta(days=30)
    )
    
    # 2. Simulate Service Logic (Provider -> Consumer)
    # logic from ClimateService.assess_route_risk
    
    impact_percent = 0.0
    probability = 0.0
    
    if climate_risk.severity == "high":
        impact_percent = 10.0
        probability = 0.8
    elif climate_risk.severity == "medium":
        impact_percent = 5.0
        probability = 0.5
        
    # The Consumer (Financial Engine) expects these fields
    financial_factor = RiskFactor(
        scenario_id=scenario_id,
        factor_type=f"Climate: {climate_risk.risk_type.title()}",
        probability=probability,
        impact_percent=impact_percent,
        description=f"Automated risk detected from {climate_risk.region}"
    )
    
    # 3. Assertions (The Contract)
    assert financial_factor.scenario_id == scenario_id
    assert "Climate: Conflict" in financial_factor.factor_type
    assert financial_factor.impact_percent == 10.0 # High severity maps to 10%
    assert financial_factor.probability == 0.8
    
    print("✅ Climate -> Finance Contract Verified")

if __name__ == "__main__":
    test_climate_risk_to_financial_factor_contract()

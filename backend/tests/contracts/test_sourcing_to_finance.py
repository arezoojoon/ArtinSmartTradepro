
import sys
import os
import pytest
from uuid import uuid4

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.models.sourcing import SupplierQuote
from app.models.financial import CostComponent, TradeScenario

def test_sourcing_to_finance_contract():
    """
    Contract: A SupplierQuote must contain enough information to generate 
    valid CostComponents in the Financial Engine.
    """
    # 1. Mock Supplier Quote (The Provider)
    quote = SupplierQuote(
        id=uuid4(),
        incoterm="FOB",
        unit_price=12.50,
        currency="USD",
        moq=1000,
        payment_terms="30% Advance"
    )
    
    # 2. Mock Financial Scenario (The Consumer)
    scenario_id = uuid4()
    
    # 3. Simulate Logic: "Convert Quote to Costs"
    costs = []
    
    # Base Product Cost
    costs.append(CostComponent(
        scenario_id=scenario_id,
        name="COGS (FOB)",
        amount=quote.unit_price * quote.moq, # Total valid cost
        cost_type="variable",
        currency=quote.currency
    ))
    
    # Freight (If FOB, we must add Freight)
    if quote.incoterm == "FOB":
        costs.append(CostComponent(
            scenario_id=scenario_id,
            name="Freight Estimate",
            amount=2500.00, # Mocked lookup
            cost_type="fixed",
            currency="USD"
        ))
        
    # 4. Assertions
    assert len(costs) >= 2
    assert costs[0].amount == 12500.0 # 12.5 * 1000
    assert costs[1].name == "Freight Estimate"
    
    print("✅ Sourcing -> Finance Contract Verified")

if __name__ == "__main__":
    test_sourcing_to_finance_contract()

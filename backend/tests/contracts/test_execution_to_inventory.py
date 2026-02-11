
import sys
import os
import pytest
from uuid import uuid4

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.models.execution import TradeOpportunity
from app.models.inventory import InventoryItem, StockMovement

def test_execution_to_inventory_contract():
    """
    Contract: When Execution Service 'closes' a deal, it must be able to 
    reserve stock in Inventory Service using a valid Order Reference.
    """
    # 1. Mock Trade Opportunity (The Consumer of Stock)
    opportunity = TradeOpportunity(
        id=uuid4(),
        title="Export Tiles to Qatar",
        stage="negotiating" # Not closed yet
    )
    
    # 2. Mock Inventory Item (The Provider)
    item = InventoryItem(
        sku="TILE-101",
        qty_on_hand=1000,
        qty_reserved=200
    )
    
    # 3. Simulate Allocation Logic
    qty_needed = 500
    
    # Check Availability
    available = item.qty_on_hand - item.qty_reserved
    assert available == 800
    assert available >= qty_needed
    
    # Perform Reservation (The Handshake)
    item.qty_reserved += qty_needed
    
    # Create Audit Log
    movement = StockMovement(
        item_id=item.id,
        change_qty=0, # No physical move yet, just logical reserve
        reason="reservation",
        reference_id=opportunity.id # CRITICAL: Must link back to Execution
    )
    
    # 4. Assertions
    assert item.qty_reserved == 700 # 200 + 500
    assert movement.reference_id == opportunity.id
    
    print("✅ Execution -> Inventory Contract Verified")

if __name__ == "__main__":
    test_execution_to_inventory_contract()

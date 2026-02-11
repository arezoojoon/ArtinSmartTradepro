from sqlalchemy.orm import Session
from app.models.inventory import Warehouse, InventoryItem, StockMovement
import uuid

class InventoryService:
    """
    Manages physical stock across warehouses.
    """

    @staticmethod
    def get_stock_level(db: Session, sku: str):
        """
        Returns total available stock for a SKU across all warehouses.
        """
        items = db.query(InventoryItem).filter(InventoryItem.sku == sku).all()
        total_qty = sum(i.qty_on_hand - i.qty_reserved for i in items)
        return total_qty

    @staticmethod
    def add_stock(db: Session, warehouse_id: uuid.UUID, sku: str, product_name: str, qty: int, reason: str = "restock"):
        """
        Adds stock to a warehouse.
        """
        item = db.query(InventoryItem).filter(
            InventoryItem.warehouse_id == warehouse_id,
            InventoryItem.sku == sku
        ).first()

        if not item:
            item = InventoryItem(
                tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000000"), # Mock Tenant
                warehouse_id=warehouse_id,
                sku=sku,
                product_name=product_name,
                qty_on_hand=0
            )
            db.add(item)
            db.flush()

        item.qty_on_hand += qty
        
        movement = StockMovement(
            item_id=item.id,
            change_qty=qty,
            reason=reason
        )
        db.add(movement)
        db.commit()
        return item

    @staticmethod
    def reserve_stock(db: Session, sku: str, qty: int, order_ref: str):
        """
        Reserves stock for a specific order. Simple FIFO allocation.
        """
        items = db.query(InventoryItem).filter(InventoryItem.sku == sku).all()
        remaining_to_reserve = qty

        for item in items:
            if remaining_to_reserve <= 0:
                break
            
            available = item.qty_on_hand - item.qty_reserved
            if available > 0:
                take = min(available, remaining_to_reserve)
                item.qty_reserved += take
                remaining_to_reserve -= take
        
        if remaining_to_reserve > 0:
            raise Exception(f"Insufficient stock for {sku}. Short by {remaining_to_reserve}")
        
        db.commit()
        return True

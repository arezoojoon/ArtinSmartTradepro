from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import datetime
import uuid

class Warehouse(Base):
    """
    Physical storage location.
    """
    __tablename__ = "inventory_warehouses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    name = Column(String, nullable=False) # e.g. "Dubai Free Zone WH-1"
    location_lat = Column(Numeric(10, 6), nullable=True)
    location_lon = Column(Numeric(10, 6), nullable=True)
    
    capacity_sqm = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

class InventoryItem(Base):
    """
    Stock tracking per SKU per Warehouse.
    """
    __tablename__ = "inventory_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("inventory_warehouses.id"), nullable=False)
    
    product_name = Column(String, nullable=False) # Link to Product catalog in future
    sku = Column(String, nullable=False, index=True)
    
    qty_on_hand = Column(Integer, default=0)
    qty_reserved = Column(Integer, default=0)
    qty_available = Column(Integer, default=0) # Computed often, but stored for query speed
    
    reorder_point = Column(Integer, default=10)
    
    warehouse = relationship("Warehouse")

class StockMovement(Base):
    """
    Ledger for all inventory changes.
    """
    __tablename__ = "inventory_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False)
    
    change_qty = Column(Integer, nullable=False) # +50 or -10
    reason = Column(String, nullable=False) # purchase_order, sales_order, damage, adjustment
    reference_id = Column(UUID(as_uuid=True), nullable=True) # Link to PO or SO
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

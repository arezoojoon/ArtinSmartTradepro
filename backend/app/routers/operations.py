from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_active_user
from app.models.inventory import Warehouse, InventoryItem
from app.models.climate import ClimateRisk
from app.services.inventory_service import InventoryService
from pydantic import BaseModel
import uuid
import datetime

router = APIRouter()

# --- Schemas ---
class WarehouseCreate(BaseModel):
    name: str
    lat: float
    lon: float
    capacity: int

class StockUpdate(BaseModel):
    sku: str
    product_name: str
    qty: int
    reason: str

class ClimateAlertCreate(BaseModel):
    region: str
    risk_type: str
    severity: str

def _get_tenant(user: User):
    tenant_id = getattr(user, "current_tenant_id", getattr(user, "tenant_id", None))
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")
    return tenant_id

# --- Inventory Endpoints ---

@router.get("/inventory/warehouses")
def get_warehouses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    tenant_id = _get_tenant(current_user)
    # Security Fix: Scope query to tenant
    return db.query(Warehouse).filter(Warehouse.tenant_id == tenant_id).all()

@router.post("/inventory/warehouses")
def create_warehouse(
    w: WarehouseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    tenant_id = _get_tenant(current_user)
    new_w = Warehouse(
        tenant_id=tenant_id, 
        name=w.name, 
        location_lat=w.lat, 
        location_lon=w.lon, 
        capacity_sqm=w.capacity
    )
    db.add(new_w)
    db.commit()
    return new_w

@router.get("/inventory/stock")
def get_stock(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    tenant_id = _get_tenant(current_user)
    # Security Fix: Fetch stocks that belong to any warehouse of this tenant
    warehouses = db.query(Warehouse.id).filter(Warehouse.tenant_id == tenant_id).subquery()
    return db.query(InventoryItem).filter(InventoryItem.warehouse_id.in_(warehouses)).all()

@router.post("/inventory/warehouses/{id}/stock")
def add_stock(
    id: str, 
    s: StockUpdate, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    tenant_id = _get_tenant(current_user)
    # Verification of warehouse ownership
    warehouse = db.query(Warehouse).filter(Warehouse.id == uuid.UUID(id), Warehouse.tenant_id == tenant_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found or belongs to another organization")
    
    return InventoryService.add_stock(db, uuid.UUID(id), s.sku, s.product_name, s.qty, s.reason)

# --- Climate Endpoints ---

@router.get("/climate/risks")
def get_climate_risks(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Climate data might be global, but enforcing auth prevents anonymous scraping
    return db.query(ClimateRisk).all()

@router.post("/climate/risks")
def report_risk(
    c: ClimateAlertCreate, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    risk = ClimateRisk(
        region=c.region,
        risk_type=c.risk_type,
        severity=c.severity,
        valid_until=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)  # Deprecation Fix
    )
    db.add(risk)
    db.commit()
    return risk

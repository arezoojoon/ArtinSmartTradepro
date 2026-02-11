from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
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

# --- Inventory Endpoints ---

@router.get("/inventory/warehouses")
def get_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).all()

@router.post("/inventory/warehouses")
def create_warehouse(w: WarehouseCreate, db: Session = Depends(get_db)):
    # Mock Tenant
    new_w = Warehouse(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000000"), 
        name=w.name, 
        location_lat=w.lat, 
        location_lon=w.lon, 
        capacity_sqm=w.capacity
    )
    db.add(new_w)
    db.commit()
    return new_w

@router.get("/inventory/stock")
def get_stock(db: Session = Depends(get_db)):
    return db.query(InventoryItem).all()

@router.post("/inventory/warehouses/{id}/stock")
def add_stock(id: str, s: StockUpdate, db: Session = Depends(get_db)):
    return InventoryService.add_stock(db, uuid.UUID(id), s.sku, s.product_name, s.qty, s.reason)

# --- Climate Endpoints ---

@router.get("/climate/risks")
def get_climate_risks(db: Session = Depends(get_db)):
    return db.query(ClimateRisk).all()

@router.post("/climate/risks")
def report_risk(c: ClimateAlertCreate, db: Session = Depends(get_db)):
    risk = ClimateRisk(
        region=c.region,
        risk_type=c.risk_type,
        severity=c.severity,
        valid_until=datetime.datetime.utcnow() + datetime.timedelta(days=7)
    )
    db.add(risk)
    db.commit()
    return risk

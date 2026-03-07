from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.models.catalog import Catalog
from pydantic import BaseModel
import uuid

router = APIRouter()

class CatalogCreate(BaseModel):
    title_en: Optional[str] = None
    title_fa: Optional[str] = None
    title_ar: Optional[str] = None
    title_ru: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    keywords: Optional[str] = None
    enabled: Optional[bool] = True
    language: Optional[str] = "en"

class CatalogUpdate(BaseModel):
    title_en: Optional[str] = None
    title_fa: Optional[str] = None
    title_ar: Optional[str] = None
    title_ru: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    keywords: Optional[str] = None
    enabled: Optional[bool] = None
    language: Optional[str] = None

@router.get("/")
def list_catalogs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    catalogs = db.query(Catalog).filter(Catalog.tenant_id == current_user.tenant_id).order_by(Catalog.created_at.desc()).all()
    return {"catalogs": catalogs}

@router.post("/")
def create_catalog(
    data: CatalogCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    new_catalog = Catalog(
        tenant_id=current_user.tenant_id,
        **data.model_dump()
    )
    db.add(new_catalog)
    db.commit()
    db.refresh(new_catalog)
    return {"message": "Catalog created", "id": new_catalog.id}

@router.put("/{id}")
def update_catalog(
    id: str,
    data: CatalogUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    catalog = db.query(Catalog).filter(
        Catalog.id == uuid.UUID(id),
        Catalog.tenant_id == current_user.tenant_id
    ).first()
    
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(catalog, key, value)
        
    db.commit()
    db.refresh(catalog)
    return {"message": "Catalog updated"}

@router.delete("/{id}")
def delete_catalog(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    catalog = db.query(Catalog).filter(
        Catalog.id == uuid.UUID(id),
        Catalog.tenant_id == current_user.tenant_id
    ).first()
    
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    db.delete(catalog)
    db.commit()
    return {"message": "Catalog deleted"}

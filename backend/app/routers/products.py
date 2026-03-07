from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.models.product import Product
from pydantic import BaseModel
import uuid

router = APIRouter()

class ProductCreate(BaseModel):
    name: str
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    name_ru: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    description_en: Optional[str] = None
    description_ar: Optional[str] = None
    description_ru: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "AED"
    stock_quantity: Optional[int] = 0
    features: Optional[list] = []
    benefits: Optional[list] = []
    selling_points: Optional[dict] = {}
    images: Optional[list] = []
    image_url: Optional[str] = None
    is_active: Optional[bool] = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    name_ru: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    description_en: Optional[str] = None
    description_ar: Optional[str] = None
    description_ru: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    stock_quantity: Optional[int] = None
    features: Optional[list] = None
    benefits: Optional[list] = None
    selling_points: Optional[dict] = None
    images: Optional[list] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

@router.get("/")
def list_products(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    products = db.query(Product).filter(Product.tenant_id == current_user.tenant_id).order_by(Product.created_at.desc()).all()
    return {"products": products}

@router.post("/")
def create_product(
    data: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    new_product = Product(
        tenant_id=current_user.tenant_id,
        **data.model_dump()
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return {"message": "Product created", "id": new_product.id}

@router.put("/{id}")
def update_product(
    id: str,
    data: ProductUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == uuid.UUID(id),
        Product.tenant_id == current_user.tenant_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
        
    db.commit()
    db.refresh(product)
    return {"message": "Product updated"}

@router.delete("/{id}")
def delete_product(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == uuid.UUID(id),
        Product.tenant_id == current_user.tenant_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}

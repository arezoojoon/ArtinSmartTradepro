from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.models.representative import Representative
from pydantic import BaseModel
import uuid

router = APIRouter()

class RepresentativeCreate(BaseModel):
    country: str
    city: str
    address: str
    phone: str
    email: str
    contact_person: str
    is_active: Optional[bool] = True
    business_card_url: Optional[str] = None
    rep_type: Optional[str] = "personal"
    office_name: Optional[str] = None

class RepresentativeUpdate(BaseModel):
    country: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_person: Optional[str] = None
    is_active: Optional[bool] = None
    business_card_url: Optional[str] = None
    rep_type: Optional[str] = None
    office_name: Optional[str] = None

@router.get("/")
def list_representatives(
    rep_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Representative).filter(Representative.tenant_id == current_user.tenant_id)
    if rep_type:
        query = query.filter(Representative.rep_type == rep_type)
    return {"representatives": query.all()}

@router.post("/")
def create_representative(
    rep: RepresentativeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    new_rep = Representative(
        tenant_id=current_user.tenant_id,
        **rep.model_dump()
    )
    db.add(new_rep)
    db.commit()
    db.refresh(new_rep)
    return {"message": "Representative created", "id": new_rep.id}

@router.put("/{id}")
def update_representative(
    id: str,
    rep_update: RepresentativeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    representative = db.query(Representative).filter(
        Representative.id == uuid.UUID(id),
        Representative.tenant_id == current_user.tenant_id
    ).first()
    
    if not representative:
        raise HTTPException(status_code=404, detail="Representative not found")

    update_data = rep_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(representative, key, value)
        
    db.commit()
    db.refresh(representative)
    return {"message": "Representative updated"}

@router.delete("/{id}")
def delete_representative(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    representative = db.query(Representative).filter(
        Representative.id == uuid.UUID(id),
        Representative.tenant_id == current_user.tenant_id
    ).first()
    
    if not representative:
        raise HTTPException(status_code=404, detail="Representative not found")

    db.delete(representative)
    db.commit()
    return {"message": "Representative deleted"}

from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tenant import Tenant
from uuid import UUID

def get_tenant(
    x_tenant_id: str = Header(None, alias="X-Tenant-ID"),
    db: Session = Depends(get_db)
) -> Tenant:
    if not x_tenant_id:
        return None 
        
    try:
        tenant_uuid = UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Tenant ID format")
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if not tenant.is_active:
        raise HTTPException(status_code=400, detail="Tenant is inactive")
        
    return tenant

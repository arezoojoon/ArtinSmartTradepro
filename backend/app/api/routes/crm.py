from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from ...db.session import get_db
from ...models.crm import CRMCompany
from ...core.tenant import get_tenant_context, TenantContext
from ...schemas.crm import CRMCompanyCreate, CRMCompanyResponse

router = APIRouter(tags=["crm"])

@router.get("/companies", response_model=List[CRMCompanyResponse])
async def list_companies(
    tenant_context: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """List companies for the current tenant."""
    # Tenant context automatically ensures we have a valid tenant_id
    stmt = (
        select(CRMCompany)
        .where(CRMCompany.tenant_id == tenant_context.tenant_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    companies = result.scalars().all()
    
    return companies

@router.post("/companies", response_model=CRMCompanyResponse)
async def create_company(
    company_data: CRMCompanyCreate,
    tenant_context: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a company in the current tenant."""
    
    new_company = CRMCompany(
        tenant_id=tenant_context.tenant_id,
        name=company_data.name,
        domain=company_data.domain,
        industry=company_data.industry
    )
    
    db.add(new_company)
    await db.commit()
    await db.refresh(new_company)
    
    return new_company

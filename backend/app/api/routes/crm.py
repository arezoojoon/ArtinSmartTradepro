from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
import uuid

from ...db.session import get_db
from ...models.crm import CRMCompany, CRMContact
from ...core.tenant import get_tenant_context, TenantContext
from ...schemas.crm import (
    CRMCompanyCreate, CRMCompanyResponse,
    CRMContactCreate, CRMContactResponse,
)

router = APIRouter(tags=["crm"])


# ─── Companies ────────────────────────────────────────────────────────

@router.get("/companies", response_model=List[CRMCompanyResponse])
async def list_companies(
    tenant_context: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 200,
    search: Optional[str] = None,
) -> Any:
    """List companies for the current tenant."""
    stmt = select(CRMCompany).where(CRMCompany.tenant_id == tenant_context.tenant_id)
    if search:
        stmt = stmt.where(
            or_(
                CRMCompany.name.ilike(f"%{search}%"),
                CRMCompany.domain.ilike(f"%{search}%"),
                CRMCompany.country.ilike(f"%{search}%"),
            )
        )
    stmt = stmt.order_by(CRMCompany.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


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


# ─── Contacts ─────────────────────────────────────────────────────────

@router.get("/contacts", response_model=List[CRMContactResponse])
async def list_contacts(
    tenant_context: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 200,
    search: Optional[str] = None,
    company_id: Optional[str] = None,
) -> Any:
    """List contacts for the current tenant."""
    stmt = select(CRMContact).where(CRMContact.tenant_id == tenant_context.tenant_id)
    if search:
        stmt = stmt.where(
            or_(
                CRMContact.first_name.ilike(f"%{search}%"),
                CRMContact.last_name.ilike(f"%{search}%"),
                CRMContact.email.ilike(f"%{search}%"),
                CRMContact.phone.ilike(f"%{search}%"),
            )
        )
    if company_id:
        stmt = stmt.where(CRMContact.company_id == company_id)
    stmt = stmt.order_by(CRMContact.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/contacts", response_model=CRMContactResponse)
async def create_contact(
    data: CRMContactCreate,
    tenant_context: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a contact in the current tenant."""
    new_contact = CRMContact(
        tenant_id=tenant_context.tenant_id,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        position=data.position,
        company_id=data.company_id,
    )
    db.add(new_contact)
    await db.commit()
    await db.refresh(new_contact)
    return new_contact

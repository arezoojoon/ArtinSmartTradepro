# backend/scripts/seed_vahid_demo.py
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# اضافه کردن مسیر پروژه
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.user import User, TenantMembership
from app.models.crm import Lead
from app.core.security import get_password_hash
from app.core.rbac import RoleEnum

async def seed_vahid_demo():
    async with AsyncSessionLocal() as session:
        # 1. ساخت Tenant اختصاصی برای شرکت وحید آقا
        print("Creating Fard Foodstuff Tenant...")
        tenant = Tenant(
            name="Fard Foodstuff Industry LLC",
            domain="fardfood.artinsmartagent.com",
            plan="enterprise",
            is_active=True
        )
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)

        # 2. ساخت اکانت کاربری وحید آقا
        print("Creating User Vahid Daneshvar...")
        vahid = User(
            email="vahid@fardfood.com",
            hashed_password=get_password_hash("Dubai@2026"),
            full_name="Vahid Daneshvar",
            is_active=True,
            current_tenant_id=tenant.id
        )
        session.add(vahid)
        await session.commit()
        await session.refresh(vahid)

        # 3. دادن دسترسی مالک (Owner)
        membership = TenantMembership(
            user_id=vahid.id,
            tenant_id=tenant.id,
            role=RoleEnum.OWNER
        )
        session.add(membership)

        # 4. تزریق لیدهای داغ نمایشگاه گلفود
        print("Injecting Gulfood Leads...")
        gulfood_leads = [
            Lead(
                tenant_id=tenant.id,
                title="Gulfood 2026 - Russian Importer",
                company_name="ELITE GROUPS (Fayuzulleov)",
                contact_name="Fayuzulleov",
                email="import@elitegroups.ru",
                phone="+7 900 123 4567",
                country="Russia",
                status="new",
                source="Gulfood Expo",
                score=95, # نمره بالا چون محصول تطابق دارد
                custom_data={"interested_in": ["Pistachio Akbari", "Dates"], "language": "Russian"}
            ),
            Lead(
                tenant_id=tenant.id,
                title="Gulfood 2026 - GCC Distributor",
                company_name="MAXONSNUTS",
                contact_name="Procurement Manager",
                email="purchasing@maxonsnuts.ae",
                phone="+971 50 000 0000",
                country="UAE",
                status="contacted",
                source="Gulfood Expo",
                score=88,
                custom_data={"interested_in": ["Walnuts", "Mixed Nuts"], "language": "Arabic/English"}
            ),
            Lead(
                tenant_id=tenant.id,
                title="Gulfood 2026 - Indian Wholesaler",
                company_name="CHAMAN DRY FRUITS",
                contact_name="Rajiv Chaman",
                email="info@chamandryfruits.in",
                phone="+91 98 000 00000",
                country="India",
                status="negotiation",
                source="Gulfood Expo",
                score=92,
                custom_data={"interested_in": ["Dates", "Spices"], "language": "English"}
            )
        ]
        session.add_all(gulfood_leads)
        await session.commit()
        
        print("✅ Demo environment for Vahid successfully seeded!")
        print("Login with: vahid@fardfood.com / Dubai@2026")

if __name__ == "__main__":
    asyncio.run(seed_vahid_demo())

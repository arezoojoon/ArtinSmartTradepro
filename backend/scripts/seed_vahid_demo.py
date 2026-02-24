# backend/scripts/seed_vahid_demo.py
import asyncio
import os
import sys

# اضافه کردن مسیر پروژه
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.tenant import Tenant, TenantMembership, TenantRole
from app.models.user import User
from app.models.lead import Lead
from app.core.security import get_password_hash

async def seed_vahid_demo():
    async with AsyncSessionLocal() as session:
        # 1. ساخت Tenant اختصاصی برای شرکت وحید آقا
        print("Creating Fard Foodstuff Tenant...")
        tenant = Tenant(
            name="Fard Foodstuff Industry LLC",
            slug="fard-foodstuff",
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
            role=TenantRole.OWNER.value
        )
        session.add(membership)

        # 4. تزریق لیدهای داغ نمایشگاه گلفود
        print("Injecting Gulfood Leads...")
        gulfood_leads = [
            Lead(
                tenant_id=tenant.id,
                company_name="ELITE GROUPS (Fayuzulleov)",
                contact_name="Fayuzulleov",
                email="import@elitegroups.ru",
                phone="+7 900 123 4567",
                country="Russia",
                status="new",
                source="Gulfood Expo",
                intent_score=95.0,
                tags=["Pistachio Akbari", "Dates", "Russian"]
            ),
            Lead(
                tenant_id=tenant.id,
                company_name="MAXONSNUTS",
                contact_name="Procurement Manager",
                email="purchasing@maxonsnuts.ae",
                phone="+971 50 000 0000",
                country="UAE",
                status="contacted",
                source="Gulfood Expo",
                intent_score=88.0,
                tags=["Walnuts", "Mixed Nuts", "Arabic/English"]
            ),
            Lead(
                tenant_id=tenant.id,
                company_name="CHAMAN DRY FRUITS",
                contact_name="Rajiv Chaman",
                email="info@chamandryfruits.in",
                phone="+91 98 000 00000",
                country="India",
                status="contacted",
                source="Gulfood Expo",
                intent_score=92.0,
                tags=["Dates", "Spices", "English"]
            )
        ]
        session.add_all(gulfood_leads)
        await session.commit()
        
        print("✅ Demo environment for Vahid successfully seeded!")
        print("Login with: vahid@fardfood.com / Dubai@2026")

if __name__ == "__main__":
    asyncio.run(seed_vahid_demo())

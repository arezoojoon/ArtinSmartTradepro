"""
Phase 6 — Seed default plans and first sys admin.
Run: cd backend && python scripts/seed_phase6.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings
from app.database import get_db_sync
from app.models.phase6 import SysPlan, SystemAdmin, PromptFamily
from app.services.sys_admin_auth import hash_password
import uuid

settings = get_settings()


def seed_plans(db):
    plans = [
        {
            "code": "professional",
            "name": "Professional",
            "description": "For growing trade teams",
            "monthly_price_usd": 299.00,
            "features": {
                "brain_engines": True,
                "hunter": True,
                "messaging": True,
                "api_access": True,
                "whitelabel": False,
            },
            "limits": {
                "messages_sent_daily": 500,
                "leads_created_monthly": 200,
                "enrich_jobs_monthly": 100,
                "brain_runs_daily": 50,
                "seats": 5,
            },
        },
        {
            "code": "enterprise",
            "name": "Enterprise",
            "description": "Full-featured for large organizations",
            "monthly_price_usd": 999.00,
            "features": {
                "brain_engines": True,
                "hunter": True,
                "messaging": True,
                "api_access": True,
                "whitelabel": True,
                "priority_support": True,
                "broadcast": True,
            },
            "limits": {
                "messages_sent_daily": 5000,
                "leads_created_monthly": 2000,
                "enrich_jobs_monthly": 1000,
                "brain_runs_daily": 500,
                "seats": 25,
            },
        },
        {
            "code": "whitelabel",
            "name": "White-Label",
            "description": "Custom branding + domain + reseller",
            "monthly_price_usd": 2999.00,
            "features": {
                "brain_engines": True,
                "hunter": True,
                "messaging": True,
                "api_access": True,
                "whitelabel": True,
                "priority_support": True,
                "broadcast": True,
                "custom_domains": True,
                "reseller_mode": True,
            },
            "limits": {
                "messages_sent_daily": -1,     # unlimited
                "leads_created_monthly": -1,   # unlimited
                "enrich_jobs_monthly": -1,
                "brain_runs_daily": -1,
                "seats": -1,
            },
        },
    ]

    for plan_data in plans:
        existing = db.query(SysPlan).filter(SysPlan.code == plan_data["code"]).first()
        if not existing:
            plan = SysPlan(**plan_data)
            db.add(plan)
            print(f"  ✓ Plan '{plan_data['code']}' created")
        else:
            print(f"  → Plan '{plan_data['code']}' already exists, skipping")
    db.commit()


def seed_prompt_families(db):
    families = [
        {"name": "cultural_strategy", "description": "Cultural negotiation and strategy per buyer country", "category": "brain"},
        {"name": "lead_reply", "description": "AI-generated lead response messages", "category": "messaging"},
        {"name": "report_summary", "description": "Business intelligence report summaries", "category": "analytics"},
        {"name": "arbitrage_insight", "description": "Trade arbitrage opportunity explanations", "category": "brain"},
        {"name": "risk_summary", "description": "Country and route risk summaries", "category": "brain"},
    ]
    for f in families:
        existing = db.query(PromptFamily).filter(PromptFamily.name == f["name"]).first()
        if not existing:
            db.add(PromptFamily(**f))
            print(f"  ✓ Prompt family '{f['name']}' created")
        else:
            print(f"  → Family '{f['name']}' exists, skipping")
    db.commit()


def seed_sys_admin(db):
    email = settings.FIRST_SUPERUSER or "sysadmin@artin.com"
    password = settings.FIRST_SUPERUSER_PASSWORD or "SysAdmin@2026!"
    existing = db.query(SystemAdmin).filter(SystemAdmin.email == email).first()
    if not existing:
        admin = SystemAdmin(
            email=email,
            password_hash=hash_password(password),
            name="Artin System Admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"  ✓ Sys admin created: {email} (password set from env)")
    else:
        print(f"  → Sys admin '{email}' already exists, skipping")


def main():
    print("\n🚀 Seeding Phase 6 Data...")
    # Use synchronous DB for seed script
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        engine = create_engine(settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
        Session = sessionmaker(bind=engine)
        db = Session()
        print("\n📋 Plans:")
        seed_plans(db)
        print("\n🤖 Prompt Families:")
        seed_prompt_families(db)
        print("\n👤 Sys Admin:")
        seed_sys_admin(db)
        db.close()
        print("\n✅ Phase 6 seed complete!\n")
    except Exception as e:
        print(f"\n❌ Seed failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Phase 6 — Seed default plans, prompt families, and first sys admin.
Run INSIDE the API container:
  docker compose exec api python3 scripts/seed_phase6.py
Or from backend/ directory with correct DATABASE_URL env set.
"""
import sys
import os

# Allow running from backend/ or project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.models.phase6 import SysPlan, PromptFamily, SystemAdmin
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)


def seed_plans(db):
    plans = [
        {
            "code": "starter",
            "name": "Starter",
            "description": "Basic plan for small teams",
            "monthly_price_usd": 0.00,
            "features": {"brain_engines": True, "hunter": True, "messaging": True, "api_access": True},
            "limits": {"messages_sent_daily": 100, "leads_created_monthly": 50, "brain_runs_daily": 10, "seats": 2},
        },
        {
            "code": "professional",
            "name": "Professional",
            "description": "For growing trade teams",
            "monthly_price_usd": 299.00,
            "features": {"brain_engines": True, "hunter": True, "messaging": True, "api_access": True, "whitelabel": False},
            "limits": {"messages_sent_daily": 500, "leads_created_monthly": 200, "brain_runs_daily": 50, "seats": 5},
        },
        {
            "code": "enterprise",
            "name": "Enterprise",
            "description": "Full-featured for large organizations",
            "monthly_price_usd": 999.00,
            "features": {"brain_engines": True, "hunter": True, "messaging": True, "api_access": True, "whitelabel": True, "priority_support": True},
            "limits": {"messages_sent_daily": 5000, "leads_created_monthly": 2000, "brain_runs_daily": 500, "seats": 25},
        },
        {
            "code": "whitelabel",
            "name": "White-Label",
            "description": "Custom branding + reseller",
            "monthly_price_usd": 2999.00,
            "features": {"brain_engines": True, "hunter": True, "messaging": True, "api_access": True, "whitelabel": True, "priority_support": True, "custom_domains": True},
            "limits": {"messages_sent_daily": -1, "leads_created_monthly": -1, "brain_runs_daily": -1, "seats": -1},
        },
    ]
    for plan_data in plans:
        existing = db.query(SysPlan).filter(SysPlan.code == plan_data["code"]).first()
        if not existing:
            db.add(SysPlan(**plan_data))
            print(f"  ✓ Plan '{plan_data['code']}' created")
        else:
            print(f"  → Plan '{plan_data['code']}' already exists, skipping")
    db.commit()


def seed_prompt_families(db):
    families = [
        {"name": "cultural_strategy", "description": "Cultural negotiation and strategy per buyer country", "category": "brain"},
        {"name": "lead_reply",        "description": "AI-generated lead response messages",                "category": "messaging"},
        {"name": "report_summary",    "description": "Business intelligence report summaries",             "category": "analytics"},
        {"name": "arbitrage_insight", "description": "Trade arbitrage opportunity explanations",           "category": "brain"},
        {"name": "risk_summary",      "description": "Country and route risk summaries",                   "category": "brain"},
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
    email    = os.environ.get("FIRST_SUPERUSER",          "sysadmin@artin.com")
    password = os.environ.get("FIRST_SUPERUSER_PASSWORD", "SysAdmin@2026!")
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
        print(f"  ✓ Sys admin created: {email}")
        print(f"    (password comes from FIRST_SUPERUSER_PASSWORD env var)")
    else:
        print(f"  → Sys admin '{email}' already exists, skipping")


def main():
    print("\n🚀 Seeding Phase 6 Data...\n")
    db = SessionLocal()
    try:
        print("📋 Plans:")
        seed_plans(db)
        print("\n🤖 Prompt Families:")
        seed_prompt_families(db)
        print("\n👤 Sys Admin:")
        seed_sys_admin(db)
        print("\n✅ Phase 6 seed complete!\n")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Seed failed: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

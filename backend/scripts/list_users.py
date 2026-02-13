import logging
from app.database import SessionLocal
# Import ALL models keys - this is critical to avoid circular dependency errors in SQLAlchemy
from app.models import (
    user, tenant, billing, subscription, crm, campaign, followup, lead, source,
    whatsapp, audit, voice, vision, ai_job, hunter, brain, execution, toolbox,
    bot_session, scheduling, product
)
from app.models.user import User

logging.basicConfig(level=logging.INFO)
db = SessionLocal()
try:
    users = db.query(User).all()
    print(f"\n--- Found {len(users)} Users ---")
    for u in users:
        print(f"ID: {u.id} | Email: {u.email} | Active: {u.is_active} | Role: {u.role}")
    print("--------------------------\n")
except Exception as e:
    print(f"Error listing users: {e}")
finally:
    db.close()

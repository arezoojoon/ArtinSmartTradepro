"""
Phase 15: Create WAHA Bot database tables.
Tables: bot_sessions, bot_events, waha_webhook_events, whatsapp_message_status_updates
Also ensures scheduling tables exist.

Run: python scripts/init_bot_tables.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import engine, Base

# Import ALL models so SQLAlchemy knows about them
from app.models import *  # noqa: F403
from app.models.bot_session import BotSession, BotEvent, WAHAWebhookEvent, WhatsAppStatusUpdate, BotDeeplinkRef
from app.models.scheduling import AvailabilitySlot, Appointment

def main():
    print("=" * 60)
    print("Phase 15: Creating WAHA Bot Tables")
    print("=" * 60)
    
    # Create only the new tables (won't affect existing ones)
    tables_to_create = [
        BotDeeplinkRef.__table__,
        BotSession.__table__,
        BotEvent.__table__,
        WAHAWebhookEvent.__table__,
        WhatsAppStatusUpdate.__table__,
        AvailabilitySlot.__table__,
        Appointment.__table__,
    ]
    
    for table in tables_to_create:
        try:
            table.create(engine, checkfirst=True)
            print(f"  ✅ {table.name}")
        except Exception as e:
            print(f"  ⚠️ {table.name}: {e}")
    
    print()
    print("✅ All Phase 15 tables created successfully!")
    print()
    print("Next steps:")
    print("  1. Set WAHA env vars in .env:")
    print("     WAHA_API_URL=http://your-waha-server:3000")
    print("     WAHA_SESSION=default")
    print("     WAHA_API_KEY=your-api-key")
    print("     WAHA_PHONE_NUMBER=971XXXXXXXX")
    print("     WAHA_WEBHOOK_SECRET=your-secret")
    print("     DEFAULT_TENANT_ID=your-tenant-uuid")
    print()
    print("  2. Configure WAHA webhook URL:")
    print("     POST https://your-domain/api/v1/waha/webhook")
    print()
    print("  3. Test: POST /api/v1/waha/deeplink?ref=test")

if __name__ == "__main__":
    main()

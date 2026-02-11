"""
QA Patch DB Updater.
Applies schema changes required for Phase 15 QA Gate.
1. Creates bot_deeplink_refs table.
2. Adds columns to bot_sessions (locked_for_human, ai_calls_today, etc).
3. Adds columns to bot_events (ai_job_id, ai_cost, etc).
"""
import sys, os
from sqlalchemy import text
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import engine
from app.models.bot_session import BotDeeplinkRef

def main():
    print("=" * 60)
    print("Applying Phase 15 QA Patches to DB...")
    print("=" * 60)

    with engine.connect() as conn:
        # 1. Create BotDeeplinkRef table
        print("1️⃣  Checking bot_deeplink_refs...")
        BotDeeplinkRef.__table__.create(conn, checkfirst=True)
        print("   ✅ Table ready.")

        # 2. Alter bot_sessions
        print("2️⃣  Patching bot_sessions...")
        try:
            conn.execute(text("ALTER TABLE bot_sessions ADD COLUMN IF NOT EXISTS locked_for_human BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE bot_sessions ADD COLUMN IF NOT EXISTS ai_calls_today INTEGER DEFAULT 0"))
            conn.execute(text("ALTER TABLE bot_sessions ADD COLUMN IF NOT EXISTS ai_calls_today_date VARCHAR"))
            print("   ✅ Columns added.")
        except Exception as e:
            print(f"   ⚠️ Error (might already exist): {e}")

        # 3. Alter bot_events
        print("3️⃣  Patching bot_events...")
        try:
            conn.execute(text("ALTER TABLE bot_events ADD COLUMN IF NOT EXISTS ai_job_id UUID"))
            conn.execute(text("ALTER TABLE bot_events ADD COLUMN IF NOT EXISTS ai_cost FLOAT"))
            conn.execute(text("ALTER TABLE bot_events ADD COLUMN IF NOT EXISTS message_id UUID"))
            print("   ✅ Columns added.")
        except Exception as e:
            print(f"   ⚠️ Error (might already exist): {e}")
        
        conn.commit()

    print("\n✅ QA DB Patch Complete!")

if __name__ == "__main__":
    main()

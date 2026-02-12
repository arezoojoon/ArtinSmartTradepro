
import os, time
import asyncio
import asyncpg

# Handle potential missing env var in local testing
DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    print("[wait_for_db] DATABASE_URL not set, skipping wait.")
    exit(0)

# Fix for SQLAlchemy asyncpg url format if needed for raw asyncpg
DB = DB_URL.replace("postgresql+asyncpg://", "postgresql://")

async def main():
    print(f"[wait_for_db] Connecting to {DB.split('@')[-1]}...")
    for i in range(60):
        try:
            conn = await asyncpg.connect(DB)
            await conn.close()
            print("[wait_for_db] db ok")
            return
        except Exception as e:
            print(f"[wait_for_db] retry {i+1}/60: {e}")
            time.sleep(1)
    raise SystemExit("DB not ready")

asyncio.run(main())

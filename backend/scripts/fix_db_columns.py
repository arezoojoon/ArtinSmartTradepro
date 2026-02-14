"""
Fix all missing database columns in one go
"""
import asyncio
from sqlalchemy import text
from app.db.session import engine

async def fix_all_missing_columns():
    """Add all missing columns that models expect but database doesn't have"""
    async with engine.begin() as conn:
        print("Adding missing columns to users table...")
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS current_tenant_id UUID REFERENCES tenants(id)'))
        
        print("Adding missing columns to auditlogs table...")
        await conn.execute(text('ALTER TABLE auditlogs ADD COLUMN IF NOT EXISTS actor_user_id UUID'))
        await conn.execute(text('ALTER TABLE auditlogs ADD COLUMN IF NOT EXISTS tenant_id UUID'))
        await conn.execute(text('ALTER TABLE auditlogs ADD COLUMN IF NOT EXISTS action VARCHAR'))
        await conn.execute(text('ALTER TABLE auditlogs ADD COLUMN IF NOT EXISTS resource_type VARCHAR'))
        await conn.execute(text('ALTER TABLE auditlogs ADD COLUMN IF NOT EXISTS resource_id VARCHAR'))
        await conn.execute(text('ALTER TABLE auditlogs ADD COLUMN IF NOT EXISTS details JSON'))
        await conn.execute(text('ALTER TABLE auditlogs ADD COLUMN IF NOT EXISTS ip_address VARCHAR'))
        await conn.execute(text('ALTER TABLE auditlogs ADD COLUMN IF NOT EXISTS user_agent VARCHAR'))
        
        print("Adding other potentially missing columns...")
        # Add other common missing columns if they don't exist
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS persona VARCHAR'))
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR'))
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superuser BOOLEAN DEFAULT FALSE'))
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE'))
        
        print("All missing columns added successfully!")

if __name__ == "__main__":
    asyncio.run(fix_all_missing_columns())

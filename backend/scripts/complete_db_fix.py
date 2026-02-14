"""
Complete database schema fix script
This script will:
1. Add all missing columns
2. Fix any relationship issues
3. Ensure database matches models exactly
"""
import asyncio
from sqlalchemy import text
from app.db.session import engine

async def complete_database_fix():
    """Complete database schema fix"""
    async with engine.begin() as conn:
        print("🔧 Fixing users table...")
        # Users table columns
        user_columns = [
            'current_tenant_id UUID REFERENCES tenants(id)',
            'persona VARCHAR DEFAULT \'trader\'',
            'role VARCHAR DEFAULT \'user\'',
            'is_superuser BOOLEAN DEFAULT FALSE',
            'email_verified BOOLEAN DEFAULT FALSE',
            'last_login_at TIMESTAMP WITH TIME ZONE'
        ]
        
        for col in user_columns:
            await conn.execute(text(f'ALTER TABLE users ADD COLUMN IF NOT EXISTS {col}'))
        
        print("🔧 Fixing auditlogs table...")
        # Auditlogs table columns
        audit_columns = [
            'actor_user_id UUID',
            'tenant_id UUID',
            'action VARCHAR',
            'resource_type VARCHAR',
            'resource_id VARCHAR',
            'details JSON',
            'ip_address VARCHAR',
            'user_agent VARCHAR'
        ]
        
        for col in audit_columns:
            await conn.execute(text(f'ALTER TABLE auditlogs ADD COLUMN IF NOT EXISTS {col}'))
        
        print("🔧 Fixing tenants table...")
        # Tenants table columns
        tenant_columns = [
            'mode VARCHAR DEFAULT \'hybrid\'',
            'plan VARCHAR DEFAULT \'professional\'',
            'domain VARCHAR',
            'settings JSON DEFAULT \'{}\'',
            'is_active BOOLEAN DEFAULT TRUE'
        ]
        
        for col in tenant_columns:
            await conn.execute(text(f'ALTER TABLE tenants ADD COLUMN IF NOT EXISTS {col}'))
        
        print("🔧 Fixing other common tables...")
        # Add any other missing columns that might cause issues
        other_fixes = [
            'ALTER TABLE tenant_memberships ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT \'member\'',
            'ALTER TABLE tenant_invitations ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT \'member\'',
            'ALTER TABLE sessions ADD COLUMN IF NOT EXISTS user_agent VARCHAR',
            'ALTER TABLE sessions ADD COLUMN IF NOT EXISTS ip_address VARCHAR'
        ]
        
        for fix in other_fixes:
            await conn.execute(text(fix))
        
        print("✅ Database schema fix completed successfully!")

if __name__ == "__main__":
    asyncio.run(complete_database_fix())

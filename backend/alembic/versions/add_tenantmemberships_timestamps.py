"""Add timestamps to tenantmemberships

Revision ID: add_tenantmemberships_timestamps
Revises: add_current_tenant_id
Create Date: 2026-02-15 13:41:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_tenantmemberships_timestamps'
down_revision = 'add_current_tenant_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add timestamps to tenantmemberships table
    op.execute("""
        ALTER TABLE tenantmemberships 
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    """)
    
    # Update existing NULL values separately for each column
    op.execute("""
        UPDATE tenantmemberships 
        SET created_at = NOW() WHERE created_at IS NULL
    """)
    
    op.execute("""
        UPDATE tenantmemberships 
        SET updated_at = NOW() WHERE updated_at IS NULL
    """)


def downgrade() -> None:
    # Remove timestamps from tenantmemberships table
    op.drop_column('tenantmemberships', 'updated_at')
    op.drop_column('tenantmemberships', 'created_at')

"""Add document classifications table

Revision ID: add_document_classifications
Revises: add_logistics_tables
Create Date: 2026-02-27 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_document_classifications'
down_revision = 'add_logistics_tables'
branch_labels = None
depends_on = None

def upgrade():
    # Create document_classifications table
    op.execute("""
        CREATE TABLE IF NOT EXISTS document_classifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            file_path TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            document_type TEXT NOT NULL,
            target_module TEXT NOT NULL,
            confidence FLOAT NOT NULL,
            classification_data JSONB,
            description TEXT,
            status TEXT DEFAULT 'processed',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    
    # Create indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_document_classifications_tenant 
        ON document_classifications(tenant_id);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_document_classifications_type 
        ON document_classifications(document_type);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_document_classifications_module 
        ON document_classifications(target_module);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_document_classifications_status 
        ON document_classifications(status);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_document_classifications_created_at 
        ON document_classifications(created_at DESC);
    """)

def downgrade():
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_document_classifications_tenant;")
    op.execute("DROP INDEX IF EXISTS idx_document_classifications_type;")
    op.execute("DROP INDEX IF EXISTS idx_document_classifications_module;")
    op.execute("DROP INDEX IF EXISTS idx_document_classifications_status;")
    op.execute("DROP INDEX IF EXISTS idx_document_classifications_created_at;")
    
    # Drop table
    op.execute("DROP TABLE IF EXISTS document_classifications;")

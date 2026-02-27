"""Add document_classifications and ai_action_logs tables

Safe migration: uses IF NOT EXISTS to avoid conflicts with tables
that may have been auto-created by SQLAlchemy metadata.create_all.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "add_doc_class_ai_logs"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # --- document_classifications ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS document_classifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            user_id UUID NOT NULL REFERENCES users(id),
            file_path TEXT NOT NULL,
            original_filename VARCHAR NOT NULL,
            document_type VARCHAR NOT NULL,
            target_module VARCHAR NOT NULL,
            confidence FLOAT DEFAULT 0.0,
            classification_data JSONB,
            description TEXT,
            status VARCHAR DEFAULT 'classified',
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_doc_class_tenant 
        ON document_classifications(tenant_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_doc_class_type 
        ON document_classifications(document_type)
    """)

    # --- ai_action_logs (companion to ai_approval_queue) ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_action_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            approval_id UUID REFERENCES ai_approval_queue(id),
            action_type VARCHAR NOT NULL,
            description TEXT,
            payload JSONB,
            result JSONB,
            was_auto_approved BOOLEAN DEFAULT false,
            confidence FLOAT DEFAULT 0.0,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_ai_action_logs_tenant 
        ON ai_action_logs(tenant_id)
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS ai_action_logs")
    op.execute("DROP TABLE IF EXISTS document_classifications")

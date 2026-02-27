"""Fix logistics_events missing created_at/updated_at, logistics_packages missing updated_at

The Base model defines created_at and updated_at for all models, but
the original logistics migration omitted these columns from
logistics_events and logistics_packages tables.

Revision ID: fix_logistics_cols
Revises: add_doc_class_ai_logs
"""
from alembic import op

revision = 'fix_logistics_cols'
down_revision = 'add_doc_class_ai_logs'
branch_labels = None
depends_on = None


def upgrade():
    # logistics_events: add created_at and updated_at (inherited from Base)
    op.execute("""
    ALTER TABLE logistics_events
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
    """)

    # logistics_packages: add updated_at (inherited from Base)
    op.execute("""
    ALTER TABLE logistics_packages
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
    """)


def downgrade():
    op.execute("ALTER TABLE logistics_events DROP COLUMN IF EXISTS created_at")
    op.execute("ALTER TABLE logistics_events DROP COLUMN IF EXISTS updated_at")
    op.execute("ALTER TABLE logistics_packages DROP COLUMN IF EXISTS updated_at")

"""Phase 8: Email Outbox table
Create email_outbox table for local_stub email service.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

revision = 'phase8_email_outbox'
down_revision = 'phase7_billing'
branch_labels = None
depends_on = None

def upgrade():
    op.execute("""
    CREATE TABLE IF NOT EXISTS email_outbox (
        id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        to_email      VARCHAR(255) NOT NULL,
        from_email    VARCHAR(255) NOT NULL,
        subject       VARCHAR(255) NOT NULL,
        content       TEXT NOT NULL,
        status        VARCHAR(50) NOT NULL DEFAULT 'pending',
        provider      VARCHAR(50) NOT NULL,
        error_message TEXT,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
        sent_at       TIMESTAMPTZ
    );
    CREATE INDEX IF NOT EXISTS idx_email_outbox_to ON email_outbox (to_email);
    CREATE INDEX IF NOT EXISTS idx_email_outbox_status ON email_outbox (status);
    """)

def downgrade():
    op.drop_table('email_outbox')

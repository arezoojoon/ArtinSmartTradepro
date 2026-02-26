"""Add message_text to crm_followup_executions

Revision ID: add_followup_message_text
Revises: phase8_email_outbox
Create Date: 2026-02-26
"""

from alembic import op
import sqlalchemy as sa

revision = 'add_followup_message_text'
down_revision = 'phase8_email_outbox'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('crm_followup_executions', sa.Column('message_text', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('crm_followup_executions', 'message_text')

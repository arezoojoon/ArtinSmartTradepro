"""v3_core_models

Revision ID: 90dc103dfe9d
Revises: 
Create Date: 2026-02-13 22:59:44.217908

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '90dc103dfe9d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Enums
    # Postgres needs explicit Enum creation
    # Create Enums safely
    # Postgres needs explicit Enum creation, but check if they exist first to avoid errors
    connection = op.get_bind()
    
    try:
        op.execute("CREATE TYPE tenantmode AS ENUM ('buyer', 'seller', 'hybrid')")
    except sa.exc.ProgrammingError:
        connection.rollback() # Type likely exists
        
    try:
        op.execute("CREATE TYPE userpersona AS ENUM ('trader', 'logistics', 'finance', 'admin')")
    except sa.exc.ProgrammingError:
        connection.rollback() # Type likely exists

    # Add Columns
    op.add_column('tenants', sa.Column('mode', sa.String(), nullable=True))
    op.add_column('users', sa.Column('persona', sa.String(), nullable=True))

    # Create Tables
    op.create_table('brain_opportunities',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('estimated_profit', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('source_data', sa.JSON(), nullable=True),
        sa.Column('actions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_brain_opportunities_tenant_id'), 'brain_opportunities', ['tenant_id'], unique=False)
    
    op.create_table('brain_signals',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('headline', sa.String(), nullable=False),
        sa.Column('summary', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('severity', sa.String(), nullable=True),
        sa.Column('impact_area', sa.String(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_brain_signals_tenant_id'), 'brain_signals', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_brain_signals_tenant_id'), table_name='brain_signals')
    op.drop_table('brain_signals')
    op.drop_index(op.f('ix_brain_opportunities_tenant_id'), table_name='brain_opportunities')
    op.drop_table('brain_opportunities')
    op.drop_column('users', 'persona')
    op.drop_column('tenants', 'mode')
    op.execute("DROP TYPE userpersona")
    op.execute("DROP TYPE tenantmode")

"""
Hunter Phase 4 Database Schema
Leads + Evidence + Enrichment Jobs + RLS
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'phase4_hunter_schema'
down_revision = 'phase2_comm_automation'
branch_labels = None
depends_on = None

def upgrade():
    # Enums
    types = [
        ('hunter_lead_status', "('new','enriched','qualified','rejected','pushed_to_crm')"),
        ('hunter_identity_type', "('email','phone','domain','linkedin','address','other')"),
        ('hunter_enrichment_status', "('queued','running','done','failed')"),
    ]
    for type_name, values in types:
        op.execute(f"""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{type_name}') THEN
                    CREATE TYPE {type_name} AS ENUM {values};
                END IF;
            END $$;
        """)
    
    # hunter_leads table
    op.create_table('hunter_leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('primary_name', sa.String(), nullable=False),
        sa.Column('country', sa.String(), nullable=False),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('industry', sa.String(), nullable=True),
        sa.Column('source_hint', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('new', 'enriched', 'qualified', 'rejected', 'pushed_to_crm', name='hunter_lead_status', create_type=False), nullable=False, default='new'),
        sa.Column('score_total', sa.Integer(), nullable=False, default=0),
        sa.Column('score_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hunter_leads_tenant_id'), 'hunter_leads', ['tenant_id'])
    op.create_index(op.f('ix_hunter_leads_status'), 'hunter_leads', ['status'])
    
    # hunter_lead_identities table
    op.create_table('hunter_lead_identities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', postgresql.ENUM('email', 'phone', 'domain', 'linkedin', 'address', 'other', name='hunter_identity_type', create_type=False), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('normalized_value', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['hunter_leads.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'type', 'normalized_value', name='uq_hunter_identities')
    )
    op.create_index(op.f('ix_hunter_lead_identities_tenant_id'), 'hunter_lead_identities', ['tenant_id'])
    op.create_index(op.f('ix_hunter_lead_identities_lead_id'), 'hunter_lead_identities', ['lead_id'])
    
    # hunter_evidence table
    op.create_table('hunter_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_name', sa.String(), nullable=False),
        sa.Column('source_name', sa.String(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column('snippet', sa.String(), nullable=True),
        sa.Column('raw', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['hunter_leads.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hunter_evidence_tenant_id'), 'hunter_evidence', ['tenant_id'])
    op.create_index(op.f('ix_hunter_evidence_lead_id'), 'hunter_evidence', ['lead_id'])
    op.create_index(op.f('ix_hunter_evidence_field_name'), 'hunter_evidence', ['field_name'])
    op.create_index('ix_hunter_evidence_lead_field', 'hunter_evidence', ['tenant_id', 'lead_id', 'field_name'])
    
    # hunter_enrichment_jobs table
    op.create_table('hunter_enrichment_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('status', postgresql.ENUM('queued', 'running', 'done', 'failed', name='hunter_enrichment_status', create_type=False), nullable=False, default='queued'),
        sa.Column('attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['hunter_leads.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hunter_enrichment_jobs_tenant_id'), 'hunter_enrichment_jobs', ['tenant_id'])
    op.create_index(op.f('ix_hunter_enrichment_jobs_lead_id'), 'hunter_enrichment_jobs', ['lead_id'])
    op.create_index(op.f('ix_hunter_enrichment_jobs_status'), 'hunter_enrichment_jobs', ['status'])
    op.create_index('ix_hunter_enrichment_jobs_scheduled', 'hunter_enrichment_jobs', ['status', 'scheduled_for'])
    
    # hunter_scoring_profiles table
    op.create_table('hunter_scoring_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('weights', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hunter_scoring_profiles_tenant_id'), 'hunter_scoring_profiles', ['tenant_id'])
    op.create_index(op.f('ix_hunter_scoring_profiles_is_default'), 'hunter_scoring_profiles', ['is_default'])
    
    # Enable RLS on all tables
    tables = [
        'hunter_leads',
        'hunter_lead_identities', 
        'hunter_evidence',
        'hunter_enrichment_jobs',
        'hunter_scoring_profiles'
    ]
    
    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        
        # Policy: Users can see their tenant's data
        op.execute(f"""
            CREATE POLICY {table}_tenant_select ON {table}
            FOR SELECT USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
        """)
        
        # Policy: Users can insert their tenant's data
        op.execute(f"""
            CREATE POLICY {table}_tenant_insert ON {table}
            FOR INSERT WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid)
        """)
        
        # Policy: Users can update their tenant's data
        op.execute(f"""
            CREATE POLICY {table}_tenant_update ON {table}
            FOR UPDATE USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
        """)
        
        # Policy: Users can delete their tenant's data
        op.execute(f"""
            CREATE POLICY {table}_tenant_delete ON {table}
            FOR DELETE USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
        """)

def downgrade():
    # Drop policies and tables
    tables = [
        'hunter_scoring_profiles',
        'hunter_enrichment_jobs',
        'hunter_evidence',
        'hunter_lead_identities',
        'hunter_leads'
    ]
    
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_select ON {table}")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_insert ON {table}")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_update ON {table}")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_delete ON {table}")
        op.drop_table(table)
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS hunter_enrichment_status")
    op.execute("DROP TYPE IF EXISTS hunter_identity_type")
    op.execute("DROP TYPE IF EXISTS hunter_lead_status")

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
    # ── 1. Enum types (Idempotent) ──────────────────────────────────────────
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

    # ── 2. Tables (Raw SQL) ────────────────────────────────────────────────
    # hunter_leads
    op.execute("""
    CREATE TABLE IF NOT EXISTS hunter_leads (
        id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id        UUID NOT NULL REFERENCES tenants(id),
        primary_name     VARCHAR NOT NULL,
        country          VARCHAR NOT NULL,
        city             VARCHAR,
        website          VARCHAR,
        industry         VARCHAR,
        source_hint      VARCHAR,
        status           hunter_lead_status NOT NULL DEFAULT 'new',
        score_total      INTEGER NOT NULL DEFAULT 0,
        score_breakdown  JSONB NOT NULL DEFAULT '{}',
        created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS ix_hunter_leads_tenant_id ON hunter_leads(tenant_id);
    CREATE INDEX IF NOT EXISTS ix_hunter_leads_status ON hunter_leads(status);
    """)

    # hunter_lead_identities
    op.execute("""
    CREATE TABLE IF NOT EXISTS hunter_lead_identities (
        id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id         UUID NOT NULL REFERENCES tenants(id),
        lead_id           UUID NOT NULL REFERENCES hunter_leads(id) ON DELETE CASCADE,
        type              hunter_identity_type NOT NULL,
        value             VARCHAR NOT NULL,
        normalized_value  VARCHAR NOT NULL,
        created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_hunter_identities UNIQUE (tenant_id, type, normalized_value)
    );
    CREATE INDEX IF NOT EXISTS ix_hunter_lead_identities_tenant_id ON hunter_lead_identities(tenant_id);
    CREATE INDEX IF NOT EXISTS ix_hunter_lead_identities_lead_id ON hunter_lead_identities(lead_id);
    """)

    # hunter_evidence
    op.execute("""
    CREATE TABLE IF NOT EXISTS hunter_evidence (
        id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id    UUID NOT NULL REFERENCES tenants(id),
        lead_id      UUID NOT NULL REFERENCES hunter_leads(id) ON DELETE CASCADE,
        field_name   VARCHAR NOT NULL,
        source_name  VARCHAR NOT NULL,
        source_url   VARCHAR,
        collected_at TIMESTAMPTZ NOT NULL,
        confidence   NUMERIC(3, 2) NOT NULL,
        snippet      VARCHAR,
        raw          JSONB,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS ix_hunter_evidence_tenant_id ON hunter_evidence(tenant_id);
    CREATE INDEX IF NOT EXISTS ix_hunter_evidence_lead_id ON hunter_evidence(lead_id);
    CREATE INDEX IF NOT EXISTS ix_hunter_evidence_field_name ON hunter_evidence(field_name);
    CREATE INDEX IF NOT EXISTS ix_hunter_evidence_lead_field ON hunter_evidence(tenant_id, lead_id, field_name);
    """)

    # hunter_enrichment_jobs
    op.execute("""
    CREATE TABLE IF NOT EXISTS hunter_enrichment_jobs (
        id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id     UUID NOT NULL REFERENCES tenants(id),
        lead_id       UUID NOT NULL REFERENCES hunter_leads(id) ON DELETE CASCADE,
        provider      VARCHAR NOT NULL,
        status        hunter_enrichment_status NOT NULL DEFAULT 'queued',
        attempts      INTEGER NOT NULL DEFAULT 0,
        scheduled_for TIMESTAMPTZ NOT NULL DEFAULT now(),
        started_at    TIMESTAMPTZ,
        finished_at   TIMESTAMPTZ,
        error         JSONB,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS ix_hunter_enrichment_jobs_tenant_id ON hunter_enrichment_jobs(tenant_id);
    CREATE INDEX IF NOT EXISTS ix_hunter_enrichment_jobs_lead_id ON hunter_enrichment_jobs(lead_id);
    CREATE INDEX IF NOT EXISTS ix_hunter_enrichment_jobs_status ON hunter_enrichment_jobs(status);
    CREATE INDEX IF NOT EXISTS ix_hunter_enrichment_jobs_scheduled ON hunter_enrichment_jobs(status, scheduled_for);
    """)

    # hunter_scoring_profiles
    op.execute("""
    CREATE TABLE IF NOT EXISTS hunter_scoring_profiles (
        id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id  UUID NOT NULL REFERENCES tenants(id),
        name       VARCHAR NOT NULL,
        weights    JSONB NOT NULL,
        is_default BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS ix_hunter_scoring_profiles_tenant_id ON hunter_scoring_profiles(tenant_id);
    CREATE INDEX IF NOT EXISTS ix_hunter_scoring_profiles_is_default ON hunter_scoring_profiles(is_default);
    """)

    # ── 3. RLS Policies ───────────────────────────────────────────────────
    tables = [
        'hunter_leads', 'hunter_lead_identities', 'hunter_evidence',
        'hunter_enrichment_jobs', 'hunter_scoring_profiles'
    ]
    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id::text = current_setting('app.tenant_id', true))
            WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))
        """)

    # ── Ensure UUID defaults (Idempotent fix for SQLAlchemy-created tables) ─────
    all_p4_tables = [
        'hunter_leads', 'hunter_lead_identities', 'hunter_evidence',
        'hunter_enrichment_jobs', 'hunter_scoring_profiles'
    ]
    for table in all_p4_tables:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT gen_random_uuid()")
    
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

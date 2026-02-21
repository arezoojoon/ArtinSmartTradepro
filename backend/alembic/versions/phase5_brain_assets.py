"""Phase 5 Brain Asset Database Schema
Asset databases for arbitrage history, supplier reliability, buyer payment behavior, and seasonality matrix
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = 'phase5_brain_assets'
down_revision = 'phase4_hunter_schema'
branch_labels = None
depends_on = None

def upgrade():
    # ── 1. Enum types (Idempotent) ──────────────────────────────────────────
    types = [
        ('arbitrage_outcome', "('won','lost','no_go','unknown')"),
        ('brain_engine_type', "('arbitrage','risk','demand','cultural')"),
        ('brain_run_status', "('success','insufficient_data','failed')"),
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
    # asset_arbitrage_history
    op.execute("""
    CREATE TABLE IF NOT EXISTS asset_arbitrage_history (
        id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id            UUID NOT NULL REFERENCES tenants(id),
        product_key          TEXT NOT NULL,
        buy_market           TEXT NOT NULL,
        sell_market          TEXT NOT NULL,
        incoterms            TEXT NOT NULL,
        buy_price            NUMERIC(15, 2) NOT NULL,
        buy_currency         TEXT NOT NULL,
        sell_price           NUMERIC(15, 2) NOT NULL,
        sell_currency        TEXT NOT NULL,
        freight_cost         NUMERIC(15, 2),
        fx_rate              NUMERIC(10, 6),
        estimated_margin_pct NUMERIC(5, 2),
        realized_margin_pct  NUMERIC(5, 2),
        outcome              arbitrage_outcome,
        decision_reason      TEXT,
        data_used            JSONB,
        created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_arbitrage_tenant_product ON asset_arbitrage_history (tenant_id, product_key);
    CREATE INDEX IF NOT EXISTS idx_arbitrage_tenant_markets ON asset_arbitrage_history (tenant_id, buy_market, sell_market);
    CREATE INDEX IF NOT EXISTS idx_arbitrage_created_at ON asset_arbitrage_history (created_at);
    """)

    # asset_supplier_reliability
    op.execute("""
    CREATE TABLE IF NOT EXISTS asset_supplier_reliability (
        id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id           UUID NOT NULL REFERENCES tenants(id),
        supplier_name       TEXT NOT NULL,
        supplier_country    TEXT NOT NULL,
        identifiers         JSONB,
        on_time_rate        NUMERIC(5, 2),
        defect_rate         NUMERIC(5, 2),
        dispute_count       INTEGER NOT NULL DEFAULT 0,
        avg_lead_time_days  INTEGER,
        reliability_score   INTEGER NOT NULL DEFAULT 0,
        evidence            JSONB,
        created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_supplier_tenant_country ON asset_supplier_reliability (tenant_id, supplier_country);
    CREATE INDEX IF NOT EXISTS idx_supplier_tenant_name ON asset_supplier_reliability (tenant_id, supplier_name);
    CREATE INDEX IF NOT EXISTS idx_supplier_reliability_score ON asset_supplier_reliability (reliability_score);
    """)

    # asset_buyer_payment_behavior
    op.execute("""
    CREATE TABLE IF NOT EXISTS asset_buyer_payment_behavior (
        id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id               UUID NOT NULL REFERENCES tenants(id),
        buyer_country           TEXT NOT NULL,
        buyer_name              TEXT,
        segment                 TEXT,
        avg_payment_delay_days  INTEGER,
        default_rate            NUMERIC(5, 2),
        preferred_terms         TEXT,
        payment_risk_score      INTEGER NOT NULL DEFAULT 0,
        evidence                JSONB,
        created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_buyer_tenant_country ON asset_buyer_payment_behavior (tenant_id, buyer_country);
    CREATE INDEX IF NOT EXISTS idx_buyer_tenant_segment ON asset_buyer_payment_behavior (tenant_id, segment);
    CREATE INDEX IF NOT EXISTS idx_buyer_risk_score ON asset_buyer_payment_behavior (payment_risk_score);
    """)

    # asset_seasonality_matrix
    op.execute("""
    CREATE TABLE IF NOT EXISTS asset_seasonality_matrix (
        id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id         UUID NOT NULL REFERENCES tenants(id),
        product_key       TEXT NOT NULL,
        country           TEXT NOT NULL,
        season_key        TEXT NOT NULL,
        demand_index      NUMERIC(8, 3),
        price_index       NUMERIC(8, 3),
        volatility_index  NUMERIC(8, 3),
        data_used         JSONB,
        created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_seasonality_matrix UNIQUE (tenant_id, product_key, country, season_key)
    );
    CREATE INDEX IF NOT EXISTS idx_seasonality_tenant_product ON asset_seasonality_matrix (tenant_id, product_key);
    CREATE INDEX IF NOT EXISTS idx_seasonality_tenant_country ON asset_seasonality_matrix (tenant_id, country);
    CREATE INDEX IF NOT EXISTS idx_seasonality_season ON asset_seasonality_matrix (season_key);
    """)

    # brain_engine_runs
    op.execute("""
    CREATE TABLE IF NOT EXISTS brain_engine_runs (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id       UUID NOT NULL REFERENCES tenants(id),
        engine_type     brain_engine_type NOT NULL,
        input_payload   JSONB NOT NULL,
        output_payload  JSONB,
        explainability  JSONB,
        status          brain_run_status NOT NULL,
        error           JSONB,
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_brain_runs_tenant_type ON brain_engine_runs (tenant_id, engine_type);
    CREATE INDEX IF NOT EXISTS idx_brain_runs_created_at ON brain_engine_runs (created_at);
    CREATE INDEX IF NOT EXISTS idx_brain_runs_status ON brain_engine_runs (status);
    """)

    # brain_data_sources
    op.execute("""
    CREATE TABLE IF NOT EXISTS brain_data_sources (
        id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id   UUID NOT NULL REFERENCES tenants(id),
        name        TEXT NOT NULL,
        type        TEXT NOT NULL,
        is_active   BOOLEAN NOT NULL DEFAULT true,
        meta        JSONB,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_brain_data_sources UNIQUE (tenant_id, name)
    );
    CREATE INDEX IF NOT EXISTS idx_brain_sources_tenant ON brain_data_sources (tenant_id);
    CREATE INDEX IF NOT EXISTS idx_brain_sources_active ON brain_data_sources (is_active);
    """)

    # cultural_profiles
    op.execute("""
    CREATE TABLE IF NOT EXISTS cultural_profiles (
        id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id         UUID NOT NULL REFERENCES tenants(id),
        country           TEXT NOT NULL,
        negotiation_style JSONB,
        do_dont           JSONB,
        typical_terms     JSONB,
        created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_cultural_tenant_country ON cultural_profiles (tenant_id, country);
    CREATE INDEX IF NOT EXISTS idx_cultural_country ON cultural_profiles (country);
    """)

    # demand_time_series
    op.execute("""
    CREATE TABLE IF NOT EXISTS demand_time_series (
        id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id     UUID NOT NULL REFERENCES tenants(id),
        product_key   TEXT NOT NULL,
        country       TEXT NOT NULL,
        date          DATE NOT NULL,
        demand_value  NUMERIC(15, 2),
        source_name   TEXT NOT NULL,
        data_used     JSONB,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_demand_time_series UNIQUE (tenant_id, product_key, country, date)
    );
    CREATE INDEX IF NOT EXISTS idx_demand_tenant_product ON demand_time_series (tenant_id, product_key);
    CREATE INDEX IF NOT EXISTS idx_demand_tenant_country ON demand_time_series (tenant_id, country);
    CREATE INDEX IF NOT EXISTS idx_demand_date ON demand_time_series (date);
    """)

    # ── 3. RLS Policies ───────────────────────────────────────────────────
    tables = [
        'asset_arbitrage_history', 'asset_supplier_reliability', 'asset_buyer_payment_behavior',
        'asset_seasonality_matrix', 'brain_engine_runs', 'brain_data_sources',
        'cultural_profiles', 'demand_time_series'
    ]
    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id::text = current_setting('app.tenant_id', true))
            WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))
        """)

    # ── 4. Default Data ───────────────────────────────────────────────────
    op.execute("""
    INSERT INTO brain_data_sources (tenant_id, name, type, is_active, meta)
    SELECT id, 'manual', 'manual_input', true, '{"description": "Manually entered data"}'::jsonb FROM tenants
    ON CONFLICT (tenant_id, name) DO NOTHING;
    """)
    op.execute("""
    INSERT INTO brain_data_sources (tenant_id, name, type, is_active, meta)
    SELECT id, 'csv_import', 'csv_upload', true, '{"description": "Data imported from CSV files"}'::jsonb FROM tenants
    ON CONFLICT (tenant_id, name) DO NOTHING;
    """)

def downgrade():
    # Drop tables in reverse order
    for table in ['demand_time_series', 'cultural_profiles', 'brain_data_sources', 'brain_engine_runs',
                   'asset_seasonality_matrix', 'asset_buyer_payment_behavior', 'asset_supplier_reliability', 
                   'asset_arbitrage_history']:
        op.drop_table(table)
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS arbitrage_outcome")
    op.execute("DROP TYPE IF EXISTS brain_engine_type")
    op.execute("DROP TYPE IF EXISTS brain_run_status")

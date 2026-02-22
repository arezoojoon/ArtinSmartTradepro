"""Phase 6 Revenue Tracking Enhancement
Add revenue analytics, churn prediction, and MRR/ARR tracking tables
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = 'phase6_revenue_tracking'
down_revision = 'phase6_sys_admin'
branch_labels = None
depends_on = None


def upgrade():
    # ── 1. Enum types (Idempotent) ──────────────────────────────────────────
    types = [
        ('revenue_period_enum', "('daily','weekly','monthly','yearly')"),
        ('revenue_event_type_enum', "('subscription_start','subscription_cancel','subscription_upgrade','subscription_downgrade','usage_charge','one_time_payment','refund')"),
    ]
    for type_name, values in types:
        op.execute(f"""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{type_name}') THEN
                    CREATE TYPE {type_name} AS ENUM {values};
                END IF;
            END $$;
        """)

    # ── 2. Revenue Snapshots ─────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS revenue_snapshots (
        id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        period           revenue_period_enum NOT NULL,
        period_start     TIMESTAMPTZ NOT NULL,
        period_end       TIMESTAMPTZ NOT NULL,
        mrr              NUMERIC(12, 2) NOT NULL DEFAULT 0,
        arr              NUMERIC(12, 2) NOT NULL DEFAULT 0,
        nrr              NUMERIC(12, 2) NOT NULL DEFAULT 0,
        active_customers INTEGER NOT NULL DEFAULT 0,
        new_customers    INTEGER NOT NULL DEFAULT 0,
        churned_customers INTEGER NOT NULL DEFAULT 0,
        total_usage_units INTEGER NOT NULL DEFAULT 0,
        avg_usage_per_customer NUMERIC(10, 2) NOT NULL DEFAULT 0,
        plan_breakdown   JSONB NOT NULL DEFAULT '{}',
        created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_revenue_snapshots_period ON revenue_snapshots (period);
    CREATE INDEX IF NOT EXISTS idx_revenue_snapshots_start ON revenue_snapshots (period_start);
    CREATE INDEX IF NOT EXISTS idx_revenue_snapshots_end ON revenue_snapshots (period_end);
    """)

    # ── 3. Revenue Events ───────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS revenue_events (
        id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id         UUID NOT NULL REFERENCES tenants(id),
        event_type        revenue_event_type_enum NOT NULL,
        event_date        TIMESTAMPTZ NOT NULL,
        amount            NUMERIC(12, 2) NOT NULL,
        currency          VARCHAR(3) NOT NULL DEFAULT 'USD',
        plan_code         VARCHAR(50),
        previous_plan_code VARCHAR(50),
        usage_metric      VARCHAR(50),
        usage_quantity    INTEGER,
        metadata          JSONB,
        processed         BOOLEAN NOT NULL DEFAULT false,
        created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_revenue_events_tenant ON revenue_events (tenant_id);
    CREATE INDEX IF NOT EXISTS idx_revenue_events_type ON revenue_events (event_type);
    CREATE INDEX IF NOT EXISTS idx_revenue_events_date ON revenue_events (event_date);
    CREATE INDEX IF NOT EXISTS idx_revenue_events_processed ON revenue_events (processed);
    """)

    # ── 4. Churn Predictions ─────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS churn_predictions (
        id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id              UUID NOT NULL REFERENCES tenants(id) UNIQUE,
        churn_probability      NUMERIC(5, 4) NOT NULL,
        risk_level             VARCHAR(20) NOT NULL,
        risk_factors           JSONB NOT NULL,
        model_version          VARCHAR(20) NOT NULL,
        prediction_date        TIMESTAMPTZ NOT NULL,
        data_freshness         TIMESTAMPTZ NOT NULL,
        retention_action_taken BOOLEAN NOT NULL DEFAULT false,
        retention_action_type  VARCHAR(50),
        retention_action_date  TIMESTAMPTZ,
        created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_churn_predictions_tenant ON churn_predictions (tenant_id);
    CREATE INDEX IF NOT EXISTS idx_churn_predictions_probability ON churn_predictions (churn_probability);
    CREATE INDEX IF NOT EXISTS idx_churn_predictions_risk_level ON churn_predictions (risk_level);
    CREATE INDEX IF NOT EXISTS idx_churn_predictions_date ON churn_predictions (prediction_date);
    """)

    # ── 5. Revenue Alerts ────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS revenue_alerts (
        id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        alert_type          VARCHAR(50) NOT NULL,
        severity            VARCHAR(20) NOT NULL,
        title               VARCHAR(200) NOT NULL,
        description         TEXT NOT NULL,
        current_value       NUMERIC(12, 2),
        previous_value      NUMERIC(12, 2),
        threshold_value     NUMERIC(12, 2),
        percentage_change   NUMERIC(5, 2),
        affected_tenant_ids JSONB,
        time_period         VARCHAR(20),
        status              VARCHAR(20) NOT NULL DEFAULT 'active',
        acknowledged_by     UUID,
        acknowledged_at     TIMESTAMPTZ,
        created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
        resolved_at         TIMESTAMPTZ
    );
    CREATE INDEX IF NOT EXISTS idx_revenue_alerts_type ON revenue_alerts (alert_type);
    CREATE INDEX IF NOT EXISTS idx_revenue_alerts_severity ON revenue_alerts (severity);
    CREATE INDEX IF NOT EXISTS idx_revenue_alerts_status ON revenue_alerts (status);
    CREATE INDEX IF NOT EXISTS idx_revenue_alerts_created ON revenue_alerts (created_at);
    """)

    # ── 6. Ensure UUID defaults (Idempotent fix for SQLAlchemy-created tables) ─────
    all_revenue_tables = [
        'revenue_snapshots', 'revenue_events', 'churn_predictions', 'revenue_alerts'
    ]
    for table in all_revenue_tables:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT gen_random_uuid()")


def downgrade():
    # Drop tables in reverse order
    for table in ['revenue_alerts', 'churn_predictions', 'revenue_events', 'revenue_snapshots']:
        op.drop_table(table)
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS revenue_period_enum")
    op.execute("DROP TYPE IF EXISTS revenue_event_type_enum")

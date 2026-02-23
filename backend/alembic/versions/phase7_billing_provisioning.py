"""Phase 7 Billing and Provisioning
Manual migration for billing_ext models.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'phase7_billing'
down_revision = 'phase6_sys_admin'
branch_labels = None
depends_on = None

def upgrade():
    # ── 0. Enum types ───────────────────────────────────────────────────────────
    types = [
        ('checkout_session_status_enum', "('open', 'complete', 'expired', 'cancelled')"),
        ('provisioning_state_enum', "('pending', 'running', 'ready', 'failed')"),
    ]
    for type_name, values in types:
        op.execute(f"""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{type_name}') THEN
                    CREATE TYPE {type_name} AS ENUM {values};
                END IF;
            END $$;
        """)

    # ── stripe_events ───────────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS stripe_events (
        event_id    VARCHAR(255) PRIMARY KEY,
        event_type  VARCHAR(100) NOT NULL,
        processed_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)

    # ── billing_checkout_sessions ───────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS billing_checkout_sessions (
        id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id          UUID NOT NULL REFERENCES tenants(id),
        user_id            UUID NOT NULL REFERENCES users(id),
        stripe_session_id  VARCHAR(255) NOT NULL UNIQUE,
        stripe_customer_id VARCHAR(255),
        plan_code          VARCHAR(50) NOT NULL,
        status             checkout_session_status_enum NOT NULL DEFAULT 'open',
        mode               VARCHAR(50) DEFAULT 'subscription',
        created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_billing_session_tenant ON billing_checkout_sessions (tenant_id);
    CREATE INDEX IF NOT EXISTS idx_billing_session_stripe ON billing_checkout_sessions (stripe_session_id);
    """)

    # ── tenant_provisioning_status ──────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS tenant_provisioning_status (
        tenant_id          UUID PRIMARY KEY REFERENCES tenants(id),
        overall_status     provisioning_state_enum NOT NULL DEFAULT 'pending',
        waha_status        provisioning_state_enum NOT NULL DEFAULT 'pending',
        crm_status         provisioning_state_enum NOT NULL DEFAULT 'pending',
        telegram_status    provisioning_state_enum NOT NULL DEFAULT 'pending',
        waha_session_name  VARCHAR(255),
        qr_ref             TEXT,
        telegram_deeplink  TEXT,
        retry_count        INTEGER NOT NULL DEFAULT 0,
        last_error         TEXT,
        created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)

    # ── RLS for tenant_provisioning_status ─────────────────────────────────────
    op.execute("ALTER TABLE tenant_provisioning_status ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_provisioning ON tenant_provisioning_status")
    op.execute("""
        CREATE POLICY tenant_isolation_provisioning ON tenant_provisioning_status
        USING (tenant_id::text = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))
    """)

def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation_provisioning ON tenant_provisioning_status")
    op.drop_table('tenant_provisioning_status')
    op.drop_table('billing_checkout_sessions')
    op.drop_table('stripe_events')
    op.execute("DROP TYPE IF EXISTS provisioning_state_enum")
    op.execute("DROP TYPE IF EXISTS checkout_session_status_enum")

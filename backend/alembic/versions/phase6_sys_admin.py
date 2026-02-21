"""Phase 6 System Admin Schema
Matches models in app/models/phase6.py exactly.
Table names: sys_audit_logs, sys_plans, tenant_subscriptions, usage_counters,
             whitelabel_configs, whitelabel_domains, email_templates,
             prompt_families, prompt_versions, prompt_runs, prompt_evals,
             system_settings, system_admins
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

revision = 'phase6_sys_admin'
down_revision = 'phase5_brain_assets'
branch_labels = None
depends_on = None


def upgrade():
    # ── 0. Enum types (Idempotent) ──────────────────────────────────────────────
    types = [
        ('sub_status_enum', "('active', 'past_due', 'canceled')"),
        ('domain_status_enum', "('pending_dns', 'active', 'disabled')"),
        ('prompt_status_enum', "('draft', 'approved', 'deprecated')"),
        ('prompt_run_status_enum', "('success', 'guardrail_rejected', 'error')"),
    ]
    for type_name, values in types:
        op.execute(f"""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{type_name}') THEN
                    CREATE TYPE {type_name} AS ENUM {values};
                END IF;
            END $$;
        """)

    # ── system_admins ───────────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS system_admins (
        id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email         VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        name          VARCHAR(255),
        is_active     BOOLEAN NOT NULL DEFAULT true,
        last_login_at TIMESTAMPTZ,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_sys_admins_email ON system_admins (email);
    CREATE INDEX IF NOT EXISTS idx_sys_admins_active ON system_admins (is_active);
    """)

    # ── sys_audit_logs ──────────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS sys_audit_logs (
        id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id           UUID,
        actor_user_id       UUID,
        actor_sys_admin_id  UUID,
        action              VARCHAR(100) NOT NULL,
        resource_type       VARCHAR(50) NOT NULL,
        resource_id         VARCHAR(255),
        before_state        JSONB,
        after_state         JSONB,
        metadata            JSONB,
        ip_address          VARCHAR(45),
        user_agent          VARCHAR(500),
        created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_sys_audit_tenant ON sys_audit_logs (tenant_id);
    CREATE INDEX IF NOT EXISTS idx_sys_audit_sys_admin ON sys_audit_logs (actor_sys_admin_id);
    CREATE INDEX IF NOT EXISTS idx_sys_audit_action ON sys_audit_logs (action);
    CREATE INDEX IF NOT EXISTS idx_sys_audit_created ON sys_audit_logs (created_at);
    """)

    # ── sys_plans ───────────────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS sys_plans (
        id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        code              VARCHAR(50) NOT NULL UNIQUE,
        name              VARCHAR(255) NOT NULL,
        description       TEXT,
        monthly_price_usd NUMERIC(10, 2),
        features          JSONB NOT NULL DEFAULT '{}',
        limits            JSONB NOT NULL DEFAULT '{}',
        is_active         BOOLEAN NOT NULL DEFAULT true,
        created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_sys_plans_code ON sys_plans (code);
    CREATE INDEX IF NOT EXISTS idx_sys_plans_active ON sys_plans (is_active);
    """)

    # ── tenant_subscriptions ────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS tenant_subscriptions (
        id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id            UUID NOT NULL UNIQUE,
        plan_id              UUID NOT NULL REFERENCES sys_plans(id),
        status               sub_status_enum NOT NULL DEFAULT 'active',
        current_period_start TIMESTAMPTZ NOT NULL DEFAULT now(),
        current_period_end   TIMESTAMPTZ,
        created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_tenant_sub_tenant ON tenant_subscriptions (tenant_id);
    CREATE INDEX IF NOT EXISTS idx_tenant_sub_plan ON tenant_subscriptions (plan_id);
    """)

    # ── usage_counters ──────────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS usage_counters (
        id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id  UUID NOT NULL,
        period_key VARCHAR(10) NOT NULL,
        metric     VARCHAR(50) NOT NULL,
        value      INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_usage_counters UNIQUE (tenant_id, period_key, metric)
    );
    CREATE INDEX IF NOT EXISTS idx_usage_tenant ON usage_counters (tenant_id);
    CREATE INDEX IF NOT EXISTS idx_usage_period ON usage_counters (period_key);
    CREATE INDEX IF NOT EXISTS idx_usage_metric ON usage_counters (metric);
    """)

    # ── whitelabel_configs ──────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS whitelabel_configs (
        id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id     UUID NOT NULL UNIQUE,
        is_enabled    BOOLEAN NOT NULL DEFAULT false,
        brand_name    VARCHAR(255),
        logo_url      VARCHAR(500),
        favicon_url   VARCHAR(500),
        primary_color VARCHAR(7),
        accent_color  VARCHAR(7),
        support_email VARCHAR(255),
        support_phone VARCHAR(50),
        custom_css    TEXT,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_wl_configs_tenant ON whitelabel_configs (tenant_id);
    CREATE INDEX IF NOT EXISTS idx_wl_configs_enabled ON whitelabel_configs (is_enabled);
    """)

    # ── whitelabel_domains ──────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS whitelabel_domains (
        id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id          UUID NOT NULL,
        domain             VARCHAR(255) NOT NULL UNIQUE,
        status             domain_status_enum NOT NULL DEFAULT 'pending_dns',
        verification_token VARCHAR(255),
        verified_at        TIMESTAMPTZ,
        config_id          UUID REFERENCES whitelabel_configs(id),
        created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_wl_domains_tenant ON whitelabel_domains (tenant_id);
    CREATE INDEX IF NOT EXISTS idx_wl_domains_domain ON whitelabel_domains (domain);
    CREATE INDEX IF NOT EXISTS idx_wl_domains_status ON whitelabel_domains (status);
    """)

    # ── email_templates ─────────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS email_templates (
        id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id  UUID NOT NULL,
        name       VARCHAR(255) NOT NULL,
        type       VARCHAR(50) NOT NULL,
        subject    VARCHAR(500) NOT NULL,
        body       TEXT NOT NULL,
        is_default BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_email_tmpl_tenant ON email_templates (tenant_id);
    CREATE INDEX IF NOT EXISTS idx_email_tmpl_type ON email_templates (type);
    """)

    # ── prompt_families ─────────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS prompt_families (
        id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name        VARCHAR(255) NOT NULL UNIQUE,
        description TEXT,
        category    VARCHAR(50) NOT NULL DEFAULT 'general',
        is_active   BOOLEAN NOT NULL DEFAULT true,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_prompt_fam_name ON prompt_families (name);
    CREATE INDEX IF NOT EXISTS idx_prompt_fam_category ON prompt_families (category);
    """)

    # ── prompt_versions ─────────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS prompt_versions (
        id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        family_id            UUID NOT NULL REFERENCES prompt_families(id),
        version              INTEGER NOT NULL,
        status               prompt_status_enum NOT NULL DEFAULT 'draft',
        model_target         VARCHAR(100) NOT NULL DEFAULT 'gemini-1.5-pro',
        system_prompt        TEXT NOT NULL,
        user_prompt_template TEXT NOT NULL,
        guardrails           JSONB NOT NULL DEFAULT '{}',
        created_by           UUID NOT NULL,
        approved_by          UUID,
        approved_at          TIMESTAMPTZ,
        created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_prompt_family_version UNIQUE (family_id, version)
    );
    CREATE INDEX IF NOT EXISTS idx_prompt_ver_family ON prompt_versions (family_id);
    CREATE INDEX IF NOT EXISTS idx_prompt_ver_status ON prompt_versions (status);
    """)

    # ── prompt_runs ─────────────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS prompt_runs (
        id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id         UUID NOT NULL,
        family_name       VARCHAR(255) NOT NULL,
        version           INTEGER NOT NULL,
        prompt_version_id UUID REFERENCES prompt_versions(id),
        engine_run_id     UUID,
        input             JSONB NOT NULL,
        output            JSONB,
        token_usage       JSONB,
        guardrail_result  JSONB,
        status            prompt_run_status_enum NOT NULL DEFAULT 'success',
        error_message     TEXT,
        created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_prompt_run_tenant ON prompt_runs (tenant_id);
    CREATE INDEX IF NOT EXISTS idx_prompt_run_family ON prompt_runs (family_name);
    CREATE INDEX IF NOT EXISTS idx_prompt_run_status ON prompt_runs (status);
    CREATE INDEX IF NOT EXISTS idx_prompt_run_created ON prompt_runs (created_at);
    """)

    # ── prompt_evals ────────────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS prompt_evals (
        id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        family_id         UUID NOT NULL REFERENCES prompt_families(id),
        version           INTEGER NOT NULL,
        prompt_version_id UUID REFERENCES prompt_versions(id),
        test_name         VARCHAR(255) NOT NULL,
        input             JSONB NOT NULL,
        expected_rules    JSONB NOT NULL,
        last_status       VARCHAR(20),
        last_result       JSONB,
        last_run_at       TIMESTAMPTZ,
        created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_prompt_eval_family ON prompt_evals (family_id);
    CREATE INDEX IF NOT EXISTS idx_prompt_eval_version ON prompt_evals (version);
    """)

    # ── system_settings ─────────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS system_settings (
        id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        key          VARCHAR(100) NOT NULL UNIQUE,
        value        JSONB NOT NULL,
        description  TEXT,
        is_sensitive BOOLEAN NOT NULL DEFAULT false,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_sys_settings_key ON system_settings (key);
    """)

    # ── RLS for tenant-scoped tables ───────────────────────────────────────────
    scoped_tables = ['whitelabel_configs', 'whitelabel_domains', 'email_templates', 'usage_counters']
    for table in scoped_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            USING (tenant_id::text = current_setting('app.tenant_id', true))
            WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))
        """)

    # ── Ensure UUID defaults (Idempotent fix for SQLAlchemy-created tables) ─────
    all_p6_tables = [
        'system_admins', 'sys_audit_logs', 'sys_plans', 'tenant_subscriptions',
        'usage_counters', 'whitelabel_configs', 'whitelabel_domains',
        'email_templates', 'prompt_families', 'prompt_versions', 'prompt_runs',
        'prompt_evals', 'system_settings'
    ]
    for table in all_p6_tables:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT gen_random_uuid()")

    # ── Default Data ───────────────────────────────────────────────────────────
    op.execute("""
    INSERT INTO sys_plans (id, code, name, monthly_price_usd, features, limits) VALUES
    (gen_random_uuid(), 'starter', 'Starter', 0.00, '{"brain_engines": true}', '{"messages_sent_daily": 100}'),
    (gen_random_uuid(), 'professional', 'Professional', 299.00, '{"brain_engines": true}', '{"messages_sent_daily": 500}'),
    (gen_random_uuid(), 'enterprise', 'Enterprise', 999.00, '{"brain_engines": true}', '{"messages_sent_daily": 5000}'),
    (gen_random_uuid(), 'whitelabel', 'White-Label', 2999.00, '{"brain_engines": true, "custom_domains": true}', '{"messages_sent_daily": -1}')
    ON CONFLICT (code) DO NOTHING;
    """)

    op.execute("""
    INSERT INTO prompt_families (id, name, category) VALUES
    (gen_random_uuid(), 'cultural_strategy', 'brain'),
    (gen_random_uuid(), 'lead_reply',        'messaging'),
    (gen_random_uuid(), 'report_summary',    'analytics'),
    (gen_random_uuid(), 'arbitrage_insight', 'brain'),
    (gen_random_uuid(), 'risk_summary',      'brain')
    ON CONFLICT (name) DO NOTHING;
    """)

    op.execute("""
    INSERT INTO system_settings (key, value) VALUES
    ('dlq_threshold',  '{"messages": 1000}'),
    ('prompt_ops',     '{"guardrails_enabled": true}'),
    ('security',       '{"ip_allowlist": []}')
    ON CONFLICT (key) DO NOTHING;
    """)


def downgrade():
    for table in ['whitelabel_configs', 'whitelabel_domains', 'email_templates', 'usage_counters']:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    for table in ['system_settings', 'prompt_evals', 'prompt_runs', 'prompt_versions',
                  'prompt_families', 'email_templates', 'whitelabel_domains', 'whitelabel_configs',
                  'usage_counters', 'tenant_subscriptions', 'sys_plans', 'sys_audit_logs',
                  'system_admins']:
        op.drop_table(table)

    op.execute("DROP TYPE IF EXISTS sub_status_enum")
    op.execute("DROP TYPE IF EXISTS domain_status_enum")
    op.execute("DROP TYPE IF EXISTS prompt_status_enum")
    op.execute("DROP TYPE IF EXISTS prompt_run_status_enum")

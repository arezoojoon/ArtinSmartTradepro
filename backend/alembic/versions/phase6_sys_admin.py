"""Phase 6 System Admin Schema
Matches models in app/models/phase6.py exactly.
Table names: sys_audit_logs, sys_plans, tenant_subscriptions, usage_counters,
             whitelabel_configs, whitelabel_domains, email_templates,
             prompt_families, prompt_versions, prompt_runs, prompt_evals,
             system_settings, system_admins
"""
from alembic import op
import sqlalchemy as sa
import uuid

revision = 'phase6_sys_admin'
down_revision = 'phase5_brain_assets'
branch_labels = None
depends_on = None


def upgrade():
    # ── system_admins ───────────────────────────────────────────────────────────
    op.create_table('system_admins',
        sa.Column('id',            sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email',         sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name',          sa.String(255), nullable=True),
        sa.Column('is_active',     sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at',    sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',    sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_sys_admins_email',    'system_admins', ['email'])
    op.create_index('idx_sys_admins_active',   'system_admins', ['is_active'])

    # ── sys_audit_logs ──────────────────────────────────────────────────────────
    op.create_table('sys_audit_logs',
        sa.Column('id',                sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id',         sa.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_user_id',     sa.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_sys_admin_id',sa.UUID(as_uuid=True), nullable=True),
        sa.Column('action',            sa.String(100), nullable=False),
        sa.Column('resource_type',     sa.String(50),  nullable=False),
        sa.Column('resource_id',       sa.String(255), nullable=True),
        sa.Column('before_state',      sa.JSON(), nullable=True),
        sa.Column('after_state',       sa.JSON(), nullable=True),
        sa.Column('metadata',          sa.JSON(), nullable=True),   # Python attr: .extra
        sa.Column('ip_address',        sa.String(45),  nullable=True),
        sa.Column('user_agent',        sa.String(500), nullable=True),
        sa.Column('created_at',        sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',        sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_sys_audit_tenant',    'sys_audit_logs', ['tenant_id'])
    op.create_index('idx_sys_audit_sys_admin', 'sys_audit_logs', ['actor_sys_admin_id'])
    op.create_index('idx_sys_audit_action',    'sys_audit_logs', ['action'])
    op.create_index('idx_sys_audit_created',   'sys_audit_logs', ['created_at'])

    # ── sys_plans ───────────────────────────────────────────────────────────────
    op.create_table('sys_plans',
        sa.Column('id',                sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('code',              sa.String(50),  nullable=False, unique=True),
        sa.Column('name',              sa.String(255), nullable=False),
        sa.Column('description',       sa.Text(),  nullable=True),
        sa.Column('monthly_price_usd', sa.Numeric(10, 2), nullable=True),
        sa.Column('features',          sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('limits',            sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('is_active',         sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at',        sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',        sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_sys_plans_code',   'sys_plans', ['code'])
    op.create_index('idx_sys_plans_active', 'sys_plans', ['is_active'])

    # ── tenant_subscriptions ────────────────────────────────────────────────────
    op.create_table('tenant_subscriptions',
        sa.Column('id',                   sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id',            sa.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('plan_id',              sa.UUID(as_uuid=True), sa.ForeignKey('sys_plans.id'), nullable=False),
        sa.Column('status',               sa.Enum('active', 'past_due', 'canceled', name='sub_status_enum'), nullable=False, server_default='active'),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('current_period_end',   sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at',           sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',           sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_tenant_sub_tenant', 'tenant_subscriptions', ['tenant_id'])
    op.create_index('idx_tenant_sub_plan',   'tenant_subscriptions', ['plan_id'])

    # ── usage_counters ──────────────────────────────────────────────────────────
    op.create_table('usage_counters',
        sa.Column('id',         sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id',  sa.UUID(as_uuid=True), nullable=False),
        sa.Column('period_key', sa.String(10), nullable=False),   # "2026-02" or "2026-02-21"
        sa.Column('metric',     sa.String(50), nullable=False),
        sa.Column('value',      sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('tenant_id', 'period_key', 'metric', name='uq_usage_counters'),
    )
    op.create_index('idx_usage_tenant',     'usage_counters', ['tenant_id'])
    op.create_index('idx_usage_period',     'usage_counters', ['period_key'])
    op.create_index('idx_usage_metric',     'usage_counters', ['metric'])

    # ── whitelabel_configs ──────────────────────────────────────────────────────
    op.create_table('whitelabel_configs',
        sa.Column('id',            sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id',     sa.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('is_enabled',    sa.Boolean(), server_default='false', nullable=False),
        sa.Column('brand_name',    sa.String(255), nullable=True),
        sa.Column('logo_url',      sa.String(500), nullable=True),
        sa.Column('favicon_url',   sa.String(500), nullable=True),
        sa.Column('primary_color', sa.String(7),   nullable=True),
        sa.Column('accent_color',  sa.String(7),   nullable=True),
        sa.Column('support_email', sa.String(255), nullable=True),
        sa.Column('support_phone', sa.String(50),  nullable=True),
        sa.Column('custom_css',    sa.Text(),  nullable=True),
        sa.Column('created_at',    sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',    sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_wl_configs_tenant',  'whitelabel_configs', ['tenant_id'])
    op.create_index('idx_wl_configs_enabled', 'whitelabel_configs', ['is_enabled'])

    # ── whitelabel_domains ──────────────────────────────────────────────────────
    op.create_table('whitelabel_domains',
        sa.Column('id',                 sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id',          sa.UUID(as_uuid=True), nullable=False),
        sa.Column('domain',             sa.String(255), nullable=False, unique=True),
        sa.Column('status',             sa.Enum('pending_dns', 'active', 'disabled', name='domain_status_enum'), nullable=False, server_default='pending_dns'),
        sa.Column('verification_token', sa.String(255), nullable=True),
        sa.Column('verified_at',        sa.DateTime(timezone=True), nullable=True),
        sa.Column('config_id',          sa.UUID(as_uuid=True), sa.ForeignKey('whitelabel_configs.id'), nullable=True),
        sa.Column('created_at',         sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',         sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_wl_domains_tenant', 'whitelabel_domains', ['tenant_id'])
    op.create_index('idx_wl_domains_domain', 'whitelabel_domains', ['domain'])
    op.create_index('idx_wl_domains_status', 'whitelabel_domains', ['status'])

    # ── email_templates ─────────────────────────────────────────────────────────
    op.create_table('email_templates',
        sa.Column('id',         sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id',  sa.UUID(as_uuid=True), nullable=False),
        sa.Column('name',       sa.String(255), nullable=False),
        sa.Column('type',       sa.String(50),  nullable=False),
        sa.Column('subject',    sa.String(500), nullable=False),
        sa.Column('body',       sa.Text(), nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_email_tmpl_tenant', 'email_templates', ['tenant_id'])
    op.create_index('idx_email_tmpl_type',   'email_templates', ['type'])

    # ── prompt_families ─────────────────────────────────────────────────────────
    op.create_table('prompt_families',
        sa.Column('id',          sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name',        sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category',    sa.String(50), nullable=False, server_default='general'),
        sa.Column('is_active',   sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at',  sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',  sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_prompt_fam_name',     'prompt_families', ['name'])
    op.create_index('idx_prompt_fam_category', 'prompt_families', ['category'])

    # ── prompt_versions ─────────────────────────────────────────────────────────
    op.create_table('prompt_versions',
        sa.Column('id',                   sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('family_id',            sa.UUID(as_uuid=True), sa.ForeignKey('prompt_families.id'), nullable=False),
        sa.Column('version',              sa.Integer(), nullable=False),
        sa.Column('status',               sa.Enum('draft', 'approved', 'deprecated', name='prompt_status_enum'), nullable=False, server_default='draft'),
        sa.Column('model_target',         sa.String(100), nullable=False, server_default='gemini-1.5-pro'),
        sa.Column('system_prompt',        sa.Text(), nullable=False),
        sa.Column('user_prompt_template', sa.Text(), nullable=False),
        sa.Column('guardrails',           sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_by',           sa.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by',          sa.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at',          sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at',           sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',           sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('family_id', 'version', name='uq_prompt_family_version'),
    )
    op.create_index('idx_prompt_ver_family', 'prompt_versions', ['family_id'])
    op.create_index('idx_prompt_ver_status', 'prompt_versions', ['status'])

    # ── prompt_runs ─────────────────────────────────────────────────────────────
    op.create_table('prompt_runs',
        sa.Column('id',                sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id',         sa.UUID(as_uuid=True), nullable=False),
        sa.Column('family_name',       sa.String(255), nullable=False),
        sa.Column('version',           sa.Integer(), nullable=False),
        sa.Column('prompt_version_id', sa.UUID(as_uuid=True), sa.ForeignKey('prompt_versions.id'), nullable=True),
        sa.Column('engine_run_id',     sa.UUID(as_uuid=True), nullable=True),
        sa.Column('input',             sa.JSON(), nullable=False),
        sa.Column('output',            sa.JSON(), nullable=True),
        sa.Column('token_usage',       sa.JSON(), nullable=True),
        sa.Column('guardrail_result',  sa.JSON(), nullable=True),
        sa.Column('status',            sa.Enum('success', 'guardrail_rejected', 'error', name='prompt_run_status_enum'), nullable=False, server_default='success'),
        sa.Column('error_message',     sa.Text(), nullable=True),
        sa.Column('created_at',        sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',        sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_prompt_run_tenant',  'prompt_runs', ['tenant_id'])
    op.create_index('idx_prompt_run_family',  'prompt_runs', ['family_name'])
    op.create_index('idx_prompt_run_status',  'prompt_runs', ['status'])
    op.create_index('idx_prompt_run_created', 'prompt_runs', ['created_at'])

    # ── prompt_evals ────────────────────────────────────────────────────────────
    op.create_table('prompt_evals',
        sa.Column('id',                sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('family_id',         sa.UUID(as_uuid=True), sa.ForeignKey('prompt_families.id'), nullable=False),
        sa.Column('version',           sa.Integer(), nullable=False),
        sa.Column('prompt_version_id', sa.UUID(as_uuid=True), sa.ForeignKey('prompt_versions.id'), nullable=True),
        sa.Column('test_name',         sa.String(255), nullable=False),
        sa.Column('input',             sa.JSON(), nullable=False),
        sa.Column('expected_rules',    sa.JSON(), nullable=False),
        sa.Column('last_status',       sa.String(20),  nullable=True),
        sa.Column('last_result',       sa.JSON(), nullable=True),
        sa.Column('last_run_at',       sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at',        sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',        sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_prompt_eval_family',  'prompt_evals', ['family_id'])
    op.create_index('idx_prompt_eval_version', 'prompt_evals', ['version'])

    # ── system_settings ─────────────────────────────────────────────────────────
    op.create_table('system_settings',
        sa.Column('id',           sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('key',          sa.String(100), nullable=False, unique=True),
        sa.Column('value',        sa.JSON(), nullable=False),
        sa.Column('description',  sa.Text(), nullable=True),
        sa.Column('is_sensitive', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at',   sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',   sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_sys_settings_key', 'system_settings', ['key'])

    # ── RLS for tenant-scoped tables ───────────────────────────────────────────
    for table in ['whitelabel_configs', 'whitelabel_domains', 'email_templates', 'usage_counters']:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            FOR ALL TO authenticated_users
            USING (tenant_id = app.current_tenant_id())
            WITH CHECK (tenant_id = app.current_tenant_id())
        """)

    # ── Default plans ──────────────────────────────────────────────────────────
    op.execute("""
    INSERT INTO sys_plans (id, code, name, description, monthly_price_usd, features, limits) VALUES
    (gen_random_uuid(), 'starter', 'Starter', 'Basic plan for small teams', 0.00,
     '{"brain_engines": true, "hunter": true, "messaging": true, "api_access": true}',
     '{"messages_sent_daily": 100, "leads_created_monthly": 50, "brain_runs_daily": 10, "seats": 2}'),
    (gen_random_uuid(), 'professional', 'Professional', 'Advanced features for growing teams', 299.00,
     '{"brain_engines": true, "hunter": true, "messaging": true, "api_access": true, "whitelabel": false}',
     '{"messages_sent_daily": 500, "leads_created_monthly": 200, "brain_runs_daily": 50, "seats": 5}'),
    (gen_random_uuid(), 'enterprise', 'Enterprise', 'Full-featured for large organizations', 999.00,
     '{"brain_engines": true, "hunter": true, "messaging": true, "api_access": true, "whitelabel": true, "priority_support": true}',
     '{"messages_sent_daily": 5000, "leads_created_monthly": 2000, "brain_runs_daily": 500, "seats": 25}'),
    (gen_random_uuid(), 'whitelabel', 'White-Label', 'Custom branding + reseller', 2999.00,
     '{"brain_engines": true, "hunter": true, "messaging": true, "api_access": true, "whitelabel": true, "priority_support": true, "custom_domains": true}',
     '{"messages_sent_daily": -1, "leads_created_monthly": -1, "brain_runs_daily": -1, "seats": -1}')
    ON CONFLICT (code) DO NOTHING
    """)

    # ── Default prompt families ─────────────────────────────────────────────────
    op.execute("""
    INSERT INTO prompt_families (id, name, description, category) VALUES
    (gen_random_uuid(), 'cultural_strategy', 'Cultural negotiation and strategy per buyer country', 'brain'),
    (gen_random_uuid(), 'lead_reply',        'AI-generated lead response messages',                 'messaging'),
    (gen_random_uuid(), 'report_summary',    'Business intelligence report summaries',              'analytics'),
    (gen_random_uuid(), 'arbitrage_insight', 'Trade arbitrage opportunity explanations',            'brain'),
    (gen_random_uuid(), 'risk_summary',      'Country and route risk summaries',                    'brain')
    ON CONFLICT (name) DO NOTHING
    """)

    # ── Default system settings ─────────────────────────────────────────────────
    op.execute("""
    INSERT INTO system_settings (key, value, description, is_sensitive) VALUES
    ('dlq_threshold',  '{"messages": 1000, "hunter_jobs": 100}', 'DLQ alert thresholds', false),
    ('prompt_ops',     '{"guardrails_enabled": true, "auto_approve": false}', 'Prompt Ops defaults', false),
    ('security',       '{"ip_allowlist": [], "require_2fa": false}', 'Security settings', true)
    ON CONFLICT (key) DO NOTHING
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

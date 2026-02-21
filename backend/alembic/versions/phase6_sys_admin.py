"""Phase 6 System Admin Schema
System administrators, audit logging, and RLS bypass infrastructure
"""
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers
revision = 'phase6_sys_admin'
down_revision = 'phase5_brain_assets'
branch_labels = None
depends_on = None

def upgrade():
    # Create system_admins table
    op.create_table('system_admins',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), server_default='admin', nullable=False)
    )
    
    # Indexes for system_admins
    op.create_index('idx_system_admins_email', 'system_admins', ['email'])
    op.create_index('idx_system_admins_active', 'system_admins', ['is_active'])
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('actor_user_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_sys_admin_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('before_state', sa.JSON(), nullable=True),
        sa.Column('after_state', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Indexes for audit_logs
    op.create_index('idx_audit_logs_tenant', 'audit_logs', ['tenant_id'])
    op.create_index('idx_audit_logs_actor_sys', 'audit_logs', ['actor_sys_admin_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    
    # Create plans table (global)
    op.create_table('plans',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('code', sa.String(length=50), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('monthly_price_usd', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('features', sa.JSON(), nullable=True),
        sa.Column('limits', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Indexes for plans
    op.create_index('idx_plans_code', 'plans', ['code'])
    op.create_index('idx_plans_active', 'plans', ['is_active'])
    
    # Create tenant_subscriptions table
    op.create_table('tenant_subscriptions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('plan_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('active', 'past_due', 'canceled', name='subscription_status'), nullable=False),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Foreign key constraint for tenant_subscriptions
    op.create_foreign_key('fk_tenant_subscriptions_plan', 'tenant_subscriptions', 'plans', ['plan_id'], ['id'])
    
    # Indexes for tenant_subscriptions
    op.create_index('idx_tenant_subscriptions_tenant', 'tenant_subscriptions', ['tenant_id'])
    op.create_index('idx_tenant_subscriptions_plan', 'tenant_subscriptions', ['plan_id'])
    op.create_index('idx_tenant_subscriptions_status', 'tenant_subscriptions', ['status'])
    
    # Create usage_counters table
    op.create_table('usage_counters',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('period_key', sa.String(length=7), nullable=False),  # YYYY-MM format
        sa.Column('metric', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Integer(), server_default='0', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Unique constraint for usage_counters
    op.create_unique_constraint('uq_usage_counters_period', 'usage_counters', 
                              ['tenant_id', 'period_key', 'metric'])
    
    # Indexes for usage_counters
    op.create_index('idx_usage_counters_tenant', 'usage_counters', ['tenant_id'])
    op.create_index('idx_usage_counters_period', 'usage_counters', ['period_key'])
    op.create_index('idx_usage_counters_metric', 'usage_counters', ['metric'])
    
    # Create whitelabel_configs table
    op.create_table('whitelabel_configs',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('is_enabled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('brand_name', sa.String(length=255), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('primary_color', sa.String(length=7), nullable=True),  # Hex color
        sa.Column('accent_color', sa.String(length=7), nullable=True),  # Hex color
        sa.Column('support_email', sa.String(length=255), nullable=True),
        sa.Column('support_phone', sa.String(length=50), nullable=True),
        sa.Column('custom_css', sa.Text(), nullable=True),
        sa.Column('favicon_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Indexes for whitelabel_configs
    op.create_index('idx_whitelabel_configs_tenant', 'whitelabel_configs', ['tenant_id'])
    op.create_index('idx_whitelabel_configs_enabled', 'whitelabel_configs', ['is_enabled'])
    
    # Create whitelabel_domains table
    op.create_table('whitelabel_domains',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False, unique=True),
        sa.Column('status', sa.Enum('pending_dns', 'active', 'disabled', name='domain_status'), nullable=False),
        sa.Column('verification_token', sa.String(length=255), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dns_check_required', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Indexes for whitelabel_domains
    op.create_index('idx_whitelabel_domains_tenant', 'whitelabel_domains', ['tenant_id'])
    op.create_index('idx_whitelabel_domains_domain', 'whitelabel_domains', ['domain'])
    op.create_index('idx_whitelabel_domains_status', 'whitelabel_domains', ['status'])
    
    # Create email_templates table
    op.create_table('email_templates',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),  # welcome, notification, etc.
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Indexes for email_templates
    op.create_index('idx_email_templates_tenant', 'email_templates', ['tenant_id'])
    op.create_index('idx_email_templates_type', 'email_templates', ['type'])
    
    # Create prompt_families table
    op.create_table('prompt_families',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(length=255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Indexes for prompt_families
    op.create_index('idx_prompt_families_name', 'prompt_families', ['name'])
    op.create_index('idx_prompt_families_category', 'prompt_families', ['category'])
    
    # Create prompt_versions table
    op.create_table('prompt_versions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('family_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('draft', 'approved', 'deprecated', name='prompt_version_status'), nullable=False),
        sa.Column('model_target', sa.String(length=100), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('user_prompt_template', sa.Text(), nullable=False),
        sa.Column('guardrails', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Foreign key constraint for prompt_versions
    op.create_foreign_key('fk_prompt_versions_family', 'prompt_versions', 'prompt_families', ['family_id'], ['id'])
    
    # Unique constraint for prompt_versions
    op.create_unique_constraint('uq_prompt_versions_family_version', 'prompt_versions', 
                              ['family_id', 'version'])
    
    # Indexes for prompt_versions
    op.create_index('idx_prompt_versions_family', 'prompt_versions', ['family_id'])
    op.create_index('idx_prompt_versions_status', 'prompt_versions', ['status'])
    op.create_index('idx_prompt_versions_created_by', 'prompt_versions', ['created_by'])
    
    # Create prompt_runs table
    op.create_table('prompt_runs',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('family_name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('engine_run_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('input', sa.JSON(), nullable=False),
        sa.Column('output', sa.JSON(), nullable=True),
        sa.Column('token_usage', sa.JSON(), nullable=True),
        sa.Column('guardrail_result', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('success', 'failed', 'guardrail_rejected', name='prompt_run_status'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Indexes for prompt_runs
    op.create_index('idx_prompt_runs_tenant', 'prompt_runs', ['tenant_id'])
    op.create_index('idx_prompt_runs_family', 'prompt_runs', ['family_name'])
    op.create_index('idx_prompt_runs_status', 'prompt_runs', ['status'])
    op.create_index('idx_prompt_runs_created_at', 'prompt_runs', ['created_at'])
    
    # Create prompt_evals table
    op.create_table('prompt_evals',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('family_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('test_name', sa.String(length=255), nullable=False),
        sa.Column('input', sa.JSON(), nullable=False),
        sa.Column('expected_rules', sa.JSON(), nullable=False),
        sa.Column('status', sa.Enum('passed', 'failed', 'skipped', name='eval_status'), nullable=False),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Foreign key constraint for prompt_evals
    op.create_foreign_key('fk_prompt_evals_family', 'prompt_evals', 'prompt_families', ['family_id'], ['id'])
    
    # Indexes for prompt_evals
    op.create_index('idx_prompt_evals_family', 'prompt_evals', ['family_id'])
    op.create_index('idx_prompt_evals_version', 'prompt_evals', ['version'])
    op.create_index('idx_prompt_evals_status', 'prompt_evals', ['status'])
    
    # Create system_settings table for configuration
    op.create_table('system_settings',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('key', sa.String(length=100), nullable=False, unique=True),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_sensitive', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Indexes for system_settings
    op.create_index('idx_system_settings_key', 'system_settings', ['key'])
    
    # Enable RLS on tenant tables (system admin tables don't need RLS)
    for table in ['whitelabel_configs', 'whitelabel_domains', 'email_templates', 'usage_counters']:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        
        # Create RLS policies for tenant tables
        op.execute(f"""
        CREATE POLICY tenant_isolation_{table} ON {table}
        FOR ALL TO authenticated_users
        USING (tenant_id = app.current_tenant_id())
        WITH CHECK (tenant_id = app.current_tenant_id())
        """)
    
    # Insert default plans
    op.execute("""
    INSERT INTO plans (id, code, name, description, monthly_price_usd, features, limits) VALUES
    (gen_random_uuid(), 'starter', 'Starter', 'Basic plan for small teams', 0.00,
     '{"brain_engines": true, "hunter": true, "messaging": true, "api_access": true}',
     '{"leads_per_month": 100, "messages_per_day": 1000, "brain_runs_per_month": 500, "users": 5}'),
    
    (gen_random_uuid(), 'professional', 'Professional', 'Advanced features for growing teams', 99.00,
     '{"brain_engines": true, "hunter": true, "messaging": true, "api_access": true, "whitelabel": true}',
     '{"leads_per_month": 1000, "messages_per_day": 10000, "brain_runs_per_month": 5000, "users": 25}'),
    
    (gen_random_uuid(), 'enterprise', 'Enterprise', 'Full-featured plan for large organizations', 499.00,
     '{"brain_engines": true, "hunter": true, "messaging": true, "api_access": true, "whitelabel": true, "priority_support": true}',
     '{"leads_per_month": 10000, "messages_per_day": 100000, "brain_runs_per_month": 50000, "users": 100}'),
    
    (gen_random_uuid(), 'whitelabel', 'White-label', 'Custom branding and domain mapping', 999.00,
     '{"brain_engines": true, "hunter": true, "messaging": true, "api_access": true, "whitelabel": true, "priority_support": true, "custom_domains": true}',
     '{"leads_per_month": 50000, "messages_per_day": 500000, "brain_runs_per_month": 250000, "users": 500}')
    ON CONFLICT (code) DO NOTHING
    """)
    
    # Insert default system settings
    op.execute("""
    INSERT INTO system_settings (key, value, description, is_sensitive) VALUES
    ('dlq_threshold', '{"messages": 1000, "hunter_jobs": 100}', 'DLQ alert thresholds', false),
    ('rate_limits', '{"sys_admin": 1000, "tenant_api": 10000}', 'Rate limit settings', false),
    ('security', '{"ip_allowlist": [], "require_2fa": false}', 'Security settings', true),
    ('prompt_ops', '{"guardrails_enabled": true, "auto_approve": false}', 'Prompt operations settings', false)
    ON CONFLICT (key) DO NOTHING
    """)
    
    # Insert default prompt families
    op.execute("""
    INSERT INTO prompt_families (id, name, description, category) VALUES
    (gen_random_uuid(), 'cultural_strategy', 'Cultural strategy and negotiation templates', 'brain'),
    (gen_random_uuid(), 'lead_reply', 'Automated lead response generation', 'messaging'),
    (gen_random_uuid(), 'report_summary', 'Business intelligence and reporting summaries', 'analytics'),
    (gen_random_uuid(), 'email_template', 'Email template generation', 'communication')
    ON CONFLICT (name) DO NOTHING
    """)

def downgrade():
    # Drop tables in reverse order
    for table in ['system_settings', 'prompt_evals', 'prompt_runs', 'prompt_versions', 'prompt_families', 
                   'email_templates', 'whitelabel_domains', 'whitelabel_configs', 'usage_counters', 
                   'tenant_subscriptions', 'plans', 'audit_logs', 'system_admins']:
        op.drop_table(table)
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS subscription_status")
    op.execute("DROP TYPE IF EXISTS domain_status")
    op.execute("DROP TYPE IF EXISTS prompt_version_status")
    op.execute("DROP TYPE IF EXISTS prompt_run_status")
    op.execute("DROP TYPE IF EXISTS eval_status")

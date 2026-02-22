-- =============================================================================
-- Artin Smart Trade - Database Initialization Script
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create database user (if not exists)
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'artin_user') THEN
      CREATE ROLE artin_user LOGIN PASSWORD 'secure_password';
   END IF;
END
$$;

-- Grant permissions to application user
GRANT CONNECT ON DATABASE artin_smart_trade TO artin_user;
GRANT USAGE ON SCHEMA public TO artin_user;
GRANT CREATE ON SCHEMA public TO artin_user;

-- Enable Row Level Security
ALTER DATABASE artin_smart_trade SET row_level_security = on;

-- Create custom types
CREATE TYPE IF NOT EXISTS user_role AS ENUM (
    'super_admin',
    'tenant_admin',
    'trade_manager',
    'sales_rep',
    'viewer'
);

CREATE TYPE IF NOT EXISTS deal_status AS ENUM (
    'lead',
    'qualified',
    'negotiating',
    'proposal',
    'closed_won',
    'closed_lost',
    'on_hold'
);

CREATE TYPE IF NOT EXISTS deal_stage AS ENUM (
    'lead',
    'qualified',
    'proposal',
    'negotiating',
    'closing',
    'closed'
);

CREATE TYPE IF NOT EXISTS subscription_plan AS ENUM (
    'starter',
    'professional',
    'enterprise'
);

CREATE TYPE IF NOT EXISTS subscription_status AS ENUM (
    'active',
    'cancelled',
    'past_due',
    'unpaid'
);

CREATE TYPE IF NOT EXISTS notification_type AS ENUM (
    'info',
    'success',
    'warning',
    'error'
);

CREATE TYPE IF NOT EXISTS audit_action AS ENUM (
    'create',
    'update',
    'delete',
    'login',
    'logout',
    'view'
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_tenants_domain ON tenants(domain);
CREATE INDEX IF NOT EXISTS idx_tenants_plan ON tenants(plan);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);

CREATE INDEX IF NOT EXISTS idx_deals_tenant_id ON deals(tenant_id);
CREATE INDEX IF NOT EXISTS idx_deals_assigned_to ON deals(assigned_to);
CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);
CREATE INDEX IF NOT EXISTS idx_deals_stage ON deals(stage);
CREATE INDEX IF NOT EXISTS idx_deals_created_at ON deals(created_at);
CREATE INDEX IF NOT EXISTS idx_deals_total_value ON deals(total_value);

CREATE INDEX IF NOT EXISTS idx_contacts_tenant_id ON contacts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_company_id ON contacts(company_id);

CREATE INDEX IF NOT EXISTS idx_companies_tenant_id ON companies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);

CREATE INDEX IF NOT EXISTS idx_milestones_deal_id ON milestones(deal_id);
CREATE INDEX IF NOT EXISTS idx_milestones_due_date ON milestones(due_date);
CREATE INDEX IF NOT EXISTS idx_milestones_status ON milestones(status);

CREATE INDEX IF NOT EXISTS idx_wallets_tenant_id ON wallets(tenant_id);
CREATE INDEX IF NOT EXISTS idx_wallets_currency ON wallets(currency);

CREATE INDEX IF NOT EXISTS idx_transactions_tenant_id ON transactions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_transactions_wallet_id ON transactions(wallet_id);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);

CREATE INDEX IF NOT EXISTS idx_subscriptions_tenant_id ON subscriptions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_plan ON subscriptions(plan);

CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_id ON audit_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_notifications_tenant_id ON notifications(tenant_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_read_at ON notifications(read_at);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_deals_search ON deals USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));
CREATE INDEX IF NOT EXISTS idx_contacts_search ON contacts USING gin(to_tsvector('english', first_name || ' ' || last_name || ' ' || COALESCE(email, '') || ' ' || COALESCE(company_name, '')));
CREATE INDEX IF NOT EXISTS idx_companies_search ON companies USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));

-- Create trigger functions for audit logging
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (tenant_id, user_id, action, table_name, record_id, old_values, new_values)
        VALUES (
            COALESCE(NEW.tenant_id, 'system'),
            COALESCE(current_setting('app.current_user_id', true), 'system'),
            'create',
            TG_TABLE_NAME,
            COALESCE(NEW.id, uuid_generate_v4()),
            NULL,
            row_to_json(NEW)
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (tenant_id, user_id, action, table_name, record_id, old_values, new_values)
        VALUES (
            COALESCE(NEW.tenant_id, 'system'),
            COALESCE(current_setting('app.current_user_id', true), 'system'),
            'update',
            TG_TABLE_NAME,
            NEW.id,
            row_to_json(OLD),
            row_to_json(NEW)
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (tenant_id, user_id, action, table_name, record_id, old_values, new_values)
        VALUES (
            COALESCE(OLD.tenant_id, 'system'),
            COALESCE(current_setting('app.current_user_id', true), 'system'),
            'delete',
            TG_TABLE_NAME,
            OLD.id,
            row_to_json(OLD),
            NULL
        );
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create RLS policies
-- Users table policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY users_tenant_policy ON users
    FOR ALL
    TO artin_user
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY users_self_policy ON users
    FOR SELECT
    TO artin_user
    USING (id = current_setting('app.current_user_id', true)::uuid);

-- Deals table policies
ALTER TABLE deals ENABLE ROW LEVEL SECURITY;

CREATE POLICY deals_tenant_policy ON deals
    FOR ALL
    TO artin_user
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Contacts table policies
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

CREATE POLICY contacts_tenant_policy ON contacts
    FOR ALL
    TO artin_user
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Companies table policies
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;

CREATE POLICY companies_tenant_policy ON companies
    FOR ALL
    TO artin_user
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Create function for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_deals_updated_at BEFORE UPDATE ON deals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create audit triggers
CREATE TRIGGER audit_users_trigger
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_deals_trigger
    AFTER INSERT OR UPDATE OR DELETE ON deals
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_contacts_trigger
    AFTER INSERT OR UPDATE OR DELETE ON contacts
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_companies_trigger
    AFTER INSERT OR UPDATE OR DELETE ON companies
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Create function for deal value calculation
CREATE OR REPLACE FUNCTION calculate_deal_margin(deal_id UUID)
RETURNS DECIMAL(10,2) AS $$
DECLARE
    deal_cost DECIMAL(10,2);
    deal_value DECIMAL(10,2);
    margin DECIMAL(10,2);
BEGIN
    SELECT total_value, estimated_cost INTO deal_value, deal_cost
    FROM deals WHERE id = deal_id;
    
    IF deal_value IS NULL OR deal_cost IS NULL OR deal_value = 0 THEN
        RETURN 0;
    END IF;
    
    margin := ((deal_value - deal_cost) / deal_value) * 100;
    RETURN ROUND(margin, 2);
END;
$$ LANGUAGE plpgsql;

-- Create function for tenant statistics
CREATE OR REPLACE FUNCTION get_tenant_statistics(tenant_uuid UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_deals', COUNT(*),
        'active_deals', COUNT(*) FILTER (WHERE status IN ('lead', 'qualified', 'negotiating', 'proposal')),
        'won_deals', COUNT(*) FILTER (WHERE status = 'closed_won'),
        'lost_deals', COUNT(*) FILTER (WHERE status = 'closed_lost'),
        'total_value', COALESCE(SUM(total_value), 0),
        'average_deal_value', COALESCE(AVG(total_value), 0),
        'total_users', (SELECT COUNT(*) FROM users WHERE tenant_id = tenant_uuid AND is_active = true),
        'created_at', (SELECT created_at FROM tenants WHERE id = tenant_uuid)
    ) INTO result
    FROM deals WHERE tenant_id = tenant_uuid;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Create function for user activity tracking
CREATE OR REPLACE FUNCTION track_user_activity(user_id UUID, action_type TEXT, details JSONB DEFAULT NULL)
RETURNS VOID AS $$
BEGIN
    INSERT INTO user_activities (user_id, action, details, created_at)
    VALUES (user_id, action_type, details, CURRENT_TIMESTAMP);
END;
$$ LANGUAGE plpgsql;

-- Create view for active deals summary
CREATE OR REPLACE VIEW active_deals_summary AS
SELECT 
    d.id,
    d.title,
    d.total_value,
    d.status,
    d.stage,
    d.created_at,
    d.updated_at,
    c.name as company_name,
    u.full_name as assigned_user,
    COALESCE(m.completed_count, 0) as completed_milestones,
    COALESCE(m.total_count, 0) as total_milestones
FROM deals d
LEFT JOIN companies c ON d.buyer_company_id = c.id
LEFT JOIN users u ON d.assigned_to = u.id
LEFT JOIN (
    SELECT 
        deal_id,
        COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
        COUNT(*) as total_count
    FROM milestones 
    GROUP BY deal_id
) m ON d.id = m.deal_id
WHERE d.status IN ('lead', 'qualified', 'negotiating', 'proposal');

-- Create view for tenant metrics
CREATE OR REPLACE VIEW tenant_metrics AS
SELECT 
    t.id as tenant_id,
    t.name as tenant_name,
    t.plan,
    t.status,
    COUNT(DISTINCT u.id) as total_users,
    COUNT(DISTINCT u.id) FILTER (WHERE u.is_active = true) as active_users,
    COUNT(DISTINCT d.id) as total_deals,
    COUNT(DISTINCT d.id) FILTER (WHERE d.status = 'closed_won') as won_deals,
    COALESCE(SUM(d.total_value), 0) as total_deal_value,
    COALESCE(SUM(d.total_value) FILTER (WHERE d.status = 'closed_won'), 0) as won_deal_value,
    COALESCE(AVG(d.total_value), 0) as average_deal_value,
    t.created_at as tenant_created_at,
    MAX(d.created_at) as last_deal_created
FROM tenants t
LEFT JOIN users u ON t.id = u.tenant_id
LEFT JOIN deals d ON t.id = d.tenant_id
GROUP BY t.id, t.name, t.plan, t.status, t.created_at;

-- Create function for data cleanup
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete audit logs older than 1 year
    DELETE FROM audit_logs WHERE created_at < CURRENT_DATE - INTERVAL '1 year';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Delete user activities older than 6 months
    DELETE FROM user_activities WHERE created_at < CURRENT_DATE - INTERVAL '6 months';
    
    -- Delete old notifications (read and older than 30 days)
    DELETE FROM notifications WHERE read_at IS NOT NULL AND read_at < CURRENT_DATE - INTERVAL '30 days';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create scheduled job for cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-old-data', '0 2 * * *', 'SELECT cleanup_old_data();');

-- Grant permissions to application user for views and functions
GRANT SELECT ON active_deals_summary TO artin_user;
GRANT SELECT ON tenant_metrics TO artin_user;
GRANT EXECUTE ON FUNCTION calculate_deal_margin(UUID) TO artin_user;
GRANT EXECUTE ON FUNCTION get_tenant_statistics(UUID) TO artin_user;
GRANT EXECUTE ON FUNCTION track_user_activity(UUID, TEXT, JSONB) TO artin_user;
GRANT EXECUTE ON FUNCTION cleanup_old_data() TO artin_user;

-- Insert initial system data
INSERT INTO system_settings (key, value, description) VALUES
('app_version', '2.0.0', 'Current application version'),
('maintenance_mode', 'false', 'Whether the application is in maintenance mode'),
('max_upload_size', '52428800', 'Maximum file upload size in bytes'),
('default_timezone', 'UTC', 'Default timezone for the application'),
('session_timeout', '900', 'Session timeout in seconds')
ON CONFLICT (key) DO NOTHING;

-- Create default admin user (will be created by deployment script)
-- This is commented out to avoid conflicts with the deployment script
-- INSERT INTO system_admins (email, full_name, hashed_password, is_active)
-- VALUES ('admin@artin-smart-trade.com', 'Super Admin', '$2b$12$...', true)
-- ON CONFLICT (email) DO NOTHING;

-- Log initialization completion
DO $$
BEGIN
    RAISE NOTICE 'Artin Smart Trade database initialized successfully';
    RAISE NOTICE 'Extensions: uuid-ossp, pg_trgm, pg_stat_statements';
    RAISE NOTICE 'Indexes created for performance optimization';
    RAISE NOTICE 'Row Level Security enabled';
    RAISE NOTICE 'Audit logging configured';
    RAISE NOTICE 'System functions and views created';
END $$;

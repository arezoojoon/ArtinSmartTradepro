-- Database Schema for Artin Smart Trade CRM (v3.2)
-- Includes: Auth, Multi-Tenancy, Billing, CRM Core, WhatsApp, Conversations, Campaigns, Follow-Ups

-- 1. Tenants
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR,
    tenant_id UUID REFERENCES tenants(id),
    role VARCHAR DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Verification Tokens
CREATE TABLE IF NOT EXISTS verification_tokens (
    token VARCHAR PRIMARY KEY,
    email VARCHAR NOT NULL,
    expires_at TIMESTAMP NOT NULL
);

-- 4. Wallets
CREATE TABLE IF NOT EXISTS wallets (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    balance NUMERIC(12, 2) DEFAULT 0.00,
    currency VARCHAR DEFAULT 'USD',
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 5. Wallet Transactions
CREATE TABLE IF NOT EXISTS wallet_transactions (
    id UUID PRIMARY KEY,
    wallet_id UUID NOT NULL REFERENCES wallets(id),
    amount NUMERIC(12, 2) NOT NULL,
    type VARCHAR NOT NULL, -- credit, debit
    description VARCHAR,
    reference_id VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Plans
CREATE TABLE IF NOT EXISTS plans (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    price_monthly NUMERIC(12, 2) NOT NULL,
    description TEXT,
    features JSONB -- Helper for list of features
);

-- 7. Subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    plan_id UUID REFERENCES plans(id),
    status VARCHAR DEFAULT 'active',
    current_period_end TIMESTAMP,
    stripe_subscription_id VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

-- CRM Core
-- 8. CRM Companies
CREATE TABLE IF NOT EXISTS crm_companies (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR NOT NULL,
    domain VARCHAR,
    industry VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 9. CRM Contacts
CREATE TABLE IF NOT EXISTS crm_contacts (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    first_name VARCHAR,
    last_name VARCHAR,
    email VARCHAR,
    phone VARCHAR,
    company_id UUID REFERENCES crm_companies(id),
    position VARCHAR,
    source VARCHAR,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 10. CRM Pipelines
CREATE TABLE IF NOT EXISTS crm_pipelines (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR NOT NULL,
    stages JSONB DEFAULT '[]', -- List of stage names
    created_at TIMESTAMP DEFAULT NOW()
);

-- 11. CRM Deals
CREATE TABLE IF NOT EXISTS crm_deals (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    pipeline_id UUID REFERENCES crm_pipelines(id),
    stage_id VARCHAR, -- ID/Name of stage in pipeline
    name VARCHAR NOT NULL,
    value NUMERIC(12, 2),
    contact_id UUID REFERENCES crm_contacts(id),
    company_id UUID REFERENCES crm_companies(id),
    status VARCHAR DEFAULT 'open', -- open, won, lost
    created_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP
);

-- 12. CRM Notes
CREATE TABLE IF NOT EXISTS crm_notes (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    entity_type VARCHAR NOT NULL, -- contact, deal, company
    entity_id UUID NOT NULL,
    content TEXT NOT NULL,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 13. CRM Tags
CREATE TABLE IF NOT EXISTS crm_tags (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR NOT NULL,
    color VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 14. WhatsApp Messages
CREATE TABLE IF NOT EXISTS whatsapp_messages (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    recipient_phone VARCHAR NOT NULL,
    direction VARCHAR DEFAULT 'outbound',
    status VARCHAR DEFAULT 'queued',
    content TEXT,
    template_name VARCHAR,
    message_id VARCHAR,
    cost NUMERIC(12, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 15. Leads (Scraped)
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    source VARCHAR,
    data JSONB,
    status VARCHAR DEFAULT 'new',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 16. Scraped Sources
CREATE TABLE IF NOT EXISTS scraped_sources (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    url VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'pending',
    result_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 17. Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    action VARCHAR NOT NULL,
    resource_type VARCHAR,
    resource_id VARCHAR,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 18. CRM Conversations (Phase C2)
CREATE TABLE IF NOT EXISTS crm_conversations (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    contact_id UUID REFERENCES crm_contacts(id),
    channel VARCHAR DEFAULT 'whatsapp',
    identifier VARCHAR NOT NULL,
    subject VARCHAR,
    last_message_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR DEFAULT 'open',
    unread_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_crm_conversations_tenant ON crm_conversations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_crm_conversations_identifier ON crm_conversations(identifier);

-- Update WhatsApp messages to link to conversations
ALTER TABLE whatsapp_messages ADD COLUMN IF NOT EXISTS conversation_id UUID REFERENCES crm_conversations(id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_conversation ON whatsapp_messages(conversation_id);

-- 19. CRM Campaigns (Phase C3)
CREATE TABLE IF NOT EXISTS crm_campaigns (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'draft',
    channel VARCHAR DEFAULT 'whatsapp',
    template_body TEXT,
    total_contacts INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_crm_campaigns_status ON crm_campaigns(status);

-- 20. CRM Campaign Segments
CREATE TABLE IF NOT EXISTS crm_campaign_segments (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES crm_campaigns(id),
    filter_json JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 21. CRM Campaign Messages
CREATE TABLE IF NOT EXISTS crm_campaign_messages (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES crm_campaigns(id),
    contact_id UUID NOT NULL REFERENCES crm_contacts(id),
    whatsapp_message_id UUID REFERENCES whatsapp_messages(id),
    status VARCHAR DEFAULT 'pending', -- pending, sent, failed
    sent_at TIMESTAMP,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_crm_campaign_messages_status ON crm_campaign_messages(status);
CREATE INDEX IF NOT EXISTS idx_crm_campaign_messages_contact ON crm_campaign_messages(contact_id);

-- 22. CRM Follow-Up Rules (Phase C4)
CREATE TABLE IF NOT EXISTS crm_followup_rules (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR NOT NULL,
    trigger_event VARCHAR DEFAULT 'no_reply',
    delay_minutes INTEGER DEFAULT 1440,
    max_attempts INTEGER DEFAULT 1,
    channel VARCHAR DEFAULT 'whatsapp',
    template_body TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_crm_followup_rules_tenant ON crm_followup_rules(tenant_id);

-- 23. CRM Follow-Up Executions (Phase C4)
CREATE TABLE IF NOT EXISTS crm_followup_executions (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    rule_id UUID REFERENCES crm_followup_rules(id),
    contact_id UUID NOT NULL REFERENCES crm_contacts(id),
    campaign_id UUID REFERENCES crm_campaigns(id),
    conversation_id UUID REFERENCES crm_conversations(id),
    attempt INTEGER DEFAULT 1,
    status VARCHAR DEFAULT 'scheduled', -- scheduled, sent, cancelled, failed
    scheduled_at TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_crm_followup_executions_tenant ON crm_followup_executions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_crm_followup_executions_scheduled ON crm_followup_executions(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_crm_followup_executions_status ON crm_followup_executions(status);
CREATE INDEX IF NOT EXISTS idx_crm_followup_executions_contact ON crm_followup_executions(contact_id);

-- 24. CRM Revenue Attribution (Phase C4)
CREATE TABLE IF NOT EXISTS crm_revenue_attributions (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    deal_id UUID NOT NULL REFERENCES crm_deals(id),
    campaign_id UUID REFERENCES crm_campaigns(id),
    message_id VARCHAR,
    attribution_type VARCHAR DEFAULT 'last_touch',
    amount NUMERIC(12, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_crm_revenue_deal ON crm_revenue_attributions(deal_id);
CREATE INDEX IF NOT EXISTS idx_crm_revenue_campaign ON crm_revenue_attributions(campaign_id);

-- 25. CRM Voice Recordings (Phase D1 — Hardened)
CREATE TABLE IF NOT EXISTS crm_voice_recordings (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    contact_id UUID REFERENCES crm_contacts(id),
    file_path VARCHAR NOT NULL,
    file_name VARCHAR,
    file_hash VARCHAR,  -- SHA256 for idempotency
    duration_seconds INTEGER,
    file_size_bytes INTEGER,
    mime_type VARCHAR DEFAULT 'audio/wav',
    credit_cost NUMERIC(6,2) DEFAULT 5.0,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_crm_voice_recordings_tenant ON crm_voice_recordings(tenant_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_crm_voice_recordings_hash ON crm_voice_recordings(tenant_id, file_hash);

-- 30. Trade Data Cache (Brain Layer 1 — Data Ingestion)
CREATE TABLE IF NOT EXISTS trade_data_cache (
    id SERIAL PRIMARY KEY,
    data_source VARCHAR NOT NULL,  -- 'un_comtrade', 'fx', 'freight', 'weather', 'political_risk'
    cache_key VARCHAR NOT NULL,
    data_json JSONB NOT NULL,
    fetched_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    is_mock BOOLEAN DEFAULT TRUE
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_trade_data_cache_key ON trade_data_cache(data_source, cache_key);

-- 31. Brain Analysis Log (Layer 3 — Decision Audit Trail)
CREATE TABLE IF NOT EXISTS brain_analysis_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    analysis_type VARCHAR NOT NULL,  -- 'full_decision', 'arbitrage', 'risk', 'demand', 'cultural'
    input_params JSONB NOT NULL,
    result_json JSONB,
    credit_cost NUMERIC(6,2),
    verdict VARCHAR,
    confidence NUMERIC(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_brain_log_tenant ON brain_analysis_log(tenant_id, created_at);

-- 26. CRM Voice Insights (Phase D1) — IMMUTABLE / APPEND-ONLY
CREATE TABLE IF NOT EXISTS crm_voice_insights (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    recording_id UUID NOT NULL REFERENCES crm_voice_recordings(id),
    transcript TEXT,
    sentiment VARCHAR DEFAULT 'NEUTRAL',
    intent VARCHAR,
    action_items JSONB DEFAULT '[]',
    key_topics JSONB DEFAULT '[]',
    urgency VARCHAR DEFAULT 'medium',
    confidence_score NUMERIC(3,2) DEFAULT 0.0,
    model_used VARCHAR DEFAULT 'gemini-2.0-pro',
    model_version VARCHAR,
    processing_time_seconds NUMERIC(6,2),
    contains_sensitive_data BOOLEAN DEFAULT FALSE,
    retention_days INTEGER DEFAULT 365,
    disclaimer TEXT DEFAULT 'AI-generated analysis. Verify before acting.',
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_crm_voice_insights_recording ON crm_voice_insights(recording_id);
CREATE INDEX IF NOT EXISTS idx_crm_voice_insights_tenant ON crm_voice_insights(tenant_id);

-- 27. AI Jobs — Unified async job tracking (Voice, Vision, Brain)
CREATE TABLE IF NOT EXISTS ai_jobs (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    job_type VARCHAR NOT NULL, -- voice_analysis, vision_scan, brain_insight
    status VARCHAR NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    input_reference UUID,    -- recording_id, image_id, etc.
    result_reference UUID,   -- insight_id
    credit_cost NUMERIC(6,2) DEFAULT 0.0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ai_jobs_tenant_status ON ai_jobs(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_ai_jobs_stuck ON ai_jobs(status, started_at);

-- 28. AI Usage — Unified per-tenant rate limiting (row-locked)
CREATE TABLE IF NOT EXISTS ai_usage (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
    voice_daily INTEGER DEFAULT 0,
    voice_hourly INTEGER DEFAULT 0,
    vision_daily INTEGER DEFAULT 0,
    vision_hourly INTEGER DEFAULT 0,
    hour_window TIMESTAMP,
    UNIQUE(tenant_id, usage_date)
);
CREATE INDEX IF NOT EXISTS idx_ai_usage_tenant_date ON ai_usage(tenant_id, usage_date);

-- Migration: Add brain rate limit columns to ai_usage table
-- Run this AFTER deploying the new code.

-- Add brain counters to ai_usage
ALTER TABLE ai_usage
    ADD COLUMN IF NOT EXISTS brain_daily INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS brain_hourly INTEGER DEFAULT 0;

-- Add missing ai_usage table if it doesn't exist
CREATE TABLE IF NOT EXISTS ai_usage (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
    voice_daily INTEGER DEFAULT 0,
    voice_hourly INTEGER DEFAULT 0,
    vision_daily INTEGER DEFAULT 0,
    vision_hourly INTEGER DEFAULT 0,
    brain_daily INTEGER DEFAULT 0,
    brain_hourly INTEGER DEFAULT 0,
    hour_window TIMESTAMP,
    UNIQUE(tenant_id, usage_date)
);

-- Add missing ai_jobs table if it doesn't exist
CREATE TABLE IF NOT EXISTS ai_jobs (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    job_type VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending',
    input_reference UUID,
    result_reference UUID,
    credit_cost NUMERIC(6,2) DEFAULT 0.0,
    error_message VARCHAR,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_jobs_tenant ON ai_jobs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ai_jobs_status ON ai_jobs(status);
CREATE INDEX IF NOT EXISTS idx_ai_usage_tenant_date ON ai_usage(tenant_id, usage_date);

-- Migration: add durable automation runtime metadata and richer integration state

ALTER TABLE automations
ADD COLUMN IF NOT EXISTS trigger_type TEXT NOT NULL DEFAULT 'cron',
ADD COLUMN IF NOT EXISTS trigger_config JSONB NOT NULL DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS max_retries INTEGER NOT NULL DEFAULT 2,
ADD COLUMN IF NOT EXISTS retry_delay_seconds INTEGER NOT NULL DEFAULT 60,
ADD COLUMN IF NOT EXISTS last_status TEXT,
ADD COLUMN IF NOT EXISTS last_error TEXT;

CREATE INDEX IF NOT EXISTS idx_automations_trigger_type
ON automations(trigger_type);

CREATE TABLE IF NOT EXISTS automation_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    automation_id UUID NOT NULL REFERENCES automations(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL DEFAULT 'default',
    trigger_type TEXT NOT NULL,
    trigger_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL,
    attempt INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    result_summary TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    next_retry_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_automation_runs_automation_id
ON automation_runs(automation_id);

CREATE INDEX IF NOT EXISTS idx_automation_runs_user_created
ON automation_runs(user_id, created_at DESC);

ALTER TABLE integrations
ADD COLUMN IF NOT EXISTS config JSONB NOT NULL DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'connected',
ADD COLUMN IF NOT EXISTS last_checked_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS last_sync_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS last_error TEXT;

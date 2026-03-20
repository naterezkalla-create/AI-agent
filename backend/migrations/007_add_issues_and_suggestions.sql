-- Migration: add issue detection and automation suggestions

CREATE TABLE IF NOT EXISTS issues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL DEFAULT 'default',
    kind TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'medium',
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.8,
    suggested_action TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_issues_user_kind_source
ON issues(user_id, kind, source_type, source_id);

CREATE INDEX IF NOT EXISTS idx_issues_user_status
ON issues(user_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS automation_suggestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL DEFAULT 'default',
    issue_id UUID REFERENCES issues(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    prompt TEXT NOT NULL,
    trigger_type TEXT NOT NULL DEFAULT 'cron',
    trigger_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    cron_expression TEXT NOT NULL DEFAULT '0 9 * * *',
    rationale TEXT,
    status TEXT NOT NULL DEFAULT 'proposed',
    risk_level TEXT NOT NULL DEFAULT 'medium',
    approved_automation_id UUID REFERENCES automations(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_automation_suggestions_user_status
ON automation_suggestions(user_id, status, created_at DESC);

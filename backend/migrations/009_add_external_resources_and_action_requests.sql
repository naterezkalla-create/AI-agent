-- Migration: add tracked external resources and approval-based external actions

CREATE TABLE IF NOT EXISTS external_resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL DEFAULT 'default',
    provider TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    remote_id TEXT NOT NULL,
    name TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'active',
    last_synced_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_external_resources_user_provider_remote
ON external_resources(user_id, provider, resource_type, remote_id);

CREATE INDEX IF NOT EXISTS idx_external_resources_user_updated
ON external_resources(user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS external_action_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL DEFAULT 'default',
    provider TEXT NOT NULL,
    action_name TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'proposed',
    risk_level TEXT NOT NULL DEFAULT 'medium',
    requires_approval BOOLEAN NOT NULL DEFAULT TRUE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result JSONB NOT NULL DEFAULT '{}'::jsonb,
    requested_by TEXT NOT NULL DEFAULT 'user',
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    executed_at TIMESTAMPTZ,
    external_resource_id UUID REFERENCES external_resources(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_external_action_requests_user_status
ON external_action_requests(user_id, status, updated_at DESC);

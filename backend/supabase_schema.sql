-- ===========================================
-- AI Agent — Supabase Database Schema
-- ===========================================
-- Run this in the Supabase SQL Editor to create all tables.

-- Enable UUID generation
create extension if not exists "uuid-ossp";

-- -------------------------------------------
-- Conversations
-- -------------------------------------------
create table if not exists conversations (
    id uuid primary key default uuid_generate_v4(),
    user_id text not null default 'default',
    title text not null default 'New conversation',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_conversations_user_id on conversations(user_id);
create index if not exists idx_conversations_updated_at on conversations(updated_at desc);

-- -------------------------------------------
-- Messages
-- -------------------------------------------
create table if not exists messages (
    id uuid primary key default uuid_generate_v4(),
    conversation_id uuid not null references conversations(id) on delete cascade,
    role text not null check (role in ('user', 'assistant', 'system')),
    content text,
    tool_calls jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_messages_conversation_id on messages(conversation_id);
create index if not exists idx_messages_created_at on messages(created_at);

-- -------------------------------------------
-- Memory Notes (long-term memory)
-- -------------------------------------------
create table if not exists memory_notes (
    id uuid primary key default uuid_generate_v4(),
    user_id text not null default 'default',
    category text not null default 'general',
    key text not null,
    content text not null,
    confidence double precision not null default 0.8,
    source text not null default 'manual',
    review_status text not null default 'active',
    last_reviewed_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists idx_memory_notes_user_key on memory_notes(user_id, key);
create index if not exists idx_memory_notes_user_category on memory_notes(user_id, category);
create index if not exists idx_memory_notes_review_status on memory_notes(user_id, review_status);

-- -------------------------------------------
-- Entities (CRM: contacts, deals, notes, etc.)
-- -------------------------------------------
create table if not exists entities (
    id uuid primary key default uuid_generate_v4(),
    user_id text not null default 'default',
    type text not null,
    data jsonb not null default '{}',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_entities_user_type on entities(user_id, type);
create index if not exists idx_entities_created_at on entities(created_at desc);

-- -------------------------------------------
-- Automations (scheduled CRON jobs)
-- -------------------------------------------
create table if not exists automations (
    id uuid primary key default uuid_generate_v4(),
    user_id text not null default 'default',
    name text not null,
    cron_expression text not null,
    prompt text not null,
    trigger_type text not null default 'cron',
    trigger_config jsonb not null default '{}',
    enabled boolean not null default true,
    max_retries integer not null default 2,
    retry_delay_seconds integer not null default 60,
    last_run timestamptz,
    last_status text,
    last_error text,
    created_at timestamptz not null default now()
);

create index if not exists idx_automations_user_id on automations(user_id);
create index if not exists idx_automations_trigger_type on automations(trigger_type);

create table if not exists automation_runs (
    id uuid primary key default uuid_generate_v4(),
    automation_id uuid not null references automations(id) on delete cascade,
    user_id text not null default 'default',
    trigger_type text not null,
    trigger_payload jsonb not null default '{}',
    status text not null,
    attempt integer not null default 0,
    error text,
    result_summary text,
    started_at timestamptz,
    finished_at timestamptz,
    next_retry_at timestamptz,
    created_at timestamptz not null default now()
);

create index if not exists idx_automation_runs_automation_id on automation_runs(automation_id);
create index if not exists idx_automation_runs_user_created on automation_runs(user_id, created_at desc);

-- -------------------------------------------
-- Cost Logs
-- -------------------------------------------
create table if not exists cost_logs (
    id uuid primary key default uuid_generate_v4(),
    user_id text not null default 'default',
    service text not null,
    operation text not null,
    input_tokens integer not null default 0,
    output_tokens integer not null default 0,
    total_tokens integer not null default 0,
    cost double precision not null default 0,
    metadata jsonb not null default '{}',
    created_at timestamptz not null default now()
);

create index if not exists idx_cost_logs_user_created on cost_logs(user_id, created_at desc);
create index if not exists idx_cost_logs_service_created on cost_logs(service, created_at desc);

-- -------------------------------------------
-- External Resources & Action Requests
-- -------------------------------------------
create table if not exists external_resources (
    id uuid primary key default uuid_generate_v4(),
    user_id text not null default 'default',
    provider text not null,
    resource_type text not null,
    remote_id text not null,
    name text not null,
    config jsonb not null default '{}',
    status text not null default 'active',
    last_synced_at timestamptz,
    last_error text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists idx_external_resources_user_provider_remote
on external_resources(user_id, provider, resource_type, remote_id);
create index if not exists idx_external_resources_user_updated
on external_resources(user_id, updated_at desc);

create table if not exists external_action_requests (
    id uuid primary key default uuid_generate_v4(),
    user_id text not null default 'default',
    provider text not null,
    action_name text not null,
    resource_type text not null,
    status text not null default 'proposed',
    risk_level text not null default 'medium',
    requires_approval boolean not null default true,
    payload jsonb not null default '{}',
    result jsonb not null default '{}',
    requested_by text not null default 'user',
    approved_by text,
    approved_at timestamptz,
    executed_at timestamptz,
    external_resource_id uuid references external_resources(id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_external_action_requests_user_status
on external_action_requests(user_id, status, updated_at desc);

-- -------------------------------------------
-- Issues & Automation Suggestions
-- -------------------------------------------
create table if not exists issues (
    id uuid primary key default uuid_generate_v4(),
    user_id text not null default 'default',
    kind text not null,
    source_type text not null,
    source_id text not null,
    title text not null,
    description text not null,
    severity text not null default 'medium',
    confidence double precision not null default 0.8,
    suggested_action text,
    status text not null default 'open',
    metadata jsonb not null default '{}',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    last_seen_at timestamptz,
    resolved_at timestamptz
);

create unique index if not exists idx_issues_user_kind_source on issues(user_id, kind, source_type, source_id);
create index if not exists idx_issues_user_status on issues(user_id, status, updated_at desc);

create table if not exists automation_suggestions (
    id uuid primary key default uuid_generate_v4(),
    user_id text not null default 'default',
    issue_id uuid references issues(id) on delete set null,
    name text not null,
    prompt text not null,
    trigger_type text not null default 'cron',
    trigger_config jsonb not null default '{}',
    cron_expression text not null default '0 9 * * *',
    rationale text,
    status text not null default 'proposed',
    risk_level text not null default 'medium',
    approved_automation_id uuid references automations(id) on delete set null,
    approved_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_automation_suggestions_user_status on automation_suggestions(user_id, status, created_at desc);

-- -------------------------------------------
-- Integrations (OAuth tokens)
-- -------------------------------------------
create table if not exists integrations (
    id uuid primary key default uuid_generate_v4(),
    user_id text not null default 'default',
    provider text not null,
    access_token_enc text not null,
    refresh_token_enc text,
    scopes text,
    config jsonb not null default '{}',
    status text not null default 'connected',
    last_checked_at timestamptz,
    last_sync_at timestamptz,
    last_error text,
    expires_at timestamptz,
    created_at timestamptz not null default now()
);

create unique index if not exists idx_integrations_user_provider on integrations(user_id, provider);

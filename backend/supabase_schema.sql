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
    enabled boolean not null default true,
    last_run timestamptz,
    created_at timestamptz not null default now()
);

create index if not exists idx_automations_user_id on automations(user_id);

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
    expires_at timestamptz,
    created_at timestamptz not null default now()
);

create unique index if not exists idx_integrations_user_provider on integrations(user_id, provider);

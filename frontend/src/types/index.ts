export interface Message {
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCall[];
}

export interface ToolCall {
  name: string;
  input: Record<string, unknown>;
  result: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Entity {
  id: string;
  type: string;
  data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Automation {
  id: string;
  name: string;
  cron_expression: string;
  prompt: string;
  enabled: boolean;
  last_run: string | null;
  last_status?: string | null;
  last_error?: string | null;
  trigger_type?: 'cron' | 'event';
  trigger_config?: Record<string, unknown>;
  max_retries?: number;
  retry_delay_seconds?: number;
  created_at: string;
}

export interface AutomationRun {
  id: string;
  automation_id: string;
  user_id: string;
  trigger_type: string;
  trigger_payload: Record<string, unknown>;
  status: 'running' | 'succeeded' | 'failed' | 'retry_scheduled';
  attempt: number;
  error?: string | null;
  result_summary?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  next_retry_at?: string | null;
  created_at: string;
}

export interface MemoryNote {
  id: string;
  category: string;
  key: string;
  content: string;
  confidence: number;
  source: string;
  review_status: string;
  last_reviewed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Integration {
  id: string;
  provider: string;
  scopes: string;
  created_at: string;
  status?: 'connected' | 'reauth_required' | 'error';
  last_checked_at?: string;
  last_sync_at?: string;
  last_error?: string | null;
  has_refresh_token?: boolean;
  capabilities?: string[];
  config?: Record<string, unknown>;
}

export interface IntegrationConnectResult {
  status: string;
  provider: string;
  integration?: Integration;
  health?: Record<string, unknown>;
  webhook_url?: string;
}

export interface IntegrationProvider {
  id: string;
  name: string;
  category: string;
  description: string;
  connection_mode: string;
  required_env: string[];
  user_secret_keys: string[];
  capabilities: string[];
  tools: string[];
  supports_realtime: boolean;
  configured_env: string[];
  is_env_ready: boolean;
  connected: boolean;
  status: string;
  last_error?: string | null;
  last_sync_at?: string | null;
  integration?: Integration;
}

export interface Issue {
  id: string;
  user_id: string;
  kind: string;
  source_type: string;
  source_id: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  confidence: number;
  suggested_action?: string | null;
  status: 'open' | 'resolved' | 'dismissed';
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  last_seen_at?: string | null;
  resolved_at?: string | null;
}

export interface AutomationSuggestion {
  id: string;
  user_id: string;
  issue_id?: string | null;
  name: string;
  prompt: string;
  trigger_type: 'cron' | 'event';
  trigger_config: Record<string, unknown>;
  cron_expression: string;
  rationale?: string | null;
  status: 'proposed' | 'approved' | 'rejected';
  risk_level: 'low' | 'medium' | 'high';
  approved_automation_id?: string | null;
  approved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserSettings {
  id: string;
  user_id: string;
  system_prompt: string;
  enabled_integrations: string[];
  preferences: {
    timezone?: string;
    theme?: string;
    notifications_enabled?: boolean;
    auto_save_conversations?: boolean;
    [key: string]: unknown;
  };
  created_at: string;
  updated_at: string;
}

export interface WSEvent {
  type: 'text_delta' | 'tool_call_start' | 'tool_call_end' | 'done' | 'error';
  text?: string;
  name?: string;
  input?: Record<string, unknown>;
  result?: string;
  conversation_id?: string;
  tool_calls?: ToolCall[];
  message?: string;
}

export interface RealtimeEvent {
  type: string;
  payload: Record<string, unknown>;
  user_id?: string;
  topics?: string[];
  timestamp?: string;
}

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

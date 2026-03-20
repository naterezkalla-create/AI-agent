import type { RealtimeEvent } from '../types';

const API_BASE = '';

function getAuthToken(): string | null {
  return localStorage.getItem('auth_token');
}

function withAuth(options: RequestInit = {}): RequestInit {
  const token = getAuthToken();
  return {
    ...options,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
  };
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(
    `${API_BASE}${path}`,
    withAuth({
      headers: { 'Content-Type': 'application/json' },
      ...options,
    }),
  );
  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API error ${res.status}: ${error}`);
  }
  return res.json();
}

// Chat
export const sendMessage = (message: string, conversationId?: string) =>
  request<{ response: string; conversation_id: string; tool_calls: unknown[] }>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, conversation_id: conversationId }),
  });

export interface ChatStreamEvent {
  type: 'text_delta' | 'tool_call_start' | 'tool_call_end' | 'done' | 'error';
  text?: string;
  name?: string;
  input?: Record<string, unknown>;
  result?: string;
  conversation_id?: string;
  tool_calls?: unknown[];
  message?: string;
  truncated?: boolean;
}

export async function streamMessage(
  message: string,
  conversationId: string | undefined,
  onEvent: (event: ChatStreamEvent) => void,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/chat/stream`, {
    ...withAuth({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    }),
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API error ${res.status}: ${error}`);
  }

  if (!res.body) {
    throw new Error('Streaming response body unavailable');
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split('\n\n');
    buffer = chunks.pop() ?? '';

    for (const chunk of chunks) {
      const line = chunk
        .split('\n')
        .find((part) => part.startsWith('data: '));

      if (!line) continue;

      const payload = line.slice(6);
      if (!payload) continue;

      onEvent(JSON.parse(payload) as ChatStreamEvent);
    }
  }

  if (buffer.trim()) {
    const line = buffer
      .split('\n')
      .find((part) => part.startsWith('data: '));
    if (line) {
      onEvent(JSON.parse(line.slice(6)) as ChatStreamEvent);
    }
  }
}

export const getConversations = () =>
  request<{ id: string; title: string; updated_at: string }[]>('/api/conversations');

export const getConversationMessages = (conversationId: string) =>
  request<
    Array<
      | { role: 'user' | 'assistant' | 'system'; content: string }
      | { role: 'user' | 'assistant' | 'system'; content: unknown[] }
    >
  >(`/api/conversations/${conversationId}/messages`);

export const deleteConversation = (id: string) =>
  request<{ deleted: boolean }>(`/api/conversations/${id}`, { method: 'DELETE' });

// Entities
export const getEntities = (type?: string) =>
  request<unknown[]>(`/entities${type ? `?entity_type=${type}` : ''}`);

export const createEntity = (type: string, data: Record<string, unknown>) =>
  request<unknown>('/entities', { method: 'POST', body: JSON.stringify({ type, data }) });

export const updateEntity = (id: string, updates: Record<string, unknown>) =>
  request<unknown>(`/entities/${id}`, { method: 'PATCH', body: JSON.stringify(updates) });

export const deleteEntity = (id: string) =>
  request<{ deleted: boolean }>(`/entities/${id}`, { method: 'DELETE' });

// Automations
export const getAutomations = () => request<unknown[]>('/automations');

export const getAutomationRuns = (automationId?: string) =>
  request<unknown[]>(`/automations/runs${automationId ? `?automation_id=${automationId}` : ''}`);

export const createAutomation = (payload: Record<string, unknown>) =>
  request<unknown>('/automations', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const updateAutomation = (id: string, updates: Record<string, unknown>) =>
  request<unknown>(`/automations/${id}`, { method: 'PATCH', body: JSON.stringify(updates) });

export const deleteAutomation = (id: string) =>
  request<{ deleted: boolean }>(`/automations/${id}`, { method: 'DELETE' });

// Memory
export const getMemoryNotes = () => request<unknown[]>('/api/admin/memory');

export const createMemoryNote = (category: string, key: string, content: string, confidence = 0.8) =>
  request<unknown>('/api/admin/memory', {
    method: 'POST',
    body: JSON.stringify({ category, key, content, confidence }),
  });

export const updateMemoryNote = (key: string, updates: Record<string, unknown>) =>
  request<unknown>(`/api/admin/memory/${key}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  });

export const deleteMemoryNote = (key: string) =>
  request<{ deleted: boolean }>(`/api/admin/memory/${key}`, { method: 'DELETE' });

// Integrations
export const getIntegrations = () => request<unknown[]>('/api/integrations');

export const getIntegrationProviders = () => request<unknown[]>('/api/integrations/providers');

export const deleteIntegration = (provider: string) =>
  request<unknown>(`/api/integrations/${provider}`, { method: 'DELETE' });

export const connectIntegration = (provider: string, payload: Record<string, unknown>) =>
  request<unknown>(`/api/integrations/${provider}/connect`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const testIntegration = (provider: string, payload?: Record<string, unknown>) =>
  request<unknown>(`/api/integrations/${provider}/test`, {
    method: 'POST',
    body: JSON.stringify(payload ?? {}),
  });

export const getExternalActionCatalog = () =>
  request<unknown[]>('/api/external-actions/catalog');

export const getExternalActionRequests = (status?: string) =>
  request<unknown[]>(`/api/external-actions/requests${status ? `?status=${encodeURIComponent(status)}` : ''}`);

export const createExternalActionRequest = (payload: Record<string, unknown>) =>
  request<unknown>('/api/external-actions/requests', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const approveExternalActionRequest = (requestId: string) =>
  request<unknown>(`/api/external-actions/requests/${requestId}/approve`, {
    method: 'POST',
  });

export const rejectExternalActionRequest = (requestId: string) =>
  request<unknown>(`/api/external-actions/requests/${requestId}/reject`, {
    method: 'POST',
  });

export const getExternalResources = (provider?: string) =>
  request<unknown[]>(`/api/external-actions/resources${provider ? `?provider=${encodeURIComponent(provider)}` : ''}`);

// Admin
export const getSystemStatus = () =>
  request<{ status: string; tools_registered: number; tool_names: string[] }>('/api/admin/status');

export const getTools = () =>
  request<{ name: string; description: string }[]>('/api/admin/tools');

export const getIssues = (status?: string) =>
  request<unknown[]>(`/api/issues${status ? `?status=${encodeURIComponent(status)}` : ''}`);

export const scanIssues = () =>
  request<{ issues: unknown[]; suggestions: unknown[] }>('/api/issues/scan', {
    method: 'POST',
  });

export const updateIssueStatus = (issueId: string, status: 'open' | 'resolved' | 'dismissed') =>
  request<unknown>(`/api/issues/${issueId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });

export const getAutomationSuggestions = (status?: string) =>
  request<unknown[]>(`/api/issues/suggestions${status ? `?status=${encodeURIComponent(status)}` : ''}`);

export const generateAutomationSuggestions = () =>
  request<unknown[]>('/api/issues/suggestions/generate', {
    method: 'POST',
  });

export const approveAutomationSuggestion = (suggestionId: string) =>
  request<unknown>(`/api/issues/suggestions/${suggestionId}/approve`, {
    method: 'POST',
  });

export const rejectAutomationSuggestion = (suggestionId: string) =>
  request<unknown>(`/api/issues/suggestions/${suggestionId}/reject`, {
    method: 'POST',
  });

export function subscribeToRealtime(
  topics: string[],
  onEvent: (event: RealtimeEvent) => void,
): () => void {
  const params = new URLSearchParams();
  if (topics.length > 0) {
    params.set('topics', topics.join(','));
  }
  const token = getAuthToken();
  if (token) {
    params.set('token', token);
  }

  const source = new EventSource(`/api/realtime/events?${params.toString()}`);
  source.onmessage = (message) => {
    onEvent(JSON.parse(message.data) as RealtimeEvent);
  };

  return () => {
    source.close();
  };
}

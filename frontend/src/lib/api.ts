const API_BASE = '';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
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
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, conversation_id: conversationId }),
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

export const deleteConversation = (id: string) =>
  request<{ deleted: boolean }>(`/api/conversations/${id}`, { method: 'DELETE' });

// Entities
export const getEntities = (type?: string) =>
  request<unknown[]>(`/entities${type ? `?entity_type=${type}` : ''}`);

export const createEntity = (type: string, data: Record<string, unknown>) =>
  request<unknown>('/entities', { method: 'POST', body: JSON.stringify({ type, data }) });

export const deleteEntity = (id: string) =>
  request<{ deleted: boolean }>(`/entities/${id}`, { method: 'DELETE' });

// Automations
export const getAutomations = () => request<unknown[]>('/automations');

export const createAutomation = (name: string, cronExpression: string, prompt: string) =>
  request<unknown>('/automations', {
    method: 'POST',
    body: JSON.stringify({ name, cron_expression: cronExpression, prompt }),
  });

export const updateAutomation = (id: string, updates: Record<string, unknown>) =>
  request<unknown>(`/automations/${id}`, { method: 'PATCH', body: JSON.stringify(updates) });

export const deleteAutomation = (id: string) =>
  request<{ deleted: boolean }>(`/automations/${id}`, { method: 'DELETE' });

// Memory
export const getMemoryNotes = () => request<unknown[]>('/api/admin/memory');

export const createMemoryNote = (category: string, key: string, content: string) =>
  request<unknown>('/api/admin/memory', {
    method: 'POST',
    body: JSON.stringify({ category, key, content }),
  });

export const deleteMemoryNote = (key: string) =>
  request<{ deleted: boolean }>(`/api/admin/memory/${key}`, { method: 'DELETE' });

// Integrations
export const getIntegrations = () => request<unknown[]>('/integrations');

export const deleteIntegration = (provider: string) =>
  request<unknown>(`/integrations/${provider}`, { method: 'DELETE' });

// Admin
export const getSystemStatus = () =>
  request<{ status: string; tools_registered: number; tool_names: string[] }>('/api/admin/status');

export const getTools = () =>
  request<{ name: string; description: string }[]>('/api/admin/tools');

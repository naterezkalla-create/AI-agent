import { useState, useEffect } from 'react';
import {
  connectIntegration,
  deleteIntegration,
  getIntegrationProviders,
  getIntegrations,
  subscribeToRealtime,
  testIntegration,
} from '../lib/api';
import { Plug, Trash2, ExternalLink, RefreshCw, ShieldAlert, CheckCircle2 } from 'lucide-react';
import type { Integration, IntegrationProvider } from '../types';

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [providers, setProviders] = useState<IntegrationProvider[]>([]);
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [webhookLabels, setWebhookLabels] = useState<Record<string, string>>({});
  const [busyProvider, setBusyProvider] = useState<string | null>(null);
  const [messages, setMessages] = useState<Record<string, string>>({});

  useEffect(() => {
    void loadPageData();
  }, []);

  useEffect(() => {
    return subscribeToRealtime(['integrations'], (event) => {
      if (event.type === 'integrations.changed') {
        void loadPageData();
      }
    });
  }, []);

  const loadPageData = async () => {
    await Promise.all([loadIntegrations(), loadProviders()]);
  };

  const loadIntegrations = async () => {
    try {
      const data = await getIntegrations() as Integration[];
      setIntegrations(data);
    } catch {
      // API may not be available
    }
  };

  const loadProviders = async () => {
    try {
      const data = await getIntegrationProviders() as IntegrationProvider[];
      setProviders(data);
    } catch {
      // API may not be available
    }
  };

  const handleOAuthConnect = (provider: string) => {
    window.location.href = `/api/integrations/${provider}/authorize`;
  };

  const handleDisconnect = async (provider: string) => {
    if (!confirm(`Disconnect ${provider}?`)) return;
    await deleteIntegration(provider);
    void loadPageData();
  };

  const handleConnect = async (provider: IntegrationProvider) => {
    setBusyProvider(provider.id);
    setMessages((current) => ({ ...current, [provider.id]: '' }));
    try {
      if (provider.connection_mode === 'oauth') {
        handleOAuthConnect(provider.id);
        return;
      }

      if (provider.connection_mode === 'webhook') {
        const result = await connectIntegration(provider.id, {
          label: webhookLabels[provider.id] || undefined,
        }) as { webhook_url?: string };
        setMessages((current) => ({
          ...current,
          [provider.id]: result.webhook_url
            ? `Webhook ready: ${result.webhook_url}`
            : 'Webhook created.',
        }));
      } else {
        const apiKey = apiKeys[provider.id]?.trim();
        if (!apiKey) {
          setMessages((current) => ({ ...current, [provider.id]: 'API key is required.' }));
          return;
        }
        await connectIntegration(provider.id, { api_key: apiKey });
        setApiKeys((current) => ({ ...current, [provider.id]: '' }));
        setMessages((current) => ({ ...current, [provider.id]: 'Connected successfully.' }));
      }
      await loadPageData();
    } catch (error) {
      setMessages((current) => ({
        ...current,
        [provider.id]: error instanceof Error ? error.message : 'Failed to connect provider.',
      }));
    } finally {
      setBusyProvider(null);
    }
  };

  const handleTest = async (provider: IntegrationProvider) => {
    setBusyProvider(provider.id);
    try {
      const apiKey = apiKeys[provider.id]?.trim();
      const result = await testIntegration(provider.id, apiKey ? { api_key: apiKey } : {}) as { health?: Record<string, unknown> };
      const healthSummary = result.health
        ? Object.values(result.health)
            .filter((value): value is string | number | boolean => value !== null && value !== undefined && value !== '')
            .map((value) => String(value))
            .join(' • ')
        : '';
      setMessages((current) => ({
        ...current,
        [provider.id]: healthSummary ? `Healthy: ${healthSummary}` : 'Connection looks healthy.',
      }));
      await loadPageData();
    } catch (error) {
      setMessages((current) => ({
        ...current,
        [provider.id]: error instanceof Error ? error.message : 'Connection test failed.',
      }));
    } finally {
      setBusyProvider(null);
    }
  };

  const isConnected = (provider: string) =>
    integrations.some((i) => i.provider === provider);

  const providerIcons: Record<string, string> = {
    google: '🔗',
    telegram: '✈️',
    slack: '💬',
    github: '🐙',
    notion: '📝',
    apify: '🕷️',
    custom_webhook: '🪝',
    openai: '🧠',
    anthropic: '🪶',
  };

  const getActionLabel = (provider: IntegrationProvider) => {
    if (provider.connection_mode === 'oauth') return 'Connect';
    if (provider.connection_mode === 'managed') return 'Managed';
    if (provider.connection_mode === 'webhook') return 'Generate webhook';
    return 'Connect key';
  };

  const getStatusMeta = (integration?: Integration) => {
    switch (integration?.status) {
      case 'connected':
        return {
          label: 'Healthy',
          icon: <CheckCircle2 size={14} className="text-green-400" />,
          className: 'text-green-400',
        };
      case 'reauth_required':
        return {
          label: 'Reconnect required',
          icon: <RefreshCw size={14} className="text-yellow-400" />,
          className: 'text-yellow-400',
        };
      case 'error':
        return {
          label: 'Needs attention',
          icon: <ShieldAlert size={14} className="text-red-400" />,
          className: 'text-red-400',
        };
      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="border-b border-gray-800 px-6 py-3">
        <h2 className="text-lg font-semibold">Integrations</h2>
        <p className="text-sm text-gray-500 mt-1">Connect external services to give your agent more capabilities.</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="space-y-4 max-w-2xl">
          {providers.map((provider) => {
            const connected = isConnected(provider.id);
            const integration = integrations.find((i) => i.provider === provider.id);
            const statusMeta = getStatusMeta(integration);

            return (
              <div
                key={provider.id}
                className="bg-gray-900 border border-gray-800 rounded-lg p-5"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{providerIcons[provider.id] ?? '🔌'}</span>
                    <div>
                      <h3 className="font-medium">{provider.name}</h3>
                      <p className="text-sm text-gray-500">{provider.description}</p>
                      <div className="flex flex-wrap gap-2 mt-3">
                        {provider.capabilities.map((scope) => (
                          <span
                            key={scope}
                            className="px-2 py-1 text-xs rounded-full bg-gray-800 text-gray-300 border border-gray-700"
                          >
                            {scope}
                          </span>
                        ))}
                      </div>
                      {connected && integration && (
                        <div className="mt-3 space-y-1">
                          <p className="text-xs text-green-400">
                            Connected since {new Date(integration.created_at).toLocaleDateString()}
                          </p>
                          {statusMeta && (
                            <div className={`flex items-center gap-2 text-xs ${statusMeta.className}`}>
                              {statusMeta.icon}
                              <span>{statusMeta.label}</span>
                              {integration.last_checked_at && (
                                <span className="text-gray-500">
                                  checked {new Date(integration.last_checked_at).toLocaleTimeString()}
                                </span>
                              )}
                            </div>
                          )}
                          {integration.capabilities && integration.capabilities.length > 0 && (
                            <p className="text-xs text-gray-500">
                              Active: {integration.capabilities.join(', ')}
                            </p>
                          )}
                          <p className="text-xs text-gray-500">
                            Mode: {provider.connection_mode.replace('_', ' ')}
                          </p>
                          {provider.id === 'custom_webhook' && Boolean(integration.config?.webhook_url) && (
                            <p className="text-xs text-blue-300 break-all">
                              Endpoint: {String(integration.config?.webhook_url ?? '')}
                            </p>
                          )}
                          {integration.last_error && (
                            <p className="text-xs text-red-400">
                              {integration.last_error}
                            </p>
                          )}
                        </div>
                      )}
                      {!connected && (
                        <div className="mt-3 text-xs text-gray-500 space-y-1">
                          {provider.required_env.length > 0 && (
                            <p>
                              Requires env: {provider.required_env.join(', ')}
                            </p>
                          )}
                          {provider.user_secret_keys.length > 0 && (
                            <p>
                              Supports user keys: {provider.user_secret_keys.join(', ')}
                            </p>
                          )}
                          {provider.connection_mode === 'api_key' && (
                            <input
                              type="password"
                              value={apiKeys[provider.id] ?? ''}
                              onChange={(event) =>
                                setApiKeys((current) => ({ ...current, [provider.id]: event.target.value }))
                              }
                              placeholder={`Paste your ${provider.name} API key`}
                              className="mt-2 w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-100"
                            />
                          )}
                          {provider.connection_mode === 'webhook' && (
                            <input
                              type="text"
                              value={webhookLabels[provider.id] ?? ''}
                              onChange={(event) =>
                                setWebhookLabels((current) => ({ ...current, [provider.id]: event.target.value }))
                              }
                              placeholder="Optional label for this endpoint"
                              className="mt-2 w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-100"
                            />
                          )}
                        </div>
                      )}
                      {messages[provider.id] && (
                        <p className="mt-3 text-xs text-blue-300 break-words">{messages[provider.id]}</p>
                      )}
                    </div>
                  </div>

                  {connected ? (
                    <div className="flex flex-col gap-2">
                      {provider.connection_mode !== 'managed' && (
                        <button
                          onClick={() => void handleTest(provider)}
                          disabled={busyProvider === provider.id}
                          className="flex items-center gap-2 px-3 py-2 bg-gray-800 text-gray-200 hover:bg-gray-700 rounded-lg text-sm transition-colors disabled:opacity-60"
                        >
                          <CheckCircle2 size={14} /> Test
                        </button>
                      )}
                      {(integration?.status === 'reauth_required' || integration?.status === 'error') && (
                        <button
                          onClick={() => handleOAuthConnect(provider.id)}
                          className="flex items-center gap-2 px-3 py-2 bg-yellow-600/20 text-yellow-300 hover:bg-yellow-600/30 rounded-lg text-sm transition-colors"
                        >
                          <RefreshCw size={14} /> Reconnect
                        </button>
                      )}
                      <button
                        onClick={() => handleDisconnect(provider.id)}
                        className="flex items-center gap-2 px-3 py-2 bg-red-600/20 text-red-400 hover:bg-red-600/30 rounded-lg text-sm transition-colors"
                      >
                        <Trash2 size={14} /> Disconnect
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => void handleConnect(provider)}
                      disabled={provider.connection_mode === 'managed' || busyProvider === provider.id}
                      className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-800 disabled:text-gray-400 text-white rounded-lg text-sm transition-colors"
                    >
                      <ExternalLink size={14} /> {getActionLabel(provider)}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Connected integrations */}
        {integrations.length > 0 && (
          <div className="max-w-2xl mt-8">
            <h3 className="text-sm text-gray-500 uppercase mb-3">Active Connections</h3>
            {integrations.map((integration) => (
              <div
                key={integration.id}
                className="flex items-center justify-between bg-gray-900/50 border border-gray-800 rounded-lg px-4 py-3 mb-2"
              >
                <div className="flex items-center gap-2">
                  <Plug size={16} className={integration.status === 'connected' ? 'text-green-400' : 'text-yellow-400'} />
                  <span className="text-sm font-medium capitalize">{integration.provider}</span>
                  <span className="text-xs text-gray-600">{integration.scopes}</span>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-600">
                    {new Date(integration.created_at).toLocaleDateString()}
                  </p>
                  {integration.status && (
                    <p className={`text-xs ${
                      integration.status === 'connected'
                        ? 'text-green-400'
                        : integration.status === 'reauth_required'
                          ? 'text-yellow-400'
                          : 'text-red-400'
                    }`}>
                      {integration.status.replace('_', ' ')}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

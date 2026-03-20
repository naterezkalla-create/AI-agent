import { useState, useEffect } from 'react';
import { getIntegrations, getIntegrationProviders, deleteIntegration, subscribeToRealtime } from '../lib/api';
import { Plug, Trash2, ExternalLink, RefreshCw, ShieldAlert, CheckCircle2 } from 'lucide-react';
import type { Integration, IntegrationProvider } from '../types';

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [providers, setProviders] = useState<IntegrationProvider[]>([]);

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

  const handleConnect = (provider: string) => {
    window.location.href = `/integrations/${provider}/authorize`;
  };

  const handleDisconnect = async (provider: string) => {
    if (!confirm(`Disconnect ${provider}?`)) return;
    await deleteIntegration(provider);
    void loadPageData();
  };

  const isConnected = (provider: string) =>
    integrations.some((i) => i.provider === provider);

  const providerIcons: Record<string, string> = {
    google: '🔗',
    telegram: '✈️',
    apify: '🕷️',
    openai: '🧠',
    anthropic: '🪶',
  };

  const getActionLabel = (provider: IntegrationProvider) => {
    if (provider.connection_mode === 'oauth') return 'Connect';
    if (provider.connection_mode === 'managed') return 'Configured by env';
    return 'Use in Settings';
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
                        </div>
                      )}
                    </div>
                  </div>

                  {connected ? (
                    <div className="flex flex-col gap-2">
                      {(integration?.status === 'reauth_required' || integration?.status === 'error') && (
                        <button
                          onClick={() => handleConnect(provider.id)}
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
                      onClick={() => provider.connection_mode === 'oauth' && handleConnect(provider.id)}
                      disabled={provider.connection_mode !== 'oauth'}
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

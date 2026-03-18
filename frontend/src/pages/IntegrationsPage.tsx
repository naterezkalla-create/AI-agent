import { useState, useEffect } from 'react';
import { getIntegrations, deleteIntegration } from '../lib/api';
import { Plug, Trash2, ExternalLink } from 'lucide-react';
import type { Integration } from '../types';

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);

  useEffect(() => {
    loadIntegrations();
  }, []);

  const loadIntegrations = async () => {
    try {
      const data = await getIntegrations() as Integration[];
      setIntegrations(data);
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
    loadIntegrations();
  };

  const isConnected = (provider: string) =>
    integrations.some((i) => i.provider === provider);

  const availableProviders = [
    {
      id: 'google',
      name: 'Google',
      description: 'Gmail, Google Calendar, Google Sheets',
      icon: '🔗',
    },
  ];

  return (
    <div className="h-full flex flex-col">
      <div className="border-b border-gray-800 px-6 py-3">
        <h2 className="text-lg font-semibold">Integrations</h2>
        <p className="text-sm text-gray-500 mt-1">Connect external services to give your agent more capabilities.</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="space-y-4 max-w-2xl">
          {availableProviders.map((provider) => {
            const connected = isConnected(provider.id);
            const integration = integrations.find((i) => i.provider === provider.id);

            return (
              <div
                key={provider.id}
                className="bg-gray-900 border border-gray-800 rounded-lg p-5"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{provider.icon}</span>
                    <div>
                      <h3 className="font-medium">{provider.name}</h3>
                      <p className="text-sm text-gray-500">{provider.description}</p>
                      {connected && integration && (
                        <p className="text-xs text-green-400 mt-2">
                          Connected since {new Date(integration.created_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>

                  {connected ? (
                    <button
                      onClick={() => handleDisconnect(provider.id)}
                      className="flex items-center gap-2 px-3 py-2 bg-red-600/20 text-red-400 hover:bg-red-600/30 rounded-lg text-sm transition-colors"
                    >
                      <Trash2 size={14} /> Disconnect
                    </button>
                  ) : (
                    <button
                      onClick={() => handleConnect(provider.id)}
                      className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors"
                    >
                      <ExternalLink size={14} /> Connect
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
                  <Plug size={16} className="text-green-400" />
                  <span className="text-sm font-medium capitalize">{integration.provider}</span>
                  <span className="text-xs text-gray-600">{integration.scopes}</span>
                </div>
                <span className="text-xs text-gray-600">
                  {new Date(integration.created_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

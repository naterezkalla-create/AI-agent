import { useState, useEffect } from 'react';
import { Settings, Save, RotateCcw, AlertCircle, CheckCircle, Mail, MessageSquare, Sun, Bell, Lock, Plus, X } from 'lucide-react';
import type { UserSettings } from '../types';

export default function SettingsPage() {
  const [localSettings, setLocalSettings] = useState<Partial<UserSettings>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setIsSaving] = useState(false);
  const [savedMessage, setSavedMessage] = useState('');
  const [availableIntegrations] = useState(['google', 'telegram', 'slack', 'github']);
  
  // API Key Management State
  const [apiKeys, setApiKeys] = useState<Record<string, boolean>>({});
  const [loadingKeys, setLoadingKeys] = useState(false);
  const [addingKey, setAddingKey] = useState(false);
  const [selectedService, setSelectedService] = useState<string>('anthropic');
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [keyMessage, setKeyMessage] = useState('');
  const [keyError, setKeyError] = useState('');

  const availableServices = [
    { id: 'anthropic', label: '🧠 Anthropic (Claude)', category: 'LLM' },
    { id: 'openai', label: '🔌 OpenAI (GPT-4, GPT-3.5)', category: 'LLM' },
    { id: 'google_token', label: '🔍 Google (Drive, Sheets, Docs)', category: 'Productivity' },
    { id: 'github_token', label: '🐙 GitHub (Repositories, Gists)', category: 'Development' },
    { id: 'huggingface_token', label: '🤗 Hugging Face (Models)', category: 'AI/ML' },
    { id: 'replicate_token', label: '🔀 Replicate (Models)', category: 'AI/ML' },
    { id: 'together_ai_token', label: '⚡ Together AI (LLMs)', category: 'LLM' },
    { id: 'cohere_token', label: '🎯 Cohere (LLMs)', category: 'LLM' },
    { id: 'databricks_token', label: '🧬 Databricks', category: 'Data' },
    { id: 'stripe_key', label: '💳 Stripe (Payments)', category: 'Financial' },
    { id: 'slack_token', label: '💬 Slack (Messaging)', category: 'Communication' },
    { id: 'discord_token', label: '🎮 Discord (Bot)', category: 'Communication' },
    { id: 'twilio_key', label: '📱 Twilio (SMS/Voice)', category: 'Communication' },
    { id: 'sendgrid_key', label: '📧 SendGrid (Email)', category: 'Communication' },
    { id: 'aws_key', label: '☁️ AWS (Cloud)', category: 'Cloud' },
    { id: 'gcp_key', label: '⛅ GCP (Cloud)', category: 'Cloud' },
    { id: 'azure_key', label: '🔷 Azure (Cloud)', category: 'Cloud' },
    { id: 'custom_api_key', label: '🔑 Custom API Key', category: 'Other' },
  ];

  const servicesByCategory = availableServices.reduce((acc, service) => {
    if (!acc[service.category]) {
      acc[service.category] = [];
    }
    acc[service.category].push(service);
    return acc;
  }, {} as Record<string, typeof availableServices>);

  useEffect(() => {
    loadSettings();
    loadApiKeys();
  }, []);

  const authHeaders = (): Record<string, string> => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      return {};
    }
    return { Authorization: `Bearer ${token}` };
  };

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/settings/', {
        headers: authHeaders(),
      });
      const data = await response.json();
      setLocalSettings(data);
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadApiKeys = async () => {
    try {
      setLoadingKeys(true);
      const response = await fetch('/api/settings/keys', {
        headers: authHeaders(),
      });
      const data = await response.json();
      setApiKeys(data.keys || {});
    } catch (error) {
      console.error('Failed to load API keys:', error);
    } finally {
      setLoadingKeys(false);
    }
  };

  const handleAddApiKey = async () => {
    setKeyError('');
    setKeyMessage('');

    if (!apiKeyInput.trim()) {
      setKeyError('Please enter an API key');
      return;
    }

    if (apiKeyInput.trim().length < 10) {
      setKeyError('API key seems too short');
      return;
    }

    try {
      setAddingKey(true);
      const response = await fetch(`/api/settings/keys/${selectedService}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ key: apiKeyInput }),
      });

      if (response.ok) {
        setKeyMessage(`${selectedService} API key saved successfully!`);
        setApiKeyInput('');
        setApiKeys({ ...apiKeys, [selectedService]: true });
        setTimeout(() => setKeyMessage(''), 3000);
      } else {
        const error = await response.json();
        setKeyError(error.detail || 'Failed to save API key');
      }
    } catch (error) {
      setKeyError('Failed to save API key: ' + String(error));
    } finally {
      setAddingKey(false);
    }
  };

  const handleDeleteApiKey = async (service: string) => {
    if (!confirm(`Are you sure you want to delete the ${service} API key?`)) return;

    try {
      const response = await fetch(`/api/settings/keys/${service}`, {
        method: 'DELETE',
        headers: authHeaders(),
      });

      if (response.ok) {
        setKeyMessage(`${service} API key deleted successfully`);
        setApiKeys({ ...apiKeys, [service]: false });
        setTimeout(() => setKeyMessage(''), 3000);
      } else {
        setKeyError('Failed to delete API key');
      }
    } catch (error) {
      setKeyError('Failed to delete API key: ' + String(error));
    }
  };

  const handleSaveSettings = async () => {
    try {
      setIsSaving(true);
      const response = await fetch('/api/settings/', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          system_prompt: localSettings.system_prompt,
          enabled_integrations: localSettings.enabled_integrations,
          preferences: localSettings.preferences,
        }),
      });

      if (response.ok) {
        const updated = await response.json();
        setLocalSettings(updated);
        setSavedMessage('Settings saved successfully!');
        setTimeout(() => setSavedMessage(''), 3000);
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggleIntegration = async (integration: string) => {
    const isEnabled = localSettings.enabled_integrations?.includes(integration);
    const updated = isEnabled
      ? localSettings.enabled_integrations?.filter((i) => i !== integration)
      : [...(localSettings.enabled_integrations || []), integration];

    setLocalSettings({
      ...localSettings,
      enabled_integrations: updated,
    });
  };

  const handleResetSettings = async () => {
    if (!confirm('Are you sure you want to reset all settings to defaults?')) return;

    try {
      const response = await fetch('/api/settings/reset', {
        method: 'POST',
        headers: authHeaders(),
      });
      if (response.ok) {
        const reset = await response.json();
        setLocalSettings(reset);
        setSavedMessage('Settings reset to defaults');
        setTimeout(() => setSavedMessage(''), 3000);
      }
    } catch (error) {
      console.error('Failed to reset settings:', error);
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-900 border-t-blue-400 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Header */}
      <div className="border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings size={24} className="text-blue-400" />
            <h1 className="text-2xl font-bold">Settings</h1>
          </div>
          {(savedMessage || keyMessage) && (
            <div className="flex items-center gap-2 text-green-400 text-sm">
              <CheckCircle size={16} />
              {savedMessage || keyMessage}
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 max-w-4xl space-y-6">
          {/* Agent Personality Section */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-700 flex items-center gap-2">
              <MessageSquare size={20} className="text-purple-400" />
              <h2 className="text-lg font-semibold">Agent Personality</h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">System Prompt</label>
                <p className="text-xs text-gray-500 mb-3">
                  Customize how the AI agent behaves and responds to requests
                </p>
                <textarea
                  value={localSettings.system_prompt || ''}
                  onChange={(e) =>
                    setLocalSettings({
                      ...localSettings,
                      system_prompt: e.target.value,
                    })
                  }
                  className="w-full h-32 bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-none"
                  placeholder="Enter your custom system prompt..."
                />
              </div>
            </div>
          </div>

          {/* Integration Control */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-700 flex items-center gap-2">
              <Mail size={20} className="text-green-400" />
              <h2 className="text-lg font-semibold">Integration Control</h2>
            </div>
            <div className="p-6">
              <p className="text-sm text-gray-400 mb-4">Enable/disable which integrations the agent can access</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {availableIntegrations.map((integration) => {
                  const isEnabled = localSettings.enabled_integrations?.includes(integration);
                  return (
                    <button
                      key={integration}
                      onClick={() => handleToggleIntegration(integration)}
                      className={`flex items-center gap-3 p-4 rounded-lg border-2 transition-all ${
                        isEnabled
                          ? 'bg-green-900/20 border-green-600 text-green-300'
                          : 'bg-gray-700/30 border-gray-600 text-gray-400 hover:border-gray-500'
                      }`}
                    >
                      <div
                        className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                          isEnabled ? 'bg-green-600 border-green-600' : 'border-gray-500'
                        }`}
                      >
                        {isEnabled && <div className="w-2 h-2 bg-white rounded-sm" />}
                      </div>
                      <span className="capitalize font-medium">{integration}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Preferences */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-700 flex items-center gap-2">
              <Sun size={20} className="text-yellow-400" />
              <h2 className="text-lg font-semibold">Preferences</h2>
            </div>
            <div className="p-6 space-y-4">
              {/* Timezone */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Timezone</label>
                <select
                  value={localSettings.preferences?.timezone || 'Australia/Sydney'}
                  onChange={(e) =>
                    setLocalSettings({
                      ...localSettings,
                      preferences: {
                        ...localSettings.preferences,
                        timezone: e.target.value,
                      },
                    })
                  }
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option>UTC</option>
                  <option>Australia/Sydney</option>
                  <option>Australia/Melbourne</option>
                  <option>Australia/Brisbane</option>
                  <option>Europe/London</option>
                  <option>Europe/Paris</option>
                  <option>US/Eastern</option>
                  <option>US/Pacific</option>
                  <option>Asia/Tokyo</option>
                  <option>Asia/Singapore</option>
                </select>
              </div>

              {/* Theme */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Theme</label>
                <select
                  value={localSettings.preferences?.theme || 'dark'}
                  onChange={(e) =>
                    setLocalSettings({
                      ...localSettings,
                      preferences: {
                        ...localSettings.preferences,
                        theme: e.target.value,
                      },
                    })
                  }
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-100 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="dark">Dark</option>
                  <option value="light">Light</option>
                  <option value="auto">Auto</option>
                </select>
              </div>

              {/* Notifications Toggle */}
              <div className="flex items-center justify-between p-4 bg-gray-700/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <Bell size={18} className="text-blue-400" />
                  <div>
                    <p className="font-medium">Enable Notifications</p>
                    <p className="text-xs text-gray-400">Get alerts for important events</p>
                  </div>
                </div>
                <button
                  onClick={() =>
                    setLocalSettings({
                      ...localSettings,
                      preferences: {
                        ...localSettings.preferences,
                        notifications_enabled: !localSettings.preferences?.notifications_enabled,
                      },
                    })
                  }
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    localSettings.preferences?.notifications_enabled ? 'bg-blue-600' : 'bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      localSettings.preferences?.notifications_enabled ? 'translate-x-5' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {/* Auto-save Toggle */}
              <div className="flex items-center justify-between p-4 bg-gray-700/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <Save size={18} className="text-green-400" />
                  <div>
                    <p className="font-medium">Auto-save Conversations</p>
                    <p className="text-xs text-gray-400">Automatically save chat history</p>
                  </div>
                </div>
                <button
                  onClick={() =>
                    setLocalSettings({
                      ...localSettings,
                      preferences: {
                        ...localSettings.preferences,
                        auto_save_conversations: !localSettings.preferences?.auto_save_conversations,
                      },
                    })
                  }
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    localSettings.preferences?.auto_save_conversations ? 'bg-green-600' : 'bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      localSettings.preferences?.auto_save_conversations ? 'translate-x-5' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* API Keys Management */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-700 flex items-center gap-2">
              <Lock size={20} className="text-red-400" />
              <h2 className="text-lg font-semibold">API Keys Management</h2>
            </div>
            <div className="p-6 space-y-4">
              {keyError && (
                <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 flex items-start gap-3">
                  <AlertCircle size={18} className="text-red-400 flex-shrink-0 mt-0.5" />
                  <p className="text-red-300 text-sm">{keyError}</p>
                </div>
              )}

              {/* Current API Keys Summary */}
              {!loadingKeys && Object.keys(apiKeys).length > 0 && (
                <div className="bg-green-900/20 border border-green-700 rounded-lg p-4">
                  <p className="text-sm font-medium text-green-300 mb-3">
                    ✓ {Object.values(apiKeys).filter(Boolean).length} service(s) configured
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {Object.entries(apiKeys).map(([service, hasKey]) =>
                      hasKey ? (
                        <div
                          key={service}
                          className="flex items-center justify-between p-2 bg-gray-700/50 rounded border border-gray-600"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <div className="w-2 h-2 bg-green-400 rounded-full flex-shrink-0" />
                            <span className="text-xs font-medium text-gray-300 truncate capitalize">
                              {availableServices.find(s => s.id === service)?.label.replace(/[^a-zA-Z0-9\s]/g, '') || service}
                            </span>
                          </div>
                          <button
                            onClick={() => handleDeleteApiKey(service)}
                            className="p-0.5 hover:bg-red-900/40 rounded text-red-400 transition-colors flex-shrink-0 ml-1"
                            title="Delete API key"
                          >
                            <X size={14} />
                          </button>
                        </div>
                      ) : null
                    )}
                  </div>
                </div>
              )}

              {/* Add New API Key Form */}
              <div className="bg-gray-700/30 border border-gray-600 rounded-lg p-4 space-y-3">
                <div className="flex items-center gap-2 mb-4">
                  <Plus size={18} className="text-blue-400" />
                  <p className="text-sm font-medium text-gray-300">Add New API Key</p>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm text-gray-400 font-medium">Select Service</label>
                  <select
                    value={selectedService}
                    onChange={(e) => setSelectedService(e.target.value)}
                    disabled={addingKey}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-blue-500"
                  >
                    <option disabled value="">Choose a service...</option>
                    {Object.entries(servicesByCategory).map(([category, services]) => (
                      <optgroup key={category} label={category}>
                        {services.map((service) => (
                          <option key={service.id} value={service.id}>
                            {service.label}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm text-gray-400 font-medium">API Key</label>
                  <input
                    type="password"
                    value={apiKeyInput}
                    onChange={(e) => setApiKeyInput(e.target.value)}
                    disabled={addingKey}
                    placeholder="Paste your API key here..."
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:border-blue-500"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !addingKey && selectedService && apiKeyInput.trim()) {
                        handleAddApiKey();
                      }
                    }}
                  />
                  <p className="text-xs text-gray-500">
                    Keys are encrypted with Fernet cipher. Never share or commit keys to version control.
                  </p>
                </div>

                <button
                  onClick={handleAddApiKey}
                  disabled={addingKey || !apiKeyInput.trim() || !selectedService}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {addingKey ? (
                    <>
                      <div className="w-3 h-3 border-2 border-blue-300 border-t-white rounded-full animate-spin" />
                      Encrypting & Saving...
                    </>
                  ) : (
                    <>
                      <Plus size={16} />
                      Add API Key
                    </>
                  )}
                </button>
              </div>

              {/* Service Categories Reference */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-4">
                {Object.entries(servicesByCategory).map(([category, services]) => (
                  <div key={category} className="text-xs">
                    <p className="font-semibold text-gray-400 mb-1">{category}</p>
                    <ul className="space-y-0.5">
                      {services.map(service => (
                        <li key={service.id} className="text-gray-500">
                          {service.label.split(' ')[0]}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>

              <div className="bg-gray-700/30 border border-gray-600 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle size={18} className="text-yellow-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-sm mb-1">�" Security Best Practices</p>
                    <ul className="text-xs text-gray-400 space-y-1 list-disc list-inside">
                      <li>Each key is encrypted individually with Fernet cipher</li>
                      <li>Keys are only decrypted when the agent needs to use them</li>
                      <li>Never paste the same key twice - each service needs its own</li>
                      <li>Rotate keys regularly for enhanced security</li>
                      <li>Use minimal permission keys (read-only when possible)</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 justify-end pb-6">
            <button
              onClick={handleResetSettings}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              <RotateCcw size={16} />
              Reset to Defaults
            </button>
            <button
              onClick={handleSaveSettings}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {saving ? (
                <>
                  <div className="w-4 h-4 border-2 border-blue-300 border-t-white rounded-full animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save size={16} />
                  Save Settings
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { Activity, Mail, Zap, TrendingUp, Clock, CheckCircle, AlertCircle, DollarSign, ShieldAlert, Bot } from 'lucide-react';
import {
  approveAutomationSuggestion,
  getAutomationSuggestions,
  getConversations,
  getIntegrations,
  getIssues,
  rejectAutomationSuggestion,
  scanIssues,
  subscribeToRealtime,
  updateIssueStatus,
} from '../lib/api';
import type { AutomationSuggestion, Integration, Conversation, Issue } from '../types';

interface Stats {
  totalConversations: number;
  totalToolCalls: number;
  connectedIntegrations: number;
  openIssues: number;
}

interface CostData {
  total_cost: number;
  total_tokens: number;
  total_operations: number;
  by_service: Record<string, { cost: number; tokens: number; operations: number }>;
  by_date: Record<string, number>;
  days: number;
}

export default function DashboardPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [costs, setCosts] = useState<CostData | null>(null);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [suggestions, setSuggestions] = useState<AutomationSuggestion[]>([]);
  const [stats, setStats] = useState<Stats>({
    totalConversations: 0,
    totalToolCalls: 0,
    connectedIntegrations: 0,
    openIssues: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  useEffect(() => {
    return subscribeToRealtime(['issues', 'automation_suggestions', 'automations', 'integrations', 'conversation'], () => {
      void loadDashboardData();
    });
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load integrations
      const integrationData = await getIntegrations() as Integration[];
      setIntegrations(integrationData || []);
      
      // Load conversations
      const conversationData = await getConversations() as Conversation[];
      setConversations(conversationData || []);
      
      // Load costs
      try {
        const token = localStorage.getItem('auth_token');
        const costData = await fetch('/api/costs/summary?days=30', {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }).then(r => r.json());
        setCosts(costData);
      } catch {
        setCosts(null);
      }

      const [issueData, suggestionData] = await Promise.all([
        getIssues('open') as Promise<Issue[]>,
        getAutomationSuggestions('proposed') as Promise<AutomationSuggestion[]>,
      ]);
      setIssues(issueData || []);
      setSuggestions(suggestionData || []);
      
      // Calculate stats
      setStats({
        totalConversations: conversationData?.length || 0,
        totalToolCalls: conversationData?.length * 5 || 0, // Approximate: 5 interactions per conversation
        connectedIntegrations: integrationData?.length || 0,
        openIssues: issueData?.length || 0,
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getIntegrationIcon = (provider: string) => {
    const icons: Record<string, string> = {
      google: '📧',
      slack: '💬',
      telegram: '✈️',
      github: '🐙',
      stripe: '💳',
    };
    return icons[provider] || '🔗';
  };

  const getIntegrationColor = (provider: string) => {
    const colors: Record<string, string> = {
      google: 'bg-blue-900/30 border-blue-800',
      slack: 'bg-purple-900/30 border-purple-800',
      telegram: 'bg-cyan-900/30 border-cyan-800',
      github: 'bg-gray-800 border-gray-700',
      stripe: 'bg-indigo-900/30 border-indigo-800',
    };
    return colors[provider] || 'bg-gray-900 border-gray-800';
  };

  const recentConversations = conversations.slice(0, 5);
  const priorityIssues = issues.slice(0, 5);
  const topSuggestions = suggestions.slice(0, 3);

  const handleScan = async () => {
    await scanIssues();
    await loadDashboardData();
  };

  const handleIssueStatus = async (issueId: string, status: 'resolved' | 'dismissed') => {
    await updateIssueStatus(issueId, status);
    await loadDashboardData();
  };

  const handleApproveSuggestion = async (suggestionId: string) => {
    await approveAutomationSuggestion(suggestionId);
    await loadDashboardData();
  };

  const handleRejectSuggestion = async (suggestionId: string) => {
    await rejectAutomationSuggestion(suggestionId);
    await loadDashboardData();
  };

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Header */}
      <div className="border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <p className="text-sm text-gray-400 mt-1">Welcome back! Here's your AI agent overview.</p>
          </div>
          <button
            onClick={loadDashboardData}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-blue-900 border-t-blue-400 rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-400">Loading dashboard...</p>
            </div>
          </div>
        ) : (
          <div className="p-6 space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-blue-700 transition-colors">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm font-medium">Conversations</p>
                    <p className="text-3xl font-bold mt-2">{stats.totalConversations}</p>
                  </div>
                  <div className="p-3 bg-blue-900/30 rounded-lg">
                    <Activity className="text-blue-400" size={24} />
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-green-700 transition-colors">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm font-medium">Connected Integrations</p>
                    <p className="text-3xl font-bold mt-2">{stats.connectedIntegrations}</p>
                  </div>
                  <div className="p-3 bg-green-900/30 rounded-lg">
                    <CheckCircle className="text-green-400" size={24} />
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-purple-700 transition-colors">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm font-medium">Tool Calls</p>
                    <p className="text-3xl font-bold mt-2">{stats.totalToolCalls}</p>
                  </div>
                  <div className="p-3 bg-purple-900/30 rounded-lg">
                    <Zap className="text-purple-400" size={24} />
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-yellow-700 transition-colors">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm font-medium">30-Day Costs</p>
                    <p className="text-3xl font-bold mt-2">
                      {costs ? `$${costs.total_cost.toFixed(2)}` : '$0.00'}
                    </p>
                    {costs && costs.total_tokens > 0 && (
                      <p className="text-xs text-gray-500 mt-1">
                        {(costs.total_tokens / 1_000_000).toFixed(2)}M tokens
                      </p>
                    )}
                  </div>
                  <div className="p-3 bg-yellow-900/30 rounded-lg">
                    <DollarSign className="text-yellow-400" size={24} />
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-red-700 transition-colors">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm font-medium">Open Issues</p>
                    <p className="text-3xl font-bold mt-2">{stats.openIssues}</p>
                  </div>
                  <div className="p-3 bg-red-900/30 rounded-lg">
                    <ShieldAlert className="text-red-400" size={24} />
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <ShieldAlert size={20} className="text-red-400" />
                  <h2 className="text-lg font-semibold">Detected Issues</h2>
                </div>
                <button
                  onClick={handleScan}
                  className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
                >
                  Scan Now
                </button>
              </div>
              <div className="divide-y divide-gray-700">
                {priorityIssues.length > 0 ? (
                  priorityIssues.map((issue) => (
                    <div key={issue.id} className="px-6 py-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{issue.title}</p>
                            <span className={`text-xs px-2 py-0.5 rounded ${
                              issue.severity === 'high'
                                ? 'bg-red-900/40 text-red-300'
                                : issue.severity === 'medium'
                                  ? 'bg-yellow-900/40 text-yellow-300'
                                  : 'bg-blue-900/40 text-blue-300'
                            }`}>
                              {issue.severity}
                            </span>
                          </div>
                          <p className="text-sm text-gray-400 mt-1">{issue.description}</p>
                          {issue.suggested_action && (
                            <p className="text-xs text-gray-500 mt-2">Suggested action: {issue.suggested_action}</p>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleIssueStatus(issue.id, 'resolved')}
                            className="px-3 py-2 bg-green-900/30 text-green-300 rounded-lg text-xs hover:bg-green-900/40 transition-colors"
                          >
                            Resolve
                          </button>
                          <button
                            onClick={() => handleIssueStatus(issue.id, 'dismissed')}
                            className="px-3 py-2 bg-gray-700 text-gray-300 rounded-lg text-xs hover:bg-gray-600 transition-colors"
                          >
                            Dismiss
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="px-6 py-8 text-center">
                    <CheckCircle size={40} className="text-green-500 mx-auto mb-3 opacity-70" />
                    <p className="text-gray-300">No active issues detected</p>
                    <p className="text-xs text-gray-500 mt-2">Run a scan after connecting more systems to surface opportunities.</p>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-700 flex items-center gap-2">
                <Bot size={20} className="text-purple-400" />
                <h2 className="text-lg font-semibold">Automation Suggestions</h2>
              </div>
              <div className="divide-y divide-gray-700">
                {topSuggestions.length > 0 ? (
                  topSuggestions.map((suggestion) => (
                    <div key={suggestion.id} className="px-6 py-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{suggestion.name}</p>
                            <span className={`text-xs px-2 py-0.5 rounded ${
                              suggestion.risk_level === 'high'
                                ? 'bg-red-900/40 text-red-300'
                                : suggestion.risk_level === 'medium'
                                  ? 'bg-yellow-900/40 text-yellow-300'
                                  : 'bg-green-900/40 text-green-300'
                            }`}>
                              {suggestion.risk_level} risk
                            </span>
                          </div>
                          <p className="text-sm text-gray-400 mt-1">{suggestion.rationale}</p>
                          <p className="text-xs text-gray-500 mt-2">
                            Trigger: {suggestion.trigger_type === 'event'
                              ? ((suggestion.trigger_config?.event_types as string[] | undefined)?.join(', ') ?? 'event')
                              : suggestion.cron_expression}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleApproveSuggestion(suggestion.id)}
                            className="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-xs text-white transition-colors"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleRejectSuggestion(suggestion.id)}
                            className="px-3 py-2 bg-gray-700 text-gray-300 rounded-lg text-xs hover:bg-gray-600 transition-colors"
                          >
                            Reject
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="px-6 py-8 text-center">
                    <Bot size={40} className="text-purple-500 mx-auto mb-3 opacity-70" />
                    <p className="text-gray-300">No automation suggestions yet</p>
                    <p className="text-xs text-gray-500 mt-2">Suggestions appear automatically when detectors find recurring issues.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Integrations Section */}
            <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-700 flex items-center gap-2">
                <Mail size={20} className="text-blue-400" />
                <h2 className="text-lg font-semibold">Connected Integrations</h2>
                {integrations.length === 0 && (
                  <span className="text-xs bg-yellow-900/30 text-yellow-300 px-2 py-1 rounded ml-auto">
                    No integrations connected
                  </span>
                )}
              </div>
              <div className="p-6">
                {integrations.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {integrations.map((integration) => (
                      <div
                        key={integration.provider}
                        className={`border rounded-lg p-4 flex items-center justify-between ${getIntegrationColor(
                          integration.provider
                        )}`}
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{getIntegrationIcon(integration.provider)}</span>
                          <div>
                            <p className="font-medium capitalize">{integration.provider}</p>
                            <p className="text-xs text-gray-400">
                              Connected {new Date(integration.created_at || Date.now()).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <CheckCircle size={20} className="text-green-400" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <AlertCircle size={40} className="text-gray-600 mx-auto mb-3 opacity-50" />
                    <p className="text-gray-400">No integrations connected yet</p>
                    <p className="text-xs text-gray-500 mt-2">Go to Integrations to connect services</p>
                  </div>
                )}
              </div>
            </div>

            {/* Cost Breakdown */}
            {costs && Object.keys(costs.by_service).length > 0 && (
              <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-700 flex items-center gap-2">
                  <DollarSign size={20} className="text-yellow-400" />
                  <h2 className="text-lg font-semibold">Cost Breakdown (30 Days)</h2>
                </div>
                <div className="p-6">
                  <div className="space-y-3">
                    {Object.entries(costs.by_service).map(([service, data]) => (
                      <div key={service} className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg">
                        <div>
                          <p className="font-medium capitalize">{service}</p>
                          <p className="text-xs text-gray-400">
                            {Math.floor(data.operations)} operations • {(data.tokens / 1_000_000).toFixed(2)}M tokens
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold">${data.cost.toFixed(2)}</p>
                          <p className="text-xs text-gray-400">
                            {((data.cost / costs.total_cost) * 100).toFixed(1)}% of total
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Recent Activity */}
            <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-700 flex items-center gap-2">
                <Clock size={20} className="text-green-400" />
                <h2 className="text-lg font-semibold">Recent Conversations</h2>
              </div>
              <div className="divide-y divide-gray-700">
                {recentConversations.length > 0 ? (
                  recentConversations.map((conv) => (
                    <div key={conv.id} className="px-6 py-4 hover:bg-gray-700/30 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="font-medium">
                            {conv.title || 'Untitled Conversation'}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(conv.created_at || Date.now()).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="px-6 py-8 text-center">
                    <Activity size={40} className="text-gray-600 mx-auto mb-3 opacity-50" />
                    <p className="text-gray-400">No conversations yet</p>
                    <p className="text-xs text-gray-500 mt-2">Start chatting to see your activity here</p>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <TrendingUp size={20} className="text-yellow-400" />
                Quick Actions
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <a
                  href="/chat"
                  className="flex items-center gap-3 p-4 bg-blue-900/20 border border-blue-800 hover:border-blue-700 rounded-lg transition-colors"
                >
                  <Mail size={18} className="text-blue-400" />
                  <span>New Chat</span>
                </a>
                <a
                  href="/integrations"
                  className="flex items-center gap-3 p-4 bg-green-900/20 border border-green-800 hover:border-green-700 rounded-lg transition-colors"
                >
                  <CheckCircle size={18} className="text-green-400" />
                  <span>Connect Integration</span>
                </a>
                <a
                  href="/entities"
                  className="flex items-center gap-3 p-4 bg-purple-900/20 border border-purple-800 hover:border-purple-700 rounded-lg transition-colors"
                >
                  <Zap size={18} className="text-purple-400" />
                  <span>Manage Entities</span>
                </a>
                <a
                  href="/memory"
                  className="flex items-center gap-3 p-4 bg-indigo-900/20 border border-indigo-800 hover:border-indigo-700 rounded-lg transition-colors"
                >
                  <Activity size={18} className="text-indigo-400" />
                  <span>View Memory</span>
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

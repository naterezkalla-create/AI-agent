import { useState, useEffect } from 'react';
import { getAutomations, getAutomationRuns, createAutomation, updateAutomation, deleteAutomation, subscribeToRealtime } from '../lib/api';
import { Plus, Trash2, Play, Pause, Edit } from 'lucide-react';
import AutomationForm from '../components/AutomationForm';
import { useToast } from '../components/ToastContainer';
import type { Automation, AutomationRun } from '../types';

export default function AutomationsPage() {
  const [automations, setAutomations] = useState<Automation[]>([]);
  const [runs, setRuns] = useState<AutomationRun[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingAuto, setEditingAuto] = useState<Automation | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  useEffect(() => {
    void loadPageData();
  }, []);

  useEffect(() => {
    return subscribeToRealtime(['automations', 'automation_runs'], (event) => {
      if (event.type === 'automations.changed' || event.type === 'automation_runs.changed') {
        void loadPageData();
      }
    });
  }, []);

  const loadPageData = async () => {
    await Promise.all([loadAutomations(), loadRuns()]);
  };

  const loadAutomations = async () => {
    try {
      const data = await getAutomations() as Automation[];
      setAutomations(data);
    } catch {
      // API may not be available
    }
  };

  const loadRuns = async () => {
    try {
      const data = await getAutomationRuns() as AutomationRun[];
      setRuns(data);
    } catch {
      // API may not be available
    }
  };

  const handleCreateOrUpdate = async (data: {
    name: string;
    cron_expression: string;
    prompt: string;
    trigger_type: 'cron' | 'event';
    trigger_config: Record<string, unknown>;
    max_retries: number;
    retry_delay_seconds: number;
  }) => {
    setIsLoading(true);
    try {
      if (editingAuto) {
        await updateAutomation(editingAuto.id, data);
        toast.toast('Automation updated successfully', 'success');
      } else {
        await createAutomation(data);
        toast.toast('Automation created successfully', 'success');
      }
      setShowForm(false);
      setEditingAuto(undefined);
      void loadPageData();
    } catch (err) {
      toast.toast(err instanceof Error ? err.message : 'Failed to save automation', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggle = async (auto: Automation) => {
    try {
      await updateAutomation(auto.id, { enabled: !auto.enabled });
      toast.toast(auto.enabled ? 'Automation paused' : 'Automation enabled', 'info');
      void loadPageData();
    } catch (err) {
      toast.toast('Failed to toggle automation', 'error');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this automation?')) return;
    try {
      await deleteAutomation(id);
      toast.toast('Automation deleted', 'success');
      void loadPageData();
    } catch (err) {
      toast.toast('Failed to delete automation', 'error');
    }
  };

  const handleEdit = (auto: Automation) => {
    setEditingAuto(auto);
    setShowForm(true);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="border-b border-gray-800 px-6 py-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Automations</h2>
        <button
          onClick={() => {
            setEditingAuto(undefined);
            setShowForm(true);
          }}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 px-3 text-sm transition-colors"
        >
          <Plus size={16} /> New Automation
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="space-y-3 max-w-4xl">
          {automations.map((auto) => {
            const latestRun = runs.find((run) => run.automation_id === auto.id);

            return (
              <div
                key={auto.id}
                className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors"
              >
                <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-medium text-white">{auto.name}</h3>
                  <p className="text-sm text-gray-400 font-mono mt-1">
                    {auto.trigger_type === 'event'
                      ? ((auto.trigger_config?.event_types as string[] | undefined)?.join(', ') ?? 'event trigger')
                      : auto.cron_expression}
                  </p>
                  <p className="text-sm text-gray-500 mt-2 line-clamp-2">{auto.prompt}</p>
                  <div className="flex flex-wrap gap-2 mt-2">
                    <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-300">
                      {auto.trigger_type === 'event' ? 'Event-driven' : 'Scheduled'}
                    </span>
                    {auto.last_status && (
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        auto.last_status === 'succeeded'
                          ? 'bg-green-600/20 text-green-400'
                          : auto.last_status === 'retry_scheduled'
                            ? 'bg-yellow-600/20 text-yellow-300'
                            : 'bg-red-600/20 text-red-400'
                      }`}>
                        {auto.last_status.replace('_', ' ')}
                      </span>
                    )}
                  </div>
                  {auto.last_run && (
                    <p className="text-xs text-gray-600 mt-2">
                      Last run: {new Date(auto.last_run).toLocaleString()}
                    </p>
                  )}
                  {latestRun && (
                    <p className="text-xs text-gray-500 mt-1">
                      Latest run: {latestRun.status.replace('_', ' ')}
                      {latestRun.error ? ` — ${latestRun.error}` : ''}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => handleToggle(auto)}
                    className={`p-2 rounded-lg transition-colors ${
                      auto.enabled
                        ? 'bg-green-600/20 text-green-400 hover:bg-green-600/30'
                        : 'bg-gray-800 text-gray-500 hover:bg-gray-700'
                    }`}
                    title={auto.enabled ? 'Pause' : 'Enable'}
                  >
                    {auto.enabled ? <Pause size={16} /> : <Play size={16} />}
                  </button>
                  <button
                    onClick={() => handleEdit(auto)}
                    className="p-2 text-gray-500 hover:text-blue-400 transition-colors"
                    title="Edit"
                  >
                    <Edit size={16} />
                  </button>
                  <button
                    onClick={() => handleDelete(auto.id)}
                    className="p-2 text-gray-500 hover:text-red-400 transition-colors"
                    title="Delete"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              </div>
            );
          })}

          {automations.length === 0 && (
            <div className="text-center text-gray-600 mt-16">
              <p className="text-3xl mb-4">⏰</p>
              <p>No automations yet.</p>
              <p className="text-sm mt-1">Create a CRON job to have the agent act automatically.</p>
            </div>
          )}

          {runs.length > 0 && (
            <div className="mt-8">
              <h3 className="text-sm text-gray-500 uppercase mb-3">Recent Runs</h3>
              <div className="space-y-2">
                {runs.slice(0, 8).map((run) => (
                  <div key={run.id} className="bg-gray-900/60 border border-gray-800 rounded-lg px-4 py-3">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-sm text-white">
                          {automations.find((auto) => auto.id === run.automation_id)?.name ?? 'Automation run'}
                        </p>
                        <p className="text-xs text-gray-500">
                          Trigger: {run.trigger_type}
                          {run.attempt > 0 ? ` • retry ${run.attempt}` : ''}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className={`text-xs ${
                          run.status === 'succeeded'
                            ? 'text-green-400'
                            : run.status === 'retry_scheduled'
                              ? 'text-yellow-300'
                              : run.status === 'running'
                                ? 'text-blue-400'
                                : 'text-red-400'
                        }`}>
                          {run.status.replace('_', ' ')}
                        </p>
                        <p className="text-xs text-gray-600">
                          {new Date(run.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    {run.error && (
                      <p className="text-xs text-red-400 mt-2">{run.error}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {showForm && (
        <AutomationForm
          initialData={editingAuto}
          onSubmit={handleCreateOrUpdate}
          onCancel={() => {
            setShowForm(false);
            setEditingAuto(undefined);
          }}
          isLoading={isLoading}
        />
      )}
    </div>
  );
}

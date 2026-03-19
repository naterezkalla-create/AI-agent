import { useState, useEffect } from 'react';
import { getAutomations, createAutomation, updateAutomation, deleteAutomation } from '../lib/api';
import { Plus, Trash2, Play, Pause, Edit } from 'lucide-react';
import AutomationForm from '../components/AutomationForm';
import { useToast } from '../components/ToastContainer';
import type { Automation } from '../types';

export default function AutomationsPage() {
  const [automations, setAutomations] = useState<Automation[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingAuto, setEditingAuto] = useState<Automation | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  useEffect(() => {
    loadAutomations();
  }, []);

  const loadAutomations = async () => {
    try {
      const data = await getAutomations() as Automation[];
      setAutomations(data);
    } catch {
      // API may not be available
    }
  };

  const handleCreateOrUpdate = async (data: {
    name: string;
    cron_expression: string;
    prompt: string;
  }) => {
    setIsLoading(true);
    try {
      if (editingAuto) {
        await updateAutomation(editingAuto.id, data);
        toast.toast('Automation updated successfully', 'success');
      } else {
        await createAutomation(data.name, data.cron_expression, data.prompt);
        toast.toast('Automation created successfully', 'success');
      }
      setShowForm(false);
      setEditingAuto(undefined);
      loadAutomations();
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
      loadAutomations();
    } catch (err) {
      toast.toast('Failed to toggle automation', 'error');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this automation?')) return;
    try {
      await deleteAutomation(id);
      toast.toast('Automation deleted', 'success');
      loadAutomations();
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
          {automations.map((auto) => (
            <div
              key={auto.id}
              className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-medium text-white">{auto.name}</h3>
                  <p className="text-sm text-gray-400 font-mono mt-1">{auto.cron_expression}</p>
                  <p className="text-sm text-gray-500 mt-2 line-clamp-2">{auto.prompt}</p>
                  {auto.last_run && (
                    <p className="text-xs text-gray-600 mt-2">
                      Last run: {new Date(auto.last_run).toLocaleString()}
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
          ))}

          {automations.length === 0 && (
            <div className="text-center text-gray-600 mt-16">
              <p className="text-3xl mb-4">⏰</p>
              <p>No automations yet.</p>
              <p className="text-sm mt-1">Create a CRON job to have the agent act automatically.</p>
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

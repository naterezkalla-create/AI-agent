import { useState, useEffect } from 'react';
import { getAutomations, createAutomation, updateAutomation, deleteAutomation } from '../lib/api';
import { Plus, Trash2, Play, Pause } from 'lucide-react';
import type { Automation } from '../types';

export default function AutomationsPage() {
  const [automations, setAutomations] = useState<Automation[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newCron, setNewCron] = useState('0 9 * * *');
  const [newPrompt, setNewPrompt] = useState('');

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

  const handleCreate = async () => {
    if (!newName || !newPrompt) return;
    await createAutomation(newName, newCron, newPrompt);
    setShowCreate(false);
    setNewName('');
    setNewPrompt('');
    loadAutomations();
  };

  const handleToggle = async (auto: Automation) => {
    await updateAutomation(auto.id, { enabled: !auto.enabled });
    loadAutomations();
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this automation?')) return;
    await deleteAutomation(id);
    loadAutomations();
  };

  return (
    <div className="h-full flex flex-col">
      <div className="border-b border-gray-800 px-6 py-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Automations</h2>
        <button
          onClick={() => setShowCreate(true)}
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
              className="bg-gray-900 border border-gray-800 rounded-lg p-4"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium">{auto.name}</h3>
                  <p className="text-sm text-gray-400 font-mono mt-1">{auto.cron_expression}</p>
                  <p className="text-sm text-gray-500 mt-2">{auto.prompt}</p>
                  {auto.last_run && (
                    <p className="text-xs text-gray-600 mt-2">
                      Last run: {new Date(auto.last_run).toLocaleString()}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleToggle(auto)}
                    className={`p-2 rounded-lg transition-colors ${
                      auto.enabled
                        ? 'bg-green-600/20 text-green-400 hover:bg-green-600/30'
                        : 'bg-gray-800 text-gray-500 hover:bg-gray-700'
                    }`}
                  >
                    {auto.enabled ? <Pause size={16} /> : <Play size={16} />}
                  </button>
                  <button
                    onClick={() => handleDelete(auto.id)}
                    className="p-2 text-gray-500 hover:text-red-400 transition-colors"
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

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">New Automation</h3>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-400 block mb-1">Name</label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g., Morning briefing"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 block mb-1">CRON Expression</label>
                <input
                  type="text"
                  value={newCron}
                  onChange={(e) => setNewCron(e.target.value)}
                  placeholder="0 9 * * *"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white font-mono placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-600 mt-1">minute hour day month weekday</p>
              </div>
              <div>
                <label className="text-sm text-gray-400 block mb-1">Prompt</label>
                <textarea
                  value={newPrompt}
                  onChange={(e) => setNewPrompt(e.target.value)}
                  placeholder="What should the agent do when this fires?"
                  rows={4}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreate}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors"
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

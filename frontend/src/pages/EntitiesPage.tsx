import { useState, useEffect } from 'react';
import { getEntities, createEntity, deleteEntity } from '../lib/api';
import { Plus, Trash2, Search } from 'lucide-react';
import type { Entity } from '../types';

export default function EntitiesPage() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [filter, setFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [newType, setNewType] = useState('contact');
  const [newData, setNewData] = useState('{\n  "name": "",\n  "email": ""\n}');

  useEffect(() => {
    loadEntities();
  }, []);

  const loadEntities = async () => {
    try {
      const data = await getEntities() as Entity[];
      setEntities(data);
    } catch {
      // API may not be available yet
    }
  };

  const handleCreate = async () => {
    try {
      const data = JSON.parse(newData);
      await createEntity(newType, data);
      setShowCreate(false);
      setNewData('{\n  "name": "",\n  "email": ""\n}');
      loadEntities();
    } catch (e) {
      alert(`Error: ${e instanceof Error ? e.message : 'Invalid JSON'}`);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this entity?')) return;
    await deleteEntity(id);
    loadEntities();
  };

  const filtered = filter
    ? entities.filter(
        (e) =>
          e.type.toLowerCase().includes(filter.toLowerCase()) ||
          JSON.stringify(e.data).toLowerCase().includes(filter.toLowerCase())
      )
    : entities;

  return (
    <div className="h-full flex flex-col">
      <div className="border-b border-gray-800 px-6 py-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Entities / CRM</h2>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 px-3 text-sm transition-colors"
        >
          <Plus size={16} /> New Entity
        </button>
      </div>

      {/* Search */}
      <div className="px-6 py-3 border-b border-gray-800">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter entities..."
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Entity list */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="space-y-3 max-w-4xl">
          {filtered.map((entity) => (
            <div
              key={entity.id}
              className="bg-gray-900 border border-gray-800 rounded-lg p-4"
            >
              <div className="flex items-start justify-between mb-2">
                <span className="text-xs font-mono bg-blue-600/20 text-blue-400 px-2 py-0.5 rounded">
                  {entity.type}
                </span>
                <button
                  onClick={() => handleDelete(entity.id)}
                  className="text-gray-500 hover:text-red-400 transition-colors"
                >
                  <Trash2 size={14} />
                </button>
              </div>
              <pre className="text-sm text-gray-300 whitespace-pre-wrap">
                {JSON.stringify(entity.data, null, 2)}
              </pre>
              <p className="text-xs text-gray-600 mt-2">
                Created: {new Date(entity.created_at).toLocaleString()}
              </p>
            </div>
          ))}

          {filtered.length === 0 && (
            <p className="text-center text-gray-600 mt-16">No entities yet. Create one or let the agent manage them.</p>
          )}
        </div>
      </div>

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Create Entity</h3>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-400 block mb-1">Type</label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="contact">Contact</option>
                  <option value="deal">Deal</option>
                  <option value="note">Note</option>
                  <option value="call_log">Call Log</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-gray-400 block mb-1">Data (JSON)</label>
                <textarea
                  value={newData}
                  onChange={(e) => setNewData(e.target.value)}
                  rows={6}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
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

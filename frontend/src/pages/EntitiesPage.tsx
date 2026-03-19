import { useState, useEffect } from 'react';
import { getEntities, createEntity, updateEntity, deleteEntity } from '../lib/api';
import { Plus, Trash2, Search, Edit } from 'lucide-react';
import EntityForm from '../components/EntityForm';
import { useToast } from '../components/ToastContainer';
import type { Entity } from '../types';

export default function EntitiesPage() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [filter, setFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingEntity, setEditingEntity] = useState<Entity | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

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

  const handleCreateOrUpdate = async (data: {
    type: string;
    data: Record<string, unknown>;
  }) => {
    setIsLoading(true);
    try {
      if (editingEntity) {
        await updateEntity(editingEntity.id, data);
        toast.toast('Entity updated successfully', 'success');
      } else {
        await createEntity(data.type, data.data);
        toast.toast('Entity created successfully', 'success');
      }
      setShowForm(false);
      setEditingEntity(undefined);
      loadEntities();
    } catch (err) {
      toast.toast(err instanceof Error ? err.message : 'Failed to save entity', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = (entity: Entity) => {
    setEditingEntity(entity);
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this entity?')) return;
    try {
      await deleteEntity(id);
      toast.toast('Entity deleted', 'success');
      loadEntities();
    } catch (err) {
      toast.toast('Failed to delete entity', 'error');
    }
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
          onClick={() => {
            setEditingEntity(undefined);
            setShowForm(true);
          }}
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
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleEdit(entity)}
                    className="p-1 text-gray-500 hover:text-blue-400 transition-colors"
                    title="Edit"
                  >
                    <Edit size={14} />
                  </button>
                  <button
                    onClick={() => handleDelete(entity.id)}
                    className="p-1 text-gray-500 hover:text-red-400 transition-colors"
                    title="Delete"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
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

      {showForm && (
        <EntityForm
          initialData={editingEntity}
          onSubmit={handleCreateOrUpdate}
          onCancel={() => {
            setShowForm(false);
            setEditingEntity(undefined);
          }}
          isLoading={isLoading}
        />
      )}
    </div>
  );
}

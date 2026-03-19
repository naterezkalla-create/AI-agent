import { useState } from 'react';
import { X } from 'lucide-react';

interface EntityFormProps {
  initialData?: {
    id: string;
    type: string;
    data: Record<string, unknown>;
  };
  onSubmit: (data: { type: string; data: Record<string, unknown> }) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

const ENTITY_TYPES = ['contact', 'company', 'lead', 'deal', 'task', 'event', 'custom'];

const TEMPLATES: Record<string, Record<string, unknown>> = {
  contact: { name: '', email: '', phone: '', company: '' },
  company: { name: '', website: '', industry: '', employees: '' },
  lead: { name: '', email: '', company: '', status: 'new' },
  deal: { name: '', value: 0, stage: 'prospecting', close_date: '' },
  task: { title: '', due_date: '', priority: 'medium', assignee: '' },
  event: { name: '', date: '', time: '', location: '' },
};

export default function EntityForm({
  initialData,
  onSubmit,
  onCancel,
  isLoading,
}: EntityFormProps) {
  const [type, setType] = useState(initialData?.type || 'contact');
  const [formData, setFormData] = useState<Record<string, unknown>>(
    initialData?.data || TEMPLATES[type] || {}
  );

  const handleChange = (key: string, value: unknown) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const handleTypeChange = (newType: string) => {
    setType(newType);
    setFormData(TEMPLATES[newType] || {});
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit({ type, data: formData });
  };

  const fields = Object.keys(formData);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-800 rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-800 sticky top-0 bg-gray-900">
          <h2 className="text-lg font-bold text-white">
            {initialData ? 'Edit Entity' : 'Create Entity'}
          </h2>
          <button
            onClick={onCancel}
            className="text-gray-500 hover:text-white transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Type */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Entity Type
            </label>
            <select
              value={type}
              onChange={(e) => handleTypeChange(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {ENTITY_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Fields */}
          {fields.map((field) => (
            <div key={field}>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' ')}
              </label>
              {typeof formData[field] === 'number' ? (
                <input
                  type="number"
                  value={formData[field]}
                  onChange={(e) => handleChange(field, Number(e.target.value))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              ) : (
                <input
                  type="text"
                  value={String(formData[field] || '')}
                  onChange={(e) => handleChange(field, e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              )}
            </div>
          ))}

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-gray-800">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 bg-gray-800 hover:bg-gray-700 text-white rounded-lg py-2 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 transition-colors disabled:opacity-50"
            >
              {isLoading ? 'Saving...' : initialData ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

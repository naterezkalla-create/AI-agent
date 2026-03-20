import { useState } from 'react';
import { X } from 'lucide-react';

interface AutomationFormProps {
  initialData?: {
    id: string;
    name: string;
    cron_expression: string;
    prompt: string;
  };
  onSubmit: (data: { name: string; cron_expression: string; prompt: string }) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

const CRON_PRESETS = [
  { label: 'Every hour', value: '0 * * * *' },
  { label: 'Every day at 9 AM', value: '0 9 * * *' },
  { label: 'Every day at 6 PM', value: '0 18 * * *' },
  { label: 'Every Monday at 9 AM', value: '0 9 * * 1' },
  { label: 'Every Friday at 5 PM', value: '0 17 * * 5' },
  { label: 'Every Sunday at midnight', value: '0 0 * * 0' },
];

const AUTOMATION_TEMPLATES = [
  {
    name: 'Daily Summary',
    cron_expression: '0 18 * * *',
    prompt: 'Review my conversations, entities, and calendar for today and prepare a short daily summary with priorities for tomorrow.',
  },
  {
    name: 'Lead Follow-up',
    cron_expression: '0 9 * * 1-5',
    prompt: 'Check my CRM entities for deals or contacts that have not been updated recently and suggest follow-up actions.',
  },
  {
    name: 'Calendar Digest',
    cron_expression: '0 7 * * *',
    prompt: 'Look at my Google Calendar for today and summarize key meetings, travel time, and preparation needed.',
  },
];

export default function AutomationForm({
  initialData,
  onSubmit,
  onCancel,
  isLoading,
}: AutomationFormProps) {
  const [name, setName] = useState(initialData?.name || '');
  const [cron, setCron] = useState(initialData?.cron_expression || '0 9 * * *');
  const [prompt, setPrompt] = useState(initialData?.prompt || '');
  const [usePreset, setUsePreset] = useState(true);

  const applyTemplate = (templateName: string) => {
    const template = AUTOMATION_TEMPLATES.find((item) => item.name === templateName);
    if (!template) return;
    setName(template.name);
    setCron(template.cron_expression);
    setPrompt(template.prompt);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !prompt) return;
    await onSubmit({ name, cron_expression: cron, prompt });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-800 rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-800 sticky top-0 bg-gray-900">
          <h2 className="text-lg font-bold text-white">
            {initialData ? 'Edit Automation' : 'Create Automation'}
          </h2>
          <button
            onClick={onCancel}
            className="text-gray-500 hover:text-white transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Name */}
          {!initialData && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Quick Start Template
              </label>
              <div className="grid gap-2">
                {AUTOMATION_TEMPLATES.map((template) => (
                  <button
                    key={template.name}
                    type="button"
                    onClick={() => applyTemplate(template.name)}
                    className="text-left bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg px-4 py-3 transition-colors"
                  >
                    <div className="text-sm font-medium text-white">{template.name}</div>
                    <div className="text-xs text-gray-400 mt-1">{template.prompt}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Automation Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Daily report generation"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {/* Cron Expression */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Schedule
            </label>
            <div className="space-y-2">
              <div className="flex gap-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={usePreset}
                    onChange={() => setUsePreset(true)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-gray-300">Use preset</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={!usePreset}
                    onChange={() => setUsePreset(false)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-gray-300">Custom CRON</span>
                </label>
              </div>

              {usePreset ? (
                <select
                  value={cron}
                  onChange={(e) => setCron(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {CRON_PRESETS.map((preset) => (
                    <option key={preset.value} value={preset.value}>
                      {preset.label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  value={cron}
                  onChange={(e) => setCron(e.target.value)}
                  placeholder="0 9 * * * (minute hour day month dayOfWeek)"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                />
              )}
              <p className="text-xs text-gray-500">Format: minute hour day month dayOfWeek</p>
            </div>
          </div>

          {/* Prompt */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Instruction/Prompt
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="What should the agent do when this automation runs?"
              rows={4}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              required
            />
          </div>

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
              disabled={isLoading || !name || !prompt}
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

import { useState } from 'react';
import { Wrench, ChevronDown, ChevronRight } from 'lucide-react';
import type { ToolCall } from '../types';

interface Props {
  toolCall: ToolCall;
}

export default function ToolCallCard({ toolCall }: Props) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="mb-2 bg-gray-900/50 rounded-lg border border-gray-700 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-gray-800/50 transition-colors"
      >
        <Wrench size={14} className="text-blue-400" />
        <span className="font-mono text-blue-400">{toolCall.name}</span>
        <span className="text-gray-500 text-xs ml-auto">
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </span>
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-2">
          <div>
            <p className="text-xs text-gray-500 uppercase mb-1">Input</p>
            <pre className="text-xs bg-gray-900 rounded p-2 overflow-x-auto text-gray-300">
              {JSON.stringify(toolCall.input, null, 2)}
            </pre>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase mb-1">Result</p>
            <pre className="text-xs bg-gray-900 rounded p-2 overflow-x-auto text-green-400 whitespace-pre-wrap">
              {toolCall.result}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

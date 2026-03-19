import { Search, Trash2 } from 'lucide-react';
import { useState } from 'react';
import type { Conversation } from '../types';

interface ConversationListProps {
  conversations: Conversation[];
  selectedId?: string;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onNew: () => void;
}

export default function ConversationList({
  conversations,
  selectedId,
  onSelect,
  onDelete,
  onNew,
}: ConversationListProps) {
  const [search, setSearch] = useState('');

  const filtered = search
    ? conversations.filter((c) =>
        c.title.toLowerCase().includes(search.toLowerCase())
      )
    : conversations;

  return (
    <div className="flex flex-col h-full bg-gray-950 border-r border-gray-800">
      <div className="p-4 border-b border-gray-800">
        <button
          onClick={onNew}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 px-3 text-sm font-medium transition-colors mb-4"
        >
          + New Chat
        </button>
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search conversations..."
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            {search ? 'No conversations found' : 'No conversations yet'}
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {filtered.map((conv) => (
              <div
                key={conv.id}
                className={`group flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-colors ${
                  selectedId === conv.id
                    ? 'bg-blue-600/20 border border-blue-600/50'
                    : 'hover:bg-gray-800'
                }`}
              >
                <div className="flex-1 min-w-0" onClick={() => onSelect(conv.id)}>
                  <p className="text-sm font-medium text-white truncate">{conv.title}</p>
                  <p className="text-xs text-gray-500 truncate">
                    {new Date(conv.updated_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(conv.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 transition-all"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

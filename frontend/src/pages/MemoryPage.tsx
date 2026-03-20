import { useState, useEffect } from 'react';
import { getMemoryNotes, createMemoryNote, updateMemoryNote, deleteMemoryNote, subscribeToRealtime } from '../lib/api';
import { Plus, Trash2, Brain, CheckCircle2, Archive } from 'lucide-react';
import type { MemoryNote } from '../types';

export default function MemoryPage() {
  const [notes, setNotes] = useState<MemoryNote[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newCategory, setNewCategory] = useState('general');
  const [newKey, setNewKey] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newConfidence, setNewConfidence] = useState(0.8);
  const [filterCategory, setFilterCategory] = useState('');

  useEffect(() => {
    loadNotes();
  }, []);

  useEffect(() => {
    return subscribeToRealtime(['memory'], (event) => {
      if (event.type === 'memory.changed') {
        void loadNotes();
      }
    });
  }, []);

  const loadNotes = async () => {
    try {
      const data = await getMemoryNotes() as MemoryNote[];
      setNotes(data);
    } catch {
      // API may not be available
    }
  };

  const handleCreate = async () => {
    if (!newKey || !newContent) return;
    await createMemoryNote(newCategory, newKey, newContent, newConfidence);
    setShowCreate(false);
    setNewKey('');
    setNewContent('');
    setNewConfidence(0.8);
    loadNotes();
  };

  const handleDelete = async (key: string) => {
    if (!confirm('Delete this memory note?')) return;
    await deleteMemoryNote(key);
    loadNotes();
  };

  const handleReviewStatus = async (key: string, reviewStatus: string) => {
    await updateMemoryNote(key, {
      review_status: reviewStatus,
      last_reviewed_at: new Date().toISOString(),
    });
    loadNotes();
  };

  const categories = [...new Set(notes.map((n) => n.category))];
  const filtered = filterCategory
    ? notes.filter((n) => n.category === filterCategory)
    : notes;

  return (
    <div className="h-full flex flex-col">
      <div className="border-b border-gray-800 px-6 py-3 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Memory</h2>
          <p className="text-sm text-gray-500">Long-term facts the agent remembers across conversations.</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 px-3 text-sm transition-colors"
        >
          <Plus size={16} /> Add Memory
        </button>
      </div>

      {/* Category filter */}
      {categories.length > 0 && (
        <div className="px-6 py-3 border-b border-gray-800 flex gap-2 flex-wrap">
          <button
            onClick={() => setFilterCategory('')}
            className={`px-3 py-1 rounded-full text-xs transition-colors ${
              !filterCategory ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={`px-3 py-1 rounded-full text-xs transition-colors ${
                filterCategory === cat
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-6">
        <div className="space-y-3 max-w-4xl">
          {filtered.map((note) => (
            <div
              key={note.id}
              className="bg-gray-900 border border-gray-800 rounded-lg p-4"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Brain size={14} className="text-purple-400" />
                  <span className="text-xs bg-purple-600/20 text-purple-400 px-2 py-0.5 rounded">
                    {note.category}
                  </span>
                  <span className="text-sm font-medium text-gray-200">{note.key}</span>
                  <span className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded">
                    confidence {Math.round((note.confidence ?? 0.8) * 100)}%
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded ${
                      note.review_status === 'reviewed'
                        ? 'bg-green-600/20 text-green-400'
                        : note.review_status === 'archived'
                          ? 'bg-gray-700 text-gray-300'
                          : 'bg-yellow-600/20 text-yellow-300'
                    }`}
                  >
                    {note.review_status}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleReviewStatus(note.key, 'reviewed')}
                    className="text-gray-500 hover:text-green-400 transition-colors"
                    title="Mark reviewed"
                  >
                    <CheckCircle2 size={14} />
                  </button>
                  <button
                    onClick={() => handleReviewStatus(note.key, 'archived')}
                    className="text-gray-500 hover:text-yellow-400 transition-colors"
                    title="Archive"
                  >
                    <Archive size={14} />
                  </button>
                  <button
                    onClick={() => handleDelete(note.key)}
                    className="text-gray-500 hover:text-red-400 transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
              <p className="text-sm text-gray-300 ml-6">{note.content}</p>
              <div className="text-xs text-gray-600 mt-2 ml-6 space-y-1">
                <p>Updated: {new Date(note.updated_at).toLocaleString()}</p>
                {note.last_reviewed_at && (
                  <p>Last reviewed: {new Date(note.last_reviewed_at).toLocaleString()}</p>
                )}
                <p>Source: {note.source}</p>
              </div>
            </div>
          ))}

          {filtered.length === 0 && (
            <div className="text-center text-gray-600 mt-16">
              <p className="text-3xl mb-4">🧠</p>
              <p>No memories yet.</p>
              <p className="text-sm mt-1">
                The agent will automatically save important facts, or you can add them manually.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Add Memory</h3>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-400 block mb-1">Category</label>
                <input
                  type="text"
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  placeholder="e.g., personal, business, preferences"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 block mb-1">Key</label>
                <input
                  type="text"
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  placeholder="e.g., user_timezone, favorite_language"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 block mb-1">Content</label>
                <textarea
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  placeholder="The fact to remember..."
                  rows={3}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 block mb-1">
                  Confidence ({Math.round(newConfidence * 100)}%)
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="1"
                  step="0.1"
                  value={newConfidence}
                  onChange={(e) => setNewConfidence(Number(e.target.value))}
                  className="w-full"
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
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

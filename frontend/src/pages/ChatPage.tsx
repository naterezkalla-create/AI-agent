import { useState, useEffect, useRef } from 'react';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import type { Message } from '../types';
import { streamMessage, getConversations, deleteConversation } from '../lib/api';
import { Plus, Trash2 } from 'lucide-react';

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [conversations, setConversations] = useState<{ id: string; title: string; updated_at: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadConversations();
  }, []);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const loadConversations = async () => {
    try {
      const convs = await getConversations();
      setConversations(convs);
    } catch {
      // API may not be available yet
    }
  };

  const handleSend = async (text: string) => {
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setIsLoading(true);

    try {
      let finalConversationId = conversationId;
      let completed = false;

      setMessages((prev) => [...prev, { role: 'assistant', content: '', toolCalls: [] }]);

      await streamMessage(text, conversationId, (event) => {
        if (event.type === 'text_delta') {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last?.role === 'assistant') {
              next[next.length - 1] = {
                ...last,
                content: `${last.content}${event.text ?? ''}`,
              };
            }
            return next;
          });
          return;
        }

        if (event.type === 'tool_call_end') {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last?.role === 'assistant') {
              const existingCalls = last.toolCalls ?? [];
              next[next.length - 1] = {
                ...last,
                toolCalls: [
                  ...existingCalls,
                  {
                    name: event.name ?? 'tool',
                    input: event.input ?? {},
                    result: event.result ?? '',
                  },
                ],
              };
            }
            return next;
          });
          return;
        }

        if (event.type === 'done') {
          completed = true;
          if (event.conversation_id) {
            finalConversationId = event.conversation_id;
            setConversationId(event.conversation_id);
          }
        }
      });

      if (!completed) {
        throw new Error('Stream ended before completion');
      }

      if (finalConversationId) {
        setConversationId(finalConversationId);
      }
      void loadConversations();
    } catch (err) {
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { role: 'assistant', content: `Error: ${err instanceof Error ? err.message : 'Unknown error'}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(undefined);
  };

  const handleDeleteConversation = async (id: string) => {
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (conversationId === id) {
        handleNewChat();
      }
    } catch {
      // ignore
    }
  };

  return (
    <div className="flex h-full">
      {/* Conversation list */}
      <div className="w-64 bg-gray-900/50 border-r border-gray-800 hidden md:flex flex-col">
        <div className="p-3 border-b border-gray-800">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 px-3 text-sm transition-colors"
          >
            <Plus size={16} />
            New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm ${
                conversationId === conv.id
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-400 hover:bg-gray-800/50 hover:text-white'
              }`}
              onClick={() => setConversationId(conv.id)}
            >
              <span className="flex-1 truncate">{conv.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteConversation(conv.id);
                }}
                className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 transition-opacity"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-800 px-6 py-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Chat</h2>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="max-w-4xl mx-auto">
            {messages.length === 0 && !isLoading && (
              <div className="text-center text-gray-600 mt-32">
                <p className="text-4xl mb-4">🤖</p>
                <p className="text-xl font-medium">How can I help you?</p>
                <p className="text-sm mt-2">I can search the web, manage your CRM, run code, and more.</p>
              </div>
            )}

            {messages.map((msg, i) => (
              <ChatMessage key={i} message={msg} />
            ))}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="bg-gray-800 text-gray-100 rounded-2xl px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <ChatInput onSend={handleSend} disabled={isLoading} />
      </div>
    </div>
  );
}

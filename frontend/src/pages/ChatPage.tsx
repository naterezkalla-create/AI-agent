import { useState, useEffect, useRef } from 'react';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import ConversationList from '../components/ConversationList';
import ConversationExport from '../components/ConversationExport';
import TypingIndicator from '../components/TypingIndicator';
import ErrorBoundary from '../components/ErrorBoundary';
import type { Message, Conversation } from '../types';
import { streamMessage, getConversations, getConversationMessages, deleteConversation } from '../lib/api';

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [conversations, setConversations] = useState<Conversation[]>([]);
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
      const convs = await getConversations() as { id: string; title: string; updated_at: string }[];
      // Add created_at field (using updated_at as fallback since API doesn't return it)
      const conversationsWithCreatedAt = convs.map(c => ({
        ...c,
        created_at: c.updated_at
      }));
      setConversations(conversationsWithCreatedAt);
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

  const handleSelectConversation = (id: string) => {
    void (async () => {
      setConversationId(id);
      setIsLoading(true);

      try {
        const history = await getConversationMessages(id);
        const restoredMessages: Message[] = history.flatMap((message) => {
          if (typeof message.content === 'string') {
            return [{ role: message.role === 'system' ? 'assistant' : message.role, content: message.content }];
          }

          const toolCalls = message.content
            .filter((item): item is { name?: string; input?: Record<string, unknown>; result?: string } =>
              typeof item === 'object' && item !== null && 'name' in item,
            )
            .map((item) => ({
              name: item.name ?? 'tool',
              input: item.input ?? {},
              result: item.result ?? '',
            }));

          const textParts = message.content
            .filter((item): item is { type?: string; text?: string; content?: string } => typeof item === 'object' && item !== null)
            .map((item) => {
              if (item.type === 'text' && item.text) return item.text;
              if (typeof item.content === 'string') return item.content;
              return '';
            })
            .filter(Boolean);

          return [
            {
              role: message.role === 'system' ? 'assistant' : message.role,
              content: textParts.join('\n').trim(),
              toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
            },
          ];
        });

        setMessages(restoredMessages);
      } catch (error) {
        setMessages([
          {
            role: 'assistant',
            content: `Error loading conversation: ${error instanceof Error ? error.message : 'Unknown error'}`,
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    })();
  };

  return (
    <div className="flex h-full">
      {/* Conversation list - hidden on mobile */}
      <div className="w-64 hidden md:flex bg-gray-950">
        <ConversationList
          conversations={conversations}
          selectedId={conversationId}
          onSelect={handleSelectConversation}
          onDelete={handleDeleteConversation}
          onNew={handleNewChat}
        />
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-800 px-6 py-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Chat</h2>
          {conversationId && messages.length > 0 && (
            <ConversationExport messages={messages} conversationId={conversationId} />
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.length === 0 && !isLoading && (
              <div className="text-center text-gray-600 mt-32">
                <p className="text-4xl mb-4">🤖</p>
                <p className="text-xl font-medium">How can I help you?</p>
                <p className="text-sm mt-2">I can search the web, manage your CRM, run code, and more.</p>
              </div>
            )}

            {messages.map((msg, i) => (
              <ErrorBoundary key={i}>
                <ChatMessage message={msg} />
              </ErrorBoundary>
            ))}

            {/* Typing indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-800 rounded-2xl px-4 py-3">
                  <TypingIndicator />
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

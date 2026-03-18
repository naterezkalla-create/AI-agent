import ReactMarkdown from 'react-markdown';
import type { Message as MessageType } from '../types';
import ToolCallCard from './ToolCallCard';

interface Props {
  message: MessageType;
}

export default function ChatMessage({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-gray-800 text-gray-100'
        }`}
      >
        {/* Tool calls */}
        {message.toolCalls?.map((tc, i) => (
          <ToolCallCard key={i} toolCall={tc} />
        ))}

        {/* Message content */}
        <div className="prose prose-invert prose-sm max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

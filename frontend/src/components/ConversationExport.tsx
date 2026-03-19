import { Download } from 'lucide-react';
import type { Message } from '../types';

interface ConversationExportProps {
  messages: Message[];
  conversationId: string;
}

export default function ConversationExport({ messages, conversationId }: ConversationExportProps) {
  const exportAsJSON = () => {
    const data = {
      conversationId,
      exportedAt: new Date().toISOString(),
      messages,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    downloadFile(blob, `conversation-${conversationId}.json`);
  };

  const exportAsMarkdown = () => {
    let markdown = `# Conversation Export\n\n**Exported:** ${new Date().toLocaleString()}\n\n---\n\n`;
    
    messages.forEach((msg) => {
      const role = msg.role === 'user' ? '👤 You' : '🤖 Agent';
      markdown += `## ${role}\n\n${msg.content}\n\n`;
      if (msg.toolCalls && msg.toolCalls.length > 0) {
        markdown += `### Tools Used\n\n`;
        msg.toolCalls.forEach((tool) => {
          markdown += `- **${tool.name}**: ${tool.result?.substring(0, 100) || 'In progress'}\n`;
        });
        markdown += `\n`;
      }
    });

    const blob = new Blob([markdown], { type: 'text/markdown' });
    downloadFile(blob, `conversation-${conversationId}.md`);
  };

  const downloadFile = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex gap-2">
      <button
        onClick={exportAsJSON}
        className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors text-sm"
        title="Export as JSON"
      >
        <Download size={16} /> JSON
      </button>
      <button
        onClick={exportAsMarkdown}
        className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors text-sm"
        title="Export as Markdown"
      >
        <Download size={16} /> Markdown
      </button>
    </div>
  );
}

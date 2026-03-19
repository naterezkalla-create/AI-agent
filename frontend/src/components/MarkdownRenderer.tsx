import { useMemo } from 'react';

interface MarkdownRendererProps {
  content: string;
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const rendered = useMemo(() => {
    let html = content;

    // Code blocks
    html = html.replace(/```[\w]*\n([\s\S]*?)```/g, (match, code) => {
      // Extract language from code block if present
      match.split('\n')[0].replace(/```/g, '').trim();
      return `<pre class="bg-gray-900 border border-gray-700 rounded p-3 my-2 overflow-x-auto"><code class="text-sm text-gray-300">${escapeHtml(code.trim())}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-900 px-1.5 py-0.5 rounded text-sm text-red-300 font-mono">$1</code>');

    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-bold text-white">$1</strong>');

    // Italic
    html = html.replace(/\*([^*]+)\*/g, '<em class="italic">$1</em>');

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:underline">$1</a>');

    // Headers
    html = html.replace(/^### (.*?)$/gm, '<h3 class="text-lg font-semibold text-white mt-3 mb-2">$1</h3>');
    html = html.replace(/^## (.*?)$/gm, '<h2 class="text-xl font-bold text-white mt-4 mb-2">$1</h2>');
    html = html.replace(/^# (.*?)$/gm, '<h1 class="text-2xl font-bold text-white mt-4 mb-2">$1</h1>');

    // Lists
    html = html.replace(/^\* (.*?)$/gm, '<li class="ml-4 text-gray-300">$1</li>');
    html = html.replace(/(<li[^>]*>.*?<\/li>)/s, '<ul class="list-disc my-2">$1</ul>');

    // Line breaks
    html = html.replace(/\n\n/g, '<br class="my-2" />');

    return html;
  }, [content]);

  return (
    <div
      className="prose prose-invert max-w-none text-gray-300"
      dangerouslySetInnerHTML={{ __html: rendered }}
    />
  );
}

function escapeHtml(text: string): string {
  const map: { [key: string]: string } = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}

import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useMutation } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Sparkles, Send } from 'lucide-react';

type Message = {
  id: number;
  text: string;
  sender: 'user' | 'ai';
};

// Render the AI's markdown (tables, bold, lists) with styles that fit the dark
// chat bubble, instead of dumping raw "| ... |" / "**" syntax as plain text.
function MarkdownMessage({ text }: { text: string }) {
  return (
    <div className="space-y-2 [&_p]:m-0 [&_ul]:my-1 [&_ul]:pl-4 [&_ul]:list-disc [&_ol]:my-1 [&_ol]:pl-4 [&_ol]:list-decimal [&_li]:my-0.5 [&_strong]:text-white [&_strong]:font-semibold [&_code]:bg-black/40 [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-[12px]">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({ children }) => (
            <div className="overflow-x-auto my-2 rounded-lg border border-[var(--border-soft)]">
              <table className="w-full text-[12px] border-collapse">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-white/5">{children}</thead>,
          th: ({ children }) => (
            <th className="text-left font-semibold text-white px-2 py-1.5 border-b border-[var(--border-soft)]">{children}</th>
          ),
          td: ({ children }) => (
            <td className="px-2 py-1.5 border-b border-[var(--border-soft)]/60">{children}</td>
          ),
          a: ({ children, href }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-[var(--color-brand-accent)] underline">{children}</a>
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}

const sendMessageToApi = async (message: string) => {
  const response = await axios.post('/api/v1/ml/chat', { message });
  return response.data.reply;
};

const SUGGESTED_PROMPTS = [
  "What's our total revenue?",
  'Which item should I promote?',
  'Summarize the 7-day forecast',
];

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, text: 'Hi! I\'m your AI analyst. I use RAG + Gemini and look at the DB, reports, and docs. Ask me in English or Russian — what would you like to know?', sender: 'ai' },
  ]);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  const mutation = useMutation({
    mutationFn: sendMessageToApi,
    onSuccess: (data) => {
      setMessages((prev) => [...prev, { id: Date.now(), text: data, sender: 'ai' }]);
    },
    onError: (error: any) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          text: `Couldn't get a response: ${error.response?.data?.detail || error.message}`,
          sender: 'ai',
        },
      ]);
    },
  });

  // Keep the latest message in view as the conversation grows.
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, mutation.isPending]);

  const handleSend = (overrideText?: string) => {
    const text = (overrideText ?? input).trim();
    if (!text || mutation.isPending) return;

    const newUserMessage: Message = { id: Date.now(), text, sender: 'user' };
    setMessages((prev) => [...prev, newUserMessage]);

    mutation.mutate(text);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full min-w-0 glass-card rounded-3xl overflow-hidden shadow-2xl">
      {/* Chat header */}
      <div
        className="px-6 py-4 border-b border-[var(--border-soft)] flex-shrink-0"
        style={{ background: 'linear-gradient(120deg, rgba(110,123,255,0.28), rgba(139,92,246,0.20))' }}
      >
        <h3 className="text-base font-bold text-white flex items-center gap-2.5 font-display">
          <span className="w-7 h-7 rounded-lg flex items-center justify-center bg-white/15 backdrop-blur">
            <Sparkles size={15} className="text-white" />
          </span>
          AI Assistant
          <span className="ml-auto flex items-center gap-1.5 text-[10px] font-semibold text-white/80 normal-case tracking-normal">
            <span className="online-dot" /> RAG + Gemini
          </span>
        </h3>
      </div>

      {/* Message list */}
      <div ref={scrollRef} className="flex-1 p-6 overflow-y-auto space-y-5 min-h-0">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fade-up`}>
            <div
              className={`px-4 py-3 rounded-2xl max-w-[85%] text-[14px] leading-relaxed ${
                msg.sender === 'user'
                  ? 'text-white shadow-lg rounded-br-md'
                  : 'glass text-[var(--color-brand-text)] rounded-bl-md'
              }`}
              style={msg.sender === 'user' ? { background: 'linear-gradient(135deg, #6e7bff, #8b5cf6)', boxShadow: '0 10px 26px -10px rgba(110,123,255,0.6)' } : undefined}
            >
              {msg.sender === 'ai' ? <MarkdownMessage text={msg.text} /> : msg.text}
            </div>
          </div>
        ))}
        {mutation.isPending && (
          <div className="flex justify-start animate-fade-up">
             <div className="px-4 py-3 rounded-2xl rounded-bl-md glass flex items-center gap-2">
                 <span className="text-[var(--color-brand-accent)] text-sm font-medium">Analyzing data</span>
                 <span className="flex gap-1">
                    {[0, 1, 2].map((i) => (
                        <span key={i} className="w-1.5 h-1.5 rounded-full bg-[var(--color-brand-accent)] animate-bounce" style={{ animationDelay: `${i * 150}ms` }} />
                    ))}
                 </span>
             </div>
          </div>
        )}
        {messages.length === 1 && !mutation.isPending && (
          <div className="flex flex-wrap gap-2 justify-start pl-1 pt-1">
            {SUGGESTED_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handleSend(prompt)}
                className="btn-outline-grad text-xs font-medium px-3 py-1.5 rounded-full text-[var(--color-brand-muted)] hover:text-white transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Input row */}
      <div className="p-4 border-t border-[var(--border-soft)] bg-white/[0.02] flex gap-3 flex-shrink-0">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          className="flex-1 min-w-0 bg-[var(--color-brand-bg)] border border-[var(--border-soft)] text-white rounded-xl px-4 py-3 outline-none focus:border-[var(--color-brand-accent)] transition-colors placeholder:text-[var(--color-brand-faint)]"
          placeholder="Ask me about the data…"
          disabled={mutation.isPending}
        />
        <button
          onClick={() => handleSend()}
          disabled={mutation.isPending}
          className="btn-accent flex-shrink-0 flex items-center gap-2 text-white px-5 py-3 rounded-xl font-bold disabled:opacity-50"
        >
          <Send size={16} />
          <span className="hidden sm:inline">{mutation.isPending ? '…' : 'Send'}</span>
        </button>
      </div>
    </div>
  );
}

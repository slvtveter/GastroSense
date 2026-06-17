import { useState } from 'react';
import axios from 'axios';
import { useMutation } from '@tanstack/react-query';

type Message = {
  id: number;
  text: string;
  sender: 'user' | 'ai';
};

const sendMessageToApi = async (message: string) => {
  const response = await axios.post('http://localhost:8000/api/v1/ml/chat', { message });
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

  const handleSend = (overrideText?: string) => {
    const text = (overrideText ?? input).trim();
    if (!text || mutation.isPending) return;

    const newUserMessage: Message = { id: Date.now(), text, sender: 'user' };
    setMessages((prev) => [...prev, newUserMessage]);

    mutation.mutate(text);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full min-w-0 border border-[var(--color-brand-border)] rounded-[20px] overflow-hidden bg-[var(--color-brand-card)] shadow-2xl">
      {/* Chat header */}
      <div className="px-6 py-4 border-b border-[var(--color-brand-border)] bg-[#1e1b4b] flex-shrink-0">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
           <span className="w-2 h-2 rounded-full bg-green-400"></span>
           AI Assistant (RAG + Gemini)
        </h3>
      </div>

      {/* Message list */}
      <div className="flex-1 p-6 overflow-y-auto space-y-6 min-h-0">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`px-4 py-3 rounded-2xl max-w-[85%] text-[14px] leading-relaxed ${
              msg.sender === 'user'
                ? 'bg-[var(--color-brand-accent)] text-white shadow-lg'
                : 'bg-[#1e293b] text-[var(--color-brand-text)] border border-[var(--color-brand-border)]'
            }`}>
              {msg.text}
            </div>
          </div>
        ))}
        {mutation.isPending && (
          <div className="flex justify-start">
             <div className="px-4 py-3 rounded-2xl bg-[#1e293b] border border-[var(--color-brand-border)]">
                 <span className="animate-pulse text-[var(--color-brand-accent)]">Analyzing data...</span>
             </div>
          </div>
        )}
        {messages.length === 1 && !mutation.isPending && (
          <div className="flex flex-wrap gap-2 justify-start pl-1">
            {SUGGESTED_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handleSend(prompt)}
                className="text-xs font-medium px-3 py-1.5 rounded-full border border-[var(--color-brand-border)] text-[var(--color-brand-muted)] hover:text-white hover:border-[var(--color-brand-accent)] transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Input row */}
      <div className="p-4 border-t border-[var(--color-brand-border)] bg-[#111827] flex gap-3 flex-shrink-0">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          className="flex-1 min-w-0 bg-[var(--color-brand-card)] border border-[var(--color-brand-border)] text-white rounded-xl px-4 py-3 outline-none focus:border-[var(--color-brand-accent)] transition-colors"
          placeholder="Ask me about the data..."
          disabled={mutation.isPending}
        />
        <button
          onClick={() => handleSend()}
          disabled={mutation.isPending}
          className="flex-shrink-0 bg-gradient-to-r from-[var(--color-brand-accent)] to-[var(--color-brand-indigo)] text-white px-6 py-3 rounded-xl font-bold hover:shadow-lg transition-transform hover:-translate-y-0.5 disabled:opacity-50 disabled:hover:translate-y-0"
        >
          {mutation.isPending ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
}

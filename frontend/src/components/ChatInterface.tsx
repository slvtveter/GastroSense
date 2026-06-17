import { useState } from 'react';
import axios from 'axios';
import { useMutation } from '@tanstack/react-query';

type Message = {
  id: number;
  text: string;
  sender: 'user' | 'ai';
};

// Функция для отправки запроса на бэкенд
const sendMessageToApi = async (message: string) => {
  const response = await axios.post('http://localhost:8000/api/v1/ml/chat', { message });
  return response.data.reply;
};

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, text: 'Привет! Я твой AI-аналитик. Я использую RAG + Gemini и смотрю на БД, отчёты и docs. Что тебя интересует?', sender: 'ai' },
  ]);
  const [input, setInput] = useState('');

  // Используем useMutation для асинхронного запроса
  const mutation = useMutation({
    mutationFn: sendMessageToApi,
    onSuccess: (data) => {
      // Добавляем ответ AI в список сообщений
      setMessages((prev) => [...prev, { id: Date.now(), text: data, sender: 'ai' }]);
    },
    onError: (error: any) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          text: `Не удалось получить ответ: ${error.response?.data?.detail || error.message}`,
          sender: 'ai',
        },
      ]);
    },
  });

  const handleSend = () => {
    if (!input.trim() || mutation.isPending) return;

    // Добавляем сообщение пользователя
    const newUserMessage: Message = { id: Date.now(), text: input, sender: 'user' };
    setMessages((prev) => [...prev, newUserMessage]);
    
    // Отправляем запрос на бэкенд
    mutation.mutate(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-[600px] border border-[var(--color-brand-border)] rounded-[20px] overflow-hidden bg-[var(--color-brand-card)] shadow-2xl">
      {/* Шапка чата */}
      <div className="px-6 py-4 border-b border-[var(--color-brand-border)] bg-[#1e1b4b]">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
           <span className="w-2 h-2 rounded-full bg-green-400"></span>
           AI Assistant (RAG + Gemini)
        </h3>
      </div>

      {/* Список сообщений */}
      <div className="flex-1 p-6 overflow-y-auto space-y-6">
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
                 <span className="animate-pulse text-[var(--color-brand-accent)]">Анализирую данные...</span>
             </div>
          </div>
        )}
      </div>

      {/* Поле ввода */}
      <div className="p-4 border-t border-[var(--color-brand-border)] bg-[#111827] flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          className="flex-1 bg-[var(--color-brand-card)] border border-[var(--color-brand-border)] text-white rounded-xl px-4 py-3 outline-none focus:border-[var(--color-brand-accent)] transition-colors"
          placeholder="Спроси меня о данных..."
          disabled={mutation.isPending}
        />
        <button 
          onClick={handleSend} 
          disabled={mutation.isPending}
          className="bg-gradient-to-r from-[var(--color-brand-accent)] to-[var(--color-brand-indigo)] text-white px-6 py-3 rounded-xl font-bold hover:shadow-lg transition-transform hover:-translate-y-0.5 disabled:opacity-50 disabled:hover:translate-y-0"
        >
          {mutation.isPending ? '...' : 'Отправить'}
        </button>
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import ThinkingProcess from '../components/Thinking';

interface ReasoningStep {
  type: 'reasoning' | 'response';
  content: string;
  sequence: number;
  task_id: string;
}

const Chat = () => {
  const [steps, setSteps] = useState<ReasoningStep[]>([]);
  const [message, setMessage] = useState('');

  const handleNewMessage = async (message: string) => {
    try {
      const response = await fetch('/api/v1/stream-chat/stream');
      const data = await response.json();
      setSteps(data);
    } catch (error) {
      console.error('Error fetching response:', error);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      handleNewMessage(message);
      setMessage('');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-3xl mx-auto p-4">
        {/* Chat Messages */}
        <div className="space-y-4 mb-4">
          <ThinkingProcess steps={steps} />
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="sticky bottom-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your message..."
              className="flex-1 rounded-lg border border-gray-200 p-2 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            />
            <button
              type="submit"
              className="rounded-lg bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Chat;
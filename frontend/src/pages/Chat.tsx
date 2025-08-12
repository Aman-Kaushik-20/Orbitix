import React, { useState, useEffect, useRef } from 'react';
import { Menu, X } from 'lucide-react';
import { Sidebar } from '../components/Sidebar';
import { ChatMessage } from '../components/ChatMessage';
import { ChatInput } from '../components/ChatInput';
import { ThinkingIndicator } from '../components/ThinkingIndicator';
import { ThemeSelector } from '../components/ThemeSelector';
import ThinkingProcess from '../components/Thinking';
import { useChatContext } from '../contexts/ChatContext';

const ChatPage: React.FC = () => {
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    chatHistory,
    currentChatId,
    messages,
    isThinking,
    steps,
    isLoading,
    selectChat,
    createNewChat,
    deleteChat,
    sendMessage,
  } = useChatContext();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, steps]);

  // Handle welcome messages - removed to prevent infinite loop
  // Welcome messages should be handled server-side or as part of chat creation

  const handleNewChat = async () => {
    await createNewChat();
  };

  const handleSendMessage = async (content: string, attachments?: any[]) => {
    await sendMessage(content, attachments);
  };

  if (isLoading) {
    return (
      <div className="flex h-screen bg-background text-foreground items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading chats...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setSidebarOpen(!isSidebarOpen)}
        chatHistory={chatHistory}
        currentChatId={currentChatId}
        onNewChat={handleNewChat}
        onSelectChat={selectChat}
        onDeleteChat={deleteChat}
      />
      <div className="flex-1 flex flex-col">
        <header className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSidebarOpen(!isSidebarOpen)}
              className="p-2 rounded-lg hover:bg-accent lg:hidden"
            >
              {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <h1 className="text-xl font-semibold">
              {currentChatId ? chatHistory.find(c => c.id === currentChatId)?.title : 'Chat'}
            </h1>
          </div>
          <ThemeSelector />
        </header>
        <main className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map(message => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {isThinking && <ThinkingIndicator />}
          {steps.length > 0 && <ThinkingProcess steps={steps} />}
          <div ref={messagesEndRef} />
        </main>
        <footer className="p-4 border-t">
          <ChatInput onSendMessage={handleSendMessage} />
        </footer>
      </div>
    </div>
  );
};

export default ChatPage;
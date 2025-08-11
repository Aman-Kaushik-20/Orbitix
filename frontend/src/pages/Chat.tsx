import React, { useState, useEffect, useRef } from 'react';
import { Menu, X } from 'lucide-react';
import { supabase } from '../utils/supabase';
import { ChatPreview, Message, Attachment } from '../types';
import { Sidebar } from '../components/Sidebar';
import { ChatMessage } from '../components/ChatMessage';
import { ChatInput } from '../components/ChatInput';
import { ThinkingIndicator } from '../components/ThinkingIndicator';
import { ThemeSelector } from '../components/ThemeSelector';
import ThinkingProcess from '../components/Thinking';
import { getTimeOfDay } from '../utils/time';
import { getUserLocationName } from '../utils/location';

const ChatPage: React.FC = () => {
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const [chatHistory, setChatHistory] = useState<ChatPreview[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const [steps, setSteps] = useState<any[]>([]);
  const [didShowWelcome, setDidShowWelcome] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchChatHistory = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        const { data, error } = await supabase
          .from('chats')
          .select('*')
          .eq('user_id', user.id)
          .order('updated_at', { ascending: false });

        if (error) {
          console.error('Error fetching chat history:', error);
        } else {
          const history = (data || []) as ChatPreview[];
          setChatHistory(history);
          if (history.length === 0) {
            handleNewChat();
          } else if (!currentChatId) {
            setCurrentChatId(history[0].id);
          }
        }
      }
    };
    fetchChatHistory();
  }, []);

  useEffect(() => {
    if (currentChatId) {
      const fetchMessages = async () => {
        const { data, error } = await supabase
          .from('messages')
          .select('*')
          .eq('chat_id', currentChatId)
          .order('created_at', { ascending: true });

        if (error) {
          console.error('Error fetching messages:', error);
        } else {
          setMessages(data as Message[]);

          try {
            const justLoggedIn = sessionStorage.getItem('justLoggedIn') === '1';
            if (justLoggedIn && !didShowWelcome) {
              const { data: { user } } = await supabase.auth.getUser();
              if (user) {
                const nameFromMetadata = (user.user_metadata && (user.user_metadata.full_name || user.user_metadata.name)) || '';
                const displayName = nameFromMetadata || user.email || 'Traveler';
                const timeOfDay = getTimeOfDay();
                const locationName = await getUserLocationName();
                const locationSuffix = locationName ? ` in ${locationName}` : '';
                const welcomeBackMessage: Message = {
                  id: `${Date.now().toString()}-wb`,
                  chat_id: currentChatId,
                  user_id: 'assistant',
                  role: 'assistant',
                  content: `Good ${timeOfDay}${locationSuffix}, welcome back ${displayName}! Ready to pick up your travel plans? I can search flights, compare stays, or craft a fresh itinerary—what would you like to do today?`,
                  created_at: new Date().toISOString(),
                };
                setMessages(prev => [...prev, welcomeBackMessage]);
                setDidShowWelcome(true);
                sessionStorage.removeItem('justLoggedIn');
              }
            }
          } catch {}
        }
      };
      fetchMessages();
    } else {
      setMessages([]);
    }
  }, [currentChatId, didShowWelcome]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleNewChat = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      const { data, error } = await supabase
        .from('chats')
        .insert({ user_id: user.id, title: 'New Chat' })
        .select();

      if (error) {
        console.error('Error creating new chat:', error);
      } else if (data) {
        const newChat = data[0] as ChatPreview;
        setChatHistory([newChat, ...chatHistory]);
        setCurrentChatId(newChat.id);
        const timeOfDay = getTimeOfDay();
        const nameFromMetadata = (user.user_metadata && (user.user_metadata.full_name || user.user_metadata.name)) || '';
        const displayName = nameFromMetadata || user.email || 'Traveler';
        const locationName = await getUserLocationName();
        const locationSuffix = locationName ? ` in ${locationName}` : '';
        const welcomeMessage: Message = {
          id: Date.now().toString(),
          chat_id: newChat.id,
          user_id: 'assistant',
          role: 'assistant',
          content: `Good ${timeOfDay}${locationSuffix}, ${displayName}! Welcome to Orbitix—your AI travel companion. I can find the best flights, stays, and experiences. What are you planning today?`,
          created_at: new Date().toISOString(),
        };
        setMessages([welcomeMessage]);
      }
    }
  };

  const handleSendMessage = async (content: string, attachments?: Attachment[]) => {
    if (!currentChatId) {
      await handleNewChat();
    }

    const user = (await supabase.auth.getUser()).data.user;
    const chatId = currentChatId!;

    const userMessage: Message = {
      id: Date.now().toString(),
      chat_id: chatId,
      user_id: user?.id || '',
      role: 'user',
      content,
      created_at: new Date().toISOString(),
      attachments,
    };
    setMessages(prev => [...prev, userMessage]);
    setIsThinking(true);
    setSteps([]);

    const response = await fetch('http://localhost:8080/api/v1/stream-chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: user?.id,
        chat_id: chatId,
        message: content,
        session_id: chatId,
        attachments: (attachments || []).map(a => ({
          id: a.id,
          name: a.name,
          type: a.type,
          size: a.size,
          url: a.url,
        })),
      }),
    });
    
    if (!response.body) {
      setIsThinking(false);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let done = false;

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const json = JSON.parse(line.substring(6));
          setSteps(prev => [...prev, json]);
        }
      }
    }
    setIsThinking(false);
  };

  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setSidebarOpen(!isSidebarOpen)}
        chatHistory={chatHistory}
        currentChatId={currentChatId}
        onNewChat={handleNewChat}
        onSelectChat={setCurrentChatId}
        onDeleteChat={async (chatId) => {
          await supabase.from('chats').delete().eq('id', chatId);
          setChatHistory(chatHistory.filter(c => c.id !== chatId));
          if (currentChatId === chatId) {
            setCurrentChatId(null);
          }
        }}
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

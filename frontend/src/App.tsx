import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { Sidebar } from './components/Sidebar';
import { ThinkingIndicator } from './components/ThinkingIndicator';
import { ThemeSelector } from './components/ThemeSelector';
import { Chat, Message, Attachment, StreamResponse, ChatPreview } from './types';
import { sendMessage, createNewChat } from './utils/api';
import { chatStorage, getTheme, setTheme } from './utils/storage';
import { cn } from './utils/cn';
import ChatPage from './pages/Chat';
import { useContext } from 'react';
import { ThemeContext } from './contexts/ThemeContext';

function App() {
  const [currentChat, setCurrentChat] = useState<Chat | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatPreview[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<Message | null>(null);
  const themeContext = useContext(ThemeContext);
  
  const chatContainerRef = useRef<HTMLDivElement>(null);

  
  useEffect(() => {
    loadChatHistory();
  }, []);

 
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [currentChat?.messages]);

  const loadChatHistory = async () => {
    try {
      const history = await chatStorage.getAllChatPreviews();
      const historyWithLastMessage = await Promise.all(history.map(async (chat) => {
        const fullChat = await chatStorage.getChat(chat.id);
        const lastMessage = fullChat?.messages[fullChat.messages.length - 1];
        return {
          ...chat,
          lastMessage: lastMessage?.role === 'assistant' ? lastMessage.content : '',
        };
      }));
      historyWithLastMessage.sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
      setChatHistory(historyWithLastMessage);
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  const handleNewChat = async () => {
    try {
      setIsLoading(true);
      const chatId = await createNewChat();
      
      const newChat: Chat = {
        id: chatId,
        title: 'New Chat',
        messages: [],
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      setCurrentChat(newChat);
      await chatStorage.saveChat(newChat);
      await loadChatHistory();
      setError(null);
    } catch (error) {
      setError('Failed to create new chat');
      console.error('Failed to create new chat:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectChat = async (chatId: string) => {
    try {
      const chat = await chatStorage.getChat(chatId);
      if (chat) {
        setCurrentChat(chat);
        setError(null);
      }
    } catch (error) {
      setError('Failed to load chat');
      console.error('Failed to load chat:', error);
    }
  };

  const handleDeleteChat = async (chatId: string) => {
    try {
      await chatStorage.deleteChat(chatId);
      if (currentChat?.id === chatId) {
        setCurrentChat(null);
      }
      await loadChatHistory();
    } catch (error) {
      setError('Failed to delete chat');
      console.error('Failed to delete chat:', error);
    }
  };

  const handleSendMessage = async (content: string, attachments: Attachment[]) => {
    let chatToUpdate = currentChat;

    if (!chatToUpdate) {
      const newChatId = await createNewChat();
      chatToUpdate = {
        id: newChatId,
        title: 'New Chat',
        messages: [],
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      setCurrentChat(chatToUpdate);
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date(),
      attachments,
    };

    const isFirstMessage = chatToUpdate.messages.length === 0;
    const updatedChat = {
      ...chatToUpdate,
      messages: [...chatToUpdate.messages, userMessage],
      title: isFirstMessage ? content.substring(0, 50) : chatToUpdate.title,
      updatedAt: new Date(),
    };

    setCurrentChat(updatedChat);
    await chatStorage.saveChat(updatedChat);
    await loadChatHistory();

   
    setIsStreaming(true);
    setError(null);

    let assistantMessage: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };

    setStreamingMessage(assistantMessage);

    try {
      await sendMessage(
        {
          user_id: chatToUpdate.id,
          message: content,
          session_id: chatToUpdate.id,
          attachments,
        },
        (data: StreamResponse) => {
          if (data.type === 'reasoning') {
            assistantMessage.reasoning_content = (assistantMessage.reasoning_content || '') + data.content;
          } else if (data.type === 'response') {
            assistantMessage.content += data.content;
          }
          assistantMessage.streamType = data.type;
          setStreamingMessage({ ...assistantMessage });
        },
        (error: string) => {
          setError(error);
          setIsStreaming(false);
          setStreamingMessage(null);
        },
        () => {
          
          assistantMessage.isStreaming = false;
          const finalChat = {
            ...updatedChat,
            messages: [...updatedChat.messages, assistantMessage],
            updatedAt: new Date(),
          };
          
          setCurrentChat(finalChat);
          setStreamingMessage(null);
          setIsStreaming(false);
          chatStorage.saveChat(finalChat);
          loadChatHistory();
        }
      );
    } catch (error) {
      setError('Failed to send message');
      setIsStreaming(false);
      setStreamingMessage(null);
    }
  };

  return (
    <Router>
      <div className={cn(
        'h-screen flex bg-background text-foreground',
        'transition-colors duration-200'
      )}>
        {/* Sidebar */}
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          chatHistory={chatHistory}
          currentChatId={currentChat?.id || null}
          onNewChat={handleNewChat}
          onSelectChat={handleSelectChat}
          onDeleteChat={handleDeleteChat}
        />

        {/* Main chat area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="flex items-center justify-between p-4 border-b bg-card">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-semibold">
                Global Supply Chain AI Chat
              </h1>
              {currentChat && (
                <span className="text-sm text-muted-foreground">
                  {currentChat.title}
                </span>
              )}
            </div>
            <ThemeSelector />
          </header>

          {/* Chat messages */}
          <div
            ref={chatContainerRef}
            className="flex-1 overflow-y-auto p-4 space-y-4"
          >
            {currentChat ? (
              <>
                {currentChat.messages.map((message, index) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                    isLastMessage={index === currentChat.messages.length - 1}
                  />
                ))}
                
                {/* Streaming message */}
                {streamingMessage && (
                  <ChatMessage
                    message={streamingMessage}
                    isLastMessage={true}
                  />
                )}
                
                {/* Thinking indicator */}
                {isStreaming && !streamingMessage && <ThinkingIndicator />}
              </>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <h2 className="text-2xl font-semibold mb-2">
                    Welcome to Global Supply Chain AI Chat
                  </h2>
                  <p className="text-muted-foreground mb-4">
                    Start a new conversation to begin chatting with our AI assistant.
                  </p>
                  <button
                    onClick={handleNewChat}
                    disabled={isLoading}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
                  >
                    {isLoading ? 'Creating...' : 'Start New Chat'}
                  </button>
                </div>
              </div>
            )}

            {/* Error message */}
            {error && (
              <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
                <p className="text-destructive">{error}</p>
              </div>
            )}
          </div>

          {/* Chat input */}
          {currentChat && (
            <ChatInput
              onSend={handleSendMessage}
              isStreaming={isStreaming}
              disabled={isLoading}
            />
          )}
        </div>
      </div>

      <Routes>
        <Route path="/chat" element={<ChatPage />} />
        
      </Routes>
    </Router>
  );
}

export default App;

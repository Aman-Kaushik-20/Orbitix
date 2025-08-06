import React from 'react';
import { Plus, MessageSquare, Trash2, Menu, X } from 'lucide-react';
import { ChatPreview } from '../types';
import { cn } from '../utils/cn';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  chatHistory: ChatPreview[];
  currentChatId: string | null;
  onNewChat: () => void;
  onSelectChat: (chatId: string) => void;
  onDeleteChat: (chatId: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onToggle,
  chatHistory,
  currentChatId,
  onNewChat,
  onSelectChat,
  onDeleteChat,
}) => {
  const formatDate = (date: Date) => {
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 168) { // 7 days
      return date.toLocaleDateString([], { weekday: 'short' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-80 bg-card text-card-foreground border-r',
          'transform transition-transform duration-300 ease-in-out',
          isOpen ? 'translate-x-0' : '-translate-x-full',
          'lg:translate-x-0 lg:static lg:z-auto'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">
            Chat History
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={onNewChat}
              className="p-2 rounded-lg hover:bg-accent transition-colors"
              aria-label="New chat"
            >
              <Plus className="w-5 h-5" />
            </button>
            <button
              onClick={onToggle}
              className="p-2 rounded-lg hover:bg-accent transition-colors lg:hidden"
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Chat list */}
        <div className="flex-1 overflow-y-auto">
          {chatHistory.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground">
              <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No chats yet</p>
              <p className="text-sm">Start a new conversation to get started</p>
            </div>
          ) : (
            <div className="p-2">
              {chatHistory.map((chat) => (
                <div
                  key={chat.id}
                  className={cn(
                    'group relative p-3 rounded-lg cursor-pointer transition-colors',
                    'hover:bg-accent',
                    currentChatId === chat.id && 'bg-primary/10'
                  )}
                  onClick={() => onSelectChat(chat.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium truncate">
                        {chat.title}
                      </h3>
                      <p className="text-sm text-muted-foreground truncate mt-1">
                        {chat.lastMessage || chat.preview}
                      </p>
                      <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground/80">
                        <span>{formatDate(chat.updatedAt)}</span>
                        <span>•</span>
                        <span>{chat.messageCount} messages</span>
                      </div>
                    </div>
                    
                    {/* Delete button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteChat(chat.id);
                      }}
                      className={cn(
                        'opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-destructive/10',
                        'text-destructive',
                        'transition-all duration-200'
                      )}
                      aria-label="Delete chat"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Mobile toggle button */}
      <button
        onClick={onToggle}
        className="fixed top-4 left-4 z-30 p-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 lg:hidden"
        aria-label="Toggle sidebar"
      >
        <Menu className="w-5 h-5" />
      </button>
    </>
  );
};

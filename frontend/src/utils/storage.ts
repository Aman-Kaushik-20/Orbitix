import { openDB, DBSchema, IDBPDatabase } from 'idb';
import { Chat, ChatPreview, Message } from '../types';

interface ChatDB extends DBSchema {
  chats: {
    key: string;
    value: Chat;
  };
  chatPreviews: {
    key: string;
    value: ChatPreview;
  };
  messages: {
    key: string;
    value: Message;
    indexes: { 'by-chat': string };
  };
}

class ChatStorage {
  private db: IDBPDatabase<ChatDB> | null = null;

  async init() {
    this.db = await openDB<ChatDB>('chat-db', 1, {
      upgrade(db) {
        
        if (!db.objectStoreNames.contains('chats')) {
          db.createObjectStore('chats');
        }

        
        if (!db.objectStoreNames.contains('chatPreviews')) {
          db.createObjectStore('chatPreviews');
        }

       
        if (!db.objectStoreNames.contains('messages')) {
          const messageStore = db.createObjectStore('messages');
          messageStore.createIndex('by-chat', 'chat_id');
        }
      },
    });
  }

  async saveChat(chat: Chat) {
    if (!this.db) await this.init();
    
    await this.db!.put('chats', chat, chat.id);
    
    
    const preview: ChatPreview = {
      id: chat.id,
      user_id: chat.user_id,
      title: chat.title,
      preview: chat.messages[chat.messages.length - 1]?.content.slice(0, 100) || '',
      created_at: chat.createdAt.toISOString(),
      updated_at: chat.updatedAt.toISOString(),
      messageCount: chat.messages.length,
    };
    
    await this.db!.put('chatPreviews', preview, chat.id);
  }

  async getChat(chatId: string): Promise<Chat | null> {
    if (!this.db) await this.init();
    return await this.db!.get('chats', chatId) || null;
  }

  async getAllChatPreviews(): Promise<ChatPreview[]> {
    if (!this.db) await this.init();
    return await this.db!.getAll('chatPreviews');
  }

  async deleteChat(chatId: string) {
    if (!this.db) await this.init();
    
    await this.db!.delete('chats', chatId);
    await this.db!.delete('chatPreviews', chatId);
    
    
    const messageStore = this.db!.transaction('messages', 'readwrite').objectStore('messages');
    const messageIndex = messageStore.index('by-chat');
    const messages = await messageIndex.getAll(chatId);
    
    for (const message of messages) {
      await messageStore.delete(message.id);
    }
  }

  async addMessage(chatId: string, message: Message) {
    if (!this.db) await this.init();
    
    
    await this.db!.put('messages', { ...message, chat_id: chatId }, message.id);
    
    
    const chat = await this.getChat(chatId);
    if (chat) {
      chat.messages.push(message);
      chat.updatedAt = new Date();
      await this.saveChat(chat);
    }
  }

  async getMessages(chatId: string): Promise<Message[]> {
    if (!this.db) await this.init();
    
    const messageStore = this.db!.transaction('messages', 'readonly').objectStore('messages');
    const messageIndex = messageStore.index('by-chat');
    return await messageIndex.getAll(chatId);
  }
}

export const chatStorage = new ChatStorage();


export const getTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') return 'light';
  return (localStorage.getItem('theme') as 'light' | 'dark') || 'light';
};

export const setTheme = (theme: 'light' | 'dark') => {
  if (typeof window === 'undefined') return;
  localStorage.setItem('theme', theme);
  document.documentElement.classList.toggle('dark', theme === 'dark');
}; 
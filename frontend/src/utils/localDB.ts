interface ChatData {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface MessageData {
  id: string;
  chat_id: string;
  user_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  attachments?: any[];
}

class LocalDB {
  private dbName = 'orbitix-chat-db';
  private version = 1;
  private db: IDBDatabase | null = null;

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create chats store
        if (!db.objectStoreNames.contains('chats')) {
          const chatStore = db.createObjectStore('chats', { keyPath: 'id' });
          chatStore.createIndex('user_id', 'user_id', { unique: false });
          chatStore.createIndex('updated_at', 'updated_at', { unique: false });
        }

        // Create messages store
        if (!db.objectStoreNames.contains('messages')) {
          const messageStore = db.createObjectStore('messages', { keyPath: 'id' });
          messageStore.createIndex('chat_id', 'chat_id', { unique: false });
          messageStore.createIndex('created_at', 'created_at', { unique: false });
        }
      };
    });
  }

  async saveChat(chat: ChatData): Promise<void> {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['chats'], 'readwrite');
      const store = transaction.objectStore('chats');
      const request = store.put(chat);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  async getChats(userId: string): Promise<ChatData[]> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['chats'], 'readonly');
      const store = transaction.objectStore('chats');
      const index = store.index('user_id');
      const request = index.getAll(userId);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const chats = request.result.sort((a, b) => 
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        );
        resolve(chats);
      };
    });
  }

  async deleteChat(chatId: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['chats', 'messages'], 'readwrite');
      
      // Delete chat
      const chatStore = transaction.objectStore('chats');
      chatStore.delete(chatId);

      // Delete associated messages
      const messageStore = transaction.objectStore('messages');
      const index = messageStore.index('chat_id');
      const request = index.openCursor(IDBKeyRange.only(chatId));

      request.onsuccess = () => {
        const cursor = request.result;
        if (cursor) {
          messageStore.delete(cursor.primaryKey);
          cursor.continue();
        }
      };

      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
  }

  async saveMessage(message: MessageData): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['messages'], 'readwrite');
      const store = transaction.objectStore('messages');
      const request = store.put(message);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  async getMessages(chatId: string): Promise<MessageData[]> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['messages'], 'readonly');
      const store = transaction.objectStore('messages');
      const index = store.index('chat_id');
      const request = index.getAll(chatId);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const messages = request.result.sort((a, b) => 
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        );
        resolve(messages);
      };
    });
  }

  async updateChatTitle(chatId: string, title: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['chats'], 'readwrite');
      const store = transaction.objectStore('chats');
      const request = store.get(chatId);

      request.onsuccess = () => {
        const chat = request.result;
        if (chat) {
          chat.title = title;
          chat.updated_at = new Date().toISOString();
          store.put(chat);
        }
      };

      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
  }
}

export const localDB = new LocalDB();
export type { ChatData, MessageData };
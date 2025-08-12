import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { ChatPreview, Message, Attachment } from '../types';
import { localDB } from '../utils/localDB';
import { supabase } from '../utils/supabase';
import { getTimeOfDay } from '../utils/time';
import { getUserLocationName } from '../utils/location';

interface ChatState {
  chatHistory: ChatPreview[];
  currentChatId: string | null;
  messages: Message[];
  isThinking: boolean;
  steps: any[];
  isLoading: boolean;
}

type ChatAction =
  | { type: 'SET_CHAT_HISTORY'; payload: ChatPreview[] }
  | { type: 'SET_CURRENT_CHAT'; payload: string | null }
  | { type: 'SET_MESSAGES'; payload: Message[] }
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'SET_THINKING'; payload: boolean }
  | { type: 'SET_STEPS'; payload: any[] }
  | { type: 'ADD_STEP'; payload: any }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'ADD_CHAT'; payload: ChatPreview }
  | { type: 'DELETE_CHAT'; payload: string }
  | { type: 'UPDATE_CHAT_TITLE'; payload: { id: string; title: string } };

const initialState: ChatState = {
  chatHistory: [],
  currentChatId: null,
  messages: [],
  isThinking: false,
  steps: [],
  isLoading: true,
};

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'SET_CHAT_HISTORY':
      return { ...state, chatHistory: action.payload };
    case 'SET_CURRENT_CHAT':
      return { ...state, currentChatId: action.payload };
    case 'SET_MESSAGES':
      return { ...state, messages: action.payload };
    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };
    case 'SET_THINKING':
      return { ...state, isThinking: action.payload };
    case 'SET_STEPS':
      return { ...state, steps: action.payload };
    case 'ADD_STEP':
      return { ...state, steps: [...state.steps, action.payload] };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'ADD_CHAT':
      return { ...state, chatHistory: [action.payload, ...state.chatHistory] };
    case 'DELETE_CHAT':
      return {
        ...state,
        chatHistory: state.chatHistory.filter(chat => chat.id !== action.payload),
        currentChatId: state.currentChatId === action.payload ? null : state.currentChatId,
        messages: state.currentChatId === action.payload ? [] : state.messages,
      };
    case 'UPDATE_CHAT_TITLE':
      return {
        ...state,
        chatHistory: state.chatHistory.map(chat =>
          chat.id === action.payload.id
            ? { ...chat, title: action.payload.title, updated_at: new Date().toISOString() }
            : chat
        ),
      };
    default:
      return state;
  }
}

interface ChatContextType extends ChatState {
  loadChats: () => Promise<void>;
  createNewChat: () => Promise<string>;
  selectChat: (chatId: string) => Promise<void>;
  deleteChat: (chatId: string) => Promise<void>;
  sendMessage: (content: string, attachments?: Attachment[]) => Promise<void>;
  updateChatTitle: (chatId: string, title: string) => Promise<void>;
}

const ChatContext = createContext<ChatContextType | null>(null);

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
};

interface ChatProviderProps {
  children: ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  // Initialize local database on mount
  useEffect(() => {
    const initDB = async () => {
      try {
        await localDB.init();
        await loadChats();
      } catch (error) {
        console.error('Failed to initialize local database:', error);
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };
    initDB();
  }, []);

  // Load messages when current chat changes
  useEffect(() => {
    if (state.currentChatId) {
      loadMessages(state.currentChatId);
    } else {
      dispatch({ type: 'SET_MESSAGES', payload: [] });
    }
  }, [state.currentChatId]);

  const loadChats = async (): Promise<void> => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        dispatch({ type: 'SET_LOADING', payload: false });
        return;
      }

      // Load from local storage first
      const localChats = await localDB.getChats(user.id);
      dispatch({ type: 'SET_CHAT_HISTORY', payload: localChats });

      // If no local chats, try to sync from Supabase
      if (localChats.length === 0) {
        const { data, error } = await supabase
          .from('chats')
          .select('*')
          .eq('user_id', user.id)
          .order('updated_at', { ascending: false });

        if (!error && data) {
          const supabaseChats = data as ChatPreview[];
          // Save to local storage
          for (const chat of supabaseChats) {
            await localDB.saveChat(chat);
          }
          dispatch({ type: 'SET_CHAT_HISTORY', payload: supabaseChats });
        }
      }

      // If still no chats, create a new one
      if (localChats.length === 0) {
        await createNewChat();
      } else {
        dispatch({ type: 'SET_CURRENT_CHAT', payload: localChats[0].id });
      }

      dispatch({ type: 'SET_LOADING', payload: false });
    } catch (error) {
      console.error('Error loading chats:', error);
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const loadMessages = async (chatId: string): Promise<void> => {
    try {
      // Load from local storage first
      const localMessages = await localDB.getMessages(chatId);
      dispatch({ type: 'SET_MESSAGES', payload: localMessages });

      // If no local messages, try to sync from Supabase
      if (localMessages.length === 0) {
        const { data, error } = await supabase
          .from('messages')
          .select('*')
          .eq('chat_id', chatId)
          .order('created_at', { ascending: true });

        if (!error && data) {
          const supabaseMessages = data as Message[];
          // Save to local storage
          for (const message of supabaseMessages) {
            await localDB.saveMessage(message);
          }
          dispatch({ type: 'SET_MESSAGES', payload: supabaseMessages });
        }
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const createNewChat = async (): Promise<string> => {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('No user found');

    const newChat: ChatPreview = {
      id: `local_${Date.now()}`,
      user_id: user.id,
      title: 'New Chat',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    // Save locally first
    await localDB.saveChat(newChat);
    dispatch({ type: 'ADD_CHAT', payload: newChat });
    dispatch({ type: 'SET_CURRENT_CHAT', payload: newChat.id });

    // Add welcome message
    const nameFromMetadata = (user.user_metadata && (user.user_metadata.full_name || user.user_metadata.name)) || '';
    const displayName = nameFromMetadata || user.email || 'Traveler';
    const timeOfDay = getTimeOfDay();
    const locationName = await getUserLocationName();
    const locationSuffix = locationName ? ` in ${locationName}` : '';

    const welcomeMessage: Message = {
      id: `welcome_${Date.now()}`,
      chat_id: newChat.id,
      user_id: 'assistant',
      role: 'assistant',
      content: `Good ${timeOfDay}${locationSuffix}, ${displayName}! Welcome to Orbitix—your AI travel companion. I can find the best flights, stays, and experiences. What are you planning today?`,
      created_at: new Date().toISOString(),
    };

    await localDB.saveMessage(welcomeMessage);
    dispatch({ type: 'SET_MESSAGES', payload: [welcomeMessage] });

    // Try to save to Supabase in background
    try {
      const { data, error } = await supabase
        .from('chats')
        .insert({ user_id: user.id, title: newChat.title })
        .select();

      if (!error && data) {
        const supabaseChat = data[0] as ChatPreview;
        // Update local storage with Supabase ID
        await localDB.saveChat(supabaseChat);
        dispatch({ type: 'UPDATE_CHAT_TITLE', payload: { id: newChat.id, title: supabaseChat.title } });
        dispatch({ type: 'SET_CURRENT_CHAT', payload: supabaseChat.id });
      }
    } catch (error) {
      console.error('Failed to sync chat to Supabase:', error);
    }

    return newChat.id;
  };

  const selectChat = async (chatId: string): Promise<void> => {
    dispatch({ type: 'SET_CURRENT_CHAT', payload: chatId });
    dispatch({ type: 'SET_STEPS', payload: [] });
  };

  const deleteChat = async (chatId: string): Promise<void> => {
    // Delete locally first
    await localDB.deleteChat(chatId);
    dispatch({ type: 'DELETE_CHAT', payload: chatId });

    // Try to delete from Supabase in background
    try {
      await supabase.from('chats').delete().eq('id', chatId);
    } catch (error) {
      console.error('Failed to delete chat from Supabase:', error);
    }
  };

  const sendMessage = async (content: string, attachments?: Attachment[]): Promise<void> => {
    if (!state.currentChatId) {
      await createNewChat();
    }

    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      chat_id: state.currentChatId!,
      user_id: user.id,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
      attachments,
    };

    // Check if this is the first user message (after welcome message)
    const isFirstUserMessage = state.messages.length <= 1 && state.messages.every(m => m.role === 'assistant');
    
    // Save message locally
    await localDB.saveMessage(userMessage);
    dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
    dispatch({ type: 'SET_THINKING', payload: true });
    dispatch({ type: 'SET_STEPS', payload: [] });

    // Update chat title with first user message (truncated)
    if (isFirstUserMessage) {
      const chatTitle = content.length > 50 ? content.substring(0, 50) + '...' : content;
      await updateChatTitle(state.currentChatId!, chatTitle);
    }

    // Stream response
    try {
      const response = await fetch('https://orbitix-305269403214.europe-west1.run.app/api/v1/stream-chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.id,
          chat_id: state.currentChatId,
          message: content,
          session_id: state.currentChatId,
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
        dispatch({ type: 'SET_THINKING', payload: false });
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let assistantMessage = '';

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const json = JSON.parse(line.substring(6));
            dispatch({ type: 'ADD_STEP', payload: json });

            if (json.type === 'response') {
              assistantMessage += json.content;
            } else if (json.type === 'end') {
              // Save final assistant message
              const finalMessage: Message = {
                id: `msg_${Date.now()}_assistant`,
                chat_id: state.currentChatId!,
                user_id: 'assistant',
                role: 'assistant',
                content: assistantMessage || json.final_data || 'Stream completed',
                created_at: new Date().toISOString(),
              };
              await localDB.saveMessage(finalMessage);
              dispatch({ type: 'ADD_MESSAGE', payload: finalMessage });

              // Update chat preview with assistant response (if this is the first conversation)
              const isFirstConversation = state.messages.filter(m => m.role === 'user').length === 1;
              if (isFirstConversation && assistantMessage) {
                const preview = assistantMessage.length > 80 ? assistantMessage.substring(0, 80) + '...' : assistantMessage;
                const currentChat = state.chatHistory.find(c => c.id === state.currentChatId);
                if (currentChat) {
                  const updatedChat = { ...currentChat, preview, lastMessage: preview };
                  await localDB.saveChat(updatedChat);
                  dispatch({ type: 'SET_CHAT_HISTORY', payload: state.chatHistory.map(c => 
                    c.id === state.currentChatId ? updatedChat : c
                  )});
                }
              }
            }
          }
        }
      }
      dispatch({ type: 'SET_THINKING', payload: false });
    } catch (error) {
      console.error('Error sending message:', error);
      dispatch({ type: 'SET_THINKING', payload: false });
    }
  };

  const updateChatTitle = async (chatId: string, title: string): Promise<void> => {
    await localDB.updateChatTitle(chatId, title);
    dispatch({ type: 'UPDATE_CHAT_TITLE', payload: { id: chatId, title } });

    // Try to update in Supabase in background
    try {
      await supabase.from('chats').update({ title }).eq('id', chatId);
    } catch (error) {
      console.error('Failed to update chat title in Supabase:', error);
    }
  };

  const value: ChatContextType = {
    ...state,
    loadChats,
    createNewChat,
    selectChat,
    deleteChat,
    sendMessage,
    updateChatTitle,
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
};
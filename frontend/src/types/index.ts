export interface Message {
  id: string;
  chat_id: string;
  user_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  attachments?: Attachment[];
  isStreaming?: boolean;
  streamType?: 'reasoning' | 'response' | 'error' | 'end';
  reasoning_content?: string;
}

export interface Attachment {
  id: string;
  name: string;
  type: 'image' | 'pdf' | 'file';
  size: number;
  url?: string;
  preview?: string;
}

export interface Chat {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatPreview {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  preview?: string;
  messageCount?: number;
  lastMessage?: string;
}

export interface StreamResponse {
  type: 'reasoning' | 'response' | 'end' | 'error';
  content: string;
  sequence: number;
  task_id: string;
  final_data?: any;
}

export interface ChatRequest {
  user_id?: string;
  message: string;
  session_id?: string;
  attachments: Attachment[];
}

export interface Theme {
  mode: 'light' | 'dark';
}

export interface AppState {
  currentChat: Chat | null;
  chatHistory: ChatPreview[];
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  theme: Theme;
}

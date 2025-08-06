import { ChatRequest, StreamResponse, ChatPreview } from '../types';

const API_BASE_URL = '/api/v1';

export class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

export const parseSSEStream = async (
  response: Response,
  onChunk: (data: StreamResponse) => void,
  onError: (error: string) => void,
  onComplete: () => void
) => {
  if (!response.body) {
    throw new Error('No response body');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        onComplete();
        break;
      }

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            onChunk(data);
          } catch (e) {
            console.error('Failed to parse stream data:', e);
          }
        }
      }
    }
  } catch (error) {
    onError(error instanceof Error ? error.message : 'Stream error');
  } finally {
    reader.releaseLock();
  }
};

export const sendMessage = async (
  request: ChatRequest,
  onChunk: (data: StreamResponse) => void,
  onError: (error: string) => void,
  onComplete: () => void
) => {
  try {
    const response = await fetch(`${API_BASE_URL}/stream-chat/dummy_stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new ApiError(`HTTP error! status: ${response.status}`, response.status);
    }

    await parseSSEStream(response, onChunk, onError, onComplete);
  } catch (error) {
    if (error instanceof ApiError) {
      onError(error.message);
    } else {
      onError(error instanceof Error ? error.message : 'Network error');
    }
  }
};

export const getChatHistory = async (): Promise<ChatPreview[]> => {
  
  console.log('Using local storage for chat history (dummy API mode)');
  return [];
};

export const createNewChat = async (): Promise<string> => {// For testing with dummy API, generate a new chat ID locally
  console.log('Creating new chat locally (dummy API mode)');
  return `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export const uploadFile = async (file: File): Promise<string> => {
 
  console.log('Creating local file URL (dummy API mode)');
  return URL.createObjectURL(file);
}; 
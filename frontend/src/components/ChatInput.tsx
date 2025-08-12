import React, { useState, useRef } from 'react';
import { Send, Paperclip, X, Loader2 } from 'lucide-react';
import { useAutosize } from '../hooks/useAutosize';
import { Attachment } from '../types';
import { cn } from '../utils/cn';

interface ChatInputProps {
  onSendMessage: (message: string, attachments?: Attachment[]) => void;
  isStreaming?: boolean;
  disabled?: boolean;
}

// Define the shape of the data returned from our new backend endpoint
interface UploadResponse {
  type: 'image' | 'pdf' | 'audio' | 'video' | 'file';
  url: string;
  filename: string;
}

// Updated helper function to handle multiple files in a single request
const uploadFiles = async (files: File[]): Promise<UploadResponse[]> => {
  const formData = new FormData();
  // Append all files under the key 'files', which the backend expects
  files.forEach(file => {
    formData.append('files', file);
  });

  // IMPORTANT: Replace with your actual backend URL if it differs
  const backendUrl = 'https://orbitix-305269403214.europe-west1.run.app/api/v1/upload';

  try {
    const response = await fetch(backendUrl, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'File upload failed');
    }

    const result = await response.json();
    // The backend now returns { uploaded_files: [...] }
    return result.uploaded_files;
  } catch (error) {
    console.error('File upload process failed:', error);
    alert('An error occurred during file upload. Please try again.');
    throw error;
  }
};


export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isStreaming,
  disabled = false,
}) => {
  const [message, setMessage] = useState('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useAutosize(message);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if ((!message.trim() && attachments.length === 0) || isStreaming || disabled || isUploading) return;

    onSendMessage(message.trim(), attachments);
    setMessage('');
    setAttachments([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    if (!selectedFiles.length) return;

    // 1. Validate all files before uploading
    const validFiles = selectedFiles.filter(file => {
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        alert(`File ${file.name} is too large. Maximum size is 10MB.`);
        return false;
      }
      const allowedTypes = ['image/*', 'application/pdf'];
      const isValidType = allowedTypes.some(type =>
        type === 'image/*' ? file.type.startsWith('image/') : file.type === type
      );
      if (!isValidType) {
        alert(`File type for ${file.name} is not supported. Please upload images or PDFs only.`);
        return false;
      }
      return true;
    });

    if (validFiles.length === 0) return;

    try {
      setIsUploading(true);
      // 2. Send all valid files in a single API call
      const uploadedFileData = await uploadFiles(validFiles);

      // 3. Map the response from the backend to the frontend's Attachment type
      const newAttachments = uploadedFileData.map((uploadedFile): Attachment => {
        const originalFile = validFiles.find(f => f.name === uploadedFile.filename);
        return {
          id: crypto.randomUUID(),
          name: uploadedFile.filename,
          type: uploadedFile.type === 'image' ? 'image' : 'pdf', // Adjust as needed
          size: originalFile?.size || 0,
          url: uploadedFile.url,
        };
      });

      // 4. Update the state with the new attachments
      setAttachments(prev => [...prev, ...newAttachments]);

    } catch (error) {
      // The uploadFiles function already handles showing an alert to the user
      console.error("Could not upload files.", error);
    } finally {
      setIsUploading(false);
    }

    // Reset file input so the user can select the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeAttachment = (id: string) => {
    setAttachments(prev => prev.filter(att => att.id !== id));
  };

  return (
    <div className="border-t bg-background p-4">
      {/* Upload progress indicator */}
      {isUploading && (
        <div className="mb-3 p-3 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">Uploading files...</span>
          </div>
        </div>
      )}

      {/* Attachments preview */}
      {attachments.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {attachments.map(attachment => (
            <div
              key={attachment.id}
              className="relative group"
            >
              {attachment.type === 'image' && attachment.url ? (
                // Image preview
                <div className="relative">
                  <img
                    src={attachment.url}
                    alt={attachment.name}
                    className="w-20 h-20 object-cover rounded-lg border"
                  />
                  <button
                    type="button"
                    onClick={() => removeAttachment(attachment.id)}
                    className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
                    disabled={isUploading}
                  >
                    <X className="w-3 h-3" />
                  </button>
                  <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs p-1 rounded-b-lg truncate">
                    {attachment.name}
                  </div>
                </div>
              ) : (
                // File preview (non-image)
                <div className="flex items-center gap-2 p-2 bg-muted rounded-lg">
                  <span className="text-sm truncate max-w-[200px]">
                    {attachment.name}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeAttachment(attachment.id)}
                    className="text-muted-foreground hover:text-foreground"
                    disabled={isUploading}
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex gap-3">
        {/* File upload button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isStreaming || disabled || isUploading}
          className={cn(
            'flex-shrink-0 p-2 rounded-lg border',
            'hover:bg-accent transition-colors',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
          aria-label="Attach file"
        >
          {isUploading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Paperclip className="w-5 h-5" />
          )}
        </button>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,.pdf"
          onChange={handleFileSelect}
          className="hidden"
        />

        {/* Message input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Shift+Enter for new line)"
            disabled={isStreaming || disabled || isUploading}
            className={cn(
              'w-full resize-none rounded-lg border',
              'px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary',
              'bg-background text-foreground',
              'placeholder-muted-foreground',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'min-h-[44px] max-h-[200px]'
            )}
            rows={1}
          />
        </div>

        {/* Send button */}
        <button
          type="submit"
          disabled={(!message.trim() && attachments.length === 0) || isStreaming || disabled || isUploading}
          className={cn(
            'flex-shrink-0 p-3 rounded-lg bg-primary text-primary-foreground',
            'hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary',
            'disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
          )}
          aria-label="Send message"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  );
};

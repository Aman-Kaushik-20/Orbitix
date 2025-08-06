import React, { useState, useRef } from 'react';
import { Send, Paperclip, X } from 'lucide-react';
import { useAutosize } from '../hooks/useAutosize';
import { Attachment } from '../types';
import { cn } from '../utils/cn';

interface ChatInputProps {
  onSend: (message: string, attachments: Attachment[]) => void;
  isStreaming: boolean;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ 
  onSend, 
  isStreaming, 
  disabled = false 
}) => {
  const [message, setMessage] = useState('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useAutosize(message);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isStreaming || disabled) return;

    onSend(message.trim(), attachments);
    setMessage('');
    setAttachments([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    files.forEach(file => {
      // Validate file size (10MB limit)
      if (file.size > 10 * 1024 * 1024) {
        alert(`File ${file.name} is too large. Maximum size is 10MB.`);
        return;
      }

      // Validate file type
      const allowedTypes = ['image/*', 'application/pdf'];
      const isValidType = allowedTypes.some(type => {
        if (type === 'image/*') {
          return file.type.startsWith('image/');
        }
        return file.type === type;
      });

      if (!isValidType) {
        alert(`File type ${file.type} is not supported. Please upload images or PDFs only.`);
        return;
      }

      const attachment: Attachment = {
        id: crypto.randomUUID(),
        name: file.name,
        type: file.type.startsWith('image/') ? 'image' : 'pdf',
        size: file.size,
        url: URL.createObjectURL(file),
      };

      setAttachments(prev => [...prev, attachment]);
    });

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeAttachment = (id: string) => {
    setAttachments(prev => prev.filter(att => att.id !== id));
  };

  return (
    <div className="border-t bg-background p-4">
      {/* Attachments preview */}
      {attachments.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {attachments.map(attachment => (
            <div
              key={attachment.id}
              className="flex items-center gap-2 p-2 bg-muted rounded-lg"
            >
              <span className="text-sm truncate max-w-[200px]">
                {attachment.name}
              </span>
              <button
                type="button"
                onClick={() => removeAttachment(attachment.id)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex gap-3">
        {/* File upload button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isStreaming || disabled}
          className={cn(
            'flex-shrink-0 p-2 rounded-lg border',
            'hover:bg-accent transition-colors',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
          aria-label="Attach file"
        >
          <Paperclip className="w-5 h-5" />
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
            disabled={isStreaming || disabled}
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
          disabled={!message.trim() || isStreaming || disabled}
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

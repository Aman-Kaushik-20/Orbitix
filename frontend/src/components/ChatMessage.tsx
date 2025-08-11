import React from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import { Message, Attachment } from '../types';
import { FileText, Image, File } from 'lucide-react';
import { cn } from '../utils/cn';
import CodeBlock from './CodeBlock';

interface ChatMessageProps {
  message: Message;
  isLastMessage?: boolean;
}

const AttachmentPreview: React.FC<{ attachment: Attachment }> = ({ attachment }) => {
  const getIcon = () => {
    switch (attachment.type) {
      case 'image':
        return <Image className="w-4 h-4" />;
      case 'pdf':
        return <FileText className="w-4 h-4" />;
      default:
        return <File className="w-4 h-4" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="flex items-center gap-2 p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
      {getIcon()}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{attachment.name}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {formatFileSize(attachment.size)}
        </p>
      </div>
    </div>
  );
};

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, isLastMessage }) => {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  const isSystem = message.role === 'system';

  return (
    <div
      className={cn(
        'flex gap-3 p-4 transition-all duration-200',
        isUser ? 'justify-end' : 'justify-start',
        isLastMessage && 'animate-typing'
      )}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
          <span className="text-primary-foreground text-sm font-medium">
            {isSystem ? 'S' : 'AI'}
          </span>
        </div>
      )}

      <div
        className={cn(
          'max-w-[80%] rounded-2xl px-4 py-3',
          isUser
            ? 'bg-primary text-primary-foreground'
            : isSystem
            ? 'bg-muted text-muted-foreground'
            : 'bg-card text-card-foreground border'
        )}
      >
        {/* Message content */}
        <div className="prose prose-sm max-w-none dark:prose-invert">
          {isAssistant ? (
            <ReactMarkdown
              rehypePlugins={[rehypeRaw]}
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return match ? (
                    <CodeBlock language={match[1]} value={String(children).replace(/\n$/, '')} />
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          ) : (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}
        </div>

        {/* Attachments */}
        {message.attachments && message.attachments.length > 0 && (
          <div className="mt-3 space-y-2">
            {message.attachments.map((attachment) => (
              <AttachmentPreview key={attachment.id} attachment={attachment} />
            ))}
          </div>
        )}

        {/* Timestamp */}
        <div
          className={cn(
            'text-xs mt-2',
            isUser ? 'text-primary-foreground/80' : 'text-muted-foreground'
          )}
        >
          {new Date(message.created_at).toLocaleTimeString()}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-muted rounded-full flex items-center justify-center">
          <span className="text-muted-foreground text-sm font-medium">
            U
          </span>
        </div>
      )}
    </div>
  );
};

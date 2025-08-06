import { useEffect, useRef } from 'react';

export const useAutosize = (value: string) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    
    textarea.style.height = 'auto';
    
    
    const scrollHeight = textarea.scrollHeight;
    const maxHeight = 200;
    const newHeight = Math.min(scrollHeight, maxHeight);
    
    textarea.style.height = `${newHeight}px`;
    
    
    textarea.style.overflowY = scrollHeight > maxHeight ? 'auto' : 'hidden';
  }, [value]);

  return textareaRef;
}; 
import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { cn } from '../utils/cn';

interface ThemeToggleProps {
  theme: 'light' | 'dark';
  onToggle: () => void;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ theme, onToggle }) => {
  return (
    <button
      onClick={onToggle}
      className={cn(
        'p-2 rounded-lg border border-gray-300 dark:border-gray-600',
        'hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-primary-500'
      )}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      {theme === 'light' ? (
        <Moon className="w-5 h-5" />
      ) : (
        <Sun className="w-5 h-5" />
      )}
    </button>
  );
}; 
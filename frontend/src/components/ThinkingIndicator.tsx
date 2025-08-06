import React from 'react';

export const ThinkingIndicator: React.FC = () => {
  return (
    <div className="flex gap-3 p-4">
      <div className="flex-shrink-0 w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center">
        <span className="text-white text-sm font-medium">AI</span>
      </div>
      
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">AI is thinking</span>
          <div className="thinking-dots">
            <div></div>
            <div></div>
            <div></div>
          </div>
        </div>
      </div>
    </div>
  );
}; 
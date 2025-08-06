import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Clipboard, Check } from 'lucide-react';

interface CodeBlockProps {
  language: string;
  value: string;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ language, value }) => {
  const [isCopied, setIsCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <div className="relative group">
      <SyntaxHighlighter style={tomorrow as any} language={language} PreTag="div">
        {value}
      </SyntaxHighlighter>
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 p-1.5 bg-gray-700 rounded-md text-gray-300 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white opacity-0 group-hover:opacity-100 transition-opacity"
        aria-label="Copy code"
      >
        {isCopied ? <Check className="w-4 h-4" /> : <Clipboard className="w-4 h-4" />}
      </button>
    </div>
  );
};

export default CodeBlock;

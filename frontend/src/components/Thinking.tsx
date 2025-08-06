import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronRight, Brain } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import { cn } from '../utils/cn';
import CodeBlock from './CodeBlock';

interface ReasoningStep {
  type: 'reasoning' | 'response';
  content: string;
  sequence: number;
  task_id: string;
}

interface ThinkingProcessProps {
  steps: ReasoningStep[];
  className?: string;
}

const ThinkingProcess = ({ steps, className }: ThinkingProcessProps) => {
  const [showSteps, setShowSteps] = useState(true);
  const finalResponse = steps.find(step => step.type === 'response');

  return (
    <div className={cn("space-y-4", className)}>
      {/* Thinking Process Card */}
      <motion.div
        className="overflow-hidden rounded-lg border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/30"
      >
        <div
          className="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-gray-100/50"
          onClick={() => setShowSteps(!showSteps)}
        >
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-600">
              Thought
            </span>
          </div>
          {showSteps ? (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-500" />
          )}
        </div>

        <AnimatePresence>
          {showSteps && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-3 pb-3"
            >
              {steps
                .filter(step => step.type === 'reasoning')
                .map((step, index) => (
                  <motion.div
                    key={step.sequence}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="mt-2 text-sm text-gray-500 dark:text-gray-400"
                  >
                    {step.content}
                  </motion.div>
                ))}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Final Response Card */}
      {finalResponse && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900"
        >
          <div className="prose prose-sm dark:prose-invert max-w-none">
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
              {finalResponse.content}
            </ReactMarkdown>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default ThinkingProcess;

import React from 'react';
import { TextBlock } from '../types/script';
import ReactMarkdown from 'react-markdown';

interface TextRendererProps {
  block: TextBlock;
}

const TextRenderer: React.FC<TextRendererProps> = ({ block }) => {
  return (
    <div className="prose max-w-none">
      <ReactMarkdown>{block.markdown}</ReactMarkdown>
    </div>
  );
};

export default TextRenderer;

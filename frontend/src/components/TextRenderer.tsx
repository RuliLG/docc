import React from 'react';
import { TextBlock } from '../types/script';
import ReactMarkdown from 'react-markdown';
import './TextRenderer.css';

interface TextRendererProps {
  block: TextBlock;
}

const TextRenderer: React.FC<TextRendererProps> = ({ block }) => {
  return (
    <div className="text-renderer">
      <div className="text-content">
        <ReactMarkdown>{block.markdown}</ReactMarkdown>
      </div>
    </div>
  );
};

export default TextRenderer;
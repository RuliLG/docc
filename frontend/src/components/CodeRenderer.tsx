import React, { useEffect, useState, useRef } from 'react';
import { CodeBlock, LineRange } from '../types/script';
import Editor, { Monaco } from '@monaco-editor/react';
import ReactMarkdown from 'react-markdown';
import { FileText } from 'lucide-react';
import './CodeRenderer.css';
import { env } from '../common/env';

interface CodeRendererProps {
  block: CodeBlock;
}

const CodeRenderer: React.FC<CodeRendererProps> = ({ block }) => {
  const [fileContent, setFileContent] = useState<string>('');
  const [language, setLanguage] = useState<string>('javascript');
  const monacoRef = useRef<any>(null);
  const editorRef = useRef<any>(null);
  const decorationIdsRef = useRef<string[]>([]);

  useEffect(() => {
    const fetchFileContent = async () => {
      try {
        // Fetch entire file content from backend
        const params = new URLSearchParams({
          file_path: block.file
        });

        const response = await fetch(`${env.apiUrl}/file-content?${params}`);

        if (response.ok) {
          const data = await response.json();
          setFileContent(data.content);
        } else {
          console.error('Failed to fetch file content:', response.statusText);
          setFileContent('## Error fetching file content ##');
        }
      } catch (error) {
        console.error('Error fetching file content:', error);
        setFileContent('## Error fetching file content ##');
      }
    };

    fetchFileContent();

    // Determine language from file extension
    const extension = block.file.split('.').pop()?.toLowerCase();
    const langMap: { [key: string]: string } = {
      'py': 'python',
      'js': 'javascript',
      'ts': 'typescript',
      'jsx': 'javascript',
      'tsx': 'typescript',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'c',
      'go': 'go',
      'rs': 'rust',
      'php': 'php',
      'rb': 'ruby'
    };
    setLanguage(langMap[extension || ''] || 'javascript');
  }, [block.file]);

  const getHighlightedLines = (): number[] => {
    const lines: number[] = [];
    block.relevant_lines.forEach((range: LineRange) => {
      // Handle both formats: {line: 20} and {from_line: 10, to_line: 15} or {from: 10, to: 15}
      if (range.line !== undefined && range.line !== null) {
        lines.push(range.line);
      } else if (range.from_line !== undefined && range.to_line !== undefined) {
        // Handle from_line/to_line format
        for (let i = range.from_line; i <= range.to_line; i++) {
          lines.push(i);
        }
      } else if (range.from !== undefined && range.to !== undefined) {
        // Handle from/to format
        for (let i = range.from; i <= range.to; i++) {
          lines.push(i);
        }
      }
    });
    return lines;
  };

  const handleEditorDidMount = (editor: any, monaco: Monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    // Don't apply highlighting immediately - wait for content to be loaded
  };

  const applyLineHighlighting = () => {
    if (!editorRef.current || !monacoRef.current) return;

    const highlightedLines = getHighlightedLines();
    const model = editorRef.current.getModel();
    if (!model) return;

    const totalLines = model.getLineCount();
    const decorations: any[] = [];

    // Create decorations for non-relevant lines
    for (let i = 1; i <= totalLines; i++) {
      if (!highlightedLines.includes(i)) {
        decorations.push({
          range: new monacoRef.current.Range(i, 1, i, 1),
          options: {
            isWholeLine: true,
            className: 'dimmed-line',
            inlineClassName: 'dimmed-line-inline'
          }
        });
      }
    }

    // Apply decorations - clear old ones first
    decorationIdsRef.current = editorRef.current.deltaDecorations(decorationIdsRef.current, decorations);
  };

  // Re-apply highlighting when content or relevant lines change
  useEffect(() => {
    if (fileContent && editorRef.current) {
      applyLineHighlighting();
    }
  }, [fileContent, block.relevant_lines]);

  return (
    <div className="code-renderer">
      <div className="code-section">
        <div className="file-header">
          <FileText size={16} />
          <span className="file-path">{block.file}</span>
        </div>
        <div className="editor-container">
          <Editor
            height="600px"
            language={language}
            value={fileContent}
            theme="vs-dark"
            onMount={handleEditorDidMount}
            options={{
              readOnly: true,
              fontSize: 14,
              lineNumbers: 'on',
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              automaticLayout: true,
              lineHeight: 20
            }}
          />
        </div>
      </div>

      <div className="explanation-section">
        <div className="prose prose-invert max-w-none p-4">
          <ReactMarkdown>{block.markdown}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
};

export default CodeRenderer;

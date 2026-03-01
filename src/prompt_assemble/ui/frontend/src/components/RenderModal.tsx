import React, { useState, useRef } from 'react';
import { FiX, FiCopy } from 'react-icons/fi';
import { renderPrompt } from '../utils/renderer';
import { xmlToJson } from '../utils/xmlToJson';
import '../styles/RenderModal.css';

interface RenderModalProps {
  isOpen: boolean;
  content: string;
  variables: Record<string, string>;
  allPrompts: Array<{ name: string; content: string; tags?: string[] }>;
  onClose: () => void;
}

type OutputFormat = 'xml' | 'json';
type RenderState = 'loading' | 'ready' | 'error';

const RenderModal: React.FC<RenderModalProps> = ({
  isOpen,
  content,
  variables,
  allPrompts,
  onClose,
}) => {
  const [outputFormat, setOutputFormat] = useState<OutputFormat>('xml');
  const [renderState, setRenderState] = useState<RenderState>('loading');
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const preRef = useRef<HTMLPreElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const isMouseDownOnOverlay = useRef(false);

  // Perform rendering when modal opens
  React.useEffect(() => {
    if (!isOpen) return;

    const performRender = async () => {
      try {
        setRenderState('loading');
        setError('');

        console.log('RenderModal: Starting render with', {
          contentLength: content.length,
          variablesCount: Object.keys(variables).length,
          availablePromptsCount: allPrompts.length,
        });

        // Build fetcher for prompts
        const fetchPrompt = async (name: string): Promise<string> => {
          // First check in-memory prompts
          const prompt = allPrompts.find(
            (p) => p.name.toLowerCase() === name.toLowerCase()
          );
          if (!prompt) {
            throw new Error(`Prompt not found: ${name}`);
          }

          // If we have content, return it
          if (prompt.content) {
            return prompt.content;
          }

          // Otherwise fetch from API
          try {
            const response = await fetch(`/api/prompts/${encodeURIComponent(name)}`);
            if (response.ok) {
              const data = await response.json();
              return data.content || '';
            }
          } catch (e) {
            console.warn(`Failed to fetch prompt content from API: ${name}`, e);
          }

          return '';
        };

        // Build tag finder - AND intersection (all tags must match)
        const findByTags = (tags: string[]): string[] => {
          const lowerTags = tags.map((t) => t.toLowerCase());
          console.log('findByTags: searching for tags', lowerTags, 'in', allPrompts.length, 'prompts');

          const matching = allPrompts.filter((prompt) => {
            const promptTags = (prompt.tags || []).map((t) => t.toLowerCase());
            // All requested tags must be present (AND intersection)
            return lowerTags.every((tag) => promptTags.includes(tag));
          });

          console.log('findByTags: found', matching.length, 'matching prompts:', matching.map((p) => p.name));

          // Return names in reverse order (most recent first)
          return matching.reverse().map((p) => p.name);
        };

        // Render the prompt
        const rendered = await renderPrompt(
          content,
          variables,
          fetchPrompt,
          findByTags
        );

        setOutput(rendered);
        setRenderState('ready');
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : String(err);
        setError(errorMessage);
        setRenderState('error');
      }
    };

    performRender();
  }, [isOpen, content, variables, allPrompts]);

  const handleMouseDown = (e: React.MouseEvent) => {
    isMouseDownOnOverlay.current = e.target === overlayRef.current;
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (isMouseDownOnOverlay.current && e.target === overlayRef.current) {
      onClose();
    }
    isMouseDownOnOverlay.current = false;
  };

  const handleCopy = () => {
    const textToCopy = outputFormat === 'json' ? output : output;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isOpen) return null;

  const displayOutput = outputFormat === 'json' ? xmlToJson(output) : output;

  return (
    <div
      ref={overlayRef}
      className="modal-overlay"
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
    >
      <div className="modal-content render-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header render-modal-header">
          <h2>Rendered Output</h2>
          <div className="format-toggle">
            <button
              className={`format-btn ${outputFormat === 'xml' ? 'active' : ''}`}
              onClick={() => setOutputFormat('xml')}
            >
              XML
            </button>
            <button
              className={`format-btn ${outputFormat === 'json' ? 'active' : ''}`}
              onClick={() => setOutputFormat('json')}
            >
              JSON
            </button>
          </div>
          <button className="modal-close" onClick={onClose}>
            <FiX size={24} />
          </button>
        </div>

        {/* Output Display */}
        <div className="render-modal-body">
          {renderState === 'loading' && (
            <div className="render-loading">
              <div className="spinner"></div>
              <p>Rendering...</p>
            </div>
          )}

          {renderState === 'error' && (
            <div className="render-error">
              <p className="error-title">Error during rendering:</p>
              <pre className="error-message">{error}</pre>
            </div>
          )}

          {renderState === 'ready' && (
            <pre ref={preRef} className="render-output">
              {displayOutput}
            </pre>
          )}
        </div>

        {/* Footer */}
        <div className="render-modal-footer">
          <button
            className="btn btn-secondary"
            onClick={handleCopy}
            title="Copy to clipboard"
          >
            <FiCopy size={16} />
            {copied ? 'Copied!' : 'Copy'}
          </button>
          <button className="btn btn-primary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default RenderModal;

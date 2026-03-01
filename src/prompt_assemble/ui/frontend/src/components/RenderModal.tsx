import React, { useState, useRef } from 'react';
import { FiX, FiCopy } from 'react-icons/fi';
import { renderPrompt, formatXml } from '../utils/renderer';
import { xmlToJson } from '../utils/xmlToJson';
import '../styles/RenderModal.css';

interface VariableSet {
  id: string;
  name: string;
  variables: Record<string, string>;
}

interface Document {
  id: string;
  name: string;
  content: string;
  metadata: {
    description: string;
    tags: string[];
    owner?: string;
    revisionComments?: string;
  };
  isDirty: boolean;
  isLocked: boolean;
  savedAt?: string;
  previousVersionId?: string;
  variableSetIds?: string[];
  variableOverrides?: Record<string, Record<string, string>>;
}

interface RenderModalProps {
  isOpen: boolean;
  content: string;
  variables: Record<string, string>;
  allPrompts: Array<{ name: string; content: string; tags?: string[] }>;
  documents?: Document[];
  variableSets?: VariableSet[];
  onClose: () => void;
}

type OutputFormat = 'xml' | 'json';
type RenderState = 'loading' | 'ready' | 'error';

const RenderModal: React.FC<RenderModalProps> = ({
  isOpen,
  content,
  variables,
  allPrompts,
  documents = [],
  variableSets = [],
  onClose,
}) => {
  const [outputFormat, setOutputFormat] = useState<OutputFormat>('xml');
  const [renderState, setRenderState] = useState<RenderState>('loading');
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [width, setWidth] = useState(900);
  const [height, setHeight] = useState(600);
  const [isResizing, setIsResizing] = useState(false);
  const preRef = useRef<HTMLPreElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const isMouseDownOnOverlay = useRef(false);
  const resizeStartPos = useRef({ x: 0, y: 0, width: 0, height: 0 });

  // Get merged variables for a prompt (if it's a document)
  const getPromptVariables = async (promptName: string): Promise<Record<string, string>> => {
    // Check if this prompt is a document in our documents list
    const doc = documents.find((d) => d.name.toLowerCase() === promptName.toLowerCase());
    if (!doc) {
      return {};
    }

    // Merge variables for this document
    const setIds = doc.variableSetIds || [];
    const overrides = doc.variableOverrides || {};
    let merged: Record<string, string> = {};

    for (const setId of setIds) {
      const varSet = variableSets.find((vs) => vs.id === setId);
      if (varSet) {
        merged = { ...merged, ...varSet.variables };
      }

      // Apply overrides for this set (overrides win)
      const setOverrides = overrides[setId] || {};
      merged = { ...merged, ...setOverrides };
    }

    console.log(`getPromptVariables: Found document "${promptName}" with variables:`, merged);
    return merged;
  };

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
          documentsCount: documents.length,
        });

        // Load variable set subscriptions for the current document
        let mergedVariables = { ...variables };

        // Try to get currentDocId from documents
        const currentDoc = documents.find((d) => d.content === content);
        if (currentDoc && currentDoc.name) {
          try {
            const response = await fetch(`/api/prompts/${encodeURIComponent(currentDoc.name)}/variable-sets`);
            if (response.ok) {
              const data = await response.json();
              const { variableSetIds, overrides } = data;

              // Merge variables from subscribed variable sets
              for (const varSetId of variableSetIds) {
                const varSet = variableSets.find((vs) => vs.id === varSetId);
                if (varSet && varSet.variables) {
                  // Add variables from this set
                  for (const varName in varSet.variables) {
                    mergedVariables[varName] = varSet.variables[varName];
                  }
                }
              }

              // Apply overrides (overrides take precedence)
              for (const varSetId in overrides) {
                for (const varName in overrides[varSetId]) {
                  mergedVariables[varName] = overrides[varSetId][varName];
                }
              }
            }
          } catch (e) {
            console.warn('Failed to load variable sets:', e);
          }
        }

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

        // Render the prompt with variable hierarchy support
        const rendered = await renderPrompt(
          content,
          mergedVariables,
          fetchPrompt,
          findByTags,
          getPromptVariables
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
  }, [isOpen, content, variables, allPrompts, documents, variableSets]);

  const handleMouseDown = (e: React.MouseEvent) => {
    isMouseDownOnOverlay.current = e.target === overlayRef.current;
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (isMouseDownOnOverlay.current && e.target === overlayRef.current) {
      onClose();
    }
    isMouseDownOnOverlay.current = false;
    setIsResizing(false);
  };

  const handleResizeStart = (e: React.MouseEvent) => {
    setIsResizing(true);
    resizeStartPos.current = {
      x: e.clientX,
      y: e.clientY,
      width,
      height,
    };
    e.preventDefault();
  };

  React.useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - resizeStartPos.current.x;
      const deltaY = e.clientY - resizeStartPos.current.y;

      const newWidth = Math.max(400, resizeStartPos.current.width + deltaX);
      const newHeight = Math.max(300, resizeStartPos.current.height + deltaY);

      setWidth(newWidth);
      setHeight(newHeight);
    };

    const handleMouseUpGlobal = () => {
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUpGlobal);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUpGlobal);
    };
  }, [isResizing]);

  const handleCopy = () => {
    const textToCopy = outputFormat === 'json' ? output : output;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isOpen) return null;

  const displayOutput = outputFormat === 'json' ? xmlToJson(output) : formatXml(output);

  return (
    <div
      ref={overlayRef}
      className="modal-overlay"
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
    >
      <div
        className="modal-content render-modal"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: `${width}px`,
          height: `${height}px`,
          maxWidth: '90vw',
          maxHeight: '90vh',
        }}
      >
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

        {/* Resize Handle */}
        <div
          className="resize-handle"
          onMouseDown={handleResizeStart}
          title="Drag to resize"
        />
      </div>
    </div>
  );
};

export default RenderModal;

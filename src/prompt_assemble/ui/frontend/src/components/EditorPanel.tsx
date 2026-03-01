import React, { useState, useRef, useEffect } from 'react';
import { FiArrowUp, FiChevronRight, FiChevronLeft } from 'react-icons/fi';
import CodeMirror from '@uiw/react-codemirror';
import { oneDark } from '@codemirror/theme-one-dark';
import { promptSyntaxHighlight } from '../utils/promptLanguage';
import { countTokens, formatTokenCount } from '../utils/tokenCounter';
import '../styles/EditorPanel.css';

interface Document {
  id: string;
  name: string;
  content: string;
  isDirty: boolean;
  metadata?: any;
}

interface Prompt {
  name: string;
}

interface EditorPanelProps {
  document: Document;
  allPrompts: Prompt[];
  onContentChange: (content: string) => void;
  onBookmarkJump: (line: number) => void;
}

interface AutocompleteState {
  visible: boolean;
  x: number;
  y: number;
  query: string;
  matches: string[];
  selectedIndex: number;
}

const EditorPanel: React.FC<EditorPanelProps> = ({
  document,
  allPrompts,
  onContentChange,
  onBookmarkJump,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const [autocomplete, setAutocomplete] = useState<AutocompleteState>({
    visible: false,
    x: 0,
    y: 0,
    query: '',
    matches: [],
    selectedIndex: 0,
  });
  const [bookmarks, setBookmarks] = useState<number[]>([]);
  const [history, setHistory] = useState<string[]>([document.content]);
  const [historyIndex, setHistoryIndex] = useState(0);
  const [showHints, setShowHints] = useState(() => {
    // Load from localStorage
    if (typeof window !== 'undefined') {
      const cached = window.localStorage.getItem('editor-hints-visible');
      return cached ? cached === 'true' : true; // Default: visible
    }
    return true;
  });
  const [tokenCount, setTokenCount] = useState(0);

  // Extract bookmarks from document and update token count
  useEffect(() => {
    try {
      if (!document) {
        console.warn('EditorPanel: document is undefined');
        return;
      }

      const content = document.content || '';
      const lines = content.split('\n');
      const newBookmarks = lines
        .map((line, idx) => {
          // Support both HTML comments <!-- --> and #! comments
          if (line.includes('<!--') || line.includes('#!')) {
            return idx;
          }
          return -1;
        })
        .filter((idx) => idx !== -1);
      setBookmarks(newBookmarks);

      // Update token count on document change
      setTokenCount(countTokens(content));
    } catch (error) {
      console.error('Error in EditorPanel useEffect:', error);
    }
  }, [document?.content]);

  // Save hints visibility to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('editor-hints-visible', showHints.toString());
    }
  }, [showHints]);

  const handleContentChange = (value: string) => {
    onContentChange(value);

    // Update history
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(value);
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);

    // Update token count
    setTokenCount(countTokens(value));

    // Check for autocomplete trigger - assume cursor at end of content for pasted text
    checkAutocomplete(value, value.length);
  };

  const checkAutocomplete = (content: string, cursorPos: number) => {
    // TODO: Rebuild autocomplete for CodeMirror with proper positioning
    // For now, keep disabled to prevent content display issues
    setAutocomplete({ ...autocomplete, visible: false });
  };

  const insertPrompt = (promptName: string) => {
    const content = document.content;
    // Find the most recent [[PROMPT: pattern in the content
    const lastPromptIdx = content.lastIndexOf('[[PROMPT:');

    if (lastPromptIdx !== -1) {
      const newContent =
        content.substring(0, lastPromptIdx) +
        `[[PROMPT: ${promptName}]]` +
        content.substring(lastPromptIdx + 9); // 9 = length of '[[PROMPT:'

      onContentChange(newContent);
      setAutocomplete({ ...autocomplete, visible: false });
    }
  };

  const handleKeyDown = (e: any) => {
    if (autocomplete.visible) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setAutocomplete({
          ...autocomplete,
          selectedIndex: Math.min(
            autocomplete.selectedIndex + 1,
            autocomplete.matches.length - 1
          ),
        });
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setAutocomplete({
          ...autocomplete,
          selectedIndex: Math.max(autocomplete.selectedIndex - 1, 0),
        });
      } else if (e.key === 'Enter') {
        e.preventDefault();
        insertPrompt(autocomplete.matches[autocomplete.selectedIndex]);
      } else if (e.key === 'Escape') {
        setAutocomplete({ ...autocomplete, visible: false });
      }
    } else {
      // Standard undo/redo
      if (e.ctrlKey || e.metaKey) {
        if (e.key === 'z') {
          e.preventDefault();
          handleUndo();
        } else if (e.key === 'y') {
          e.preventDefault();
          handleRedo();
        }
      }
    }
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      onContentChange(history[newIndex]);
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      const newIndex = historyIndex + 1;
      setHistoryIndex(newIndex);
      onContentChange(history[newIndex]);
    }
  };

  const handleBookmarkJump = (lineNum: number) => {
    if (textareaRef.current) {
      const lines = (document.content || '').split('\n');
      let pos = 0;
      for (let i = 0; i < Math.min(lineNum, lines.length); i++) {
        pos += lines[i].length + 1; // +1 for newline
      }
      textareaRef.current.setSelectionRange(pos, pos);
      textareaRef.current.focus();
      textareaRef.current.scrollTop =
        (lineNum / (document.content || '').split('\n').length) *
        textareaRef.current.scrollHeight;
    }
  };

  const getLineNumbers = () => {
    const lines = (document.content || '').split('\n').length;
    return Array.from({ length: lines }, (_, i) => i + 1);
  };

  // Guard against missing document
  if (!document) {
    return (
      <div className="editor-panel">
        <div style={{ padding: '20px', color: '#999' }}>
          <p>No document loaded</p>
        </div>
      </div>
    );
  }

  return (
    <div className="editor-panel">
      {/* Bookmarks and token count navigation */}
      {bookmarks.length > 0 && (
        <div className="bookmarks-bar">
          <span className="prompt-id-label">{document.name}</span>
          <span className="token-count-inline">{formatTokenCount(tokenCount)}</span>
          <span className="bookmarks-label">Bookmarks:</span>
          {bookmarks.map((line) => (
            <button
              key={line}
              className="bookmark-btn"
              onClick={() => handleBookmarkJump(line)}
            >
              Line {line + 1}
            </button>
          ))}
        </div>
      )}
      {bookmarks.length === 0 && (
        <div className="bookmarks-bar">
          <span className="prompt-id-label">{document.name}</span>
          <span className="token-count-inline">{formatTokenCount(tokenCount)}</span>
        </div>
      )}

      {/* Editor */}
      <div className="editor-wrapper">
        <CodeMirror
          value={document.content}
          height="100%"
          width="100%"
          onChange={handleContentChange}
          theme={oneDark}
          className="editor-codemirror"
          extensions={[promptSyntaxHighlight()]}
          basicSetup={{
            lineNumbers: true,
            highlightActiveLineGutter: true,
            foldGutter: true,
            dropCursor: true,
            allowMultipleSelections: true,
            indentOnInput: false,
            bracketMatching: true,
            closeBrackets: true,
            autocompletion: true,
            rectangularSelection: true,
            highlightSelectionMatches: true,
            searchKeymap: true,
          }}
        />

        {/* Syntax highlighting reference - collapsible */}
        <div className={`editor-syntax-hints ${!showHints ? 'collapsed' : ''}`}>
          <div className="hints-header">
            <span>Syntax Reference</span>
            <button
              className="hints-toggle"
              onClick={() => setShowHints(!showHints)}
              title={showHints ? 'Collapse' : 'Expand'}
            >
              {showHints ? <FiChevronRight size={16} /> : <FiChevronLeft size={16} />}
            </button>
          </div>
          {showHints && (
            <div className="hints-content">
              <div className="hint">[[VAR_NAME]] - Variable substitution</div>
              <div className="hint">[[PROMPT: name]] - Component injection</div>
              <div className="hint">[[PROMPT_TAG: tag1, tag2]] - Tag-based injection</div>
              <div className="hint">{`<!-- comment -->`} - Bookmark</div>
              <div className="hint">#! comment - Bookmark</div>
            </div>
          )}
        </div>
      </div>

      {/* Autocomplete dropdown */}
      {autocomplete.visible && (
        <div
          className="autocomplete"
          style={{
            left: autocomplete.x,
            top: autocomplete.y + 50,
          }}
        >
          {autocomplete.matches.length > 0 ? (
            <>
              <div className="autocomplete-header">
                <FiArrowUp size={14} /> Press Enter to insert
              </div>
              {autocomplete.matches.map((match, idx) => (
                <div
                  key={match}
                  className={`autocomplete-item ${
                    idx === autocomplete.selectedIndex ? 'selected' : ''
                  }`}
                  onClick={() => insertPrompt(match)}
                >
                  {match}
                </div>
              ))}
            </>
          ) : (
            <div className="autocomplete-header" style={{ color: '#999' }}>
              Start typing to match prompts
            </div>
          )}
        </div>
      )}

      {/* Status bar */}
      <div className="editor-status">
        <span>{(document.content || '').split('\n').length} lines</span>
        <span>{(document.content || '').length} characters</span>
      </div>
    </div>
  );
};

export default EditorPanel;

import React, { useState, useRef } from 'react';
import { FiX } from 'react-icons/fi';
import '../styles/ExportModal.css';

interface ExportModalProps {
  allTags: string[];
  currentPromptName?: string;
  onExport: (filters: { tags: string[]; names: string[] }) => void;
  onClose: () => void;
}

type ExportType = 'current' | 'all' | 'tags' | 'names';

const ExportModal: React.FC<ExportModalProps> = ({
  allTags,
  currentPromptName,
  onExport,
  onClose,
}) => {
  const overlayRef = useRef<HTMLDivElement>(null);
  const isMouseDownOnOverlay = useRef(false);
  const [exportType, setExportType] = useState<ExportType>(currentPromptName ? 'current' : 'all');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [searchNames, setSearchNames] = useState('');

  const handleToggleTag = (tag: string) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter((t) => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  const handleExport = () => {
    const filters = {
      tags: exportType === 'tags' ? selectedTags : [],
      names: exportType === 'current' && currentPromptName
        ? [currentPromptName]
        : (exportType === 'names' ? [searchNames] : []),
    };
    onExport(filters);
    onClose();
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    isMouseDownOnOverlay.current = e.target === overlayRef.current;
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (isMouseDownOnOverlay.current && e.target === overlayRef.current) {
      onClose();
    }
    isMouseDownOnOverlay.current = false;
  };

  return (
    <div
      ref={overlayRef}
      className="modal-overlay"
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
    >
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Export Prompts</h2>
          <button className="modal-close" onClick={onClose}>
            <FiX size={24} />
          </button>
        </div>

        <div className="modal-body">
          {/* Export Type Selection */}
          <div className="form-group">
            <label>Export Type</label>
            <div className="radio-group">
              {currentPromptName && (
                <label className="radio-option">
                  <input
                    type="radio"
                    value="current"
                    checked={exportType === 'current'}
                    onChange={(e) => setExportType(e.target.value as ExportType)}
                  />
                  <span>Export Current Prompt: <strong>{currentPromptName}</strong></span>
                </label>
              )}
              <label className="radio-option">
                <input
                  type="radio"
                  value="all"
                  checked={exportType === 'all'}
                  onChange={(e) => setExportType(e.target.value as ExportType)}
                />
                <span>Export All Prompts</span>
              </label>
              <label className="radio-option">
                <input
                  type="radio"
                  value="tags"
                  checked={exportType === 'tags'}
                  onChange={(e) => setExportType(e.target.value as ExportType)}
                />
                <span>Export by Tags (AND intersection)</span>
              </label>
              <label className="radio-option">
                <input
                  type="radio"
                  value="names"
                  checked={exportType === 'names'}
                  onChange={(e) => setExportType(e.target.value as ExportType)}
                />
                <span>Export by Name/Partial Match</span>
              </label>
            </div>
          </div>

          {/* Tags Selection */}
          {exportType === 'tags' && (
            <div className="form-group">
              <label>Select Tags</label>
              <div className="tags-grid">
                {allTags.map((tag) => (
                  <label key={tag} className="checkbox-tag">
                    <input
                      type="checkbox"
                      checked={selectedTags.includes(tag)}
                      onChange={() => handleToggleTag(tag)}
                    />
                    <span>{tag}</span>
                  </label>
                ))}
              </div>
              {selectedTags.length === 0 && (
                <p className="hint-text">Select at least one tag to export</p>
              )}
            </div>
          )}

          {/* Name Search */}
          {exportType === 'names' && (
            <div className="form-group">
              <label htmlFor="search">Prompt Name (partial match)</label>
              <input
                id="search"
                type="text"
                value={searchNames}
                onChange={(e) => setSearchNames(e.target.value)}
                placeholder="e.g., 'greeting' will match 'greeting', 'greeting_short', etc."
                className="form-input"
              />
            </div>
          )}

          {/* Export Format Info */}
          <div className="export-info">
            <p className="info-title">📦 Export Format</p>
            <p className="info-text">
              Single prompt will be saved as a <code>.prompt</code> file.<br />
              Multiple prompts will be saved as a <code>.zip</code> file containing individual <code>.prompt</code> files.
            </p>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={handleExport}
            disabled={
              (exportType === 'current' && !currentPromptName) ||
              (exportType === 'tags' && selectedTags.length === 0) ||
              (exportType === 'names' && !searchNames.trim())
            }
          >
            Export as .prompt File(s)
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExportModal;

import React, { useState, useRef } from 'react';
import { FiX } from 'react-icons/fi';
import '../styles/DocumentProperties.css';

interface Document {
  id: string;
  name: string;
  metadata: {
    description: string;
    tags: string[];
    owner?: string;
    revisionComments?: string;
  };
  savedAt?: string;
}

interface DocumentPropertiesProps {
  document: Document;
  allTags: string[];
  allPromptNames?: string[];
  onSave: (metadata: any) => void;
  onClose: () => void;
}

const DocumentProperties: React.FC<DocumentPropertiesProps> = ({
  document,
  allTags,
  allPromptNames = [],
  onSave,
  onClose,
}) => {
  const overlayRef = useRef<HTMLDivElement>(null);
  const isMouseDownOnOverlay = useRef(false);
  const [displayName, setDisplayName] = useState(document.name);
  const [description, setDescription] = useState(document.metadata.description || '');
  const [tags, setTags] = useState<string[]>(document.metadata.tags || []);
  const [owner, setOwner] = useState(document.metadata.owner || '');
  const [tagInput, setTagInput] = useState('');

  // Normalize display name to stored name (lowercase, spaces -> underscores/hyphens)
  const normalizedName = displayName
    .toLowerCase()
    .replace(/\s+/g, '_')
    .replace(/[^a-z0-9_-]/g, '');

  // Check if the name already exists (excluding current document)
  const nameExists = !!(normalizedName && normalizedName !== document.name &&
    allPromptNames.some(name => name.toLowerCase() === normalizedName.toLowerCase()));

  // Update state when document prop changes
  React.useEffect(() => {
    setDisplayName(document.name);
    setDescription(document.metadata.description || '');
    setTags(document.metadata.tags || []);
    setOwner(document.metadata.owner || '');
    setTagInput('');
  }, [document.id, document.name, document.metadata]);

  const handleAddTag = (tag: string) => {
    const trimmedTag = tag.trim().toLowerCase();
    if (trimmedTag && !tags.includes(trimmedTag)) {
      setTags([...tags, trimmedTag]);
      setTagInput('');
    }
  };

  const handleTagInputChange = (value: string) => {
    setTagInput(value);

    // Handle space or comma as delimiters
    if (value.includes(' ') || value.includes(',')) {
      const parts = value.split(/[\s,]+/);
      const newTag = parts[0];
      if (newTag) {
        handleAddTag(newTag);
      }
      setTagInput(parts[parts.length - 1]);
    }
  };

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter((t) => t !== tagToRemove));
  };

  const handleSave = () => {
    // Prevent saving with empty normalized name
    if (!normalizedName || !normalizedName.trim()) {
      return; // Button should be disabled, but this is a safety check
    }
    onSave({
      name: normalizedName,
      description,
      tags,
      owner,
    });
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
          <h2>Document Properties</h2>
          <button className="modal-close" onClick={onClose}>
            <FiX size={24} />
          </button>
        </div>

        <div className="modal-body">
          {/* Display Name */}
          <div className="form-group">
            <div className="label-with-hint">
              <label htmlFor="displayName">Display Name</label>
              <span className="label-hint">Any name you'd like</span>
            </div>
            <input
              id="displayName"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="e.g., My Greeting Prompt"
              className="form-input"
            />
          </div>

          {/* Prompt ID */}
          <div className="form-group compact">
            <input
              id="promptId"
              type="text"
              value={normalizedName || 'invalid'}
              disabled
              className="form-input prompt-id-field"
            />
            <p className="hint-text">Unique identifier</p>
          </div>

          {/* Description */}
          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of this prompt's purpose"
              className="form-textarea"
              rows={3}
            />
          </div>

          {/* Owner */}
          <div className="form-group">
            <label htmlFor="owner">Owner</label>
            <input
              id="owner"
              type="text"
              value={owner}
              onChange={(e) => {
                // Convert to lowercase
                setOwner(e.target.value.toLowerCase());
              }}
              placeholder="e.g., team-platform, alice"
              className="form-input"
            />
          </div>

          {/* Tags */}
          <div className="form-group">
            <label htmlFor="tags">Tags</label>
            <div className="tags-input-container">
              <div className="tags-display">
                {tags.map((tag) => (
                  <span key={tag} className="tag-badge">
                    {tag}
                    <button
                      type="button"
                      onClick={() => removeTag(tag)}
                      className="tag-remove"
                      title="Remove tag"
                    >
                      ×
                    </button>
                  </span>
                ))}
                <input
                  id="tags"
                  type="text"
                  value={tagInput}
                  onChange={(e) => handleTagInputChange(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddTag(tagInput);
                    }
                  }}
                  placeholder={tags.length === 0 ? "Add tags (space or comma separated)" : "Add more..."}
                  className="tags-input-field"
                />
              </div>
            </div>

            {/* Suggested tags */}
            {allTags.filter((tag) => !tags.includes(tag)).length > 0 && (
              <div className="suggested-tags">
                <span className="suggested-tags-label">Suggested:</span>
                {allTags
                  .filter((tag) => !tags.includes(tag))
                  .slice(0, 5)
                  .map((tag) => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => handleAddTag(tag)}
                      className="suggested-tag"
                    >
                      {tag}
                    </button>
                  ))}
              </div>
            )}
          </div>

        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={!normalizedName || nameExists}
            title={nameExists ? 'A prompt with this name already exists' : !normalizedName ? 'Please enter a valid name' : ''}
            style={{ opacity: !normalizedName || nameExists ? 0.5 : 1, cursor: !normalizedName || nameExists ? 'not-allowed' : 'pointer' }}
          >
            Save Properties
          </button>
          {nameExists && (
            <p style={{ color: '#ef4444', fontSize: '12px', marginTop: '8px' }}>
              ⚠️ A prompt with this name already exists
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentProperties;

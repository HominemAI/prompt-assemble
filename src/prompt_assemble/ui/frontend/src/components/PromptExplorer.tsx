import React, { useMemo, useState, useRef } from 'react';
import { FiSearch, FiPlus, FiRefreshCw, FiX, FiCheck, FiCopy, FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import '../styles/PromptExplorer.css';

interface Prompt {
  name: string;
  content: string;
  description: string;
  tags: string[];
  owner?: string;
  updated_at?: string;
}

interface PromptExplorerProps {
  prompts: Prompt[];
  allTags: string[];
  searchQuery: string;
  selectedTags: string[];
  loading: boolean;
  activePromptName?: string;
  openDocumentNames?: string[];
  onSearchChange: (query: string) => void;
  onTagsChange: (tags: string[]) => void;
  onPromptSelect: (prompt: Prompt) => void;
  onNewPrompt: () => void;
  onRefresh: () => void;
  sidebarVisible?: boolean;
  onToggleSidebar?: () => void;
}

const PromptExplorer: React.FC<PromptExplorerProps> = ({
  prompts,
  allTags,
  searchQuery,
  selectedTags,
  loading,
  activePromptName,
  openDocumentNames,
  onSearchChange,
  onTagsChange,
  onPromptSelect,
  onNewPrompt,
  onRefresh,
  sidebarVisible = true,
  onToggleSidebar = () => {},
}) => {
  const tagInputRef = useRef<HTMLInputElement>(null);
  const [selectedOwner, setSelectedOwner] = useState<string>('');
  const [ownerSearchInput, setOwnerSearchInput] = useState('');
  const [ownerSuggestionIndex, setOwnerSuggestionIndex] = useState(-1);
  const [tagSearchInput, setTagSearchInput] = useState('');
  const [tagSuggestionIndex, setTagSuggestionIndex] = useState(-1);
  const [copiedPromptId, setCopiedPromptId] = useState<string | null>(null);

  // Get unique owners from prompts
  const allOwners = useMemo(() => {
    const owners = new Set<string>();
    prompts.forEach((p) => {
      if (p.owner) owners.add(p.owner);
    });
    return Array.from(owners).sort();
  }, [prompts]);

  // Filter owners based on search input
  const filteredOwners = useMemo(() => {
    if (!ownerSearchInput) return allOwners;
    return allOwners.filter((owner) =>
      owner.toLowerCase().includes(ownerSearchInput.toLowerCase())
    );
  }, [allOwners, ownerSearchInput]);

  // Filter tags based on search input
  const filteredTags = useMemo(() => {
    if (!tagSearchInput) return allTags;
    return allTags.filter((tag) =>
      tag.toLowerCase().includes(tagSearchInput.toLowerCase())
    );
  }, [allTags, tagSearchInput]);

  const filteredPrompts = useMemo(() => {
    return prompts.filter((prompt) => {
      // Filter by search query
      const matchesSearch =
        prompt.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        prompt.description.toLowerCase().includes(searchQuery.toLowerCase());

      // Filter by tags (AND intersection, partial match)
      const matchesTags =
        selectedTags.length === 0 ||
        selectedTags.every((tag) =>
          prompt.tags.some((promptTag) =>
            promptTag.toLowerCase().includes(tag.toLowerCase())
          )
        );

      // Filter by owner (partial match, case-insensitive)
      const matchesOwner = !selectedOwner || (prompt.owner || '').toLowerCase().includes(selectedOwner.toLowerCase());

      return matchesSearch && matchesTags && matchesOwner;
    });
  }, [prompts, searchQuery, selectedTags, selectedOwner]);

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  const renderTags = (tags: string[]) => {
    return tags.slice(0, 3).join(', ') + (tags.length > 3 ? '...' : '');
  };

  const handleCopyPromptId = (promptId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(promptId).then(() => {
      setCopiedPromptId(promptId);
      setTimeout(() => setCopiedPromptId(null), 2000);
    });
  };

  return (
    <div className="prompt-explorer">
      {/* Header */}
      <div className="explorer-header">
        <h2 style={{ display: sidebarVisible ? 'block' : 'none' }}>Prompts</h2>
        <div className="explorer-actions">
          {sidebarVisible && (
            <>
              <button
                className="btn btn-icon"
                onClick={onNewPrompt}
                title="Create new prompt"
              >
                <FiPlus size={18} />
              </button>
              <button
                className="btn btn-icon"
                onClick={onRefresh}
                disabled={loading}
                title="Refresh prompts"
              >
                <FiRefreshCw size={18} className={loading ? 'spinner' : ''} />
              </button>
            </>
          )}
          <button
            className="btn btn-icon"
            onClick={onToggleSidebar}
            title={sidebarVisible ? 'Hide sidebar' : 'Show sidebar'}
          >
            {sidebarVisible ? <FiChevronLeft size={18} /> : <FiChevronRight size={18} />}
          </button>
        </div>
      </div>

      {/* Search - Hide when collapsed */}
      {sidebarVisible && (
        <>
          <div className="explorer-search">
            <div className="search-input-wrapper">
              <FiSearch size={16} />
              <input
                type="text"
                placeholder="Search prompts..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.currentTarget.blur();
                  }
                }}
                className="search-input"
              />
            </div>
          </div>

          {/* Owner and Tags Filter */}
      <div className="filters-section">
        {/* Owner Filter */}
        <div className="filter-row">
          <div className="filter-input-wrapper">
            <span className="filter-label">Owner:</span>
            <input
              type="text"
              placeholder="Search owners..."
              value={ownerSearchInput}
              onChange={(e) => {
                setOwnerSearchInput(e.target.value);
                setOwnerSuggestionIndex(-1);
              }}
              onKeyDown={(e) => {
                if ((e.key === 'Enter' || e.key === ' ' || e.key === ',') && ownerSearchInput.trim()) {
                  e.preventDefault();
                  const valueToAdd = ownerSuggestionIndex >= 0 && filteredOwners[ownerSuggestionIndex]
                    ? filteredOwners[ownerSuggestionIndex]
                    : ownerSearchInput.trim();
                  setSelectedOwner(valueToAdd);
                  setOwnerSearchInput('');
                  setOwnerSuggestionIndex(-1);
                } else if (e.key === 'ArrowDown') {
                  e.preventDefault();
                  setOwnerSuggestionIndex((prev) =>
                    prev < filteredOwners.length - 1 ? prev + 1 : prev
                  );
                } else if (e.key === 'ArrowUp') {
                  e.preventDefault();
                  setOwnerSuggestionIndex((prev) => (prev > 0 ? prev - 1 : -1));
                }
              }}
              className="filter-search-input"
            />
            {selectedOwner && (
              <button
                className="filter-clear-btn"
                onClick={() => setSelectedOwner('')}
              >
                ✕
              </button>
            )}
          </div>
          {selectedOwner && (
            <span className="selected-chip">{selectedOwner}</span>
          )}
        </div>

        {ownerSearchInput && filteredOwners.length > 0 && (
          <div className="filter-suggestions">
            {filteredOwners.map((owner, idx) => (
              <button
                key={owner}
                className={`filter-suggestion ${ownerSuggestionIndex === idx ? 'highlighted' : ''}`}
                onClick={() => {
                  setSelectedOwner(owner);
                  setOwnerSearchInput('');
                  setOwnerSuggestionIndex(-1);
                }}
              >
                {owner}
              </button>
            ))}
          </div>
        )}

        {/* Tags Filter */}
        <div className="filter-row">
          <div className="filter-input-wrapper">
            <span className="filter-label">Tags:</span>
            <input
              ref={tagInputRef}
              type="text"
              placeholder="Search tags..."
              value={tagSearchInput}
              onChange={(e) => {
                setTagSearchInput(e.target.value);
                setTagSuggestionIndex(-1);
              }}
              onKeyDown={(e) => {
                if ((e.key === 'Enter' || e.key === ' ' || e.key === ',') && tagSearchInput.trim()) {
                  e.preventDefault();
                  const newTag = tagSuggestionIndex >= 0 && filteredTags[tagSuggestionIndex]
                    ? filteredTags[tagSuggestionIndex]
                    : tagSearchInput.trim().toLowerCase();
                  // Only add if not already in selectedTags
                  if (!selectedTags.includes(newTag)) {
                    onTagsChange([...selectedTags, newTag]);
                  }
                  setTagSearchInput('');
                  setTagSuggestionIndex(-1);
                  // Keep focus on input for additive tag entry
                  setTimeout(() => tagInputRef.current?.focus(), 0);
                } else if (e.key === 'ArrowDown') {
                  e.preventDefault();
                  setTagSuggestionIndex((prev) =>
                    prev < filteredTags.length - 1 ? prev + 1 : prev
                  );
                } else if (e.key === 'ArrowUp') {
                  e.preventDefault();
                  setTagSuggestionIndex((prev) => (prev > 0 ? prev - 1 : -1));
                }
              }}
              className="filter-search-input"
            />
            {selectedTags.length > 0 && (
              <button
                className="filter-clear-btn"
                onClick={() => onTagsChange([])}
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {selectedTags.length > 0 && (
          <div className="selected-tags">
            {selectedTags.map((tag) => (
              <span key={tag} className="tag-chip">
                {tag}
                <button
                  className="tag-chip-remove"
                  onClick={() => onTagsChange(selectedTags.filter((t) => t !== tag))}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}

        {tagSearchInput && filteredTags.length > 0 && (
          <div className="filter-suggestions">
            {filteredTags.map((tag, idx) => (
              <button
                key={tag}
                className={`filter-suggestion ${tagSuggestionIndex === idx ? 'highlighted' : ''}`}
                onClick={() => {
                  if (!selectedTags.includes(tag)) {
                    onTagsChange([...selectedTags, tag]);
                  }
                  setTagSearchInput('');
                  setTagSuggestionIndex(-1);
                }}
              >
                {tag}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Prompts List */}
      <div className="prompts-list">
        {loading ? (
          <div className="loading">Loading prompts...</div>
        ) : filteredPrompts.length === 0 ? (
          <div className="empty">nothing matches</div>
        ) : (
          filteredPrompts.map((prompt) => {
            const isOpen = openDocumentNames?.includes(prompt.name) || false;
            return (
              <div
                key={prompt.name}
                className={`prompt-item ${isOpen ? 'is-open' : ''}`}
                onClick={() => onPromptSelect(prompt)}
                style={{ cursor: 'pointer' }}
              >
                <div className="prompt-name">
                  {isOpen && <FiCheck size={16} style={{ marginRight: '6px' }} />}
                  {prompt.name}
                  <div className="prompt-copy-btn-wrapper">
                    <button
                      className="prompt-copy-btn"
                      onClick={(e) => handleCopyPromptId(prompt.name, e)}
                    >
                      <FiCopy size={14} />
                    </button>
                    <span className="copy-tooltip">
                      {copiedPromptId === prompt.name ? 'Copied!' : 'Copy ID'}
                    </span>
                  </div>
                </div>
                <div className="prompt-meta">
                  <span className="prompt-time">{formatDate(prompt.updated_at)}</span>
                  {prompt.tags && prompt.tags.length > 0 && (
                    <span className="prompt-tags">{renderTags(prompt.tags)}</span>
                  )}
                </div>
              </div>
            );
          })
        )}
          </div>
        </>
      )}
    </div>
  );
};

export default PromptExplorer;

import React, { useState, useEffect } from 'react';
import { FiX, FiPlus, FiSearch } from 'react-icons/fi';
import VariableSetEditor from './VariableSetEditor';
import '../styles/VariableSetsModal.css';

interface VariableSet {
  id: string;
  name: string;
  variables: Record<string, string>;
}

interface VariableSetsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const VariableSetsModal: React.FC<VariableSetsModalProps> = ({ isOpen, onClose }) => {
  const [variableSets, setVariableSets] = useState<VariableSet[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSetId, setSelectedSetId] = useState<string | null>(null);

  if (!isOpen) return null;

  // Filter sets by search query
  const filteredSets = variableSets.filter((set) =>
    set.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Show variable set editor if one is selected
  if (selectedSetId) {
    const selectedSet = variableSets.find((s) => s.id === selectedSetId);
    if (selectedSet) {
      return (
        <VariableSetEditor
          variableSet={selectedSet}
          onBack={() => setSelectedSetId(null)}
          onSave={(updatedSet) => {
            setVariableSets(variableSets.map((s) => (s.id === updatedSet.id ? updatedSet : s)));
            setSelectedSetId(null);
          }}
          onDelete={(id) => {
            setVariableSets(variableSets.filter((s) => s.id !== id));
            setSelectedSetId(null);
          }}
        />
      );
    }
  }

  const handleCreateNewSet = () => {
    const newSet: VariableSet = {
      id: `set-${Date.now()}`,
      name: 'New Variable Set',
      variables: {},
    };
    setVariableSets([...variableSets, newSet]);
    setSelectedSetId(newSet.id);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content variable-sets-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Variable Sets</h2>
          <button className="modal-close-btn" onClick={onClose}>
            <FiX size={20} />
          </button>
        </div>

        <div className="search-container">
          <FiSearch size={16} />
          <input
            type="text"
            placeholder="Search variable sets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="variable-sets-list">
          {filteredSets.map((set) => (
            <div
              key={set.id}
              className="variable-set-item"
              onClick={() => setSelectedSetId(set.id)}
            >
              <span className="set-name">{set.name}</span>
              <span className="var-count">{Object.keys(set.variables).length} variables</span>
            </div>
          ))}
          {filteredSets.length === 0 && (
            <div className="empty-state">
              {variableSets.length === 0 ? 'No variable sets yet' : 'No matching sets'}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-primary" onClick={handleCreateNewSet}>
            <FiPlus size={16} />
            New Variable Set
          </button>
        </div>
      </div>
    </div>
  );
};

export default VariableSetsModal;

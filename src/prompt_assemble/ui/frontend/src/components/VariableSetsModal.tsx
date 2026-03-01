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

interface NameInputState {
  isOpen: boolean;
  value: string;
  isNewSet: boolean;
  setId?: string;
}

const VariableSetsModal: React.FC<VariableSetsModalProps> = ({ isOpen, onClose }) => {
  const [variableSets, setVariableSets] = useState<VariableSet[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSetId, setSelectedSetId] = useState<string | null>(null);
  const [nameInput, setNameInput] = useState<NameInputState>({
    isOpen: false,
    value: '',
    isNewSet: false,
  });

  if (!isOpen) return null;

  const handleRenameSet = (setId: string, currentName: string) => {
    setNameInput({
      isOpen: true,
      value: currentName,
      isNewSet: false,
      setId,
    });
  };

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
          onClose={() => setSelectedSetId(null)}
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
    setNameInput({
      isOpen: true,
      value: '',
      isNewSet: true,
    });
  };

  const handleSaveName = () => {
    if (!nameInput.value.trim()) {
      alert('Please enter a name for the variable set');
      return;
    }

    if (nameInput.isNewSet) {
      const newSet: VariableSet = {
        id: `set-${Date.now()}`,
        name: nameInput.value,
        variables: {},
      };
      setVariableSets([...variableSets, newSet]);
      setSelectedSetId(newSet.id);
    } else if (nameInput.setId) {
      // Rename existing set
      setVariableSets(
        variableSets.map((set) =>
          set.id === nameInput.setId ? { ...set, name: nameInput.value } : set
        )
      );
    }

    setNameInput({
      isOpen: false,
      value: '',
      isNewSet: false,
    });
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
            <div key={set.id} className="variable-set-item-container">
              <div
                className="variable-set-item"
                onClick={() => setSelectedSetId(set.id)}
              >
                <span className="set-name">{set.name}</span>
                <span className="var-count">{Object.keys(set.variables).length} variables</span>
              </div>
              <button
                className="rename-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRenameSet(set.id, set.name);
                }}
                title="Rename this set"
              >
                ✎
              </button>
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

      {/* Name Input Dialog */}
      {nameInput.isOpen && (
        <div className="modal-overlay" onClick={() => setNameInput({ ...nameInput, isOpen: false })}>
          <div className="modal-content" style={{ width: '400px' }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{nameInput.isNewSet ? 'New Variable Set' : 'Rename Variable Set'}</h3>
              <button className="modal-close-btn" onClick={() => setNameInput({ ...nameInput, isOpen: false })}>
                <FiX size={20} />
              </button>
            </div>

            <div style={{ padding: '16px' }}>
              <input
                type="text"
                value={nameInput.value}
                onChange={(e) => setNameInput({ ...nameInput, value: e.target.value })}
                placeholder="Variable Set Name"
                className="form-input"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSaveName();
                  } else if (e.key === 'Escape') {
                    setNameInput({ ...nameInput, isOpen: false });
                  }
                }}
              />
            </div>

            <div className="modal-footer">
              <button
                className="btn-secondary"
                onClick={() => setNameInput({ ...nameInput, isOpen: false })}
              >
                Cancel
              </button>
              <button className="btn-primary" onClick={handleSaveName}>
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VariableSetsModal;

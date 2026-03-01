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
  onVariableSetsChanged?: () => void;
}

interface NameInputState {
  isOpen: boolean;
  value: string;
  isNewSet: boolean;
  setId?: string;
}

const VariableSetsModal: React.FC<VariableSetsModalProps> = ({ isOpen, onClose, onVariableSetsChanged }) => {
  const [variableSets, setVariableSets] = useState<VariableSet[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSetId, setSelectedSetId] = useState<string | null>(null);
  const [nameInput, setNameInput] = useState<NameInputState>({
    isOpen: false,
    value: '',
    isNewSet: false,
  });

  // Load variable sets from server on mount
  useEffect(() => {
    if (isOpen) {
      loadVariableSets();
    }
  }, [isOpen]);

  // Save to localStorage whenever variable sets change
  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('variable-sets', JSON.stringify(variableSets));
    }
  }, [variableSets]);

  const loadVariableSets = async () => {
    try {
      const response = await fetch('/api/variable-sets');
      if (response.ok) {
        const data = await response.json();
        setVariableSets(data.variable_sets || []);
      } else {
        // Fall back to localStorage if server fails
        loadFromLocalStorage();
      }
    } catch (error) {
      console.error('Error loading variable sets:', error);
      // Fall back to localStorage if fetch fails
      loadFromLocalStorage();
    }
  };

  const loadFromLocalStorage = () => {
    if (typeof window !== 'undefined') {
      const cached = window.localStorage.getItem('variable-sets');
      if (cached) {
        try {
          setVariableSets(JSON.parse(cached));
        } catch (e) {
          console.error('Error parsing cached variable sets:', e);
        }
      }
    }
  };

  const saveVariableSetToServer = async (set: VariableSet) => {
    try {
      const response = await fetch('/api/variable-sets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(set),
      });
      if (!response.ok) {
        console.error('Failed to save variable set');
      }
      // Reload after save
      await loadVariableSets();
      // Notify parent
      if (onVariableSetsChanged) {
        onVariableSetsChanged();
      }
    } catch (error) {
      console.error('Error saving variable set:', error);
    }
  };

  const deleteVariableSetFromServer = async (setId: string) => {
    try {
      const response = await fetch(`/api/variable-sets/${setId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        console.error('Failed to delete variable set');
      }
      // Reload after delete
      await loadVariableSets();
      // Notify parent
      if (onVariableSetsChanged) {
        onVariableSetsChanged();
      }
    } catch (error) {
      console.error('Error deleting variable set:', error);
    }
  };

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
            // Save to server
            saveVariableSetToServer(updatedSet);
          }}
          onDelete={(id) => {
            setVariableSets(variableSets.filter((s) => s.id !== id));
            setSelectedSetId(null);
            // Delete from server
            deleteVariableSetFromServer(id);
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

  const handleSaveName = async () => {
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
      // Save to server
      await saveVariableSetToServer(newSet);
    } else if (nameInput.setId) {
      // Rename existing set
      const renamedSet = variableSets.find((s) => s.id === nameInput.setId);
      if (renamedSet) {
        const updatedSet = { ...renamedSet, name: nameInput.value };
        setVariableSets(
          variableSets.map((set) =>
            set.id === nameInput.setId ? updatedSet : set
          )
        );
        // Save to server
        await saveVariableSetToServer(updatedSet);
      }
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

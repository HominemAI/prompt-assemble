import React, { useState } from 'react';
import { FiX, FiSearch, FiCheck } from 'react-icons/fi';
import '../styles/VariableSetsSelection.css';

interface VariableSet {
  id: string;
  name: string;
  variables: Record<string, string>;
}

interface VariableSetsSelectionProps {
  allVariableSets: VariableSet[];
  selectedSetIds: string[];
  onSave: (selectedIds: string[]) => void;
  onCancel: () => void;
}

const VariableSetsSelection: React.FC<VariableSetsSelectionProps> = ({
  allVariableSets,
  selectedSetIds,
  onSave,
  onCancel,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [tempSelectedIds, setTempSelectedIds] = useState<string[]>(selectedSetIds);

  const filteredSets = allVariableSets.filter((set) =>
    set.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleToggleSet = (setId: string) => {
    if (tempSelectedIds.includes(setId)) {
      setTempSelectedIds(tempSelectedIds.filter((id) => id !== setId));
    } else {
      setTempSelectedIds([...tempSelectedIds, setId]);
    }
  };

  const handleSave = () => {
    onSave(tempSelectedIds);
  };

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div
        className="modal-content variable-sets-selection"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>Select Variable Sets</h2>
          <button className="modal-close-btn" onClick={onCancel}>
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

        <div className="sets-list">
          {filteredSets.map((set) => (
            <div
              key={set.id}
              className={`set-option ${tempSelectedIds.includes(set.id) ? 'selected' : ''}`}
              onClick={() => handleToggleSet(set.id)}
            >
              <div className="checkbox">
                {tempSelectedIds.includes(set.id) && <FiCheck size={16} />}
              </div>
              <div className="set-info">
                <span className="set-name">{set.name}</span>
                <span className="var-count">{Object.keys(set.variables).length} variables</span>
              </div>
            </div>
          ))}
          {filteredSets.length === 0 && (
            <div className="empty-state">No matching variable sets</div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn-primary" onClick={handleSave}>
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default VariableSetsSelection;

import React, { useState, useEffect } from 'react';
import { FiX, FiPlus, FiSearch } from 'react-icons/fi';
import VariableSetsSelection from './VariableSetsSelection';
import VariableSetOverrideEditor from './VariableSetOverrideEditor';
import '../styles/VariableSetsSelector.css';

interface VariableSet {
  id: string;
  name: string;
  variables: Record<string, string>;
}

interface VariableSetOverrides {
  setId: string;
  overrides: Record<string, string>;
}

interface VariableSetsSelectionProps {
  isOpen: boolean;
  onClose: () => void;
  allVariableSets: VariableSet[];
  onSave?: (ids: string[], overrides: Record<string, Record<string, string>>) => void;
}

const VariableSetsSelector: React.FC<VariableSetsSelectionProps> = ({
  isOpen,
  onClose,
  allVariableSets,
  onSave,
}) => {
  const [selectedSetIds, setSelectedSetIds] = useState<string[]>([]);
  const [overrides, setOverrides] = useState<VariableSetOverrides[]>([]);
  const [showSelection, setShowSelection] = useState(false);
  const [showOverride, setShowOverride] = useState<string | null>(null);

  if (!isOpen) return null;

  const selectedSets = allVariableSets.filter((set) => selectedSetIds.includes(set.id));

  const handleAddVariableSets = () => {
    setShowSelection(true);
  };

  const handleSaveSelection = (newSelectedIds: string[]) => {
    setSelectedSetIds(newSelectedIds);
    setShowSelection(false);
  };

  const handleRemoveSet = (setId: string) => {
    setSelectedSetIds(selectedSetIds.filter((id) => id !== setId));
    setOverrides(overrides.filter((o) => o.setId !== setId));
  };

  const handleClickSet = (setId: string) => {
    setShowOverride(setId);
  };

  const handleSaveOverrides = (setId: string, newOverrides: Record<string, string>) => {
    const existingIndex = overrides.findIndex((o) => o.setId === setId);
    if (existingIndex >= 0) {
      const updated = [...overrides];
      updated[existingIndex].overrides = newOverrides;
      setOverrides(updated);
    } else {
      setOverrides([...overrides, { setId, overrides: newOverrides }]);
    }
    setShowOverride(null);
  };

  const handleClose = () => {
    // Persist selected sets and overrides before closing
    if (onSave) {
      const overridesMap: Record<string, Record<string, string>> = {};
      for (const override of overrides) {
        overridesMap[override.setId] = override.overrides;
      }
      onSave(selectedSetIds, overridesMap);
    }
    onClose();
  };

  // Show selection modal if needed
  if (showSelection) {
    return (
      <VariableSetsSelection
        allVariableSets={allVariableSets}
        selectedSetIds={selectedSetIds}
        onSave={handleSaveSelection}
        onCancel={() => setShowSelection(false)}
      />
    );
  }

  // Show override editor if needed
  if (showOverride) {
    const selectedSet = allVariableSets.find((s) => s.id === showOverride);
    if (selectedSet) {
      const setOverrides = overrides.find((o) => o.setId === showOverride)?.overrides || {};
      return (
        <VariableSetOverrideEditor
          variableSet={selectedSet}
          overrides={setOverrides}
          onSave={(newOverrides) => handleSaveOverrides(showOverride, newOverrides)}
          onCancel={() => setShowOverride(null)}
        />
      );
    }
  }

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content variable-sets-selector" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Active Variable Sets</h2>
          <button className="modal-close-btn" onClick={handleClose}>
            <FiX size={20} />
          </button>
        </div>

        <div className="selected-sets-list">
          {selectedSets.length === 0 ? (
            <div className="empty-state">No variable sets selected</div>
          ) : (
            selectedSets.map((set) => (
              <div key={set.id} className="selected-set-item" onClick={() => handleClickSet(set.id)}>
                <div className="set-info">
                  <span className="set-name">{set.name}</span>
                  <span className="var-count">{Object.keys(set.variables).length} variables</span>
                </div>
                <button
                  className="remove-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveSet(set.id);
                  }}
                  title="Remove this set"
                >
                  <FiX size={16} />
                </button>
              </div>
            ))
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-primary" onClick={handleAddVariableSets}>
            <FiPlus size={16} />
            Add Variable Set
          </button>
        </div>
      </div>
    </div>
  );
};

export default VariableSetsSelector;

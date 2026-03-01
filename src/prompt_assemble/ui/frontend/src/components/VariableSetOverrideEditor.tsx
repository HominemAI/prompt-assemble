import React, { useState } from 'react';
import { FiX, FiArrowLeft } from 'react-icons/fi';
import '../styles/VariableSetOverrideEditor.css';

interface VariableSet {
  id: string;
  name: string;
  variables: Record<string, string>;
}

interface VariableSetOverrideEditorProps {
  variableSet: VariableSet;
  overrides: Record<string, string>;
  onSave: (overrides: Record<string, string>) => void;
  onCancel: () => void;
}

const VariableSetOverrideEditor: React.FC<VariableSetOverrideEditorProps> = ({
  variableSet,
  overrides,
  onSave,
  onCancel,
}) => {
  const [currentOverrides, setCurrentOverrides] = useState<Record<string, string>>(overrides);

  const handleUpdateOverride = (key: string, value: string) => {
    setCurrentOverrides({
      ...currentOverrides,
      [key]: value,
    });
  };

  const handleSave = () => {
    onSave(currentOverrides);
  };

  const variables = Object.entries(variableSet.variables);

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div
        className="modal-content variable-override-editor"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <button className="back-btn" onClick={onCancel}>
            <FiArrowLeft size={20} />
          </button>
          <h2>{variableSet.name} - Overrides</h2>
          <button className="modal-close-btn" onClick={onCancel}>
            <FiX size={20} />
          </button>
        </div>

        <div className="overrides-container">
          {variables.length === 0 ? (
            <div className="empty-state">No variables in this set</div>
          ) : (
            variables.map(([key, defaultValue]) => (
              <div key={key} className="override-item">
                <div className="variable-label">
                  <span className="key">{key}</span>
                  <span className="default-value-label">Default:</span>
                  <span className="default-value">{defaultValue}</span>
                </div>
                <textarea
                  value={currentOverrides[key] ?? ''}
                  onChange={(e) => handleUpdateOverride(key, e.target.value)}
                  placeholder="Leave empty to use default"
                  className="override-input"
                />
              </div>
            ))
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn-primary" onClick={handleSave}>
            Save Overrides
          </button>
        </div>
      </div>
    </div>
  );
};

export default VariableSetOverrideEditor;

import React, { useState, useEffect } from 'react';
import { FiX, FiPlus, FiTrash2, FiArrowLeft } from 'react-icons/fi';
import ConfirmModal from './ConfirmModal';
import '../styles/VariableSetEditor.css';

interface VariableSet {
  id: string;
  name: string;
  variables: Record<string, string>;
}

interface VariableItem {
  key: string;
  value: string;
}

interface VariableSetEditorProps {
  variableSet: VariableSet;
  onBack: () => void;
  onSave: (updatedSet: VariableSet) => void;
  onDelete: (id: string) => void;
}

interface UnsavedModal {
  isOpen: boolean;
  action: 'back' | 'close' | null;
}

const VariableSetEditor: React.FC<VariableSetEditorProps> = ({
  variableSet,
  onBack,
  onSave,
  onDelete,
}) => {
  const [setName, setSetName] = useState(variableSet.name);
  const [variables, setVariables] = useState<VariableItem[]>([]);
  const [unsavedModal, setUnsavedModal] = useState<UnsavedModal>({ isOpen: false, action: null });
  const [deleteConfirm, setDeleteConfirm] = useState<{ isOpen: boolean; step: 1 | 2 }>({
    isOpen: false,
    step: 1,
  });
  const [deleteLineId, setDeleteLineId] = useState<string | null>(null);

  // Initialize variables from variableSet
  useEffect(() => {
    const vars = Object.entries(variableSet.variables).map(([key, value], idx) => ({
      key,
      value,
      id: `${key}-${idx}`,
    }));
    setVariables(vars as any);
  }, [variableSet]);

  const hasUnsavedChanges = () => {
    const currentVariables = variables.reduce(
      (acc, v) => {
        if (v.key.trim() !== '' || v.value.trim() !== '') {
          acc[v.key] = v.value;
        }
        return acc;
      },
      {} as Record<string, string>
    );

    return (
      setName !== variableSet.name ||
      JSON.stringify(currentVariables) !== JSON.stringify(variableSet.variables)
    );
  };

  const attemptToLeave = (action: 'back' | 'close') => {
    if (hasUnsavedChanges()) {
      setUnsavedModal({ isOpen: true, action });
    } else {
      if (action === 'back') {
        onBack();
      } else {
        // Close - handled by parent
      }
    }
  };

  const handleSave = () => {
    const cleanVariables = variables.reduce(
      (acc, v) => {
        if (v.key.trim() !== '' || v.value.trim() !== '') {
          acc[v.key] = v.value;
        }
        return acc;
      },
      {} as Record<string, string>
    );

    const updatedSet: VariableSet = {
      ...variableSet,
      name: setName,
      variables: cleanVariables,
    };

    onSave(updatedSet);
  };

  const handleAddVariable = () => {
    setVariables([...variables, { key: '', value: '', id: `new-${Date.now()}` }] as any);
  };

  const handleUpdateVariable = (
    index: number,
    field: 'key' | 'value',
    newValue: string
  ) => {
    const updated = [...variables];
    updated[index][field] = newValue;
    setVariables(updated);
  };

  const handleDeleteVariable = (index: number) => {
    if (deleteLineId === index.toString()) {
      const updated = variables.filter((_, i) => i !== index);
      setVariables(updated);
      setDeleteLineId(null);
    } else {
      setDeleteLineId(index.toString());
    }
  };

  const handleDeleteSet = () => {
    if (deleteConfirm.step === 1) {
      setDeleteConfirm({ isOpen: true, step: 2 });
    } else {
      onDelete(variableSet.id);
    }
  };

  const handleUnsavedAction = (action: 'save' | 'discard' | 'cancel') => {
    if (action === 'save') {
      handleSave();
      if (unsavedModal.action === 'back') {
        onBack();
      }
    } else if (action === 'discard') {
      if (unsavedModal.action === 'back') {
        onBack();
      }
    }
    setUnsavedModal({ isOpen: false, action: null });
  };

  return (
    <div className="modal-overlay" onClick={() => attemptToLeave('close')}>
      <div className="modal-content variable-set-editor" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <button className="back-btn" onClick={() => attemptToLeave('back')}>
            <FiArrowLeft size={20} />
          </button>
          <input
            type="text"
            value={setName}
            onChange={(e) => setSetName(e.target.value)}
            className="set-name-input"
            placeholder="Variable Set Name"
          />
          <button className="modal-close-btn" onClick={() => attemptToLeave('close')}>
            <FiX size={20} />
          </button>
        </div>

        <div className="variables-container">
          {variables.map((variable, index) => (
            <div key={index} className="variable-item">
              <input
                type="text"
                value={variable.key}
                onChange={(e) => handleUpdateVariable(index, 'key', e.target.value)}
                placeholder="Key"
                className="variable-key"
              />
              <textarea
                value={variable.value}
                onChange={(e) => handleUpdateVariable(index, 'value', e.target.value)}
                placeholder="Value"
                className="variable-value"
              />
              <button
                className={`delete-var-btn ${deleteLineId === index.toString() ? 'confirm' : ''}`}
                onClick={() => handleDeleteVariable(index)}
                title={deleteLineId === index.toString() ? 'Click again to confirm' : 'Delete'}
              >
                <FiTrash2 size={16} />
              </button>
            </div>
          ))}

          <button className="add-variable-btn" onClick={handleAddVariable}>
            <FiPlus size={16} />
            Add Variable
          </button>
        </div>

        <div className="modal-footer">
          <div className="footer-actions">
            <button className="btn-primary" onClick={handleSave}>
              Save
            </button>
            <button
              className="btn-danger"
              onClick={() => setDeleteConfirm({ isOpen: true, step: 1 })}
            >
              <FiTrash2 size={16} />
              Delete Set
            </button>
          </div>
        </div>
      </div>

      {unsavedModal.isOpen && (
        <ConfirmModal
          isOpen={unsavedModal.isOpen}
          title="Unsaved Changes"
          message="You have unsaved changes. Do you want to save them?"
          confirmText="Save"
          cancelText="Discard"
          isDangerous={false}
          onConfirm={() => handleUnsavedAction('save')}
          onCancel={() => handleUnsavedAction('discard')}
          onClose={() => handleUnsavedAction('cancel')}
          showClose={true}
        />
      )}

      {deleteConfirm.isOpen && (
        <ConfirmModal
          isOpen={deleteConfirm.isOpen}
          title={deleteConfirm.step === 1 ? 'Delete Variable Set?' : 'Are you absolutely sure?'}
          message={
            deleteConfirm.step === 1
              ? `Delete "${setName}"? This cannot be undone.`
              : 'This will permanently delete the variable set and all its variables.'
          }
          confirmText={deleteConfirm.step === 1 ? 'Delete' : 'Delete Forever'}
          cancelText="Cancel"
          isDangerous={true}
          onConfirm={handleDeleteSet}
          onCancel={() => setDeleteConfirm({ isOpen: false, step: 1 })}
        />
      )}
    </div>
  );
};

export default VariableSetEditor;

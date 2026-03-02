/**
 * Settings modal for backend configuration and switching.
 * Allows users to switch between Browser (IndexedDB) and Filesystem backends.
 */

import React, { useState } from 'react';
import { FiX, FiCheckCircle, FiAlertCircle } from 'react-icons/fi';
import { BackendMode } from '../utils/api';
import ConfirmModal from './ConfirmModal';
import '../styles/SettingsModal.css';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentBackendMode: BackendMode;
  onBackendChange: (
    newMode: BackendMode,
    importData?: boolean
  ) => Promise<void>;
  isLoading?: boolean;
  lockedBackendMode?: BackendMode; // If set, backend switching is disabled
}

type SettingsStep = 'main' | 'switch-warning' | 'folder-select' | 'verifying';

const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  currentBackendMode,
  onBackendChange,
  isLoading = false,
  lockedBackendMode,
}) => {
  const [step, setStep] = useState<SettingsStep>('main');
  const [targetMode, setTargetMode] = useState<BackendMode>(currentBackendMode);
  const [importData, setImportData] = useState(true);
  const [error, setError] = useState<string>('');
  const [progress, setProgress] = useState<string>('');

  const handleBackendToggle = (newMode: BackendMode) => {
    if (newMode === currentBackendMode) return;

    setTargetMode(newMode);
    setError('');
    setProgress('');

    if (newMode === 'filesystem') {
      setStep('switch-warning');
    } else {
      setStep('switch-warning');
    }
  };

  const handleConfirmSwitch = async () => {
    try {
      setStep('verifying');
      setProgress('Switching backend...');

      await onBackendChange(targetMode, importData);

      setProgress('');
      setError('');
      setStep('main');
      // Slight delay before closing for UX
      setTimeout(onClose, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      setStep('switch-warning');
    }
  };

  const handleCancel = () => {
    setStep('main');
    setError('');
    setProgress('');
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Settings</h2>
          <button className="modal-close" onClick={onClose}>
            <FiX size={24} />
          </button>
        </div>

        {step === 'main' && (
          <div className="settings-body">
            <div className="settings-section">
              <h3>Storage Backend</h3>
              {lockedBackendMode ? (
                <div className="locked-notice">
                  <p>
                    <strong>📌 Backend Locked</strong>
                  </p>
                  <p>
                    This deployment is configured to use{' '}
                    <strong>
                      {lockedBackendMode === 'local' ? 'Browser Storage (IndexedDB)' : 'Filesystem Storage'}
                    </strong>{' '}
                    only. Backend switching is disabled.
                  </p>
                </div>
              ) : (
                <p className="settings-description">
                  Choose where your prompts are stored.
                </p>
              )}

              <div className="backend-options">
                {/* Browser Only Option */}
                <div
                  className={`backend-option ${
                    currentBackendMode === 'local' ? 'active' : ''
                  } ${lockedBackendMode ? 'disabled' : ''}`}
                  onClick={() => !lockedBackendMode && handleBackendToggle('local')}
                >
                  <div className="option-icon">🌐</div>
                  <div className="option-content">
                    <h4>Browser Only</h4>
                    <p>
                      Stored in your browser's IndexedDB. Survives restarts but
                      isolated to this browser.
                    </p>
                    <ul className="option-features">
                      <li>✓ Works offline</li>
                      <li>✓ No server needed</li>
                      <li>✓ Private to this device</li>
                      <li>✗ Not editable in external editors</li>
                    </ul>
                  </div>
                  {currentBackendMode === 'local' && (
                    <FiCheckCircle className="active-indicator" />
                  )}
                </div>

                {/* Filesystem Option */}
                <div
                  className={`backend-option ${
                    currentBackendMode === 'filesystem' ? 'active' : ''
                  } ${lockedBackendMode ? 'disabled' : ''}`}
                  onClick={() => !lockedBackendMode && handleBackendToggle('filesystem')}
                >
                  <div className="option-icon">📁</div>
                  <div className="option-content">
                    <h4>Filesystem Storage</h4>
                    <p>
                      Files saved to your disk. Editable in any editor, can be
                      version controlled.
                    </p>
                    <ul className="option-features">
                      <li>✓ Works offline</li>
                      <li>✓ Editable in VS Code, etc.</li>
                      <li>✓ Version control compatible</li>
                      <li>✓ Shareable across devices</li>
                    </ul>
                  </div>
                  {currentBackendMode === 'filesystem' && (
                    <FiCheckCircle className="active-indicator" />
                  )}
                </div>
              </div>

              <div className="settings-footer">
                <button className="btn btn-secondary" onClick={onClose}>
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {step === 'switch-warning' && (
          <div className="settings-body">
            {targetMode === 'filesystem' ? (
              <div className="warning-section">
                <div className="warning-icon">
                  <FiAlertCircle size={32} />
                </div>
                <h3>Switch to Filesystem Storage?</h3>

                <div className="warning-content">
                  <div className="warning-box">
                    <p>
                      <strong>⚠️ Important:</strong>
                    </p>
                    <ul>
                      <li>
                        You'll select a folder that becomes your source of truth
                      </li>
                      <li>
                        All .prompt and .txt files will be imported recursively
                      </li>
                      <li>
                        <strong>Do NOT edit files manually</strong> outside this
                        app
                      </li>
                      <li>Version history will be saved in a .versions/ folder</li>
                    </ul>
                  </div>

                  <div className="import-option">
                    <label>
                      <input
                        type="checkbox"
                        checked={importData}
                        onChange={(e) => setImportData(e.target.checked)}
                      />
                      <span>
                        <strong>Import current browser data</strong>
                        <br />
                        <small>
                          Copy all prompts, variable sets, and subscriptions
                          from browser storage to the filesystem folder
                        </small>
                      </span>
                    </label>
                  </div>

                  {error && <div className="error-message">{error}</div>}
                </div>

                <div className="settings-footer">
                  <button
                    className="btn btn-secondary"
                    onClick={handleCancel}
                    disabled={isLoading}
                  >
                    Cancel
                  </button>
                  <button
                    className="btn btn-primary"
                    onClick={handleConfirmSwitch}
                    disabled={isLoading}
                  >
                    {isLoading ? 'Switching...' : 'Continue'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="warning-section">
                <div className="warning-icon">
                  <FiCheckCircle size={32} />
                </div>
                <h3>Switch Back to Browser Storage?</h3>

                <div className="warning-content">
                  <p>
                    Your filesystem data will remain untouched in its folder.
                    You can switch back to it anytime.
                  </p>
                  <p>
                    Your previous browser storage (IndexedDB) is still available
                    and will be restored.
                  </p>

                  {error && <div className="error-message">{error}</div>}
                </div>

                <div className="settings-footer">
                  <button
                    className="btn btn-secondary"
                    onClick={handleCancel}
                    disabled={isLoading}
                  >
                    Cancel
                  </button>
                  <button
                    className="btn btn-primary"
                    onClick={handleConfirmSwitch}
                    disabled={isLoading}
                  >
                    {isLoading ? 'Switching...' : 'Switch Back'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {step === 'verifying' && (
          <div className="settings-body">
            <div className="progress-section">
              <div className="progress-spinner" />
              <h3>Setting up storage...</h3>
              {progress && <p className="progress-message">{progress}</p>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SettingsModal;

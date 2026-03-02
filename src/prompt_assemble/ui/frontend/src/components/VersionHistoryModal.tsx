import React, { useState, useRef, useEffect } from 'react';
import { FiX } from 'react-icons/fi';
import { useBackend } from '../contexts/BackendContext';
import '../styles/DocumentProperties.css';

interface Version {
  version: number;
  content: string;
  createdAt: string;
  revisionComment: string;
}

interface VersionHistoryModalProps {
  promptName: string;
  currentRevisionComment?: string;
  currentSavedAt?: string;
  onRevert: (version: Version) => void;
  onClose: () => void;
}

const VersionHistoryModal: React.FC<VersionHistoryModalProps> = ({
  promptName,
  currentRevisionComment,
  currentSavedAt,
  onRevert,
  onClose,
}) => {
  const { backend } = useBackend();
  const overlayRef = useRef<HTMLDivElement>(null);
  const isMouseDownOnOverlay = useRef(false);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [versions, setVersions] = useState<Version[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch version history on mount
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        console.log(`[VersionHistoryModal] Fetching history for: ${promptName}`);
        const history = await backend.getPromptHistory(promptName);
        console.log(`[VersionHistoryModal] Received ${history?.length || 0} versions:`, history);
        setVersions(history.map(entry => ({
          version: entry.version,
          content: '', // Content will be loaded on revert
          createdAt: entry.timestamp,
          revisionComment: entry.comment,
        })));
        setError(null);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to fetch version history';
        console.error(`[VersionHistoryModal] Error: ${errorMsg}`, err);
        setError(errorMsg);
        setVersions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [promptName]);

  const handleRevert = () => {
    if (selectedVersion !== null) {
      const selected = versions.find(v => v.version === selectedVersion);
      if (selected) {
        console.log(`[VersionHistoryModal] Reverting to version ${selected.version}`);
        onRevert(selected);
        onClose();
      }
    }
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
          <h2>Version History</h2>
          <button className="modal-close" onClick={onClose}>
            <FiX size={24} />
          </button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label>Revisions</label>
            <div className="version-list">
              {loading ? (
                <div className="version-placeholder">Loading version history...</div>
              ) : error ? (
                <div className="version-placeholder">Error: {error}</div>
              ) : (
                <>
                  {/* Current version - always shown at top */}
                  <div
                    className={`version-item ${selectedVersion === null ? 'selected' : ''}`}
                    onClick={() => setSelectedVersion(null)}
                  >
                    <div className="version-header">
                      <div className="version-number">Current Version</div>
                      <div className="version-time">
                        {currentSavedAt
                          ? new Date(currentSavedAt).toLocaleString()
                          : 'Not yet saved'}
                      </div>
                    </div>
                    <div className="version-comment">
                      {currentRevisionComment || '(no comment)'}
                    </div>
                    <div className="version-label">Current</div>
                  </div>

                  {/* Historical versions */}
                  {versions.length > 0 && (
                    <>
                      <div style={{ borderTop: '1px solid #ddd', margin: '8px 0' }} />
                      {versions.map((version) => (
                        <div
                          key={version.version}
                          className={`version-item ${selectedVersion === version.version ? 'selected' : ''}`}
                          onClick={() => setSelectedVersion(version.version)}
                        >
                          <div className="version-header">
                            <div className="version-number">Version {version.version}</div>
                            <div className="version-time">
                              {version.createdAt
                                ? new Date(version.createdAt).toLocaleString()
                                : 'Unknown date'}
                            </div>
                          </div>
                          <div className="version-comment">
                            {version.revisionComment || '(no comment)'}
                          </div>
                        </div>
                      ))}
                    </>
                  )}
                  {versions.length === 0 && (
                    <div className="version-placeholder">No previous revisions</div>
                  )}
                </>
              )}
            </div>
          </div>

          <p className="hint-text">
            Select a previous version and click "Revert" to restore it as the new current version.
          </p>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
          <button
            className="btn btn-warning"
            onClick={handleRevert}
            disabled={selectedVersion === null}
          >
            Revert to Selected
          </button>
        </div>
      </div>
    </div>
  );
};

export default VersionHistoryModal;

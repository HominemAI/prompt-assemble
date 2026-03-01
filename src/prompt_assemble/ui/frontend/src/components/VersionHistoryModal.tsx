import React, { useState, useRef } from 'react';
import { FiX } from 'react-icons/fi';
import '../styles/DocumentProperties.css';

interface VersionHistoryModalProps {
  currentRevisionComment?: string;
  currentSavedAt?: string;
  onRevert: (revisionComment: string) => void;
  onClose: () => void;
}

const VersionHistoryModal: React.FC<VersionHistoryModalProps> = ({
  currentRevisionComment,
  currentSavedAt,
  onRevert,
  onClose,
}) => {
  const overlayRef = useRef<HTMLDivElement>(null);
  const isMouseDownOnOverlay = useRef(false);
  const [selectedComment, setSelectedComment] = useState<string | null>(null);

  const handleRevert = () => {
    if (selectedComment !== null) {
      onRevert(selectedComment);
      onClose();
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
              <div
                className={`version-item ${selectedComment === null ? 'selected' : ''}`}
                onClick={() => setSelectedComment(null)}
              >
                <div className="version-time">
                  {currentSavedAt
                    ? new Date(currentSavedAt).toLocaleString()
                    : 'Not yet saved'}
                </div>
                <div className="version-comment">
                  {currentRevisionComment || 'No revision comment'}
                </div>
                <div className="version-label">Current</div>
              </div>

              {/* Future: Add historical versions here */}
              <div className="version-placeholder">
                No previous versions yet
              </div>
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
            disabled={selectedComment === null}
          >
            Revert to Selected
          </button>
        </div>
      </div>
    </div>
  );
};

export default VersionHistoryModal;

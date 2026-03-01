import React, { useState, useRef } from 'react';
import { FiX } from 'react-icons/fi';
import '../styles/DocumentProperties.css';

interface RevisionCommentModalProps {
  onSave: (comment: string) => void;
  onCancel: () => void;
  previousComment?: string;
}

const RevisionCommentModal: React.FC<RevisionCommentModalProps> = ({
  onSave,
  onCancel,
  previousComment,
}) => {
  const overlayRef = useRef<HTMLDivElement>(null);
  const isMouseDownOnOverlay = useRef(false);
  const [comment, setComment] = useState('');

  const handleSave = () => {
    onSave(comment);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    isMouseDownOnOverlay.current = e.target === overlayRef.current;
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (isMouseDownOnOverlay.current && e.target === overlayRef.current) {
      onCancel();
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
          <h2>Save with Revision Comment</h2>
          <button className="modal-close" onClick={onCancel}>
            <FiX size={24} />
          </button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label htmlFor="comment">What changed?</label>
            <textarea
              id="comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Briefly describe what you changed in this revision..."
              className="form-textarea"
              rows={4}
              autoFocus
            />
            <p className="hint-text">
              This helps you track what was modified in each version.
            </p>
          </div>

          {previousComment && (
            <div className="form-group">
              <label>Previous Revision Comment</label>
              <div className="revision-history">
                <p className="revision-comments-text">{previousComment}</p>
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={handleSave}>
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default RevisionCommentModal;

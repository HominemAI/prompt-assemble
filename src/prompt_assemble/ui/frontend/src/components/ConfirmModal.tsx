import React, { useRef } from 'react';

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmText?: string;
  cancelText?: string;
  isDangerous?: boolean;
}

const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  title,
  message,
  onConfirm,
  onCancel,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  isDangerous = false,
}) => {
  const overlayRef = useRef<HTMLDivElement>(null);
  const isMouseDownOnOverlay = useRef(false);

  if (!isOpen) return null;

  const handleMouseDown = (e: React.MouseEvent) => {
    // Only track if mousedown was on the overlay itself, not on content
    isMouseDownOnOverlay.current = e.target === overlayRef.current;
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    // Close only if both mousedown and mouseup were on the overlay
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
          <h2>{title}</h2>
        </div>
        <div className="modal-body">
          <p style={{ margin: '0 0 20px 0', lineHeight: '1.5' }}>{message}</p>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onCancel}>
            {cancelText}
          </button>
          <button
            className={isDangerous ? 'btn btn-danger' : 'btn btn-primary'}
            onClick={onConfirm}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;

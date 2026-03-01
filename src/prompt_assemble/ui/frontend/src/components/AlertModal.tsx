import React, { useRef } from 'react';

interface AlertModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  onClose: () => void;
}

const AlertModal: React.FC<AlertModalProps> = ({ isOpen, title, message, onClose }) => {
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
          <h2>{title}</h2>
        </div>
        <div className="modal-body">
          <p style={{ margin: '0 0 20px 0', lineHeight: '1.5' }}>{message}</p>
        </div>
        <div className="modal-footer">
          <button className="btn btn-primary" onClick={onClose}>
            OK
          </button>
        </div>
      </div>
    </div>
  );
};

export default AlertModal;

import React, { useRef, useState } from 'react';
import { FiX, FiSend } from 'react-icons/fi';
import { supabase } from '../integrations/supabase/client';
import '../styles/FeedbackModal.css';

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const FeedbackModal: React.FC<FeedbackModalProps> = ({ isOpen, onClose }) => {
  const overlayRef = useRef<HTMLDivElement>(null);
  const isMouseDownOnOverlay = useRef(false);
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  if (!isOpen) return null;

  const handleMouseDown = (e: React.MouseEvent) => {
    isMouseDownOnOverlay.current = e.target === overlayRef.current;
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (isMouseDownOnOverlay.current && e.target === overlayRef.current) {
      handleClose();
    }
    isMouseDownOnOverlay.current = false;
  };

  const handleClose = () => {
    if (isSubmitting) return;
    setEmail('');
    setMessage('');
    setSubmitStatus('idle');
    setErrorMessage('');
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!message.trim()) {
      setErrorMessage('Please enter some feedback');
      return;
    }

    if (!supabase) {
      setErrorMessage('Feedback service is not configured');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const { error } = await supabase.functions.invoke('send-support-email', {
        body: {
          name: 'PAMBL Feedback',
          email: email.trim() || 'anonymous@hominem.ai',
          subject: 'pambl-feedback',
          message: message.trim(),
          to: 'support+feedback@hominem.ai',
        },
      });

      if (error) throw error;

      setSubmitStatus('success');
      setMessage('');
      setEmail('');

      setTimeout(() => {
        handleClose();
      }, 2000);
    } catch (error) {
      console.error('Error submitting feedback:', error);
      setSubmitStatus('error');
      setErrorMessage(
        error instanceof Error ? error.message : 'Failed to submit feedback. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      ref={overlayRef}
      className="modal-overlay"
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
    >
      <div className="modal-content feedback-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Send Feedback</h2>
          <button
            className="modal-close"
            onClick={handleClose}
            disabled={isSubmitting}
            title="Close feedback"
          >
            <FiX size={24} />
          </button>
        </div>

        {submitStatus === 'success' ? (
          <div className="modal-body feedback-success">
            <div className="success-icon">✓</div>
            <p className="success-message">Thank you for your feedback!</p>
            <p className="success-subtext">We appreciate your input.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="modal-body feedback-form">
              {submitStatus === 'error' && (
                <div className="error-message">
                  <p>{errorMessage}</p>
                </div>
              )}

              <div className="form-group">
                <label htmlFor="feedback-email">Email (optional)</label>
                <input
                  id="feedback-email"
                  type="email"
                  placeholder="your@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isSubmitting}
                  className="form-input"
                />
                <p className="form-help">We'll use this to follow up if needed</p>
              </div>

              <div className="form-group">
                <label htmlFor="feedback-message">Feedback</label>
                <textarea
                  id="feedback-message"
                  placeholder="Share your thoughts, suggestions, or report an issue..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  disabled={isSubmitting}
                  className="form-textarea"
                  rows={6}
                />
              </div>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleClose}
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSubmitting || !message.trim()}
              >
                {isSubmitting ? (
                  <>
                    <span className="spinner-mini"></span>
                    Sending...
                  </>
                ) : (
                  <>
                    <FiSend size={16} />
                    Send Feedback
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default FeedbackModal;

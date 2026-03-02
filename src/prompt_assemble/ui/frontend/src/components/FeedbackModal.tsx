import React, { useRef, useState } from 'react';
import { FiX, FiSend } from 'react-icons/fi';
import { Turnstile } from '@marsidev/react-turnstile';
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
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  React.useEffect(() => {
    console.log('[FeedbackModal] isOpen changed:', isOpen);
  }, [isOpen]);

  if (!isOpen) return null;

  console.log('[FeedbackModal] Rendering modal, supabase configured:', !!supabase);

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
    setTurnstileToken(null);
    setSubmitStatus('idle');
    setErrorMessage('');
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    console.log('[FeedbackModal] Submit handler called');
    e.preventDefault();

    if (!message.trim()) {
      console.log('[FeedbackModal] No message entered');
      setErrorMessage('Please enter some feedback');
      return;
    }

    if (!turnstileToken) {
      console.log('[FeedbackModal] No Turnstile token');
      setErrorMessage('Please complete the human verification');
      return;
    }

    if (!supabase) {
      console.log('[FeedbackModal] Supabase not configured');
      setErrorMessage('Feedback service is not configured');
      return;
    }

    console.log('[FeedbackModal] Starting submit...');
    setIsSubmitting(true);
    setErrorMessage('');

    try {
      console.log('[FeedbackModal] Invoking Supabase function...');
      const { error } = await supabase.functions.invoke('send-support-email', {
        body: {
          name: 'PAMBL Feedback',
          email: email.trim() || 'anonymous@hominem.ai',
          subject: 'pambl-feedback',
          message: `[SENT_FROM_PAMBL_INTERFACE]\n\n${message.trim()}`,
          to: 'support+feedback@hominem.ai',
          turnstileToken,
        },
      });

      console.log('[FeedbackModal] Supabase response received, error:', error);

      if (error) throw error;

      console.log('[FeedbackModal] Success!');
      setSubmitStatus('success');
      setMessage('');
      setEmail('');
      setTurnstileToken(null);

      setTimeout(() => {
        console.log('[FeedbackModal] Closing modal after success');
        handleClose();
      }, 2000);
    } catch (error) {
      console.error('[FeedbackModal] Error submitting feedback:', error);
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

              <div className="form-group turnstile-group">
                <Turnstile
                  siteKey="0x4AAAAAACU1s6Em0oH4MRAG"
                  onSuccess={(token) => {
                    console.log('[FeedbackModal] Turnstile success:', token);
                    setTurnstileToken(token);
                  }}
                  onError={() => {
                    console.log('[FeedbackModal] Turnstile error');
                    setTurnstileToken(null);
                  }}
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
                disabled={isSubmitting || !message.trim() || !turnstileToken}
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

import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { useBreakpoint, useKeyboardVisible } from '../../config/breakpoints';

/**
 * Enterprise Adaptive Bottom Sheet & Modal Dialog
 * Desktop: Centered Modal Window
 * Mobile: Slide-up Bottom Sheet with Drag Indicator & Soft Keyboard Offset
 */
export default function BottomSheetModal({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  maxWidth = '560px'
}) {
  const { isMobile } = useBreakpoint();
  const { isKeyboardVisible, keyboardHeight } = useKeyboardVisible();

  // Disable body scroll when modal is active
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 2000,
        display: 'flex',
        alignItems: isMobile ? 'flex-end' : 'center',
        justifyContent: 'center',
        padding: isMobile ? '0' : '24px'
      }}
    >
      {/* Dark Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(5, 8, 16, 0.75)',
          backdropFilter: 'blur(var(--blur-amount))',
          WebkitBackdropFilter: 'blur(var(--blur-amount))'
        }}
      />

      {/* Modal / Bottom Sheet Panel */}
      <div
        style={{
          position: 'relative',
          width: isMobile ? '100%' : `min(100%, ${maxWidth})`,
          maxHeight: isMobile ? '88vh' : '85vh',
          background: 'var(--color-bg-surface)',
          border: '1px solid var(--color-border-subtle)',
          borderRadius: isMobile
            ? 'var(--radius-xl) var(--radius-xl) 0 0'
            : 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          display: 'flex',
          flexDirection: 'column',
          zIndex: 2001,
          paddingBottom: isMobile
            ? `calc(var(--safe-area-bottom) + ${isKeyboardVisible ? keyboardHeight : 16}px)`
            : '20px',
          transition: 'transform 0.25s cubic-bezier(0.2, 0.8, 0.2, 1)'
        }}
      >
        {/* Mobile Drag Handle */}
        {isMobile && (
          <div
            style={{
              width: '40px',
              height: '4px',
              background: 'rgba(255, 255, 255, 0.2)',
              borderRadius: '9999px',
              margin: '10px auto 4px auto'
            }}
          />
        )}

        {/* Modal Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            borderBottom: '1px solid var(--color-border-subtle)'
          }}
        >
          <div>
            {title && (
              <h3 style={{ fontSize: 'var(--font-size-h3)', fontWeight: '700', color: 'var(--color-text-primary)' }}>
                {title}
              </h3>
            )}
            {subtitle && (
              <div style={{ fontSize: 'var(--font-size-small)', color: 'var(--color-text-muted)' }}>
                {subtitle}
              </div>
            )}
          </div>

          <button
            onClick={onClose}
            className="touch-target-44"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--color-text-secondary)',
              cursor: 'pointer',
              padding: '6px'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Scrollable Body */}
        <div
          style={{
            padding: '20px',
            overflowY: 'auto',
            flex: 1,
            WebkitOverflowScrolling: 'touch'
          }}
        >
          {children}
        </div>
      </div>
    </div>
  );
}

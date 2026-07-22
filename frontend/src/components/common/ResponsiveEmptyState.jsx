import React from 'react';
import { useBreakpoint } from '../../config/breakpoints';
import { AlertCircle } from 'lucide-react';

export default function ResponsiveEmptyState({
  icon: Icon = AlertCircle,
  title = 'No Data Available',
  description = 'No active records match your current filter parameters.',
  actionLabel,
  onAction
}) {
  const { isMobile } = useBreakpoint();

  return (
    <div
      className="glass-panel"
      style={{
        padding: isMobile ? '20px 16px' : '48px 32px',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: isMobile ? '8px' : '16px',
        margin: '16px 0'
      }}
    >
      <div
        style={{
          width: isMobile ? '40px' : '64px',
          height: isMobile ? '40px' : '64px',
          borderRadius: '50%',
          background: 'rgba(99, 102, 241, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-accent-primary)'
        }}
      >
        <Icon size={isMobile ? 22 : 32} />
      </div>

      <div>
        <h4 style={{ fontSize: isMobile ? '1rem' : '1.2rem', fontWeight: '700', color: 'var(--color-text-primary)' }}>
          {title}
        </h4>
        <p style={{ fontSize: isMobile ? '0.8rem' : '0.9rem', color: 'var(--color-text-secondary)', maxWidth: '400px', margin: '4px auto 0 auto' }}>
          {description}
        </p>
      </div>

      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="touch-target-44"
          style={{
            padding: '10px 20px',
            background: 'var(--color-accent-primary)',
            color: '#ffffff',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            fontWeight: '600',
            fontSize: '0.85rem',
            cursor: 'pointer',
            marginTop: '8px',
            width: isMobile ? '100%' : 'auto'
          }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

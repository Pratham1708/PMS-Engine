import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function ErrorState({
  title = 'Unable to Load Data',
  message = 'A network or system error occurred while retrieving quantitative data.',
  onRetry
}) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '36px 24px',
        textAlign: 'center',
        background: 'rgba(239, 68, 68, 0.08)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid rgba(239, 68, 68, 0.25)',
        margin: '16px 0'
      }}
    >
      <div
        style={{
          width: '48px',
          height: '48px',
          borderRadius: '50%',
          background: 'rgba(239, 68, 68, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '12px',
          color: '#ef4444'
        }}
      >
        <AlertTriangle size={24} />
      </div>
      <h4 style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--color-text-primary)', marginBottom: '6px' }}>
        {title}
      </h4>
      <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', maxWidth: '400px', marginBottom: onRetry ? '16px' : '0' }}>
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            background: 'rgba(239, 68, 68, 0.2)',
            color: '#ef4444',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.85rem',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          <RefreshCw size={14} /> Retry Request
        </button>
      )}
    </div>
  );
}

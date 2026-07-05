import React from 'react';

/**
 * Shared layout component to show async task progress.
 *
 * @param {string} props.status - idle, pending, running, complete, failed
 * @param {number} props.elapsedTime - Time elapsed in seconds
 * @param {string} props.error - Error details if failed
 * @param {Function} props.onReset - Reset handler to go back to config form
 */
export default function ExperimentProgress({ status, elapsedTime, error, onReset }) {
  if (status === 'idle') return null;

  const getStatusBadgeClass = () => {
    switch (status) {
      case 'pending': return 'lab-status-badge pending';
      case 'running': return 'lab-status-badge running';
      case 'complete': return 'lab-status-badge complete';
      case 'failed': return 'lab-status-badge failed';
      default: return 'lab-status-badge';
    }
  };

  const getProgressBarClass = () => {
    if (status === 'complete') return 'lab-progress-bar complete';
    if (status === 'running') return 'lab-progress-bar running';
    return 'lab-progress-bar';
  };

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="card" style={{
      padding: '24px',
      margin: '20px 0',
      background: 'var(--bg-card)',
      border: '1px solid var(--border-primary)',
      borderRadius: 'var(--radius-lg)',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'between', gap: '15px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '15px', fontWeight: '600' }}>Experiment Status:</span>
          <span className={getStatusBadgeClass()}>{status}</span>
        </div>
        <div style={{ marginLeft: 'auto', fontSize: '14px', color: 'var(--text-secondary)' }}>
          Elapsed Time: <strong>{formatTime(elapsedTime)}</strong>
        </div>
      </div>

      {(status === 'pending' || status === 'running') && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="lab-progress-bar-container">
            <div className={getProgressBarClass()}></div>
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Executing quantitative simulation on server thread pool...
          </span>
        </div>
      )}

      {status === 'complete' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="lab-progress-bar-container">
            <div className="lab-progress-bar complete"></div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <span style={{ fontSize: '13px', color: '#10b981', fontWeight: '500' }}>
              ✓ Backtest execution completed successfully.
            </span>
            <button
              onClick={onReset}
              className="btn-primary"
              style={{
                marginLeft: 'auto',
                padding: '6px 14px',
                fontSize: '13px',
                borderRadius: '6px',
                cursor: 'pointer'
              }}
            >
              Configure New Run
            </button>
          </div>
        </div>
      )}

      {status === 'failed' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{
            background: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
            color: '#ef4444',
            fontSize: '13px',
            fontFamily: 'monospace',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all'
          }}>
            {error || 'An unexpected error occurred during execution.'}
          </div>
          <button
            onClick={onReset}
            className="btn-secondary"
            style={{
              alignSelf: 'flex-start',
              padding: '6px 14px',
              fontSize: '13px',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Reset Form
          </button>
        </div>
      )}
    </div>
  );
}


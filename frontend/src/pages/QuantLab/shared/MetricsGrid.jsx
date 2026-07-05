import React from 'react';

/**
 * Shared layout component to render key-value metrics from quant experiments.
 *
 * @param {Object} props.metrics - Flat dictionary of metric_name -> metric_value.
 */
export default function MetricsGrid({ metrics, scrollable = true }) {
  if (!metrics || Object.keys(metrics).length === 0) return null;

  // Format utility
  const formatMetric = (key, val) => {
    if (val === null || val === undefined) return '—';
    const num = parseFloat(val);
    if (isNaN(num)) return String(val);

    const k = key.toLowerCase();
    
    // Percentage format
    if (k.endsWith('_pct') || k.includes('win_rate') || k.includes('return') || k.includes('capture') || k.includes('rate') || k.includes('percent')) {
      // If it's already in 0-100 format, just add %
      if (Math.abs(num) > 1.0 || num === 0) {
        return `${num.toFixed(2)}%`;
      }
      return `${(num * 100).toFixed(2)}%`;
    }

    // Integer metrics
    if (k.includes('count') || k.includes('trades') || k.includes('days') || k.includes('bars') || k.includes('splits') || k.includes('folds') || k === 'n') {
      return Math.round(num).toString();
    }

    // Currency values
    if (k.includes('capital') || k.includes('pnl') || k.includes('equity') || k.includes('amount')) {
      return '₹' + num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    // Default float format (Sharpe, Calmar, t-stat, etc.)
    return num.toFixed(3);
  };

  // Human-readable labels
  const formatLabel = (key) => {
    return key
      .replace(/_pct$/, ' (%)')
      .replace(/_ratio$/, '')
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  // Filter out meta parameters or json blobs from rendering
  const displayableMetrics = Object.entries(metrics).filter(([key]) => {
    const k = key.toLowerCase();
    return !k.endsWith('_json') && !k.includes('strategy_type') && !k.includes('outcome') && k !== 'experiment_id';
  });

  return (
    <div style={scrollable ? {
      display: 'flex',
      flexDirection: 'row',
      gap: '16px',
      margin: '20px 0',
      paddingBottom: '8px',
      whiteSpace: 'nowrap',
      width: '100%',
    } : {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
      gap: '16px',
      margin: '20px 0'
    }}>
      {displayableMetrics.map(([key, val]) => (
        <div key={key} className="card" style={scrollable ? {
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          textAlign: 'center',
          border: '1px solid var(--border-primary)',
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          minWidth: '220px',
          flex: '0 0 auto'
        } : {
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          textAlign: 'center',
          border: '1px solid var(--border-primary)',
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)'
        }}>
          <span style={{
            fontSize: '11px',
            textTransform: 'uppercase',
            color: 'var(--text-secondary)',
            letterSpacing: '0.5px',
            marginBottom: '6px',
            whiteSpace: 'normal',
            lineHeight: '1.3'
          }}>
            {formatLabel(key)}
          </span>
          <span style={{
            fontSize: '20px',
            fontWeight: '700',
            fontFamily: 'monospace',
            color: 'var(--text-primary)'
          }}>
            {formatMetric(key, val)}
          </span>
        </div>
      ))}
    </div>
  );
}


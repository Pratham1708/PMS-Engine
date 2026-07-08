import React from 'react';

/**
 * ChartToggle.jsx
 * Switch button group to choose between Line and Candlestick modes.
 */
export default function ChartToggle({ mode, onChange }) {
  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      background: 'rgba(255, 255, 255, 0.05)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: '6px',
      padding: '2px',
      gap: '2px',
    }}>
      <button
        onClick={() => onChange('line')}
        style={{
          background: mode === 'line' ? '#6366f1' : 'transparent',
          border: 'none',
          color: mode === 'line' ? '#fff' : 'rgba(255, 255, 255, 0.65)',
          padding: '4px 10px',
          borderRadius: '4px',
          fontSize: '11px',
          fontWeight: 600,
          cursor: 'pointer',
          transition: 'all 0.15s ease',
          outline: 'none',
        }}
        title="Switch to Line Chart"
      >
        📈 Line
      </button>
      <button
        onClick={() => onChange('candlestick')}
        style={{
          background: mode === 'candlestick' ? '#6366f1' : 'transparent',
          border: 'none',
          color: mode === 'candlestick' ? '#fff' : 'rgba(255, 255, 255, 0.65)',
          padding: '4px 10px',
          borderRadius: '4px',
          fontSize: '11px',
          fontWeight: 600,
          cursor: 'pointer',
          transition: 'all 0.15s ease',
          outline: 'none',
        }}
        title="Switch to Candlestick Chart"
      >
        📊 Candle
      </button>
    </div>
  );
}

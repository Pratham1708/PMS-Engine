import React from 'react';

export default function StockDetailDrawer({ symbol, stockPayload, onClose }) {
  if (!symbol) return null;

  const ohlcv = stockPayload?.ohlcv || {};
  const indicators = stockPayload?.indicators || {};

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: '420px',
        background: '#0f172a',
        borderLeft: '1px solid #1e293b',
        boxShadow: '-8px 0 24px rgba(0,0,0,0.5)',
        zIndex: 1000,
        padding: '24px',
        overflowY: 'auto',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h3 style={{ margin: 0, color: '#f8fafc', fontSize: '20px', fontWeight: '800' }}>{symbol}</h3>
          <span style={{ fontSize: '11px', color: '#38bdf8' }}>Live Pipeline Drilldown Data</span>
        </div>
        <button
          onClick={onClose}
          style={{ background: '#1e293b', color: '#94a3b8', border: 'none', borderRadius: '6px', width: '32px', height: '32px', cursor: 'pointer', fontWeight: '700' }}
        >
          ✕
        </button>
      </div>

      {/* OHLCV Summary */}
      <div style={{ background: '#1e293b', padding: '12px', borderRadius: '8px', marginBottom: '16px' }}>
        <h4 style={{ margin: '0 0 8px 0', color: '#f8fafc', fontSize: '12px' }}>Market Quote (OHLCV)</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', fontSize: '12px', color: '#94a3b8' }}>
          <div>Open: <strong style={{ color: '#f8fafc' }}>₹{ohlcv.Open || ohlcv.open || '—'}</strong></div>
          <div>Close: <strong style={{ color: '#f8fafc' }}>₹{ohlcv.Close || ohlcv.close || ohlcv.CurrentPrice || '—'}</strong></div>
          <div>High: <strong style={{ color: '#10b981' }}>₹{ohlcv.High || ohlcv.high || '—'}</strong></div>
          <div>Low: <strong style={{ color: '#ef4444' }}>₹{ohlcv.Low || ohlcv.low || '—'}</strong></div>
          <div>Volume: <strong style={{ color: '#38bdf8' }}>{(ohlcv.Volume || ohlcv.volume || 0).toLocaleString()}</strong></div>
        </div>
      </div>

      {/* Technical Indicators */}
      <div style={{ background: '#1e293b', padding: '12px', borderRadius: '8px', marginBottom: '16px' }}>
        <h4 style={{ margin: '0 0 8px 0', color: '#38bdf8', fontSize: '12px' }}>Technical Indicators</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', fontSize: '12px', color: '#94a3b8' }}>
          <div>EMA 20: <strong style={{ color: '#f8fafc' }}>{indicators.ema20 || indicators.ema_20 || '—'}</strong></div>
          <div>EMA 50: <strong style={{ color: '#f8fafc' }}>{indicators.ema50 || indicators.ema_50 || '—'}</strong></div>
          <div>EMA 200: <strong style={{ color: '#f8fafc' }}>{indicators.ema200 || indicators.ema_200 || '—'}</strong></div>
          <div>RSI (14): <strong style={{ color: '#a855f7' }}>{indicators.rsi || indicators.rsi_14 || '—'}</strong></div>
          <div>MACD: <strong style={{ color: '#38bdf8' }}>{indicators.macd || '—'}</strong></div>
          <div>ADX: <strong style={{ color: '#f59e0b' }}>{indicators.adx || indicators.adx_14 || '—'}</strong></div>
        </div>
      </div>
    </div>
  );
}

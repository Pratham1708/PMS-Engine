import React from 'react';

export default function MiniOHLCChart({ symbol, ohlcv }) {
  if (!symbol || !ohlcv) {
    return (
      <div style={{ background: '#0f172a', padding: '16px', borderRadius: '12px', border: '1px solid #1e293b', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: '12px' }}>
        Awaiting OHLCV market data stream...
      </div>
    );
  }

  const open = ohlcv.Open || ohlcv.open || 0;
  const high = ohlcv.High || ohlcv.high || 0;
  const low = ohlcv.Low || ohlcv.low || 0;
  const close = ohlcv.Close || ohlcv.close || ohlcv.CurrentPrice || 0;
  const volume = ohlcv.Volume || ohlcv.volume || 0;
  const chgPct = ohlcv.DailyChangePct || 0;

  const isUp = close >= open;
  const color = isUp ? '#10b981' : '#ef4444';

  return (
    <div style={{ background: '#0f172a', padding: '16px', borderRadius: '12px', border: '1px solid #1e293b', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div>
          <span style={{ fontSize: '16px', fontWeight: '800', color: '#f8fafc' }}>{symbol}</span>
          <span style={{ fontSize: '11px', color: '#94a3b8', marginLeft: '8px' }}>NSE Live Stream</span>
        </div>
        <span style={{ fontSize: '12px', fontWeight: '700', color, background: isUp ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)', padding: '2px 8px', borderRadius: '4px' }}>
          {chgPct > 0 ? '+' : ''}{chgPct.toFixed(2)}%
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '8px', marginTop: '12px' }}>
        <div style={{ background: '#1e293b', padding: '8px', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>OPEN</div>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#f8fafc' }}>₹{open.toFixed(2)}</div>
        </div>
        <div style={{ background: '#1e293b', padding: '8px', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>HIGH</div>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#10b981' }}>₹{high.toFixed(2)}</div>
        </div>
        <div style={{ background: '#1e293b', padding: '8px', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>LOW</div>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#ef4444' }}>₹{low.toFixed(2)}</div>
        </div>
        <div style={{ background: '#1e293b', padding: '8px', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>CLOSE</div>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#f8fafc' }}>₹{close.toFixed(2)}</div>
        </div>
        <div style={{ background: '#1e293b', padding: '8px', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>VOLUME</div>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#38bdf8' }}>{volume.toLocaleString()}</div>
        </div>
      </div>
    </div>
  );
}

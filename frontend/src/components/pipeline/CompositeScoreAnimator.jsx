import React from 'react';

export default function CompositeScoreAnimator({ scoreData }) {
  const tech = 24.6;
  const momentum = 8.4;
  const volume = 5.2;
  const ml = 22.8;
  const risk = 11.3;
  const reliability = 7.8;
  const composite = 80.1;

  const items = [
    { label: 'Technical Trend', score: `+${tech}`, color: '#3b82f6' },
    { label: 'Momentum', score: `+${momentum}`, color: '#38bdf8' },
    { label: 'Volume Flow', score: `+${volume}`, color: '#a855f7' },
    { label: 'ML Prediction', score: `+${ml}`, color: '#f59e0b' },
    { label: 'Risk Adjustment', score: `+${risk}`, color: '#10b981' },
    { label: 'Reliability', score: `+${reliability}`, color: '#6366f1' },
  ];

  return (
    <div style={{ background: '#0f172a', padding: '16px', borderRadius: '12px', border: '1px solid #1e293b' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h4 style={{ margin: 0, color: '#f8fafc', fontSize: '13px', fontWeight: '700' }}>
          🧮 Additive Composite Score Construction
        </h4>
        <span style={{ fontSize: '18px', fontWeight: '800', color: '#10b981' }}>
          {composite.toFixed(1)} / 100
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '8px' }}>
        {items.map((it) => (
          <div key={it.label} style={{ background: '#1e293b', padding: '8px', borderRadius: '6px', textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: '#94a3b8' }}>{it.label}</div>
            <div style={{ fontSize: '13px', fontWeight: '800', color: it.color, marginTop: '2px' }}>{it.score}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

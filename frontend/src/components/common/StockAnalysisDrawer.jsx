import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Legend, ReferenceLine
} from 'recharts';
import { testStockStrategy, fetchSnapshotsList, previewStrategyExplain } from '../../api/strategyApi';
import LoadingSpinner from './LoadingSpinner';
import RatingBadge from './RatingBadge';

// ── Colour helpers ─────────────────────────────────────────────────────────────

const ratingColor = (rec) => {
  if (!rec) return '#94a3b8';
  if (rec.includes('STRONG BUY')) return '#10b981';
  if (rec.includes('BUY')) return '#34d399';
  if (rec.includes('STRONG SELL')) return '#ef4444';
  if (rec.includes('SELL')) return '#f87171';
  return '#f59e0b';
};

const contribColor = (v) => (v > 0 ? '#10b981' : v < 0 ? '#ef4444' : '#94a3b8');

const PIE_PALETTE = [
  '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444',
  '#06b6d4', '#ec4899', '#a78bfa', '#34d399', '#fb923c',
];

// ── SVG Arc Gauge ──────────────────────────────────────────────────────────────

function ArcGauge({ value, max = 100, size = 120, label, color = '#3b82f6', showPercent = true }) {
  const r = (size - 16) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = Math.PI * r; // half arc
  const pct = Math.min(Math.max(value / max, 0), 1);
  const dash = circumference * pct;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <svg width={size} height={size / 2 + 12} style={{ overflow: 'visible' }}>
        {/* Track */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={8}
          strokeLinecap="round"
        />
        {/* Fill */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke={color}
          strokeWidth={8}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference}`}
          style={{ transition: 'stroke-dasharray 0.6s ease' }}
        />
        {/* Value */}
        <text x={cx} y={cy + 4} textAnchor="middle" fill="#f1f5f9" fontSize={size < 100 ? 14 : 18} fontWeight="bold">
          {showPercent ? `${Math.round(value)}%` : Math.round(value)}
        </text>
      </svg>
      <span style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center' }}>{label}</span>
    </div>
  );
}

// ── Waterfall tooltip ──────────────────────────────────────────────────────────

function WaterfallTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  return (
    <div style={{ background: '#0a1628', border: '1px solid rgba(255,255,255,0.12)', padding: '10px 14px', borderRadius: 8, fontSize: 12 }}>
      <div style={{ fontWeight: 'bold', color: '#e2e8f0', marginBottom: 4 }}>{d.name}</div>
      <div style={{ color: 'var(--text-muted)' }}>Weight: {d.weight != null ? `${(d.weight * 100).toFixed(1)}%` : '—'}</div>
      <div style={{ color: contribColor(d.contribution), fontWeight: 'bold', marginTop: 2 }}>
        Contribution: {d.contribution > 0 ? '+' : ''}{d.contribution?.toFixed(2)}
      </div>
    </div>
  );
}

// ── Main Drawer ────────────────────────────────────────────────────────────────

/**
 * StockAnalysisDrawer
 *
 * Props:
 *  symbol          – ticker string, e.g. "RELIANCE"
 *  companyName     – display name
 *  currentDefinition – the currently built strategy definition object
 *  strategies      – array of saved strategies (for Compare tab)
 *  cachedRank      – rank from full-universe run (optional)
 *  cachedTotal     – total stocks from full-universe run (optional)
 *  onClose         – close callback
 */
export default function StockAnalysisDrawer({
  symbol,
  companyName,
  currentDefinition,
  strategies = [],
  cachedRank = null,
  cachedTotal = null,
  onClose,
}) {
  const [activeTab, setActiveTab] = useState('overview');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // What-if tab state
  const [whatIfWeights, setWhatIfWeights] = useState({});
  const [whatIfResult, setWhatIfResult] = useState(null);
  const [whatIfLoading, setWhatIfLoading] = useState(false);
  const whatIfTimer = useRef(null);

  // Compare tab state
  const [compareResults, setCompareResults] = useState([]);
  const [compareLoading, setCompareLoading] = useState(false);

  // Historical tab state
  const [snapshots, setSnapshots] = useState([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState(null);
  const [histResult, setHistResult] = useState(null);
  const [histLoading, setHistLoading] = useState(false);

  // ── Initial load ─────────────────────────────────────────────────────────────

  useEffect(() => {
    if (!symbol || !currentDefinition) return;
    setLoading(true);
    setError(null);
    testStockStrategy(currentDefinition, symbol)
      .then(res => {
        setResult(res.data);
        // Seed what-if weights from the current definition
        const seedWeights = {};
        (currentDefinition.weights || []).forEach(w => {
          seedWeights[w.feature_id] = w.weight;
        });
        setWhatIfWeights(seedWeights);
        setWhatIfResult(res.data);
      })
      .catch(err => {
        console.error('[StockAnalysisDrawer] test-stock failed', err);
        setError('Could not load strategy analysis. Ensure the backend is running.');
      })
      .finally(() => setLoading(false));
  }, [symbol, currentDefinition]);

  // ── Compare tab ──────────────────────────────────────────────────────────────

  useEffect(() => {
    if (activeTab !== 'compare' || !symbol || !currentDefinition) return;
    if (compareResults.length > 0) return; // already loaded
    setCompareLoading(true);
    const allStrats = [
      { strategy_id: '__current__', strategy_name: '★ Current (Unsaved)', strategy_definition: currentDefinition },
      ...strategies,
    ];
    Promise.allSettled(
      allStrats.map(s =>
        previewStrategyExplain(s.strategy_definition, symbol)
          .then(r => ({ name: s.strategy_name, id: s.strategy_id, score: r.data?.current_value, data: r.data }))
          .catch(() => ({ name: s.strategy_name, id: s.strategy_id, score: null, data: null }))
      )
    ).then(settled => {
      setCompareResults(settled.map(p => p.value || p.reason));
    }).finally(() => setCompareLoading(false));
  }, [activeTab]);

  // ── Historical tab ───────────────────────────────────────────────────────────

  useEffect(() => {
    if (activeTab !== 'historical' && snapshots.length > 0) return;
    if (activeTab === 'historical' && snapshots.length === 0) {
      fetchSnapshotsList(8)
        .then(r => setSnapshots(r.data || []))
        .catch(() => setSnapshots([]));
    }
  }, [activeTab]);

  const loadHistoricalResult = useCallback((snapId) => {
    if (!snapId || !symbol || !currentDefinition) return;
    setHistLoading(true);
    setHistResult(null);
    testStockStrategy(currentDefinition, symbol, snapId)
      .then(r => setHistResult(r.data))
      .catch(() => setHistResult(null))
      .finally(() => setHistLoading(false));
  }, [symbol, currentDefinition]);

  // ── What-if debounce ─────────────────────────────────────────────────────────

  const handleWhatIfSlider = (featureId, newWeight) => {
    const updated = { ...whatIfWeights, [featureId]: parseFloat(newWeight) };
    setWhatIfWeights(updated);

    clearTimeout(whatIfTimer.current);
    whatIfTimer.current = setTimeout(() => {
      // Build a patched definition
      const patchedDef = {
        ...currentDefinition,
        weights: (currentDefinition.weights || []).map(w =>
          w.feature_id === featureId ? { ...w, weight: parseFloat(newWeight) } : { ...w, weight: updated[w.feature_id] ?? w.weight }
        ),
      };
      setWhatIfLoading(true);
      testStockStrategy(patchedDef, symbol)
        .then(r => setWhatIfResult(r.data))
        .catch(() => {})
        .finally(() => setWhatIfLoading(false));
    }, 500);
  };

  // ── Recommendation label / colour ──────────────────────────────────────────

  const rec = result?.recommendation || 'HOLD';
  const recColor = ratingColor(rec);
  const score = result?.strategy_score ?? 0;
  const confidence = result?.confidence ?? 0;
  const rank = result?.rank ?? cachedRank;
  const total = result?.total_stocks ?? cachedTotal;

  const tabs = [
    { id: 'overview', label: '📊 Overview' },
    { id: 'breakdown', label: '🔬 Breakdown' },
    { id: 'whatif', label: '⚗️ What-If' },
    { id: 'compare', label: '⚖️ Compare' },
    { id: 'historical', label: '📅 Historical' },
  ];

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0,
          background: 'rgba(0,0,0,0.55)',
          backdropFilter: 'blur(4px)',
          zIndex: 1000,
        }}
      />

      {/* Drawer panel */}
      <div
        style={{
          position: 'fixed',
          top: 0, right: 0,
          width: 'min(860px, 95vw)',
          height: '100vh',
          background: 'linear-gradient(135deg, #0a1628 0%, #0d1f3c 100%)',
          border: '1px solid rgba(59,130,246,0.2)',
          borderRight: 'none',
          boxShadow: '-8px 0 40px rgba(0,0,0,0.5)',
          zIndex: 1001,
          display: 'flex',
          flexDirection: 'column',
          overflowY: 'auto',
        }}
      >
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(59,130,246,0.06)',
          flexShrink: 0,
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 22, fontWeight: 'bold', color: '#e2e8f0' }}>{companyName || symbol}</span>
              <span style={{ fontSize: 13, color: 'var(--text-muted)', background: 'rgba(255,255,255,0.06)', padding: '2px 8px', borderRadius: 4 }}>{symbol}</span>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>Strategy Analysis Panel</div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: '#e2e8f0',
              borderRadius: 8,
              padding: '8px 14px',
              cursor: 'pointer',
              fontSize: 16,
            }}
          >✕</button>
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex',
          gap: 0,
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          overflowX: 'auto',
          flexShrink: 0,
        }}>
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '12px 18px',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === tab.id ? '2px solid #3b82f6' : '2px solid transparent',
                color: activeTab === tab.id ? '#3b82f6' : 'var(--text-muted)',
                fontWeight: activeTab === tab.id ? 'bold' : 'normal',
                fontSize: 13,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'color 0.2s',
              }}
            >{tab.label}</button>
          ))}
        </div>

        {/* Tab content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: 60, gap: 16 }}>
              <LoadingSpinner />
              <span style={{ color: 'var(--text-muted)', fontSize: 14 }}>Executing strategy on {symbol}…</span>
            </div>
          ) : error ? (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <div style={{ color: '#ef4444', fontSize: 16, marginBottom: 8 }}>⚠️ Analysis Failed</div>
              <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>{error}</div>
            </div>
          ) : (
            <>
              {/* ── TAB: OVERVIEW ─────────────────────────────────────────── */}
              {activeTab === 'overview' && (
                <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                  {/* Score hero row */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
                    {/* Big Score */}
                    <div style={{ padding: 20, borderRadius: 12, background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)', textAlign: 'center' }}>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>Strategy Score</div>
                      <div style={{ fontSize: 42, fontWeight: 'bold', color: recColor, lineHeight: 1 }}>{score.toFixed(2)}</div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>Range: −100 to +100</div>
                    </div>

                    {/* Recommendation */}
                    <div style={{ padding: 20, borderRadius: 12, background: `rgba(${recColor === '#10b981' ? '16,185,129' : recColor === '#ef4444' ? '239,68,68' : '245,158,11'},0.08)`, border: `1px solid ${recColor}30`, textAlign: 'center' }}>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>Recommendation</div>
                      <div style={{ fontSize: 20, fontWeight: 'bold', color: recColor }}>{rec}</div>
                      {rank && (
                        <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-muted)' }}>
                          Rank <span style={{ color: '#e2e8f0', fontWeight: 'bold' }}>{rank}</span>
                          {total ? <> / {total}</> : ''}
                        </div>
                      )}
                    </div>

                    {/* Confidence gauge */}
                    <div style={{ padding: 16, borderRadius: 12, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                      <ArcGauge value={confidence} max={100} size={110} label="Confidence" color="#8b5cf6" showPercent />
                    </div>
                  </div>

                  {/* Sub-scores row */}
                  {(result?.technical_score != null || result?.ml_score != null || result?.gru_score != null || result?.risk_score != null) && (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
                      {[
                        { label: 'Technical', val: result.technical_score, color: '#3b82f6' },
                        { label: 'ML Score', val: result.ml_score, color: '#8b5cf6' },
                        { label: 'GRU Score', val: result.gru_score, color: '#06b6d4' },
                        { label: 'Risk Score', val: result.risk_score, color: '#f59e0b' },
                      ].map(({ label, val, color }) => val != null && (
                        <div key={label} style={{ padding: '12px 16px', borderRadius: 8, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', textAlign: 'center' }}>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
                          <div style={{ fontSize: 22, fontWeight: 'bold', color }}>{val.toFixed(1)}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Explanation narrative */}
                  {result?.explanation?.dynamic_explanation && (
                    <div style={{ padding: 16, borderRadius: 8, background: 'rgba(59,130,246,0.04)', border: '1px solid rgba(59,130,246,0.1)', fontSize: 13, lineHeight: 1.6, color: '#cbd5e1' }}>
                      💡 {result.explanation.dynamic_explanation}
                    </div>
                  )}

                  {/* Score composition table */}
                  {result?.feature_breakdown?.length > 0 && (
                    <div>
                      <h4 style={{ margin: '0 0 12px', fontSize: 14, color: '#60a5fa' }}>Score Composition</h4>
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                          <thead>
                            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                              {['Feature', 'Raw Value', 'Weight', 'Contribution', 'Direction'].map(h => (
                                <th key={h} style={{ padding: '8px 12px', textAlign: h === 'Feature' ? 'left' : 'center', color: 'var(--text-muted)', fontWeight: 600 }}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {result.feature_breakdown.map((f, i) => (
                              <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                                <td style={{ padding: '8px 12px', fontWeight: 'bold', color: '#e2e8f0' }}>{f.name}</td>
                                <td style={{ padding: '8px 12px', textAlign: 'center', color: '#94a3b8' }}>{f.raw_value != null ? Number(f.raw_value).toFixed(2) : '—'}</td>
                                <td style={{ padding: '8px 12px', textAlign: 'center', color: '#94a3b8' }}>{f.weight != null ? `${(f.weight * 100).toFixed(1)}%` : '—'}</td>
                                <td style={{ padding: '8px 12px', textAlign: 'center', fontWeight: 'bold', color: contribColor(f.contribution) }}>
                                  {f.contribution > 0 ? '+' : ''}{f.contribution?.toFixed(2)}
                                </td>
                                <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                                  <span style={{
                                    padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 'bold',
                                    background: f.direction === 'positive' ? 'rgba(16,185,129,0.12)' : f.direction === 'negative' ? 'rgba(239,68,68,0.12)' : 'rgba(148,163,184,0.12)',
                                    color: f.direction === 'positive' ? '#10b981' : f.direction === 'negative' ? '#ef4444' : '#94a3b8',
                                  }}>{f.direction?.toUpperCase() || 'NEUTRAL'}</span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* ── TAB: BREAKDOWN ────────────────────────────────────────── */}
              {activeTab === 'breakdown' && (
                <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                  {/* Waterfall chart */}
                  {result?.feature_breakdown?.length > 0 && (
                    <div>
                      <h4 style={{ margin: '0 0 12px', fontSize: 14, color: '#60a5fa' }}>Feature Contribution Waterfall</h4>
                      <ResponsiveContainer width="100%" height={220}>
                        <BarChart data={result.feature_breakdown} margin={{ top: 0, right: 10, left: -10, bottom: 40 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                          <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} angle={-35} textAnchor="end" interval={0} />
                          <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
                          <Tooltip content={<WaterfallTooltip />} />
                          <ReferenceLine y={0} stroke="rgba(255,255,255,0.15)" />
                          <Bar dataKey="contribution" radius={[4, 4, 0, 0]}>
                            {result.feature_breakdown.map((entry, idx) => (
                              <Cell key={idx} fill={contribColor(entry.contribution)} fillOpacity={0.85} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Weight Pie + Technical vs ML comparison */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                    {/* Weight pie chart */}
                    {result?.feature_breakdown?.length > 0 && (
                      <div>
                        <h4 style={{ margin: '0 0 12px', fontSize: 14, color: '#60a5fa' }}>Weight Allocation</h4>
                        <ResponsiveContainer width="100%" height={200}>
                          <PieChart>
                            <Pie
                              data={result.feature_breakdown.map(f => ({ name: f.name, value: Math.abs(f.weight || 0) }))}
                              cx="50%" cy="50%"
                              outerRadius={75}
                              dataKey="value"
                              nameKey="name"
                              label={({ name, percent }) => `${name.substring(0, 6)}… ${(percent * 100).toFixed(0)}%`}
                              labelLine={false}
                            >
                              {result.feature_breakdown.map((_, i) => (
                                <Cell key={i} fill={PIE_PALETTE[i % PIE_PALETTE.length]} />
                              ))}
                            </Pie>
                            <Tooltip formatter={(v) => `${(v * 100).toFixed(1)}%`} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    )}

                    {/* Technical vs ML bar */}
                    <div>
                      <h4 style={{ margin: '0 0 12px', fontSize: 14, color: '#60a5fa' }}>Score Components</h4>
                      {[
                        { label: 'Technical', val: result?.technical_score, color: '#3b82f6', max: 100 },
                        { label: 'Machine Learning', val: result?.ml_score, color: '#8b5cf6', max: 100 },
                        { label: 'GRU / Sequential', val: result?.gru_score, color: '#06b6d4', max: 100 },
                        { label: 'Risk Score', val: result?.risk_score, color: '#f59e0b', max: 100 },
                      ].map(({ label, val, color, max }) => val != null && (
                        <div key={label} style={{ marginBottom: 12 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 12 }}>
                            <span style={{ color: '#94a3b8' }}>{label}</span>
                            <span style={{ color, fontWeight: 'bold' }}>{val.toFixed(1)}</span>
                          </div>
                          <div style={{ height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                            <div style={{
                              height: '100%', borderRadius: 3,
                              background: color,
                              width: `${Math.min(Math.max((val + 100) / 200, 0), 1) * 100}%`,
                              transition: 'width 0.6s ease',
                            }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Category breakdown from feature_attributions */}
                  {result?.explanation?.feature_attributions?.length > 0 && (
                    <div>
                      <h4 style={{ margin: '0 0 12px', fontSize: 14, color: '#60a5fa' }}>Category Contribution</h4>
                      {result.explanation.feature_attributions.map((cat, i) => (
                        <div key={i} style={{ marginBottom: 10, padding: '10px 14px', borderRadius: 8, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                            <span style={{ fontWeight: 'bold', color: '#e2e8f0' }}>{cat.category}</span>
                            <span style={{ color: contribColor(cat.subtotal), fontWeight: 'bold' }}>
                              {cat.subtotal > 0 ? '+' : ''}{cat.subtotal?.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ── TAB: WHAT-IF ──────────────────────────────────────────── */}
              {activeTab === 'whatif' && (
                <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                  {/* Score delta hero */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
                    <div style={{ padding: 16, borderRadius: 10, background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)', textAlign: 'center' }}>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Original Score</div>
                      <div style={{ fontSize: 28, fontWeight: 'bold', color: recColor }}>{score.toFixed(2)}</div>
                    </div>
                    <div style={{ padding: 16, borderRadius: 10, background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.2)', textAlign: 'center', position: 'relative' }}>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>New Score</div>
                      {whatIfLoading
                        ? <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 4 }}><LoadingSpinner /></div>
                        : <div style={{ fontSize: 28, fontWeight: 'bold', color: ratingColor(whatIfResult?.recommendation) }}>{whatIfResult?.strategy_score?.toFixed(2) ?? '—'}</div>
                      }
                    </div>
                    <div style={{ padding: 16, borderRadius: 10, background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.15)', textAlign: 'center' }}>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Delta</div>
                      {(() => {
                        const delta = (whatIfResult?.strategy_score ?? score) - score;
                        return (
                          <div style={{ fontSize: 28, fontWeight: 'bold', color: contribColor(delta) }}>
                            {delta > 0 ? '+' : ''}{delta.toFixed(2)}
                          </div>
                        );
                      })()}
                    </div>
                  </div>

                  <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: 0 }}>
                    ⚗️ Adjust weights below and see how the score changes in real time. Changes are <strong>not saved</strong>.
                  </p>

                  {/* Weight sliders */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    {(currentDefinition?.weights || []).map(w => {
                      const currentW = whatIfWeights[w.feature_id] ?? w.weight;
                      const fname = result?.feature_breakdown?.find(f =>
                        f.name.toLowerCase().includes(w.feature_id.toLowerCase().replace(/_/g, ' '))
                      )?.name || w.feature_id;
                      return (
                        <div key={w.feature_id} style={{ padding: '12px 16px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.01)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                            <span style={{ fontSize: 13, fontWeight: 'bold', color: '#e2e8f0' }}>{fname}</span>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Original: {w.weight?.toFixed(1)}%</span>
                              <span style={{ fontSize: 13, fontWeight: 'bold', color: '#3b82f6' }}>→ {currentW?.toFixed(1)}%</span>
                            </div>
                          </div>
                          <input
                            type="range"
                            min="0" max="100" step="0.5"
                            value={currentW}
                            onChange={e => handleWhatIfSlider(w.feature_id, e.target.value)}
                            style={{ width: '100%' }}
                          />
                        </div>
                      );
                    })}
                    {(!currentDefinition?.weights || currentDefinition.weights.length === 0) && (
                      <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No feature weights configured. Go back to Step 3 to add weights.</p>
                    )}
                  </div>
                </div>
              )}

              {/* ── TAB: COMPARE ──────────────────────────────────────────── */}
              {activeTab === 'compare' && (
                <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: 0 }}>
                    Comparing all saved strategies against <strong>{symbol}</strong>. Sorted by score descending.
                  </p>
                  {compareLoading ? (
                    <div style={{ textAlign: 'center', padding: 40 }}><LoadingSpinner /></div>
                  ) : compareResults.length === 0 ? (
                    <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No strategies to compare. Save at least one strategy in the library.</p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                      {[...compareResults]
                        .sort((a, b) => (b.score ?? -999) - (a.score ?? -999))
                        .map((r, i) => {
                          const s = r.score ?? 0;
                          const rRec = r.data?.current_value >= 35 ? (r.data.current_value >= 55 ? 'STRONG BUY' : 'BUY')
                            : r.data?.current_value <= -15 ? 'SELL' : 'HOLD';
                          const rc = ratingColor(rRec);
                          return (
                            <div key={i} style={{
                              padding: '14px 16px',
                              borderRadius: 10,
                              border: r.id === '__current__' ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.06)',
                              background: r.id === '__current__' ? 'rgba(59,130,246,0.06)' : 'rgba(255,255,255,0.02)',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                            }}>
                              <div>
                                <div style={{ fontWeight: 'bold', fontSize: 14, color: '#e2e8f0' }}>{r.name}</div>
                                {r.id === '__current__' && <div style={{ fontSize: 11, color: '#3b82f6', marginTop: 2 }}>Active (unsaved)</div>}
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                                {r.score != null ? (
                                  <>
                                    <span style={{ fontSize: 22, fontWeight: 'bold', color: rc }}>{s.toFixed(2)}</span>
                                    <span style={{
                                      padding: '4px 10px', borderRadius: 6, fontSize: 11, fontWeight: 'bold',
                                      background: `${rc}18`, color: rc,
                                    }}>{rRec}</span>
                                  </>
                                ) : (
                                  <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>No data</span>
                                )}
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  )}
                </div>
              )}

              {/* ── TAB: HISTORICAL ───────────────────────────────────────── */}
              {activeTab === 'historical' && (
                <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: 0 }}>
                    Test this strategy on historical snapshots using the Historical Snapshot Vault.
                  </p>

                  {/* Snapshot date picker */}
                  {snapshots.length === 0 ? (
                    <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No historical snapshots available. Run the pipeline to generate snapshots.</p>
                  ) : (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                      {snapshots.map(snap => (
                        <button
                          key={snap.snapshot_id}
                          onClick={() => {
                            setSelectedSnapshot(snap.snapshot_id);
                            loadHistoricalResult(snap.snapshot_id);
                          }}
                          style={{
                            padding: '8px 14px',
                            borderRadius: 8,
                            border: selectedSnapshot === snap.snapshot_id
                              ? '1px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)',
                            background: selectedSnapshot === snap.snapshot_id
                              ? 'rgba(59,130,246,0.12)' : 'rgba(255,255,255,0.02)',
                            color: selectedSnapshot === snap.snapshot_id ? '#3b82f6' : '#94a3b8',
                            cursor: 'pointer',
                            fontSize: 12,
                            fontWeight: selectedSnapshot === snap.snapshot_id ? 'bold' : 'normal',
                            transition: 'all 0.2s',
                          }}
                        >
                          {snap.market_date || snap.snapshot_date}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Historical result */}
                  {histLoading && (
                    <div style={{ textAlign: 'center', padding: 30 }}><LoadingSpinner /></div>
                  )}

                  {histResult && !histLoading && (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
                      <div style={{ padding: 20, borderRadius: 10, background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)', textAlign: 'center' }}>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Historical Score</div>
                        <div style={{ fontSize: 32, fontWeight: 'bold', color: ratingColor(histResult.recommendation) }}>
                          {histResult.strategy_score?.toFixed(2)}
                        </div>
                      </div>
                      <div style={{ padding: 20, borderRadius: 10, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', textAlign: 'center' }}>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>Historical Rating</div>
                        <div style={{ fontSize: 18, fontWeight: 'bold', color: ratingColor(histResult.recommendation) }}>{histResult.recommendation}</div>
                      </div>
                      <div style={{ padding: 20, borderRadius: 10, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', textAlign: 'center' }}>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>vs Current</div>
                        {(() => {
                          const d = (histResult.strategy_score ?? 0) - score;
                          return (
                            <div style={{ fontSize: 24, fontWeight: 'bold', color: contribColor(d) }}>
                              {d > 0 ? '+' : ''}{d.toFixed(2)}
                            </div>
                          );
                        })()}
                      </div>
                    </div>
                  )}

                  {/* Historical feature table */}
                  {histResult?.feature_breakdown?.length > 0 && !histLoading && (
                    <div>
                      <h4 style={{ margin: '0 0 12px', fontSize: 14, color: '#60a5fa' }}>Historical Feature Contributions</h4>
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                          <thead>
                            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                              {['Feature', 'Raw Value', 'Weight', 'Contribution'].map(h => (
                                <th key={h} style={{ padding: '8px 12px', textAlign: h === 'Feature' ? 'left' : 'center', color: 'var(--text-muted)' }}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {histResult.feature_breakdown.map((f, i) => (
                              <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                                <td style={{ padding: '8px 12px', color: '#e2e8f0' }}>{f.name}</td>
                                <td style={{ padding: '8px 12px', textAlign: 'center', color: '#94a3b8' }}>{f.raw_value != null ? Number(f.raw_value).toFixed(2) : '—'}</td>
                                <td style={{ padding: '8px 12px', textAlign: 'center', color: '#94a3b8' }}>{f.weight != null ? `${(f.weight * 100).toFixed(1)}%` : '—'}</td>
                                <td style={{ padding: '8px 12px', textAlign: 'center', fontWeight: 'bold', color: contribColor(f.contribution) }}>
                                  {f.contribution > 0 ? '+' : ''}{f.contribution?.toFixed(2)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}

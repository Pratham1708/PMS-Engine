import React, { useState } from 'react';
import { runStressTest } from '../../api/labApi';
import MetricsGrid from './shared/MetricsGrid';

export default function StressTestLab() {
  const [symbol, setSymbol] = useState('^NSEI');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runStressTest({ symbol });
      setData(res.data);
    } catch (err) {
      console.error(err);
      setError('Failed to run stress test audit.');
    } finally {
      setLoading(false);
    }
  };

  const getRatingColor = (rating) => {
    if (rating === 'A') return '#10b981';
    if (rating === 'B') return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>⛈️ Historical Crisis Stress Tester</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Simulate strategy performance and drawdown risk during catastrophic historical periods (2008 Financial Crisis, 2020 COVID Crash, and Budget Days).
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '300px 1fr',
        gap: '24px',
        alignItems: 'start'
      }}>
        {/* Settings */}
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px' }}>
            Parameters
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Ticker Symbol</label>
              <input
                type="text"
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              />
            </div>
            <button
              onClick={handleRun}
              className="btn-primary"
              style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
              disabled={loading}
            >
              {loading ? 'Simulating...' : '⛈️ Run Stress Test'}
            </button>
          </div>
        </div>

        {/* Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {error && (
            <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px' }}>
              ⚠️ {error}
            </div>
          )}

          {loading ? (
            <div style={{ textAlign: 'center', padding: '60px 0' }}>
              <div className="spinner" style={{ margin: '0 auto 16px auto', border: '4px solid rgba(255,255,255,0.1)', borderTop: '4px solid var(--accent-primary)', borderRadius: '50%', width: '40px', height: '40px', animation: 'spin 1s linear infinite' }}></div>
              <p style={{ color: 'var(--text-secondary)' }}>Re-indexing price feed and computing drawdowns during crisis windows...</p>
            </div>
          ) : data ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              
              {/* Summary Cards */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
                gap: '16px'
              }}>
                <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                  <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>Overall Resilience Score</div>
                  <div style={{ fontSize: '32px', fontWeight: '800', marginTop: '4px', fontFamily: 'monospace' }}>
                    {data.overall_resilience_score} / 100
                  </div>
                </div>
                <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                  <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>Resilience Rating</div>
                  <div style={{ fontSize: '32px', fontWeight: '800', marginTop: '4px', color: getRatingColor(data.rating) }}>
                    {data.rating}-Grade
                  </div>
                </div>
              </div>

              {/* Crisis Performance Table */}
              <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Crisis Performance Log</h3>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table" style={{ width: '100%' }}>
                    <thead>
                      <tr>
                        <th>Crisis Period</th>
                        <th>Date Range</th>
                        <th>Description</th>
                        <th style={{ textAlign: 'center' }}>Return (%)</th>
                        <th style={{ textAlign: 'center' }}>Max Drawdown</th>
                        <th style={{ textAlign: 'center' }}>Score</th>
                        <th style={{ textAlign: 'center' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.crisis_performance?.map((p) => (
                        <tr key={p.name}>
                          <td><strong>{p.name}</strong></td>
                          <td style={{ fontSize: '12px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{p.period}</td>
                          <td style={{ fontSize: '12.5px', color: 'var(--text-muted)', maxWidth: '280px', wordBreak: 'break-word' }}>{p.description}</td>
                          <td style={{ textAlign: 'center', fontWeight: '700', color: p.return_pct >= 0 ? '#10b981' : '#ef4444' }}>
                            {p.return_pct}%
                          </td>
                          <td style={{ textAlign: 'center', color: '#ef4444', fontWeight: '600' }}>{p.max_drawdown}%</td>
                          <td style={{ textAlign: 'center', fontFamily: 'monospace' }}>{p.resilience_score}</td>
                          <td style={{ textAlign: 'center' }}>
                            <span style={{
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: '600',
                              background: p.status === 'Resilient' ? 'rgba(16,185,129,0.1)' : p.status === 'Stable' ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)',
                              color: p.status === 'Resilient' ? '#10b981' : p.status === 'Stable' ? '#f59e0b' : '#ef4444'
                            }}>
                              {p.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="card" style={{ padding: '40px', textAlign: 'center', border: '1px dashed var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
              <p style={{ color: 'var(--text-secondary)' }}>Click "Run Stress Test" to audit resilience across key crisis periods.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

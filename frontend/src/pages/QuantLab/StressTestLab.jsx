import React, { useState } from 'react';
import { runStressTest } from '../../api/labApi';
import MetricsGrid from './shared/MetricsGrid';

import LabWorkflowGuide from '../../components/common/LabWorkflowGuide';

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
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>⛈️ Historical Crisis Stress Tester</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Simulate strategy performance and drawdown risk during catastrophic historical crisis events.
        </p>
      </div>

      <LabWorkflowGuide
        title="Crisis Stress Tester"
        description="Evaluate strategy drawdown resilience during historical crises (2008 GFC, 2020 COVID Crash, 2022 Inflation/Rate Hikes)."
        icon="⛈️"
        steps={[
          { title: '1. Select Asset or Strategy', desc: 'Choose target asset symbol (e.g. ^NSEI).' },
          { title: '2. Execute Stress Test', desc: 'Click Run Crisis Stress Test to audit historical drawdown windows.' },
          { title: '3. Review Drawdown Depth', desc: 'Examine maximum peak-to-trough drawdowns during each crisis event.' },
          { title: '4. Assess Recovery Duration', desc: 'Check the number of trading days required to recover previous highs.' }
        ]}
      />

      <div className="quant-lab-split-grid">
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
                  <table className="data-table" style={{ width: '100%', tableLayout: 'fixed', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr>
                        <th style={{ width: '20%', padding: '12px 14px' }}>Crisis Period</th>
                        <th style={{ width: '17%', padding: '12px 14px' }}>Date Range</th>
                        <th style={{ width: '31%', padding: '12px 14px' }}>Description</th>
                        <th style={{ width: '10%', textAlign: 'center', padding: '12px 14px' }}>Return (%)</th>
                        <th style={{ width: '10%', textAlign: 'center', padding: '12px 14px' }}>Max Drawdown</th>
                        <th style={{ width: '6%', textAlign: 'center', padding: '12px 14px' }}>Score</th>
                        <th style={{ width: '6%', textAlign: 'center', padding: '12px 14px' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.crisis_performance?.map((p) => (
                        <tr key={p.name}>
                          <td style={{ padding: '14px', verticalAlign: 'middle', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            <strong>{p.name}</strong>
                          </td>
                          <td style={{ padding: '14px', fontSize: '12px', color: 'var(--text-secondary)', whiteSpace: 'nowrap', verticalAlign: 'middle' }}>
                            {p.period}
                          </td>
                          <td style={{ padding: '14px', fontSize: '12.5px', color: 'var(--text-muted)', whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.4', verticalAlign: 'middle' }}>
                            {p.description}
                          </td>
                          <td style={{ padding: '14px', textAlign: 'center', fontWeight: '700', color: p.return_pct >= 0 ? '#10b981' : '#ef4444', whiteSpace: 'nowrap', verticalAlign: 'middle' }}>
                            {p.return_pct > 0 ? `+${p.return_pct}%` : `${p.return_pct}%`}
                          </td>
                          <td style={{ padding: '14px', textAlign: 'center', color: '#ef4444', fontWeight: '600', whiteSpace: 'nowrap', verticalAlign: 'middle' }}>
                            {p.max_drawdown}%
                          </td>
                          <td style={{ padding: '14px', textAlign: 'center', fontFamily: 'monospace', fontWeight: '600', verticalAlign: 'middle' }}>
                            {p.resilience_score}
                          </td>
                          <td style={{ padding: '14px', textAlign: 'center', verticalAlign: 'middle', whiteSpace: 'nowrap' }}>
                            <span style={{
                              padding: '3px 10px',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: '600',
                              background: p.status === 'Resilient' ? 'rgba(16,185,129,0.12)' : p.status === 'Stable' ? 'rgba(245,158,11,0.12)' : 'rgba(239,68,68,0.12)',
                              color: p.status === 'Resilient' ? '#10b981' : p.status === 'Stable' ? '#f59e0b' : '#ef4444',
                              border: `1px solid ${p.status === 'Resilient' ? 'rgba(16,185,129,0.25)' : p.status === 'Stable' ? 'rgba(245,158,11,0.25)' : 'rgba(239,68,68,0.25)'}`
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

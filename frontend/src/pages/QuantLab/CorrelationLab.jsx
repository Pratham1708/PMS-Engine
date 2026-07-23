import React, { useState } from 'react';
import { getCorrelationLab } from '../../api/labApi';
import ChartPanel from './shared/ChartPanel';

export default function CorrelationLab() {
  const [symbol, setSymbol] = useState('RELIANCE');
  const [period, setPeriod] = useState('3Y');

  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getCorrelationLab(symbol, period);
      setData(res.data);
    } catch (err) {
      console.error(err);
      setError('Failed to calculate correlations.');
    } finally {
      setLoading(false);
    }
  };

  const getCorrelationCharts = () => {
    if (!data?.rolling_correlation || data.rolling_correlation.length === 0) return [];
    return [
      {
        key: 'rolling_corr',
        title: `60D Rolling Return Correlation with ^NSEI Benchmark`,
        type: 'line',
        data: data.rolling_correlation,
        xKey: 'date',
        yKeys: ['correlation'],
        colors: ['#3b82f6'],
      }
    ];
  };

  // Helper to render correlation matrices in tabular heatmaps
  const renderHeatmap = (headers, matrix) => {
    if (!headers || !matrix) return null;
    return (
      <div style={{ overflowX: 'auto', marginTop: '12px' }}>
        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center' }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left', background: 'rgba(255,255,255,0.02)' }}></th>
              {headers.map((h) => (
                <th key={h} style={{ fontSize: '12px', whiteSpace: 'nowrap' }}>{h.replace('Score', '')}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {headers.map((rowHeader) => (
              <tr key={rowHeader}>
                <td style={{ textAlign: 'left', fontWeight: '700', fontSize: '12px', background: 'rgba(255,255,255,0.02)', whiteSpace: 'nowrap' }}>
                  {rowHeader.replace('Score', '')}
                </td>
                {headers.map((colHeader) => {
                  const match = matrix.find(
                    (m) => (m.a === rowHeader && m.b === colHeader) || (m.a === colHeader && m.b === rowHeader)
                  );
                  const val = match ? match.val : (rowHeader === colHeader ? 1.0 : 0.0);
                  // Greenish opacity for positive correlation, reddish opacity for negative correlation
                  const opacity = Math.min(1, Math.abs(val));
                  const bg = val >= 0 
                    ? `rgba(16, 185, 129, ${opacity * 0.4})` 
                    : `rgba(239, 68, 68, ${opacity * 0.4})`;

                  return (
                    <td
                      key={colHeader}
                      style={{
                        background: bg,
                        fontFamily: 'monospace',
                        fontWeight: '700',
                        fontSize: '12px',
                        padding: '12px 6px',
                        border: '1px solid var(--border-primary)',
                        color: opacity > 0.6 ? '#fff' : 'var(--text-primary)'
                      }}
                      title={`${rowHeader} x ${colHeader}: ${val}`}
                    >
                      {val.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>🧬 Cross-Correlation & Redundancy Lab</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Research rolling asset correlation, inspect sub-score collinearity matrix, and audit redundant indicators.
        </p>
      </div>

      <div className="quant-lab-split-grid">
        {/* Settings */}
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px' }}>
            Parameters
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Stock Symbol</label>
              <input
                type="text"
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Horizon Period</label>
              <select
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
              >
                <option value="1Y">1 Year History Window</option>
                <option value="3Y">3 Years History Window</option>
                <option value="5Y">5 Years History Window</option>
              </select>
            </div>
            <button
              onClick={handleRun}
              className="btn-primary"
              style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
              disabled={loading}
            >
              {loading ? 'Analyzing...' : '🚀 Calculate Correlations'}
            </button>
          </div>
        </div>

        {/* Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {error && (
            <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px' }}>
              ⚠️ {error}
            </div>
          )}

          {loading ? (
            <div style={{ textAlign: 'center', padding: '60px 0' }}>
              <div className="spinner" style={{ margin: '0 auto 16px auto', border: '4px solid rgba(255,255,255,0.1)', borderTop: '4px solid var(--accent-primary)', borderRadius: '50%', width: '40px', height: '40px', animation: 'spin 1s linear infinite' }}></div>
              <p style={{ color: 'var(--text-secondary)' }}>Calculating cross-correlation matrix and redundant indicators...</p>
            </div>
          ) : data ? (
            <>
              {/* Redundant Indicators alerts */}
              {data.redundant_indicators?.length > 0 && (
                <div style={{
                  padding: '16px',
                  background: 'rgba(245,158,11,0.06)',
                  border: '1px solid rgba(245,158,11,0.15)',
                  borderRadius: 'var(--radius-lg)',
                  color: '#f59e0b'
                }}>
                  <strong style={{ fontSize: '15px', display: 'block', marginBottom: '8px' }}>⚠️ Redundant Signal Pairs Detected (|r| &gt; 0.60)</strong>
                  <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', lineHeight: '1.6' }}>
                    {data.redundant_indicators.map((pair) => (
                      <li key={pair}>
                        <strong>{pair}</strong> exhibit collinearity. Consider avoiding using them jointly in the scoring formula.
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Heatmaps Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                {/* Feature Score Heatmap */}
                {data.feature_correlation?.features && (
                  <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                    <h3 style={{ fontSize: '15px', fontWeight: '700' }}>Score Collinearity Matrix</h3>
                    <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '12px' }}>Correlation coefficient between sub-scores in database records.</p>
                    {renderHeatmap(data.feature_correlation.features, data.feature_correlation.matrix)}
                  </div>
                )}

                {/* Technical Indicator Heatmap */}
                {data.indicator_correlation?.indicators && (
                  <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                    <h3 style={{ fontSize: '15px', fontWeight: '700' }}>Technical Indicator Correlation</h3>
                    <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '12px' }}>Correlation of daily signal triggers (BUY/SELL rules) on {data.symbol}.</p>
                    {renderHeatmap(data.indicator_correlation.indicators, data.indicator_correlation.matrix)}
                  </div>
                )}
              </div>

              {/* Rolling Return Chart */}
              {data.rolling_correlation?.length > 0 && (
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Rolling 60-Day Benchmark Beta Correlation</h3>
                  <ChartPanel charts={getCorrelationCharts()} />
                </div>
              )}
            </>
          ) : (
            <div className="card" style={{ padding: '40px', textAlign: 'center', border: '1px dashed var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
              <p style={{ color: 'var(--text-secondary)' }}>Click "Calculate Correlations" to start cross-correlation checks.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

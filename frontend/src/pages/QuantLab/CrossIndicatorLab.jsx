import React, { useState } from 'react';
import { runCrossIndicator } from '../../api/labApi';
import ChartPanel from './shared/ChartPanel';

export default function CrossIndicatorLab() {
  const [symbol, setSymbol] = useState('RELIANCE');
  const [period, setPeriod] = useState('3Y');
  const [targetMetric, setTargetMetric] = useState('sharpe');
  
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runCrossIndicator({ symbol, period, target_metric: targetMetric });
      setData(res.data);
    } catch (err) {
      console.error(err);
      setError('Failed to calculate cross-indicator rankings.');
    } finally {
      setLoading(false);
    }
  };

  const getEquityChart = () => {
    if (!data?.top_equity_curve) return [];
    return [{
      key: 'equity_curve',
      title: `Top-Ranked Combo Equity Growth`,
      type: 'area',
      data: data.top_equity_curve,
      xKey: 'date',
      yKeys: ['portfolio'],
      colors: ['#10b981'],
    }];
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>📊 Cross-Indicator Combination Research</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Evaluate joint-indicator strategy logic (Logical Intersections) across single, dual, and triple signal rules.
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
                <option value="1Y">1 Year History</option>
                <option value="3Y">3 Years History</option>
                <option value="5Y">5 Years History</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Optimizing Metric</label>
              <select
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={targetMetric}
                onChange={(e) => setTargetMetric(e.target.value)}
              >
                <option value="sharpe">Sharpe Ratio</option>
                <option value="cagr">CAGR (%)</option>
                <option value="win_rate">Win Rate (%)</option>
              </select>
            </div>
            <button
              onClick={handleRun}
              className="btn-primary"
              style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
              disabled={loading}
            >
              {loading ? 'Evaluating...' : '🚀 Compare Combinations'}
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
              <p style={{ color: 'var(--text-secondary)' }}>Backtesting indicator intersections...</p>
            </div>
          ) : data ? (
            <>
              {/* Rankings Table */}
              <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Combinations Performance Ranks</h3>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table" style={{ width: '100%' }}>
                    <thead>
                      <tr>
                        <th style={{ textAlign: 'center' }}>Rank</th>
                        <th>Combination Formula</th>
                        <th style={{ textAlign: 'center' }}>Complexity</th>
                        <th style={{ textAlign: 'center' }}>CAGR</th>
                        <th style={{ textAlign: 'center' }}>Sharpe Ratio</th>
                        <th style={{ textAlign: 'center' }}>Max Drawdown</th>
                        <th style={{ textAlign: 'center' }}>Win Rate</th>
                        <th style={{ textAlign: 'center' }}>Trades</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.rankings?.map((r) => (
                        <tr key={r.rank} style={{ background: r.rank === 1 ? 'rgba(16,185,129,0.05)' : 'none' }}>
                          <td style={{ textAlign: 'center' }}><strong>#{r.rank}</strong></td>
                          <td><strong>{r.combination}</strong></td>
                          <td style={{ textAlign: 'center' }}>{r.complexity}</td>
                          <td style={{ textAlign: 'center', color: r.cagr >= 0 ? '#10b981' : '#ef4444' }}>{r.cagr}%</td>
                          <td style={{ textAlign: 'center', fontWeight: '700' }}>{r.sharpe}</td>
                          <td style={{ textAlign: 'center', color: '#ef4444' }}>{r.max_drawdown}%</td>
                          <td style={{ textAlign: 'center' }}>{r.win_rate}%</td>
                          <td style={{ textAlign: 'center' }}>{r.trades_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Top Equity Curve */}
              {data.top_equity_curve?.length > 0 && (
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Equity Growth Chart of Best Combo</h3>
                  <ChartPanel charts={getEquityChart()} />
                </div>
              )}
            </>
          ) : (
            <div className="card" style={{ padding: '40px', textAlign: 'center', border: '1px dashed var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
              <p style={{ color: 'var(--text-secondary)' }}>Click "Compare Combinations" to start research.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

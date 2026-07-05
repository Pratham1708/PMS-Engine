import React, { useState } from 'react';
import { runEnsemble } from '../../api/labApi';
import MetricsGrid from './shared/MetricsGrid';

export default function EnsembleLab() {
  const [period, setPeriod] = useState('3Y');
  const [capital, setCapital] = useState(100000);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runEnsemble({ period, initial_capital: capital });
      setData(res.data);
    } catch (err) {
      console.error(err);
      setError('Failed to run ensemble strategies evaluation.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>🤖 Ensemble Strategy Research Laboratory</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Compare performance when combining sub-scores via Weighted Voting, Majority Voting, Probabilities, and Rank Aggregation.
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
            Ensemble settings
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Backtest Horizon Period</label>
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
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Initial Capital (INR)</label>
              <input
                type="number"
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={capital}
                onChange={(e) => setCapital(parseFloat(e.target.value) || 100000)}
              />
            </div>
            <button
              onClick={handleRun}
              className="btn-primary"
              style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
              disabled={loading}
            >
              {loading ? 'Evaluating...' : '🚀 Compare Ensembles'}
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
              <p style={{ color: 'var(--text-secondary)' }}>Evaluating voting/averaging strategies...</p>
            </div>
          ) : data ? (
            <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Ensemble Strategy Performance Comparison</h3>
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table" style={{ width: '100%' }}>
                  <thead>
                    <tr>
                      <th>Aggregation Method</th>
                      <th style={{ textAlign: 'center' }}>CAGR</th>
                      <th style={{ textAlign: 'center' }}>Sharpe Ratio</th>
                      <th style={{ textAlign: 'center' }}>Max Drawdown</th>
                      <th style={{ textAlign: 'center' }}>Win Rate</th>
                      <th style={{ textAlign: 'center' }}>Total Trades</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.map((r, idx) => (
                      <tr key={idx}>
                        <td><strong>{r.method}</strong></td>
                        <td style={{ textAlign: 'center', color: r.cagr >= 0 ? '#10b981' : '#ef4444', fontWeight: '700' }}>
                          {r.cagr}%
                        </td>
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
          ) : (
            <div className="card" style={{ padding: '40px', textAlign: 'center', border: '1px dashed var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
              <p style={{ color: 'var(--text-secondary)' }}>Click "Compare Ensembles" to start comparison.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

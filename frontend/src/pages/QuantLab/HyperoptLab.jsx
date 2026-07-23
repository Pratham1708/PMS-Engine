import React, { useState } from 'react';
import { runHyperopt } from '../../api/labApi';

import LabWorkflowGuide from '../../components/common/LabWorkflowGuide';

export default function HyperoptLab() {
  const [target, setTarget] = useState('ml_model');
  const [symbol, setSymbol] = useState('^NSEI');
  const [period, setPeriod] = useState('3Y');
  const [metric, setMetric] = useState('sharpe_ratio');
  
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const handleOptimize = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runHyperopt({ target, symbol, period, target_metric: metric });
      setData(res.data);
    } catch (err) {
      console.error(err);
      setError('Failed to optimize hyperparameters.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>⚡ Hyperparameter Optimization Laboratory</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Optimize ML model classification thresholds, risk targets, or Kelly fraction sizing configurations.
        </p>
      </div>

      <LabWorkflowGuide
        title="Hyperparameter Lab"
        description="Grid search optimization across ML threshold boundaries, stop-loss percentages, and trade entry/exit rules."
        icon="🎛️"
        steps={[
          { title: '1. Select Optimization Target', desc: 'Choose target domain (ml_model, risk_thresholds, or position_sizing).' },
          { title: '2. Select Metric', desc: 'Choose target optimization metric (e.g. sharpe_ratio).' },
          { title: '3. Launch Grid Search', desc: 'Click Run Parameter Optimization to search boundary settings.' },
          { title: '4. Review Optimal Grid', desc: 'Inspect top parameter settings and metric lift over default rules.' }
        ]}
      />

      <div className="quant-lab-split-grid responsive-split-grid" style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '24px', alignItems: 'start' }}>
        {/* Settings */}
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px' }}>
            Optimization settings
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Optimization Target</label>
              <select
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={target}
                onChange={(e) => setTarget(e.target.value)}
              >
                <option value="ml_model">ML Model Bounds</option>
                <option value="risk_thresholds">Risk TP/SL Limits</option>
                <option value="position_sizing">Position Kelly/ATR Sizing</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Benchmark Ticker</label>
              <input
                type="text"
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
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
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Objective Metric</label>
              <select
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={metric}
                onChange={(e) => setMetric(e.target.value)}
              >
                <option value="sharpe_ratio">Sharpe Ratio</option>
                <option value="cagr_pct">CAGR (%)</option>
                <option value="win_rate_pct">Win Rate (%)</option>
              </select>
            </div>
            <button
              onClick={handleOptimize}
              className="btn-primary"
              style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
              disabled={loading}
            >
              {loading ? 'Optimizing...' : '🚀 Start Optimization'}
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
              <p style={{ color: 'var(--text-secondary)' }}>Searching grid combinations in background...</p>
            </div>
          ) : data ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {/* Best configuration */}
              <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '16px', color: 'var(--accent-primary)' }}>🏆 Optimal Parameters Found</h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px' }}>
                  {Object.entries(data.best_params || {}).map(([pName, pVal]) => (
                    <div key={pName} style={{ padding: '14px 20px', border: '1px solid var(--border-primary)', borderRadius: '8px', background: 'rgba(255,255,255,0.01)', minWidth: '150px' }}>
                      <div style={{ fontSize: '10px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>{pName.replace('_', ' ')}</div>
                      <div style={{ fontSize: '20px', fontWeight: '800', marginTop: '4px', color: '#3b82f6' }}>{pVal}</div>
                    </div>
                  ))}
                  <div style={{ padding: '14px 20px', border: '1px solid var(--border-primary)', borderRadius: '8px', background: 'rgba(16,185,129,0.05)', minWidth: '150px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Target {metric.replace('_', ' ').toUpperCase()}</div>
                    <div style={{ fontSize: '20px', fontWeight: '800', marginTop: '4px', color: '#10b981' }}>{data.best_score}</div>
                  </div>
                </div>
              </div>

              {/* Grid iterations */}
              <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Grid Search Matrix Outcomes</h3>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table" style={{ width: '100%' }}>
                    <thead>
                      <tr>
                        {data.results?.[0] && Object.keys(data.results[0]).map((key) => (
                          <th key={key} style={{ textAlign: 'center' }}>{key.replace('_', ' ').toUpperCase()}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {data.results?.map((row, idx) => (
                        <tr key={idx}>
                          {Object.values(row).map((val, cidx) => (
                            <td key={cidx} style={{ textAlign: 'center' }}>
                              {typeof val === 'number' ? val.toFixed(3) : val}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="card" style={{ padding: '40px', textAlign: 'center', border: '1px dashed var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
              <p style={{ color: 'var(--text-secondary)' }}>Click "Start Optimization" to run parameter searches.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

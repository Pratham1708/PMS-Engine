import React, { useState } from 'react';
import { runPositionSizing } from '../../api/labApi';
import ChartPanel from './shared/ChartPanel';

import LabWorkflowGuide from '../../components/common/LabWorkflowGuide';

export default function PositionSizingLab() {
  const [symbol, setSymbol] = useState('RELIANCE');
  const [period, setPeriod] = useState('3Y');
  const [riskPct, setRiskPct] = useState(2.0);

  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runPositionSizing({
        symbol,
        period,
        risk_pct: parseFloat(riskPct)
      });
      setData(res.data);
    } catch (err) {
      console.error(err);
      setError('Failed to run position sizing simulation.');
    } finally {
      setLoading(false);
    }
  };

  const getSizingCharts = () => {
    if (!data?.curves || data.curves.length === 0) return [];
    return [
      {
        key: 'sizing_curves',
        title: 'Capital Sizing Growth Comparison (INR)',
        type: 'line',
        data: data.curves,
        xKey: 'date',
        yKeys: ['Fixed Capital', 'Fixed Fractional', 'Kelly Fraction', 'Volatility Sizing'],
        colors: ['#6366f1', '#10b981', '#f59e0b', '#ef4444'],
      }
    ];
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>📐 Capital Allocation & Sizing Laboratory</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Evaluate compounding and drawdown profiles under Fixed, Kelly, Half-Kelly, and Volatility Parity sizing.
        </p>
      </div>

      <LabWorkflowGuide
        title="Position Sizing Lab"
        description="Simulate strategy equity growth under Fixed Fractional, Kelly Criterion, Half-Kelly, and Volatility Parity sizing rules."
        icon="📐"
        steps={[
          { title: '1. Configure Parameters', desc: 'Enter stock symbol (RELIANCE.NS) and risk per trade % (2.0%).' },
          { title: '2. Run Compounding Simulation', desc: 'Click Run Position Sizing Simulation to calculate capital curves.' },
          { title: '3. Compare Sizing Rules', desc: 'Evaluate final compounding performance across Kelly vs Fixed Risk rules.' },
          { title: '4. Assess Drawdowns', desc: 'Analyze trade drawdown volatility under aggressive vs conservative sizing.' }
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
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Asset Symbol</label>
              <input
                type="text"
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Backtest Period</label>
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
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Fixed Fractional Risk (%)</label>
              <input
                type="number"
                step="0.1"
                min="0.1"
                max="10"
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={riskPct}
                onChange={(e) => setRiskPct(e.target.value)}
              />
            </div>
            <button
              onClick={handleRun}
              className="btn-primary"
              style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
              disabled={loading}
            >
              {loading ? 'Simulating...' : '📐 Compare Sizing Models'}
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
              <p style={{ color: 'var(--text-secondary)' }}>Compounding allocations over trade logs...</p>
            </div>
          ) : data ? (
            <>
              {/* Summary Table */}
              <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Model compounding comparison</h3>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table" style={{ width: '100%' }}>
                    <thead>
                      <tr>
                        <th>Sizing Model</th>
                        <th style={{ textAlign: 'center' }}>CAGR (%)</th>
                        <th style={{ textAlign: 'center' }}>Max Drawdown (%)</th>
                        <th style={{ textAlign: 'center' }}>Ending Portfolio Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.summary?.map((s) => (
                        <tr key={s.model}>
                          <td><strong>{s.model}</strong></td>
                          <td style={{ textAlign: 'center', fontWeight: '700', color: s.cagr >= 0 ? '#10b981' : '#ef4444' }}>
                            {s.cagr}%
                          </td>
                          <td style={{ textAlign: 'center', color: '#ef4444' }}>{s.max_dd}%</td>
                          <td style={{ textAlign: 'center', fontFamily: 'monospace', fontWeight: '600' }}>
                            ₹{s.final_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Chart */}
              {data.curves?.length > 0 && (
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Equity Growth Paths Comparison</h3>
                  <ChartPanel charts={getSizingCharts()} />
                </div>
              )}
            </>
          ) : (
            <div className="card" style={{ padding: '40px', textAlign: 'center', border: '1px dashed var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
              <p style={{ color: 'var(--text-secondary)' }}>Click "Compare Sizing Models" to run compounding checks.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

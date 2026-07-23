import React, { useState } from 'react';
import { runPortfolioConstruction } from '../../api/labApi';
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

import LabWorkflowGuide from '../../components/common/LabWorkflowGuide';

export default function PortfolioConstructionLab() {
  const [symbolsText, setSymbolsText] = useState('RELIANCE, TCS, HDFCBANK, INFY');
  const [period, setPeriod] = useState('3Y');

  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const symbols = symbolsText
        .split(',')
        .map((s) => s.trim().toUpperCase())
        .filter((s) => s.length > 0);
      
      if (symbols.length < 2) {
        throw new Error('Please enter at least 2 tickers for optimization.');
      }

      const res = await runPortfolioConstruction({
        symbols,
        period
      });
      setData(res.data);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to run portfolio optimization.');
    } finally {
      setLoading(false);
    }
  };

  const renderWeights = (weights) => {
    if (!weights) return null;
    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '6px' }}>
        {Object.entries(weights).map(([sym, wt]) => (
          <div
            key={sym}
            style={{
              padding: '4px 10px',
              background: 'rgba(99,102,241,0.1)',
              border: '1px solid rgba(99,102,241,0.2)',
              borderRadius: '20px',
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <span style={{ fontWeight: '700', color: '#c7d2fe' }}>{sym}</span>
            <span style={{ fontWeight: '800', color: '#818cf8', fontFamily: 'monospace' }}>{wt}%</span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>📐 Mean-Variance Portfolio Optimizer</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Map the Efficient Frontier and calculate optimized weight models (Maximum Sharpe Ratio, Minimum Variance, Risk Parity, and Equal Weight).
        </p>
      </div>

      <LabWorkflowGuide
        title="Portfolio Optimizer"
        description="Calculate Markowitz Efficient Frontier scatter plots and Tangency Portfolio optimal asset weights."
        icon="💼"
        steps={[
          { title: '1. Input Stock Symbols', desc: 'Enter comma-separated stock tickers (e.g. RELIANCE, TCS, HDFCBANK, INFY).' },
          { title: '2. Run Optimization', desc: 'Click Run Portfolio Optimization to calculate Efficient Frontier scatter plot.' },
          { title: '3. Inspect Scatter Plot', desc: 'View risk-return trade-offs across simulated portfolio weight allocations.' },
          { title: '4. Extract Optimal Weights', desc: 'Obtain exact percentage weight allocations for Maximum Sharpe & Minimum Volatility portfolios.' }
        ]}
      />

      <div className="quant-lab-split-grid responsive-split-grid" style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px', alignItems: 'start' }}>
        {/* Settings */}
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px' }}>
            Optimizer Settings
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Stock Symbols (comma separated)
              </label>
              <textarea
                className="input"
                style={{ width: '100%', minHeight: '80px', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff', resize: 'vertical' }}
                value={symbolsText}
                onChange={(e) => setSymbolsText(e.target.value)}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Estimation History Window</label>
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
            <button
              onClick={handleRun}
              className="btn-primary"
              style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
              disabled={loading}
            >
              {loading ? 'Optimizing...' : '📐 Calculate Frontier & Weights'}
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
              <p style={{ color: 'var(--text-secondary)' }}>Computing covariance matrix and running random portfolio simulations...</p>
            </div>
          ) : data ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              
              {/* Optimization Models Table */}
              <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Allocation Model Portfolios</h3>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table" style={{ width: '100%' }}>
                    <thead>
                      <tr>
                        <th>Optimization Objective</th>
                        <th style={{ textAlign: 'center' }}>Expected Return (Ann. %)</th>
                        <th style={{ textAlign: 'center' }}>Expected Volatility (Ann. %)</th>
                        <th style={{ textAlign: 'center' }}>Sharpe Ratio</th>
                        <th>Target Weight Allocations</th>
                      </tr>
                    </thead>
                    <tbody>
                      {['max_sharpe', 'min_variance', 'risk_parity', 'equal_weight'].map((key) => {
                        const m = data[key];
                        if (!m) return null;
                        const titleMap = {
                          max_sharpe: 'Maximum Sharpe Ratio',
                          min_variance: 'Minimum Volatility (Variance)',
                          risk_parity: 'Risk Parity (Inverse Volatility)',
                          equal_weight: 'Equal Weight allocation'
                        };
                        return (
                          <tr key={key} style={{ borderBottom: '1px solid var(--border-primary)' }}>
                            <td><strong>{titleMap[key]}</strong></td>
                            <td style={{ textAlign: 'center', fontWeight: '700', color: '#10b981' }}>{m.return}%</td>
                            <td style={{ textAlign: 'center', color: '#f59e0b' }}>{m.volatility}%</td>
                            <td style={{ textAlign: 'center', fontWeight: '800' }}>{m.sharpe}</td>
                            <td style={{ padding: '12px 6px' }}>{renderWeights(m.weights)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Efficient Frontier Scatter */}
              {data.efficient_frontier?.length > 0 && (
                <div className="card" style={{ padding: '24px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>
                    Simulated Portfolios & Efficient Frontier Curve
                  </h3>
                  <div style={{ height: '350px', width: '100%' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: -20 }}>
                        <CartesianGrid stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />
                        <XAxis
                          type="number"
                          dataKey="volatility"
                          name="Volatility"
                          stroke="var(--text-muted)"
                          fontSize={11}
                          unit="%"
                          label={{ value: 'Annual Volatility (%)', position: 'bottom', offset: 0, fill: 'var(--text-secondary)', fontSize: 11 }}
                        />
                        <YAxis
                          type="number"
                          dataKey="return"
                          name="Return"
                          stroke="var(--text-muted)"
                          fontSize={11}
                          unit="%"
                          label={{ value: 'Annual Expected Return (%)', angle: -90, position: 'left', offset: 10, fill: 'var(--text-secondary)', fontSize: 11 }}
                        />
                        <Tooltip
                          cursor={{ strokeDasharray: '3 3' }}
                          contentStyle={{ background: '#111827', borderColor: 'var(--border-primary)', borderRadius: '6px' }}
                          formatter={(value, name) => [value + '%', name]}
                        />
                        <Scatter name="Portfolios" data={data.efficient_frontier} fill="#6366f1" opacity={0.6} />
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="card" style={{ padding: '40px', textAlign: 'center', border: '1px dashed var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
              <p style={{ color: 'var(--text-secondary)' }}>Click "Calculate Frontier & Weights" to start portfolio optimization checks.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

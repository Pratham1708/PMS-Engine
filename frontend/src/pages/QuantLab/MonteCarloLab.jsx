import React, { useState } from 'react';
import { runMonteCarlo } from '../../api/labApi';
import ChartPanel from './shared/ChartPanel';
import MetricsGrid from './shared/MetricsGrid';
import LabWorkflowGuide from '../../components/common/LabWorkflowGuide';

export default function MonteCarloLab() {
  const [symbol, setSymbol] = useState('^NSEI');
  const [period, setPeriod] = useState('3Y');
  const [sims, setSims] = useState(250);
  const [days, setDays] = useState(252);
  
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runMonteCarlo({
        symbol,
        period,
        n_simulations: sims,
        horizon_days: days
      });
      setData(res.data);
    } catch (err) {
      console.error(err);
      setError('Failed to execute Monte Carlo simulations.');
    } finally {
      setLoading(false);
    }
  };

  const getMonteCarloCharts = () => {
    if (!data?.simulated_paths || data.simulated_paths.length === 0) return [];
    
    // Transform paths: [{step: 0, path_0: val, path_1: val, ...}]
    const steps = data.simulated_paths[0].length;
    const chartData = [];
    for (let step = 0; step < steps; step++) {
      const row = { step };
      data.simulated_paths.forEach((path, idx) => {
        row[`path_${idx}`] = Math.round(path[step]);
      });
      chartData.push(row);
    }

    const yKeys = data.simulated_paths.slice(0, 10).map((_, idx) => `path_${idx}`);
    const colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#3b82f6', '#ec4899', '#14b8a6', '#f43f5e', '#a855f7'];

    return [
      {
        key: 'mc_paths',
        title: 'Bootstrap Resampled Equity Paths (INR)',
        type: 'line',
        data: chartData,
        xKey: 'step',
        yKeys: yKeys,
        colors: colors,
      },
      {
        key: 'cagr_dist',
        title: 'Probability Distribution of Expected CAGR (%)',
        type: 'bar',
        data: data.cagr_distribution || [],
        xKey: 'label',
        yKeys: ['count'],
        colors: ['#10b981'],
      },
      {
        key: 'mdd_dist',
        title: 'Probability Distribution of Worst Drawdowns (%)',
        type: 'bar',
        data: data.mdd_distribution || [],
        xKey: 'label',
        yKeys: ['count'],
        colors: ['#ef4444'],
      }
    ];
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>🎲 Monte Carlo Simulation Sandbox</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Run randomized bootstrap resamplings on historical returns to calculate confidence bounds and expected drawdowns.
        </p>
      </div>

      <LabWorkflowGuide
        title="Monte Carlo Sandbox"
        description="Model forward equity trajectories and tail risk bounds using bootstrap return resampling."
        icon="🎲"
        steps={[
          { title: '1. Configure Parameters', desc: 'Select symbol (^NSEI), simulation count (250), and horizon (252 days).' },
          { title: '2. Run Resampling', desc: 'Click Run Monte Carlo Simulation to launch resampled trial runs.' },
          { title: '3. Inspect Equity Trails', desc: 'View 5th percentile (bearish), 50th percentile (median), and 95th percentile paths.' },
          { title: '4. Assess Risk Metrics', desc: 'Evaluate Value at Risk (VaR 95%) and Expected Shortfall bounds.' }
        ]}
      />

      <div style={{
        display: 'grid',
        gridTemplateColumns: '300px 1fr',
        gap: '24px',
        alignItems: 'start'
      }}>
        {/* Settings */}
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px' }}>
            Simulation settings
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
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
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Historical Source Period</label>
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
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Simulation Paths Count</label>
              <input
                type="number"
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={sims}
                onChange={(e) => setSims(parseInt(e.target.value) || 250)}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Path Trading Days (Horizon)</label>
              <input
                type="number"
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={days}
                onChange={(e) => setDays(parseInt(e.target.value) || 252)}
              />
            </div>
            <button
              onClick={handleRun}
              className="btn-primary"
              style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
              disabled={loading}
            >
              {loading ? 'Simulating...' : '🎲 Run Simulations'}
            </button>
          </div>
        </div>

        {/* Outputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {error && (
            <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px' }}>
              ⚠️ {error}
            </div>
          )}

          {loading ? (
            <div style={{ textAlign: 'center', padding: '60px 0' }}>
              <div className="spinner" style={{ margin: '0 auto 16px auto', border: '4px solid rgba(255,255,255,0.1)', borderTop: '4px solid var(--accent-primary)', borderRadius: '50%', width: '40px', height: '40px', animation: 'spin 1s linear infinite' }}></div>
              <p style={{ color: 'var(--text-secondary)' }}>Bootstrap resampling returns and generating paths...</p>
            </div>
          ) : data ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              
              {/* Expected CAGR & Drawdowns metrics */}
              <MetricsGrid
                metrics={{
                  'Expected Median CAGR': `${data.expected_cagr}%`,
                  'Expected Max Drawdown': `${data.expected_max_dd}%`,
                  '95% CAGR Confidence Range': `[${data.cagr_95_ci?.[0]}%, ${data.cagr_95_ci?.[1]}%]`,
                  '99% CAGR Confidence Range': `[${data.cagr_99_ci?.[0]}%, ${data.cagr_99_ci?.[1]}%]`,
                  '95% Drawdown Value at Risk': `${data.mdd_95_ci}%`,
                  '99% Drawdown Value at Risk': `${data.mdd_99_ci}%`,
                }}
              />

              {/* Chart curves */}
              <ChartPanel charts={getMonteCarloCharts()} />
            </div>
          ) : (
            <div className="card" style={{ padding: '40px', textAlign: 'center', border: '1px dashed var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
              <p style={{ color: 'var(--text-secondary)' }}>Click "Run Simulations" to start Monte Carlo simulation checks.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

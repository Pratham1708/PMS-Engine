import React, { useState } from 'react';
import { detectRegimes, getRegimeResult } from '../../api/labApi';
import useExperiment from './shared/useExperiment';
import ExperimentProgress from './shared/ExperimentProgress';
import ChartPanel from './shared/ChartPanel';

import LabWorkflowGuide from '../../components/common/LabWorkflowGuide';

export default function RegimeLab() {
  const [symbol, setSymbol] = useState('^NSEI');
  const [period, setPeriod] = useState('3Y');
  
  // Custom experiment hook for running regime detection
  const regHook = useExperiment(detectRegimes, getRegimeResult, getRegimeResult);

  const handleDetectRegimes = () => {
    regHook.run({ symbol, period });
  };

  // Convert timeline data for ChartPanel
  const getTimelineChart = () => {
    if (!regHook.result?.regime_timeline) return [];
    
    // The timeline typically contains date, close, regime_value (e.g. 0: normal, 1: high vol, etc.)
    return [{
      key: 'regime_timeline',
      title: 'Benchmark Price & Volatility Regime Timeline',
      type: 'line',
      data: regHook.result.regime_timeline,
      xKey: 'date',
      yKeys: ['close'],
      colors: ['#3b82f6'],
    }];
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>🌊 Market Regime Detection Lab</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Identify structural market regimes (Bull, Bear, High Volatility, Flat) based on rolling volatility and return thresholds.
        </p>
      </div>

      <LabWorkflowGuide
        title="Market Regime Lab"
        description="Classify market environments into Bull, Bear, and Sideways/High-Vol regimes using rolling benchmark trend and ATR metrics."
        icon="🌊"
        steps={[
          { title: '1. Select Benchmark Index', desc: 'Choose benchmark ticker (default ^NSEI / NIFTY 50) and timeframe (3Y).' },
          { title: '2. Detect Regimes', desc: 'Click Detect Market Regimes to execute regime classification algorithms.' },
          { title: '3. Inspect Timeline', desc: 'Review the visual timeline showing regime shifts across historical years.' },
          { title: '4. Analyze Stats', desc: 'Evaluate mean daily return, daily volatility, and time spent in each regime state.' }
        ]}
      />

      <div className="quant-lab-split-grid responsive-split-grid" style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '24px', alignItems: 'start' }}>
        {/* Settings Box */}
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px' }}>
            Regime Parameters
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Benchmark Symbol (yFinance)</label>
              <input
                type="text"
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="e.g. ^NSEI, ^BSESN"
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Historical Period</label>
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
              onClick={handleDetectRegimes}
              className="btn-primary"
              style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
              disabled={regHook.status === 'running'}
            >
              🌊 Run Detection
            </button>
          </div>
        </div>

        {/* Results Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          <ExperimentProgress
            status={regHook.status}
            elapsedTime={regHook.elapsedTime}
            error={regHook.error}
            onReset={regHook.reset}
          />

          {regHook.status === 'complete' && regHook.result && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              
              {/* Regime Stats Grid/Table */}
              <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Volatility Phase Summary</h3>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table" style={{ width: '100%' }}>
                    <thead>
                      <tr>
                        <th>Regime Label</th>
                        <th style={{ textAlign: 'center' }}>Total Trading Days</th>
                        <th style={{ textAlign: 'center' }}>Time Occupancy (%)</th>
                        <th style={{ textAlign: 'center' }}>Mean Daily Return</th>
                        <th style={{ textAlign: 'center' }}>Daily Volatility (Std Dev)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {regHook.result.regime_stats?.map((stat) => (
                        <tr key={stat.regime}>
                          <td>
                            <strong>
                              {stat.regime === 'High Volatility' ? '🔴 ' : '🟢 '}
                              {stat.regime}
                            </strong>
                          </td>
                          <td style={{ textAlign: 'center' }}>{stat.days}</td>
                          <td style={{ textAlign: 'center' }}>{stat.pct_time}%</td>
                          <td style={{ textAlign: 'center', color: stat.avg_daily_return >= 0 ? '#10b981' : '#ef4444' }}>
                            {stat.avg_daily_return?.toFixed(4)}%
                          </td>
                          <td style={{ textAlign: 'center' }}>{stat.volatility_daily?.toFixed(4)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Timeline Chart */}
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Regime Price Plot</h3>
                <ChartPanel charts={getTimelineChart()} />
              </div>

            </div>
          )}

        </div>
      </div>
    </div>
  );
}

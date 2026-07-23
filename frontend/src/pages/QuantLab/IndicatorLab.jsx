import React, { useEffect, useState } from 'react';
import {
  getIndicators,
  runIndicatorBacktest,
  getExperimentStatus,
  getIndicatorResult,
  runIndicatorOptimize,
  getOptimizeResult,
} from '../../api/labApi';
import useExperiment from './shared/useExperiment';
import ExperimentProgress from './shared/ExperimentProgress';
import MetricsGrid from './shared/MetricsGrid';
import ChartPanel from './shared/ChartPanel';

import LabWorkflowGuide from '../../components/common/LabWorkflowGuide';

export default function IndicatorLab() {
  const [indicators, setIndicators] = useState([]);
  const [selectedInd, setSelectedInd] = useState('');
  const [symbol, setSymbol] = useState('RELIANCE');
  const [period, setPeriod] = useState('3Y');
  const [params, setParams] = useState({});
  const [loading, setLoading] = useState(true);

  // Optimization params
  const [optMetric, setOptMetric] = useState('sharpe_ratio');
  const [optSplits, setOptSplits] = useState(3);
  const [activeSubTab, setActiveSubTab] = useState('backtest'); // backtest, optimize

  // Experiments hooks
  const btHook = useExperiment(runIndicatorBacktest, getExperimentStatus, getIndicatorResult);
  const optHook = useExperiment(runIndicatorOptimize, getExperimentStatus, getOptimizeResult);

  useEffect(() => {
    async function loadIndicators() {
      try {
        const res = await getIndicators();
        setIndicators(res.data || []);
        if (res.data?.length > 0) {
          const first = res.data[0];
          setSelectedInd(first.name);
          initializeParams(first);
        }
      } catch (err) {
        console.error('Failed to load indicators:', err);
      } finally {
        setLoading(false);
      }
    }
    loadIndicators();
  }, []);

  const initializeParams = (indicator) => {
    const defaultParams = {};
    if (indicator?.params) {
      Object.entries(indicator.params).forEach(([name, meta]) => {
        defaultParams[name] = meta.default;
      });
    }
    setParams(defaultParams);
  };

  const handleIndicatorChange = (e) => {
    const name = e.target.value;
    setSelectedInd(name);
    const ind = indicators.find((i) => i.name === name);
    initializeParams(ind);
  };

  const handleParamChange = (name, value) => {
    setParams((prev) => ({ ...prev, [name]: parseFloat(value) || value }));
  };

  const handleRunBacktest = () => {
    btHook.run({
      symbol,
      indicator: selectedInd,
      params,
      period,
    });
  };

  const handleRunOptimization = () => {
    optHook.run({
      symbol,
      indicator: selectedInd,
      target_metric: optMetric,
      period,
      n_splits: optSplits,
    });
  };

  const currentMeta = indicators.find((i) => i.name === selectedInd);

  const getChartConfigs = () => {
    if (!btHook.result?.charts) return [];
    const charts = btHook.result.charts;
    return [
      {
        key: 'equity',
        title: 'Equity Curve',
        type: 'area',
        data: charts.equity_curve || [],
        xKey: 'date',
        yKeys: ['portfolio', 'benchmark'],
        colors: ['#6366f1', '#10b981'],
      },
      {
        key: 'drawdown',
        title: 'Drawdown (%)',
        type: 'area',
        data: charts.drawdown || [],
        xKey: 'date',
        yKeys: 'drawdown_pct',
        colors: ['#ef4444'],
      },
      {
        key: 'rolling_sharpe',
        title: 'Rolling Sharpe',
        type: 'line',
        data: charts.rolling_sharpe || [],
        xKey: 'date',
        yKeys: 'sharpe',
        colors: ['#3b82f6'],
      },
      {
        key: 'return_dist',
        title: 'Return Distribution',
        type: 'bar',
        data: charts.return_distribution || [],
        xKey: 'bucket',
        yKeys: 'count',
        colors: ['#8b5cf6'],
      }
    ];
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>📊 Technical Indicator Lab</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Backtest single technical indicators, evaluate signal CAGR & Sharpe ratio, and optimize parameters.
        </p>
      </div>

      <LabWorkflowGuide
        title="Indicator Lab"
        description="Simulate historical performance for RSI, MACD, Moving Averages, and Bollinger Bands to optimize trading signals."
        icon="📊"
        steps={[
          { title: '1. Select Stock & Horizon', desc: 'Enter stock symbol (e.g. RELIANCE.NS) and lookback timeframe (e.g. 3Y).' },
          { title: '2. Choose Indicator', desc: 'Select RSI, MACD, EMA, SMA, or Bollinger Bands from standard indicator registry.' },
          { title: '3. Tune Parameters', desc: 'Configure period windows, overbought/oversold levels, or fast/slow moving averages.' },
          { title: '4. Execute & Evaluate', desc: 'Click Run Indicator Backtest to inspect Sharpe ratio, Win rate, and Equity Curve.' }
        ]}
      />

      <div className="quant-lab-split-grid responsive-split-grid" style={{ display: 'grid', gridTemplateColumns: '350px 1fr', gap: '24px', alignItems: 'start' }}>
        {/* Panel A: Configuration Panel */}
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px' }}>
            Settings
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
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Backtest Horizon</label>
              <select
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
              >
                <option value="1M">1 Month</option>
                <option value="3M">3 Months</option>
                <option value="6M">6 Months</option>
                <option value="1Y">1 Year</option>
                <option value="3Y">3 Years</option>
                <option value="5Y">5 Years</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Technical Indicator</label>
              <select
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={selectedInd}
                onChange={handleIndicatorChange}
                disabled={loading}
              >
                {indicators.map((ind) => (
                  <option key={ind.name} value={ind.name}>{ind.label}</option>
                ))}
              </select>
            </div>

            {/* Dynamic Params */}
            {currentMeta?.params && Object.keys(currentMeta.params).length > 0 && (
              <div style={{ marginTop: '10px', borderTop: '1px solid var(--border-primary)', paddingTop: '15px' }}>
                <h3 style={{ fontSize: '13px', fontWeight: '700', marginBottom: '12px', color: 'var(--text-secondary)' }}>Parameters</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {Object.entries(currentMeta.params).map(([name, meta]) => (
                    <div key={name}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                        <span>{name.replace('_', ' ').toUpperCase()}</span>
                        <span>{params[name]}</span>
                      </div>
                      <input
                        type="range"
                        min={meta.min}
                        max={meta.max}
                        step={meta.step}
                        value={params[name] || meta.default}
                        onChange={(e) => handleParamChange(name, e.target.value)}
                        style={{ width: '100%' }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div style={{ display: 'flex', borderBottom: '1px solid var(--border-primary)', marginTop: '10px' }}>
              <button
                onClick={() => setActiveSubTab('backtest')}
                style={{
                  background: 'none', border: 'none', padding: '6px 12px', cursor: 'pointer', fontSize: '13px',
                  color: activeSubTab === 'backtest' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  borderBottom: activeSubTab === 'backtest' ? '2px solid var(--accent-primary)' : '2px solid transparent'
                }}
              >
                Backtest
              </button>
              <button
                onClick={() => setActiveSubTab('optimize')}
                style={{
                  background: 'none', border: 'none', padding: '6px 12px', cursor: 'pointer', fontSize: '13px',
                  color: activeSubTab === 'optimize' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  borderBottom: activeSubTab === 'optimize' ? '2px solid var(--accent-primary)' : '2px solid transparent'
                }}
              >
                Grid Optimize
              </button>
            </div>

            {activeSubTab === 'backtest' ? (
              <button onClick={handleRunBacktest} className="btn-primary" style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}>
                ▶ Run Backtest
              </button>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Target Metric</label>
                  <select
                    className="input"
                    style={{ width: '100%', padding: '6px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                    value={optMetric}
                    onChange={(e) => setOptMetric(e.target.value)}
                  >
                    <option value="sharpe_ratio">Sharpe Ratio</option>
                    <option value="cagr_pct">CAGR Return</option>
                    <option value="win_rate_pct">Win Rate</option>
                    <option value="calmar_ratio">Calmar Ratio</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Walk-Forward Splits</label>
                  <input
                    type="number"
                    className="input"
                    style={{ width: '100%', padding: '6px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                    value={optSplits}
                    onChange={(e) => setOptSplits(parseInt(e.target.value) || 3)}
                  />
                </div>
                <button onClick={handleRunOptimization} className="btn-primary" style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}>
                  ⚙ Run Optimization
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Panel B: Output Results / Dashboard */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Active Job Progress */}
          <ExperimentProgress
            status={activeSubTab === 'backtest' ? btHook.status : optHook.status}
            elapsedTime={activeSubTab === 'backtest' ? btHook.elapsedTime : optHook.elapsedTime}
            error={activeSubTab === 'backtest' ? btHook.error : optHook.error}
            onReset={activeSubTab === 'backtest' ? btHook.reset : optHook.reset}
          />

          {/* Backtest Results */}
          {activeSubTab === 'backtest' && btHook.status === 'complete' && btHook.result && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '8px' }}>Experiment Metrics</h3>
                <MetricsGrid metrics={btHook.result.metrics} />
              </div>

              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Interactive Charts</h3>
                <ChartPanel charts={getChartConfigs()} />
              </div>
            </div>
          )}

          {/* Optimization Results */}
          {activeSubTab === 'optimize' && optHook.status === 'complete' && optHook.result && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px', color: '#10b981' }}>✓ Optimization Complete</h3>
                <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '15px' }}>
                  The grid search evaluated <strong>{optHook.result.total_combinations}</strong> combinations using <strong>{optHook.result.params?.n_splits || 3}-fold Walk-Forward</strong>.
                </p>
                <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
                  <div style={{ padding: '12px', borderRadius: '6px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-primary)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Best Out-of-Sample {optHook.result.target_metric}</div>
                    <div style={{ fontSize: '20px', fontWeight: '700', marginTop: '4px' }}>{optHook.result.best_metric_value}</div>
                  </div>
                  <div style={{ padding: '12px', borderRadius: '6px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-primary)', minWidth: '150px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Best Parameter Set</div>
                    <div style={{ fontSize: '14px', fontWeight: '700', marginTop: '6px' }}>
                      {Object.entries(optHook.result.best_params || {}).map(([k, v]) => (
                        <div key={k}>{k}: <strong>{v}</strong></div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {optHook.result.optimization_surface?.length > 0 && (
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Optimization Parameter Surface Heatmap</h3>
                  <ChartPanel charts={[
                    {
                      key: 'heatmap',
                      title: 'Parameter Grid Surface',
                      type: 'bar',
                      data: optHook.result.optimization_surface,
                      xKey: Object.keys(optHook.result.best_params || {})[0],
                      yKeys: optHook.result.target_metric,
                      colors: ['#3b82f6'],
                    }
                  ]} />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


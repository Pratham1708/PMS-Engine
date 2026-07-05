import React, { useEffect, useState } from 'react';
import { listExperiments, runBenchmarkCompare, getBenchmarkResult } from '../../api/labApi';
import useExperiment from './shared/useExperiment';
import ExperimentProgress from './shared/ExperimentProgress';
import MetricsGrid from './shared/MetricsGrid';
import ChartPanel from './shared/ChartPanel';

const BENCHMARKS = [
  { key: 'NIFTY50', label: 'Nifty 50' },
  { key: 'SENSEX', label: 'BSE Sensex' },
  { key: 'MIDCAP150', label: 'Nifty Midcap 150' },
  { key: 'SMALLCAP250', label: 'Nifty Smallcap 250' },
  { key: 'NIFTY_IT', label: 'Nifty IT' },
  { key: 'NIFTY_BANK', label: 'Nifty Bank' },
  { key: 'GOLD_ETF', label: 'Gold BeES ETF' }
];

export default function BenchmarkComparison() {
  const [strategyExperiments, setStrategyExperiments] = useState([]);
  const [selectedExpId, setSelectedExpId] = useState('');
  const [selectedBenchmark, setSelectedBenchmark] = useState('NIFTY50');
  const [period, setPeriod] = useState('3Y');
  
  // Custom experiment hook for running benchmark comparison
  const benchHook = useExperiment(runBenchmarkCompare, getBenchmarkResult, getBenchmarkResult);

  useEffect(() => {
    async function loadPortfolioExperiments() {
      try {
        const res = await listExperiments({ module: 'portfolio_backtest' });
        const list = res.data || [];
        // Filter only completed ones
        const completed = list.filter((e) => e.status === 'complete');
        setStrategyExperiments(completed);
        if (completed.length > 0) {
          setSelectedExpId(completed[0].experiment_id);
        }
      } catch (err) {
        console.error('Failed to load portfolio experiments list:', err);
      }
    }
    loadPortfolioExperiments();
  }, [benchHook.status]);

  const handleRunComparison = () => {
    if (!selectedExpId) {
      alert('Please select a completed portfolio backtest first.');
      return;
    }
    benchHook.run({
      strategy_experiment_id: selectedExpId,
      benchmark_key: selectedBenchmark,
      period
    });
  };

  const getCharts = () => {
    if (!benchHook.result?.charts) return [];

    const list = [];
    const eqData = benchHook.result.charts.equity || [];
    if (eqData.length > 0) {
      list.push({
        key: 'equity',
        title: 'Comparative Equity Growth',
        type: 'area',
        data: eqData,
        xKey: 'date',
        yKeys: ['portfolio', 'benchmark'],
        colors: ['#3b82f6', '#9ca3af'],
      });
    }

    const ddData = benchHook.result.charts.drawdown || [];
    if (ddData.length > 0) {
      list.push({
        key: 'drawdown',
        title: 'Drawdowns Compared',
        type: 'line',
        data: ddData,
        xKey: 'date',
        yKeys: ['drawdown_portfolio', 'drawdown_benchmark'],
        colors: ['#ef4444', '#f59e0b'],
      });
    }

    return list;
  };

  // Convert string metric to formatted float
  const formatMetric = (val, isPct = false) => {
    const num = parseFloat(val);
    if (isNaN(num)) return val;
    return isPct ? `${num.toFixed(1)}%` : num.toFixed(2);
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>📈 Strategy vs Benchmark Comparison Lab</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Evaluate strategy active risk, tracking error, alpha/beta sensitivities, and capture ratios against index benchmarks.
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '320px 1fr',
        gap: '24px',
        alignItems: 'start'
      }}>
        {/* Settings Box */}
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px' }}>
            Comparison Settings
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Select Strategy Backtest</label>
              {strategyExperiments.length === 0 ? (
                <div>
                  <input
                    type="text"
                    className="input"
                    style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                    value={selectedExpId}
                    onChange={(e) => setSelectedExpId(e.target.value)}
                    placeholder="Enter Experiment ID manually"
                  />
                  <span style={{ fontSize: '10px', color: 'var(--text-secondary)', marginTop: '4px', display: 'block' }}>
                    No completed portfolio backtests found in database. Run a portfolio backtest first.
                  </span>
                </div>
              ) : (
                <select
                  className="input"
                  style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                  value={selectedExpId}
                  onChange={(e) => setSelectedExpId(e.target.value)}
                >
                  {strategyExperiments.map((e) => (
                    <option key={e.experiment_id} value={e.experiment_id}>
                      {e.name} ({e.params?.period || 'N/A'})
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Benchmark Index</label>
              <select
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={selectedBenchmark}
                onChange={(e) => setSelectedBenchmark(e.target.value)}
              >
                {BENCHMARKS.map((b) => (
                  <option key={b.key} value={b.key}>{b.label}</option>
                ))}
              </select>
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

            <button
              onClick={handleRunComparison}
              className="btn-primary"
              style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
              disabled={benchHook.status === 'running' || !selectedExpId}
            >
              📊 Compare to Index
            </button>
          </div>
        </div>

        {/* Results Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          <ExperimentProgress
            status={benchHook.status}
            elapsedTime={benchHook.elapsedTime}
            error={benchHook.error}
            onReset={benchHook.reset}
          />

          {benchHook.status === 'complete' && benchHook.result && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {/* Header Info */}
              <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '17px', fontWeight: '700' }}>
                  Backtest vs {benchHook.result.benchmark_label || benchHook.result.benchmark_key}
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '4px' }}>
                  Period: {period} · Analysis Completed: {benchHook.result.completed_at}
                </p>
              </div>

              {/* Advanced Comparison Metrics */}
              <MetricsGrid
                metrics={{
                  'Alpha (Annualized)': formatMetric(benchHook.result.alpha, true),
                  'Beta': formatMetric(benchHook.result.beta),
                  'Tracking Error': formatMetric(benchHook.result.tracking_error, true),
                  'Information Ratio': formatMetric(benchHook.result.information_ratio),
                  'Upside Capture Ratio': formatMetric(benchHook.result.upside_capture, true),
                  'Downside Capture Ratio': formatMetric(benchHook.result.downside_capture, true),
                  'Benchmark CAGR': formatMetric(benchHook.result.metrics?.benchmark_cagr, true),
                  'Benchmark Max Drawdown': formatMetric(benchHook.result.metrics?.benchmark_max_drawdown, true),
                }}
              />

              {/* Comparative Charts */}
              <ChartPanel charts={getCharts()} />
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

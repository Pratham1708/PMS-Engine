import React, { useEffect, useState } from 'react';
import { getPortfolioStrategies, runPortfolioBacktest, getPortfolioResult, comparePortfolioStrategies } from '../../api/labApi';
import useExperiment from './shared/useExperiment';
import ExperimentProgress from './shared/ExperimentProgress';
import MetricsGrid from './shared/MetricsGrid';
import ChartPanel from './shared/ChartPanel';

export default function PortfolioStrategies() {
  const [strategies, setStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState('top_n_monthly');
  const [maxStocks, setMaxStocks] = useState(10);
  const [period, setPeriod] = useState('3Y');
  const [initialCapital, setInitialCapital] = useState(100000);
  
  // Custom experiment hook for running single backtest
  const portHook = useExperiment(runPortfolioBacktest, getPortfolioResult, getPortfolioResult);

  // Comparison states
  const [completedBacktests, setCompletedBacktests] = useState([]);
  const [comparedResults, setComparedResults] = useState(null);
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    async function loadStrategies() {
      try {
        const res = await getPortfolioStrategies();
        setStrategies(res.data || []);
      } catch (err) {
        console.error('Failed to load strategies list:', err);
      }
    }
    loadStrategies();
  }, []);

  // When a backtest finishes, save its details for potential comparison
  useEffect(() => {
    if (portHook.status === 'complete' && portHook.result) {
      const alreadyExists = completedBacktests.some(
        (b) => b.experiment_id === portHook.result.experiment_id
      );
      if (!alreadyExists) {
        setCompletedBacktests((prev) => [
          ...prev,
          {
            experiment_id: portHook.result.experiment_id,
            strategy: portHook.result.params?.strategy || selectedStrategy,
            name: portHook.result.params?.strategy
              ? `Backtest: ${portHook.result.params.strategy.toUpperCase()} (${portHook.result.params.period})`
              : `Backtest Run`,
            cagr: portHook.result.metrics?.cagr || 0.0,
            sharpe: portHook.result.metrics?.sharpe || 0.0,
            max_drawdown: portHook.result.metrics?.max_drawdown || 0.0,
          }
        ]);
      }
    }
  }, [portHook.status, portHook.result]);

  const handleStartBacktest = () => {
    portHook.run({
      strategy: selectedStrategy,
      n: maxStocks,
      period,
      initial_capital: initialCapital
    });
  };

  const handleCompare = async () => {
    if (completedBacktests.length < 2) return;
    setComparing(true);
    try {
      const ids = completedBacktests.map((b) => b.experiment_id).join(',');
      const res = await comparePortfolioStrategies(ids);
      setComparedResults(res.data);
    } catch (err) {
      console.error(err);
      alert('Failed to compare portfolio strategies.');
    } finally {
      setComparing(false);
    }
  };

  // Format charts for ChartPanel
  const getCharts = () => {
    if (!portHook.result?.charts) return [];

    const list = [];
    const eqData = portHook.result.charts.equity || [];
    if (eqData.length > 0) {
      list.push({
        key: 'equity',
        title: 'Equity Growth (INR)',
        type: 'area',
        data: eqData,
        xKey: 'date',
        yKeys: ['portfolio', 'benchmark'],
        colors: ['#3b82f6', '#475569'],
      });
    }

    const ddData = portHook.result.charts.drawdown || [];
    if (ddData.length > 0) {
      list.push({
        key: 'drawdown',
        title: 'Drawdown Curve (%)',
        type: 'line',
        data: ddData,
        xKey: 'date',
        yKeys: ['drawdown'],
        colors: ['#ef4444'],
      });
    }

    const weightData = portHook.result.charts.smart_beta_weights || [];
    if (weightData.length > 0) {
      list.push({
        key: 'weights',
        title: 'Optimized Weight Allocations (%)',
        type: 'bar',
        data: weightData.map((w) => ({ symbol: w.symbol, weight: w.weight * 100 })),
        xKey: 'symbol',
        yKeys: ['weight'],
        colors: ['#8b5cf6'],
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
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>💼 Quantitative Portfolio Backtesting</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Backtest diversified portfolios and Smart Beta index rotation strategies built using composite scoring engines.
        </p>
      </div>

      <div className="quant-lab-split-grid responsive-split-grid" style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px', alignItems: 'start' }}>
        {/* Settings Box */}
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px' }}>
            Backtest Parameters
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Rebalancing Strategy</label>
              <select
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
              >
                {strategies.map((s) => (
                  <option key={s.name} value={s.name}>{s.label}</option>
                ))}
              </select>
            </div>

            {selectedStrategy !== 'sector_momentum' && (
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Max Stock Holdings (N)</label>
                <input
                  type="number"
                  className="input"
                  style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                  value={maxStocks}
                  onChange={(e) => setMaxStocks(parseInt(e.target.value) || 10)}
                  min={1}
                  max={50}
                />
              </div>
            )}

            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Backtest Period</label>
              <select
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
              >
                <option value="1Y">1 Year Historical Analysis</option>
                <option value="3Y">3 Years Historical Analysis</option>
                <option value="5Y">5 Years Historical Analysis</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Initial Capital (INR)</label>
              <input
                type="number"
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={initialCapital}
                onChange={(e) => setInitialCapital(parseFloat(e.target.value) || 100000)}
                step={10000}
              />
            </div>

            <button
              onClick={handleStartBacktest}
              className="btn-primary"
              style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
              disabled={portHook.status === 'running'}
            >
              🚀 Run Backtest
            </button>
          </div>
        </div>

        {/* Results Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          <ExperimentProgress
            status={portHook.status}
            elapsedTime={portHook.elapsedTime}
            error={portHook.error}
            onReset={portHook.reset}
          />

          {portHook.status === 'complete' && portHook.result && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {/* Strategy Header Info */}
              <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div>
                    <h3 style={{ fontSize: '18px', fontWeight: '700' }}>
                      {strategies.find((s) => s.name === selectedStrategy)?.label || selectedStrategy.toUpperCase()} Backtest Result
                    </h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '4px' }}>
                      Period: {period} · Initial Capital: ₹{initialCapital.toLocaleString()} · Completed: {portHook.result.completed_at}
                    </p>
                  </div>
                </div>
              </div>

              {/* Metrics Grid */}
              <MetricsGrid
                metrics={{
                  'CAGR': formatMetric(portHook.result.metrics?.cagr, true),
                  'Sharpe Ratio': formatMetric(portHook.result.metrics?.sharpe),
                  'Max Drawdown': formatMetric(portHook.result.metrics?.max_drawdown, true),
                  'Win Rate': formatMetric(portHook.result.metrics?.win_rate, true),
                  'Profit Factor': formatMetric(portHook.result.metrics?.profit_factor),
                  'Sortino Ratio': formatMetric(portHook.result.metrics?.sortino),
                  'Alpha (vs Bench)': formatMetric(portHook.result.metrics?.alpha, true),
                  'Beta (vs Bench)': formatMetric(portHook.result.metrics?.beta),
                }}
              />

              {/* Charts Panel */}
              <ChartPanel charts={getCharts()} />

              {/* Allocations table/list */}
              {portHook.result.symbols?.length > 0 && (
                <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Participating Asset Universe</h3>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {portHook.result.symbols.map((sym) => (
                      <span key={sym} style={{ padding: '4px 10px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-primary)', borderRadius: '4px', fontSize: '12px', fontWeight: '600' }}>
                        {sym}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Sector Allocations */}
              {portHook.result.top_sectors?.length > 0 && (
                <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Top Selected Sector Allocations</h3>
                  <div style={{ overflowX: 'auto' }}>
                    <table className="data-table" style={{ width: '100%' }}>
                      <thead>
                        <tr>
                          <th>Sector Name</th>
                          <th style={{ textAlign: 'center' }}>Composite Sector Return Rank</th>
                        </tr>
                      </thead>
                      <tbody>
                        {portHook.result.top_sectors.map((sec, idx) => (
                          <tr key={idx}>
                            <td><strong>{sec}</strong></td>
                            <td style={{ textAlign: 'center' }}>Rank #{idx + 1}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

            </div>
          )}

          {/* Side-by-Side Strategy Comparison Tool */}
          {completedBacktests.length > 0 && (
            <div className="card" style={{ padding: '24px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)', marginTop: '20px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '8px' }}>Side-by-Side Comparison</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '16px' }}>
                Compare completed backtests side-by-side using the metric matrix comparison.
              </p>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
                {completedBacktests.map((b) => (
                  <div key={b.experiment_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px', background: 'rgba(255,255,255,0.01)', border: '1px solid var(--border-primary)', borderRadius: '6px' }}>
                    <div>
                      <span style={{ fontSize: '13px', fontWeight: '600' }}>{b.name}</span>
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)', marginLeft: '12px' }}>
                        CAGR: {b.cagr?.toFixed(1)}% · MaxDD: {b.max_drawdown?.toFixed(1)}% · Sharpe: {b.sharpe?.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {completedBacktests.length >= 2 && (
                <button
                  onClick={handleCompare}
                  className="btn-secondary"
                  style={{ padding: '10px 16px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
                  disabled={comparing}
                >
                  {comparing ? 'Comparing...' : '⚖️ Compare All Backtests'}
                </button>
              )}

              {comparedResults && (
                <div style={{ overflowX: 'auto', marginTop: '20px' }}>
                  <table className="data-table" style={{ width: '100%' }}>
                    <thead>
                      <tr>
                        <th>Metric</th>
                        {comparedResults.map((c) => (
                          <th key={c.experiment_id} style={{ textAlign: 'center' }}>
                            {c.strategy.toUpperCase()} ({c.period})
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>CAGR</strong></td>
                        {comparedResults.map((c) => (
                          <td key={c.experiment_id} style={{ textAlign: 'center', fontWeight: '700', color: '#10b981' }}>
                            {formatMetric(c.metrics.cagr, true)}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td><strong>Sharpe Ratio</strong></td>
                        {comparedResults.map((c) => (
                          <td key={c.experiment_id} style={{ textAlign: 'center' }}>
                            {formatMetric(c.metrics.sharpe)}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td><strong>Max Drawdown</strong></td>
                        {comparedResults.map((c) => (
                          <td key={c.experiment_id} style={{ textAlign: 'center', color: '#ef4444' }}>
                            {formatMetric(c.metrics.max_drawdown, true)}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td><strong>Win Rate</strong></td>
                        {comparedResults.map((c) => (
                          <td key={c.experiment_id} style={{ textAlign: 'center' }}>
                            {formatMetric(c.metrics.win_rate, true)}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td><strong>Profit Factor</strong></td>
                        {comparedResults.map((c) => (
                          <td key={c.experiment_id} style={{ textAlign: 'center' }}>
                            {formatMetric(c.metrics.profit_factor)}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td><strong>Initial Capital</strong></td>
                        {comparedResults.map((c) => (
                          <td key={c.experiment_id} style={{ textAlign: 'center' }}>
                            ₹{c.initial_capital?.toLocaleString()}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

import React, { useEffect, useState } from 'react';
import { getCompositeAnalysis, optimizeWeights, getWeightOptResult, getRegimeWeights } from '../../api/labApi';
import useExperiment from './shared/useExperiment';
import ExperimentProgress from './shared/ExperimentProgress';

export default function CompositeValidationLab() {
  const [analysisData, setAnalysisData] = useState(null);
  const [regimeData, setRegimeData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [stepSize, setStepSize] = useState(0.10);
  const [targetMetric, setTargetMetric] = useState('rank_ic');
  const [activeSubTab, setActiveSubTab] = useState('current');

  // Custom hook for optimizing weights
  const optHook = useExperiment(optimizeWeights, getWeightOptResult, getWeightOptResult);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const resAnalysis = await getCompositeAnalysis();
      setAnalysisData(resAnalysis.data);

      const resRegime = await getRegimeWeights();
      setRegimeData(resRegime.data);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch composite weight metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleStartOptimization = () => {
    optHook.run({ step: stepSize, target_metric: targetMetric });
  };

  // Helper to color weights
  const getWeightColor = (weight) => {
    if (weight >= 0.4) return '#6366f1';
    if (weight >= 0.25) return '#3b82f6';
    if (weight >= 0.1) return '#10b981';
    return 'var(--text-secondary)';
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Warning Banner */}
      <div style={{
        background: 'rgba(245, 158, 11, 0.08)',
        border: '1px solid rgba(245, 158, 11, 0.2)',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '28px',
        display: 'flex',
        alignItems: 'start',
        gap: '12px'
      }}>
        <span style={{ fontSize: '20px' }}>⚠️</span>
        <div>
          <h4 style={{ color: '#f59e0b', fontWeight: '700', fontSize: '14px', margin: 0, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Research Laboratory Sandbox
          </h4>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', margin: '4px 0 0 0', lineHeight: '1.4' }}>
            All optimizations, grid searches, and weight allocations calculated inside this module are purely for simulation and scientific validation. 
            The production weights of the PMS scoring engine remain unchanged to preserve institutional continuity.
          </p>
        </div>
      </div>

      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>⚖️ Composite Score Validation & Weights Optimizer</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Audit sub-score weights, measure partial correlations, and optimize the linear ensemble model configurations.
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '250px 1fr',
        gap: '24px',
        alignItems: 'start'
      }}>
        {/* Navigation Sidebar */}
        <div className="card" style={{ padding: '16px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <button
              onClick={() => setActiveSubTab('current')}
              className={`tab-btn-vertical ${activeSubTab === 'current' ? 'active' : ''}`}
              style={{ textAlign: 'left', padding: '10px 12px', background: activeSubTab === 'current' ? 'rgba(255,255,255,0.05)' : 'none', border: 'none', borderRadius: '6px', cursor: 'pointer', color: activeSubTab === 'current' ? 'var(--accent-primary)' : 'var(--text-primary)', fontWeight: activeSubTab === 'current' ? '600' : 'normal' }}
            >
              📊 Current Weights Analysis
            </button>
            <button
              onClick={() => setActiveSubTab('optimizer')}
              className={`tab-btn-vertical ${activeSubTab === 'optimizer' ? 'active' : ''}`}
              style={{ textAlign: 'left', padding: '10px 12px', background: activeSubTab === 'optimizer' ? 'rgba(255,255,255,0.05)' : 'none', border: 'none', borderRadius: '6px', cursor: 'pointer', color: activeSubTab === 'optimizer' ? 'var(--accent-primary)' : 'var(--text-primary)', fontWeight: activeSubTab === 'optimizer' ? '600' : 'normal' }}
            >
              ⚡ Grid Search Optimizer
            </button>
            <button
              onClick={() => setActiveSubTab('regimes')}
              className={`tab-btn-vertical ${activeSubTab === 'regimes' ? 'active' : ''}`}
              style={{ textAlign: 'left', padding: '10px 12px', background: activeSubTab === 'regimes' ? 'rgba(255,255,255,0.05)' : 'none', border: 'none', borderRadius: '6px', cursor: 'pointer', color: activeSubTab === 'regimes' ? 'var(--accent-primary)' : 'var(--text-primary)', fontWeight: activeSubTab === 'regimes' ? '600' : 'normal' }}
            >
              🌊 Regime Optimal Weights
            </button>
          </div>
        </div>

        {/* Tab Content */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {error && (
            <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px' }}>
              ⚠️ {error}
            </div>
          )}

          {loading && !analysisData ? (
            <div style={{ textAlign: 'center', padding: '60px 0' }}>
              <div className="spinner" style={{ margin: '0 auto 16px auto', border: '4px solid rgba(255,255,255,0.1)', borderTop: '4px solid var(--accent-primary)', borderRadius: '50%', width: '40px', height: '40px', animation: 'spin 1s linear infinite' }}></div>
              <p style={{ color: 'var(--text-secondary)' }}>Loading composite weight profiles...</p>
            </div>
          ) : (
            <>
              {activeSubTab === 'current' && analysisData && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  {/* Summary Table */}
                  <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                    <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Current Weights and Explanatory Power</h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '20px' }}>
                      This table shows the current linear weights set in the scoring engine compared to their <strong>Semi-Partial Correlation</strong> with Nifty 50 tickers' actual forward returns.
                    </p>
                    <div style={{ overflowX: 'auto' }}>
                      <table className="data-table" style={{ width: '100%' }}>
                        <thead>
                          <tr>
                            <th>Sub-Score Feature</th>
                            <th style={{ textAlign: 'center' }}>Production Weight</th>
                            <th style={{ textAlign: 'center' }}>Semi-Partial Correlation</th>
                            <th style={{ textAlign: 'center' }}>Estimated Marginal Contribution</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(analysisData.partial_correlations || {}).map(([scoreName, val]) => (
                            <tr key={scoreName}>
                              <td><strong>{scoreName}</strong></td>
                              <td style={{ textAlign: 'center', fontWeight: '700', color: '#3b82f6' }}>
                                {(val.current_weight * 100).toFixed(0)}%
                              </td>
                              <td style={{ textAlign: 'center', color: val.semi_partial_correlation >= 0 ? '#10b981' : '#ef4444' }}>
                                {val.semi_partial_correlation.toFixed(4)}
                              </td>
                              <td style={{ textAlign: 'center' }}>
                                {val.estimated_contribution_pct.toFixed(1)}%
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {activeSubTab === 'optimizer' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  {/* Optimizer Settings */}
                  <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                    <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Grid Search Parameters</h3>
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                      gap: '20px',
                      alignItems: 'end'
                    }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Grid Step Size</label>
                        <select
                          className="input"
                          style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                          value={stepSize}
                          onChange={(e) => setStepSize(parseFloat(e.target.value))}
                        >
                          <option value={0.25}>0.25 (Coarse - 15 Combos)</option>
                          <option value={0.20}>0.20 (Medium - 35 Combos)</option>
                          <option value={0.10}>0.10 (Standard - 286 Combos)</option>
                          <option value={0.05}>0.05 (Fine - 1,771 Combos)</option>
                        </select>
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Target Optimisation Metric</label>
                        <select
                          className="input"
                          style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                          value={targetMetric}
                          onChange={(e) => setTargetMetric(e.target.value)}
                        >
                          <option value="rank_ic">Spearman Rank IC (Correlation)</option>
                        </select>
                      </div>
                      <button
                        onClick={handleStartOptimization}
                        className="btn-primary"
                        style={{ padding: '10px 16px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
                        disabled={optHook.status === 'running'}
                      >
                        🚀 Run Grid Weight Search
                      </button>
                    </div>
                  </div>

                  <ExperimentProgress
                    status={optHook.status}
                    elapsedTime={optHook.elapsedTime}
                    error={optHook.error}
                    onReset={optHook.reset}
                  />

                  {optHook.status === 'complete' && optHook.result && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                      {/* Best Weights Display */}
                      <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                        <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '16px' }}>🏆 Best Weights Allocation Found</h3>
                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                          gap: '16px'
                        }}>
                          {Object.entries(optHook.result.best_weights || {}).map(([col, val]) => (
                            <div key={col} style={{ padding: '16px', border: '1px solid var(--border-primary)', borderRadius: '8px', background: 'rgba(255,255,255,0.01)', textAlign: 'center' }}>
                              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>{col}</div>
                              <div style={{ fontSize: '24px', fontWeight: '800', marginTop: '6px', color: getWeightColor(val) }}>
                                {(val * 100).toFixed(0)}%
                              </div>
                            </div>
                          ))}
                        </div>
                        <div style={{ marginTop: '16px', padding: '12px', border: '1px solid var(--border-primary)', borderRadius: '6px', background: 'rgba(16,185,129,0.05)', fontSize: '13px' }}>
                          Best Spearman Rank IC: <strong>{optHook.result.best_metric_value?.toFixed(4)}</strong> (Evaluated {optHook.result.total_combinations} combinations)
                        </div>
                      </div>

                      {/* Top 20 table */}
                      <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                        <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Top 20 Score Weight Configurations</h3>
                        <div style={{ overflowX: 'auto' }}>
                          <table className="data-table" style={{ width: '100%' }}>
                            <thead>
                              <tr>
                                <th>#</th>
                                <th style={{ textAlign: 'center' }}>Technical Weight</th>
                                <th style={{ textAlign: 'center' }}>ML Weight</th>
                                <th style={{ textAlign: 'center' }}>GRU Weight</th>
                                <th style={{ textAlign: 'center' }}>Reliability Weight</th>
                                <th style={{ textAlign: 'center' }}>Spearman Rank IC</th>
                              </tr>
                            </thead>
                            <tbody>
                              {optHook.result.top_results?.map((r, idx) => (
                                <tr key={idx} style={{ background: idx === 0 ? 'rgba(99,102,241,0.05)' : 'none' }}>
                                  <td><strong>{idx + 1}</strong></td>
                                  <td style={{ textAlign: 'center' }}>{(r.TechnicalScore * 100).toFixed(0)}%</td>
                                  <td style={{ textAlign: 'center' }}>{(r.MLScore * 100).toFixed(0)}%</td>
                                  <td style={{ textAlign: 'center' }}>{(r.GRUScore * 100).toFixed(0)}%</td>
                                  <td style={{ textAlign: 'center' }}>{(r.ReliabilityScore * 100).toFixed(0)}%</td>
                                  <td style={{ textAlign: 'center', fontWeight: '700', color: '#10b981' }}>{r.rank_ic?.toFixed(4)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeSubTab === 'regimes' && regimeData && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  {/* Regime specific allocation analysis */}
                  <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                    <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Regime-Specific Optimal Weight Mappings</h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '20px' }}>
                      Shows optimized weighting profiles based on different market volatility partitions, demonstrating weight sensitivity during structural breaks.
                    </p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                      {Object.entries(regimeData.regime_weights || {}).map(([regimeName, rdata]) => (
                        <div key={regimeName} style={{ padding: '16px', border: '1px solid var(--border-primary)', borderRadius: '8px', background: 'rgba(255,255,255,0.01)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px', marginBottom: '12px' }}>
                            <span style={{ fontSize: '14px', fontWeight: '700', color: '#f59e0b' }}>🌊 Regime: {regimeName}</span>
                            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                              Sample Size: <strong>{rdata.n} rows</strong> · Rank IC: <strong>{rdata.ic.toFixed(4)}</strong>
                            </span>
                          </div>
                          <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                            gap: '12px'
                          }}>
                            {Object.entries(rdata.optimal_weights || {}).map(([col, wVal]) => (
                              <div key={col} style={{ textAlign: 'center', padding: '10px', background: 'rgba(255,255,255,0.02)', borderRadius: '6px' }}>
                                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{col}</div>
                                <div style={{ fontSize: '18px', fontWeight: '800', color: getWeightColor(wVal), marginTop: '4px' }}>
                                  {(wVal * 100).toFixed(0)}%
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

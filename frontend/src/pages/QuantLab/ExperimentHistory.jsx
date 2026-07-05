import React, { useEffect, useState } from 'react';
import { listExperiments, getExperimentDetail, deleteExperiment, exportExperimentUrl, getExperimentsSummary } from '../../api/labApi';

const MODULES = [
  { value: '', label: 'All Modules' },
  { value: 'indicator_backtest', label: 'Indicator Backtest' },
  { value: 'indicator_optimize', label: 'Indicator Optimization' },
  { value: 'pms_score_validation', label: 'Engine Validation' },
  { value: 'model_compare', label: 'Model Lab' },
  { value: 'composite_optimize', label: 'Composite Optimization' },
  { value: 'portfolio_backtest', label: 'Portfolio Backtest' },
  { value: 'sector_performance', label: 'Sector Analysis' },
  { value: 'regime_detection', label: 'Regime Detection' },
  { value: 'benchmark_comparison', label: 'Benchmark Comparison' }
];

const STATUSES = [
  { value: '', label: 'All Statuses' },
  { value: 'complete', label: 'Complete' },
  { value: 'running', label: 'Running' },
  { value: 'failed', label: 'Failed' },
  { value: 'pending', label: 'Pending' }
];

export default function ExperimentHistory() {
  const [experiments, setExperiments] = useState([]);
  const [summary, setSummary] = useState({ total: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filters
  const [moduleFilter, setModuleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [symbolSearch, setSymbolSearch] = useState('');

  // Selected experiment detail modal/expansion
  const [activeDetail, setActiveDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const fetchExperiments = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listExperiments({
        module: moduleFilter || undefined,
        status: statusFilter || undefined,
        symbol: symbolSearch || undefined,
        limit: 50
      });
      setExperiments(res.data || []);
      
      const sumRes = await getExperimentsSummary();
      setSummary(sumRes.data || { total: 0 });
    } catch (err) {
      console.error(err);
      setError('Failed to fetch experiment log records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExperiments();
  }, [moduleFilter, statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchExperiments();
  };

  const handleViewDetail = async (expId) => {
    if (activeDetail && activeDetail.experiment_id === expId) {
      setActiveDetail(null);
      return;
    }
    setLoadingDetail(true);
    try {
      const res = await getExperimentDetail(expId);
      setActiveDetail(res.data);
    } catch (err) {
      console.error(err);
      alert('Failed to load experiment detail variables.');
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleDelete = async (expId) => {
    if (!window.confirm('Are you sure you want to hard-delete this experiment run and all its metrics/charts? This cannot be undone.')) {
      return;
    }
    try {
      await deleteExperiment(expId);
      setExperiments((prev) => prev.filter((e) => e.experiment_id !== expId));
      if (activeDetail && activeDetail.experiment_id === expId) {
        setActiveDetail(null);
      }
    } catch (err) {
      console.error(err);
      alert('Failed to delete experiment.');
    }
  };

  const getModuleLabel = (moduleVal) => {
    const found = MODULES.find((m) => m.value === moduleVal);
    return found ? found.label : moduleVal;
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>🗂 Experiment History & Run Log</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Browse, analyze metrics, export configurations, or clean up past quantitative research experiments.
        </p>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px', marginBottom: '20px' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="card" style={{ padding: '16px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)', marginBottom: '24px' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'end' }}>
          <div style={{ flex: 1, minWidth: '180px' }}>
            <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Research Module</label>
            <select
              className="input"
              style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
              value={moduleFilter}
              onChange={(e) => setModuleFilter(e.target.value)}
            >
              {MODULES.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>

          <div style={{ flex: 1, minWidth: '150px' }}>
            <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Status</label>
            <select
              className="input"
              style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              {STATUSES.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>

          <div style={{ flex: 1.2, minWidth: '200px' }}>
            <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Ticker Search</label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                className="input"
                style={{ flex: 1, padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={symbolSearch}
                onChange={(e) => setSymbolSearch(e.target.value.toUpperCase())}
                placeholder="e.g. NIFTY50, RELIANCE"
              />
              <button type="submit" className="btn-secondary" style={{ padding: '8px 14px', borderRadius: '6px', cursor: 'pointer' }}>
                Search
              </button>
            </div>
          </div>
        </form>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <div className="spinner" style={{ margin: '0 auto 16px auto', border: '4px solid rgba(255,255,255,0.1)', borderTop: '4px solid var(--accent-primary)', borderRadius: '50%', width: '32px', height: '32px', animation: 'spin 1s linear infinite' }}></div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Querying SQLite database experiments registry...</p>
        </div>
      ) : experiments.length === 0 ? (
        <div className="card" style={{ padding: '60px', textAlign: 'center', border: '1px dashed var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <p style={{ color: 'var(--text-secondary)' }}>No experiments found matching the filter options.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Main Experiments List Table */}
          <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table" style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th>Experiment ID (Hash)</th>
                    <th>Name</th>
                    <th>Module</th>
                    <th style={{ textAlign: 'center' }}>Ticker</th>
                    <th style={{ textAlign: 'center' }}>Status</th>
                    <th>Started At</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {experiments.map((e) => (
                    <React.Fragment key={e.experiment_id}>
                      <tr>
                        <td style={{ fontFamily: 'monospace', fontSize: '11px', color: 'var(--text-muted)' }}>
                          {e.experiment_id.slice(0, 8)}...
                        </td>
                        <td>
                          <strong>{e.name}</strong>
                        </td>
                        <td>
                          <span style={{ fontSize: '12px' }}>{getModuleLabel(e.lab_module)}</span>
                        </td>
                        <td style={{ textAlign: 'center', fontFamily: 'monospace', fontWeight: 'bold' }}>
                          {e.symbol || 'PORTFOLIO'}
                        </td>
                        <td style={{ textAlign: 'center' }}>
                          <span className={`lab-status-badge ${e.status}`}>
                            {e.status}
                          </span>
                        </td>
                        <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                          {e.started_at}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <div style={{ display: 'inline-flex', gap: '6px' }}>
                            <button
                              onClick={() => handleViewDetail(e.experiment_id)}
                              className="btn-secondary"
                              style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '4px' }}
                            >
                              {activeDetail && activeDetail.experiment_id === e.experiment_id ? 'Hide' : 'Inspect'}
                            </button>
                            <a
                              href={exportExperimentUrl(e.experiment_id)}
                              className="btn-secondary"
                              style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '4px', textDecoration: 'none', display: 'inline-block' }}
                              download
                            >
                              📥 JSON
                            </a>
                            <button
                              onClick={() => handleDelete(e.experiment_id)}
                              className="btn-secondary"
                              style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '4px', color: '#ef4444' }}
                            >
                              🗑 Delete
                            </button>
                          </div>
                        </td>
                      </tr>

                      {/* Expanded row showing metrics details */}
                      {activeDetail && activeDetail.experiment_id === e.experiment_id && (
                        <tr>
                          <td colSpan={7} style={{ background: 'rgba(255,255,255,0.01)', padding: '20px', borderTop: '1px solid var(--border-primary)', borderBottom: '1px solid var(--border-primary)' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                              <div>
                                <h4 style={{ fontSize: '13px', fontWeight: '700', marginBottom: '8px', color: 'var(--accent-primary)' }}>Configuration Parameters</h4>
                                <pre style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '6px', fontSize: '11px', fontFamily: 'monospace', overflowX: 'auto', border: '1px solid var(--border-primary)' }}>
                                  {JSON.stringify(activeDetail.params, null, 2)}
                                </pre>
                                <div style={{ fontSize: '12px', marginTop: '10px' }}>
                                  Version: <strong>v{activeDetail.version}</strong> · Reproducibility Seed: <strong>{activeDetail.reproducibility_seed}</strong>
                                </div>
                                {activeDetail.error_msg && (
                                  <div style={{ marginTop: '12px', padding: '10px', background: 'rgba(239,68,68,0.1)', color: '#ef4444', borderRadius: '6px', fontSize: '12px', border: '1px solid rgba(239,68,68,0.2)' }}>
                                    <strong>Run Error:</strong> {activeDetail.error_msg}
                                  </div>
                                )}
                              </div>

                              <div>
                                <h4 style={{ fontSize: '13px', fontWeight: '700', marginBottom: '8px', color: 'var(--accent-primary)' }}>Calculated Output Metrics</h4>
                                {activeDetail.metrics && Object.keys(activeDetail.metrics).length > 0 ? (
                                  <pre style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '6px', fontSize: '11px', fontFamily: 'monospace', overflowX: 'auto', maxHeight: '200px', border: '1px solid var(--border-primary)' }}>
                                    {JSON.stringify(activeDetail.metrics, null, 2)}
                                  </pre>
                                ) : (
                                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>No performance metrics recorded for this experiment type.</p>
                                )}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

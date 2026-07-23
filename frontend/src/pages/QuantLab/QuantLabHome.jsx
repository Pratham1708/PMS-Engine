import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getExperimentsSummary,
  listExperiments,
  getValidationDashboard,
  getDriftAlerts,
  getMarketBreadth
} from '../../api/labApi';

const MODULES_CORE = [
  { path: '/lab/indicators', name: 'Indicator Lab', desc: 'Backtest technical indicators, signals, and parameters.', icon: '📊' },
  { path: '/lab/cross-indicator', name: 'Cross-Indicator Lab', desc: 'Rank logical dual/triple joint indicator rules.', icon: '⚡' },
  { path: '/lab/engine', name: 'Engine Validation', desc: 'Verify predictive correlation of technical & ML scores.', icon: '🧪' },
  { path: '/lab/models', name: 'Model Lab', desc: 'Compare ML model calibration, pricing stability, and SHAP.', icon: '🤖' },
  { path: '/lab/ensemble', name: 'Ensemble Strategy Lab', desc: 'Weighted, Majority, and Rank voting ensemble methods.', icon: '🧠', isLocked: true, remark: 'Coming Soon' },
  { path: '/lab/features', name: 'Feature Lab', desc: 'Examine feature correlation, VIF, and mutual info.', icon: '🧬' },
  { path: '/lab/composite', name: 'Composite Lab', desc: 'Research sub-score weights and partial correlations.', icon: '⚖️' },
];

const MODULES_SIMULATION = [
  { path: '/lab/monte-carlo', name: 'Monte Carlo Sandbox', desc: 'Resampled bootstrap CAGR / DD confidence bounds.', icon: '🎲' },
  { path: '/lab/stress', name: 'Crisis Stress Tester', desc: 'Test historical crisis drawdown resilience.', icon: '⛈️' },
  { path: '/lab/hyperopt', name: 'Parameter Hyperopt', desc: 'Optimize boundaries, risk rules, and trade limits.', icon: '🎛️' },
  { path: '/lab/sizing', name: 'Position Sizing Lab', desc: 'Evaluate Compounding under Kelly, Volatility & Fixed rules.', icon: '📐' },
  { path: '/lab/construction', name: 'Portfolio Optimizer', desc: 'Efficient frontier and Sharpe weights solver.', icon: '💼' },
  { path: '/lab/portfolio', name: 'Portfolio Lab', desc: 'Backtest diversified Top-N and Smart Beta strategies.', icon: '🏢', isLocked: true, remark: 'Coming Soon' },
];

const MODULES_AUDITS = [
  { path: '/lab/validation', name: 'Rec. Validation', desc: 'Audit BUY/SELL recommendation horizon accuracies.', icon: '✅' },
  { path: '/lab/correlation', name: 'Correlation Lab', desc: 'Score collinearity matrices and redundancy alerts.', icon: '🔗', isLocked: true, remark: 'Coming Soon' },
  { path: '/lab/breadth', name: 'Market Breadth', desc: 'A/D timeline and participation indicators.', icon: '📈' },
  { path: '/lab/liquidity', name: 'Liquidity Auditor', desc: 'ADV, Amihud, and gap-frequency suitability filter.', icon: '💧' },
  { path: '/lab/drift', name: 'Drift Monitor', desc: 'Divergence metrics alert manager.', icon: '🛡️', isLocked: true, remark: 'Coming Soon' },
  { path: '/lab/regime', name: 'Regime Lab', desc: 'Identify market regimes and regime score weights.', icon: '🌊' },
  { path: '/lab/benchmark', name: 'Benchmark Compare', desc: 'Alpha, Beta, Info Ratio vs standard indices.', icon: '📊', isLocked: true, remark: 'Coming Soon' },
  { path: '/lab/experiments', name: 'Experiment History', desc: 'Browse, filter, and review completed runs registry.', icon: '🗂' },
  { path: '/lab/reports', name: 'Lab Reports', desc: 'Print-ready HTML/PDF research logs generator.', icon: '📋' }
];

export default function QuantLabHome() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState({ total: 0, by_status: {}, by_module: {} });
  const [recentExps, setRecentExps] = useState([]);
  const [accuracy, setAccuracy] = useState(null);
  const [driftAlerts, setDriftAlerts] = useState([]);
  const [breadth, setBreadth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const sumRes = await getExperimentsSummary();
        setSummary(sumRes.data);

        const recRes = await listExperiments({ limit: 4 });
        setRecentExps(recRes.data);

        const accRes = await getValidationDashboard();
        setAccuracy(accRes.data);

        const driftRes = await getDriftAlerts();
        setDriftAlerts(driftRes.data || []);

        const breadthRes = await getMarketBreadth('6M');
        setBreadth(breadthRes.data);
      } catch (err) {
        console.error('Failed to load lab homepage dashboard details:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '12px' }}>
            🔬 Quant Research Laboratory
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
            Institutional Portfolio Validation Platform & Backtesting Environment · PMS Engine v2
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button
            onClick={() => navigate('/lab/experiments')}
            className="btn-secondary"
            style={{ padding: '8px 16px', borderRadius: '6px', fontSize: '13px', cursor: 'pointer' }}
          >
            🗂 Registry History
          </button>
          <button
            onClick={() => navigate('/lab/reports')}
            className="btn-primary"
            style={{ padding: '8px 16px', borderRadius: '6px', fontSize: '13px', cursor: 'pointer', fontWeight: '600' }}
          >
            📋 Compile Lab Reports
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
        gap: '16px',
        marginBottom: '32px'
      }}>
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>Total Experiments</div>
          <div style={{ fontSize: '28px', fontWeight: '800', marginTop: '4px', fontFamily: 'monospace' }}>{summary.total}</div>
        </div>
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>Active Runs</div>
          <div style={{ fontSize: '28px', fontWeight: '800', marginTop: '4px', color: '#3b82f6', fontFamily: 'monospace' }}>
            {summary.by_status?.running || 0}
          </div>
        </div>
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>Drift Alert Status</div>
          <div style={{ fontSize: '28px', fontWeight: '800', marginTop: '4px', color: driftAlerts.length > 0 ? '#ef4444' : '#10b981', fontFamily: 'monospace' }}>
            {driftAlerts.length > 0 ? `${driftAlerts.length} Active` : 'Stable'}
          </div>
        </div>
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>Market Participation</div>
          <div style={{ fontSize: '28px', fontWeight: '800', marginTop: '4px', color: '#f59e0b', fontFamily: 'monospace' }}>
            {breadth ? `${breadth.current_participation_pct}%` : '—'}
          </div>
        </div>
      </div>

      {/* Research Pipeline Promotion Stage Stepper */}
      <div className="card" style={{ padding: '24px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)', marginBottom: '32px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '16px' }}>Research Pipeline Promotion Workflow</h3>
        <div className="quant-workflow-grid">
          {[
            { stage: '1. Idea Formulation', desc: 'Technical & joint rule backtests.', icon: '💡', active: true, color: '#6366f1' },
            { stage: '2. Multi-Model Tuning', desc: 'ML models calibration and hyperopt.', icon: '🎛️', active: true, color: '#8b5cf6' },
            { stage: '3. Risk & Drift Audit', desc: 'Monte Carlo limits and drift monitors.', icon: '🛡️', active: true, color: '#3b82f6' },
            { stage: '4. Production Approval', desc: 'Promote weights to recommendation engine.', icon: '🚀', active: true, color: '#10b981' }
          ].map((step, idx) => (
            <div
              key={idx}
              style={{
                padding: '16px',
                background: 'rgba(255,255,255,0.01)',
                border: `1px solid var(--border-primary)`,
                borderLeft: `4px solid ${step.color}`,
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                minWidth: 0
              }}
            >
              <span style={{ fontSize: '20px', flexShrink: 0 }}>{step.icon}</span>
              <div style={{ minWidth: 0 }}>
                <h4 style={{ fontSize: '13.5px', fontWeight: '700', margin: 0, wordBreak: 'break-word' }}>{step.stage}</h4>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px', margin: 0, wordBreak: 'break-word' }}>{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Split Layout: Modules on Left, Live Alert Feed & Metrics on Right */}
      <div className="quant-home-split-grid">
        {/* Left Side: Modular Categories */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
          
          {/* Category 1: Alpha Core & Signals */}
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-primary)', paddingBottom: '6px' }}>
              Alpha & Signals Research (Scoring engines)
            </h3>
            <div className="lab-module-grid">
              {MODULES_CORE.map((mod) => (
                <div
                  key={mod.path}
                  onClick={() => navigate(mod.path)}
                  className="lab-module-card"
                  style={{
                    position: 'relative',
                    opacity: mod.isLocked ? 0.85 : 1,
                    border: mod.isLocked ? '1px solid rgba(245, 158, 11, 0.25)' : undefined,
                    background: mod.isLocked ? 'rgba(245, 158, 11, 0.02)' : undefined
                  }}
                >
                  {mod.isLocked && (
                    <div style={{
                      position: 'absolute',
                      top: '12px',
                      right: '12px',
                      fontSize: '10px',
                      padding: '2px 8px',
                      borderRadius: '12px',
                      background: 'rgba(245, 158, 11, 0.15)',
                      color: '#f59e0b',
                      border: '1px solid rgba(245, 158, 11, 0.3)',
                      fontWeight: '700',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}>
                      🔒 {mod.remark || 'Coming Soon'}
                    </div>
                  )}
                  <div style={{ fontSize: '26px', marginBottom: '8px' }}>{mod.icon}</div>
                  <div>
                    <h4 style={{ fontSize: '14.5px', fontWeight: '600', marginBottom: '4px', color: 'var(--text-primary)' }}>{mod.name}</h4>
                    <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4', margin: 0 }}>{mod.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Category 2: Risk Tuning & Portfolio Optimization */}
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-primary)', paddingBottom: '6px' }}>
              Risk Simulation & Portfolio Optimization
            </h3>
            <div className="lab-module-grid">
              {MODULES_SIMULATION.map((mod) => (
                <div
                  key={mod.path}
                  onClick={() => navigate(mod.path)}
                  className="lab-module-card"
                  style={{
                    position: 'relative',
                    opacity: mod.isLocked ? 0.85 : 1,
                    border: mod.isLocked ? '1px solid rgba(245, 158, 11, 0.25)' : undefined,
                    background: mod.isLocked ? 'rgba(245, 158, 11, 0.02)' : undefined
                  }}
                >
                  {mod.isLocked && (
                    <div style={{
                      position: 'absolute',
                      top: '12px',
                      right: '12px',
                      fontSize: '10px',
                      padding: '2px 8px',
                      borderRadius: '12px',
                      background: 'rgba(245, 158, 11, 0.15)',
                      color: '#f59e0b',
                      border: '1px solid rgba(245, 158, 11, 0.3)',
                      fontWeight: '700',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}>
                      🔒 {mod.remark || 'Coming Soon'}
                    </div>
                  )}
                  <div style={{ fontSize: '26px', marginBottom: '8px' }}>{mod.icon}</div>
                  <div>
                    <h4 style={{ fontSize: '14.5px', fontWeight: '600', marginBottom: '4px', color: 'var(--text-primary)' }}>{mod.name}</h4>
                    <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4', margin: 0 }}>{mod.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Category 3: System Audits & Utilities */}
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-primary)', paddingBottom: '6px' }}>
              System Integrity Audits & Utilities
            </h3>
            <div className="lab-module-grid">
              {MODULES_AUDITS.map((mod) => (
                <div
                  key={mod.path}
                  onClick={() => navigate(mod.path)}
                  className="lab-module-card"
                  style={{
                    position: 'relative',
                    opacity: mod.isLocked ? 0.85 : 1,
                    border: mod.isLocked ? '1px solid rgba(245, 158, 11, 0.25)' : undefined,
                    background: mod.isLocked ? 'rgba(245, 158, 11, 0.02)' : undefined
                  }}
                >
                  {mod.isLocked && (
                    <div style={{
                      position: 'absolute',
                      top: '12px',
                      right: '12px',
                      fontSize: '10px',
                      padding: '2px 8px',
                      borderRadius: '12px',
                      background: 'rgba(245, 158, 11, 0.15)',
                      color: '#f59e0b',
                      border: '1px solid rgba(245, 158, 11, 0.3)',
                      fontWeight: '700',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}>
                      🔒 {mod.remark || 'Coming Soon'}
                    </div>
                  )}
                  <div style={{ fontSize: '26px', marginBottom: '8px' }}>{mod.icon}</div>
                  <div>
                    <h4 style={{ fontSize: '14.5px', fontWeight: '600', marginBottom: '4px', color: 'var(--text-primary)' }}>{mod.name}</h4>
                    <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4', margin: 0 }}>{mod.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Right Side: Feed Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Active Drift Warning Feed */}
          {driftAlerts.length > 0 && (
            <div style={{
              padding: '16px',
              background: 'rgba(239, 68, 68, 0.05)',
              border: '1px solid rgba(239, 68, 68, 0.15)',
              borderRadius: 'var(--radius-lg)'
            }}>
              <h4 style={{ fontSize: '13px', fontWeight: '700', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '6px', margin: '0 0 10px 0' }}>
                ⚠️ Active Scoring Divergence Alerts
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {driftAlerts.slice(0, 2).map((alert) => (
                  <div key={alert.id} style={{ fontSize: '12px', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.03)', paddingBottom: '6px' }}>
                    <strong>{alert.metric_name}</strong>: {alert.message}
                  </div>
                ))}
              </div>
              <button
                onClick={() => navigate('/lab/drift')}
                style={{ fontSize: '11px', background: 'none', border: 'none', color: '#ef4444', textDecoration: 'underline', padding: 0, marginTop: '8px', cursor: 'pointer' }}
              >
                Go to Drift Alert Manager
              </button>
            </div>
          )}

          {/* Recent Runs Registry */}
          <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
            <h3 style={{ fontSize: '14.5px', fontWeight: '700', marginBottom: '14px' }}>Recent Runs Registry</h3>
            {recentExps.length === 0 ? (
              <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>No runs in database.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {recentExps.map((e) => (
                  <div
                    key={e.experiment_id}
                    onClick={() => navigate(`/lab/experiments?id=${e.experiment_id}`)}
                    style={{
                      padding: '10px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-primary)',
                      background: 'rgba(255,255,255,0.01)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '12.5px', fontWeight: '600' }}>{e.name}</div>
                      <span style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>({e.started_at})</span>
                    </div>
                    <span className={`lab-status-badge ${e.status}`} style={{ fontSize: '9px', padding: '1px 6px' }}>
                      {e.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recommendation Accuracy Summary */}
          <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
            <h3 style={{ fontSize: '14.5px', fontWeight: '700', marginBottom: '14px' }}>Recommendation Validation Accuracies</h3>
            {!accuracy || !accuracy.by_rating ? (
              <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Run validation processor first.</div>
            ) : (
              <div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {Object.entries(accuracy.by_rating).map(([rating, val]) => {
                    const horizons = ['30', '20', '10', '5', '1'];
                    let selectedHorizon = null;
                    let accuracyPct = null;
                    for (const h of horizons) {
                      if (val[h] && val[h].accuracy_pct !== null && val[h].accuracy_pct !== undefined) {
                        selectedHorizon = h;
                        accuracyPct = val[h].accuracy_pct;
                        break;
                      }
                    }
                    return (
                      <div key={rating} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '13px' }}>
                        <span style={{ fontWeight: '600' }}>{rating}</span>
                        <span style={{ fontWeight: '700', color: accuracyPct !== null && accuracyPct >= 60 ? '#10b981' : '#f59e0b' }}>
                          {selectedHorizon ? `${accuracyPct}% (${selectedHorizon}D)` : '—'}
                        </span>
                      </div>
                    );
                  })}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '14px', textAlign: 'right' }}>
                  Total audited rows: <strong>{accuracy.total_validated}</strong>
                </div>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}

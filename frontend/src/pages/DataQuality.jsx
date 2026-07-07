import { useState, useEffect } from 'react';
import { fetchLatestDataQuality, fetchSnapshotStatus } from '../api/stocks';
import LoadingSpinner from '../components/common/LoadingSpinner';

const CHECK_SEVERITY_COLORS = {
  pass:    { label: 'Pass',    color: '#10b981', bg: 'rgba(16,185,129,0.12)' },
  warning: { label: 'Warning', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  fail:    { label: 'Fail',    color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
};

export default function DataQuality() {
  const [dq, setDq] = useState(null);
  const [snapshotDate, setSnapshotDate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [dqRes, statusRes] = await Promise.all([
          fetchLatestDataQuality(),
          fetchSnapshotStatus(),
        ]);
        setDq(dqRes.data);
        setSnapshotDate(statusRes.data?.latest_snapshot?.snapshot_date);
      } catch (err) {
        setError('No data quality reports available. Generate a snapshot first.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="page-error">{error}</div>;
  if (!dq) return <div className="page-empty">No data quality metrics found.</div>;

  const healthColor = dq.health_score >= 85 ? '#10b981' : dq.health_score >= 60 ? '#f59e0b' : '#ef4444';

  return (
    <div className="dq-page">
      <div className="dq-header">
        <h1 className="dq-title">🛡️ Data Quality & Pre-Publish Validation</h1>
        {snapshotDate && <span className="dq-date">Snapshot Date: {snapshotDate}</span>}
        <p className="dq-subtitle">
          Real-time diagnostics, API limits, database coverage audits, and institutional rule validation checks.
        </p>
      </div>

      {/* Main Health Card */}
      <div className="dq-health-summary-card">
        <div className="dq-health-dial-col">
          <div className="dq-health-dial" style={{ borderColor: healthColor }}>
            <span className="dq-health-dial-val" style={{ color: healthColor }}>
              {dq.health_score?.toFixed(0)}%
            </span>
            <span className="dq-health-dial-label">Health Score</span>
          </div>
        </div>
        <div className="dq-health-details-col">
          <h2 className={`dq-health-status-title text-${dq.status}`}>
            System Status: {dq.status?.toUpperCase() || 'UNKNOWN'}
          </h2>
          <p className="dq-health-status-desc">
            Calculated across 12 institutional validation checks. Critical failures block the official publishing engine.
          </p>
          <div className="dq-checks-summary-pills">
            <span className="dq-summary-pill bg-green">{dq.validation_pass_count} Passed</span>
            <span className="dq-summary-pill bg-yellow">{dq.validation_warn_count} Warnings</span>
            <span className="dq-summary-pill bg-red">{dq.validation_fail_count} Failed</span>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="dq-metrics-row">
        <div className="dq-metric-card">
          <div className="dq-metric-val">{dq.coverage_pct?.toFixed(1)}%</div>
          <div className="dq-metric-label">Universe Coverage</div>
          <div className="dq-metric-sub">{dq.downloaded_count} of {dq.universe_size} downloaded</div>
        </div>
        <div className="dq-metric-card">
          <div className="dq-metric-val text-red">{dq.failed_count || 0}</div>
          <div className="dq-metric-label">Failed Downloads</div>
          <div className="dq-metric-sub">Skipped and logged</div>
        </div>
        <div className="dq-metric-card">
          <div className="dq-metric-val">{dq.cached_count || 0}</div>
          <div className="dq-metric-label">Cached / Mocked</div>
          <div className="dq-metric-sub">Sourced from static mock data</div>
        </div>
        <div className="dq-metric-card">
          <div className="dq-metric-val">
            {dq.freshness_hours != null ? `${dq.freshness_hours.toFixed(1)}h` : '—'}
          </div>
          <div className="dq-metric-label">Data Freshness</div>
          <div className="dq-metric-sub">Age since pipeline trigger</div>
        </div>
      </div>

      {/* Failed Symbols List (if any) */}
      {dq.failed_symbols?.length > 0 && (
        <div className="dq-failed-symbols-card">
          <h3>🚨 Failed Download Symbols</h3>
          <p>The following symbols failed to download price quotes from the API feed and fell back to static caches:</p>
          <div className="dq-failed-list">
            {dq.failed_symbols.map((sym) => (
              <span key={sym} className="dq-failed-item">{sym?.replace('.NS', '')}</span>
            ))}
          </div>
        </div>
      )}

      {/* Validation Checks Table */}
      <div className="dq-checks-card">
        <h3>📋 12 Institutional Pre-Publish Validation Checks</h3>
        <table className="dq-checks-table">
          <thead>
            <tr>
              <th>Check Name</th>
              <th>Status</th>
              <th>Result Detail</th>
              <th className="num-col">Threshold</th>
              <th className="num-col">Actual Value</th>
            </tr>
          </thead>
          <tbody>
            {dq.validation_checks?.map((check) => {
              const statusCfg = CHECK_SEVERITY_COLORS[check.status] || { label: check.status, color: '#6b7280', bg: 'rgba(0,0,0,0.05)' };
              return (
                <tr key={check.check_name}>
                  <td><strong>{check.check_name?.replace(/_/g, ' ').toUpperCase()}</strong></td>
                  <td>
                    <span className="dq-status-pill" style={{ color: statusCfg.color, backgroundColor: statusCfg.bg }}>
                      {statusCfg.label}
                    </span>
                  </td>
                  <td>{check.detail || '—'}</td>
                  <td className="num-col">{check.threshold != null ? check.threshold : '—'}</td>
                  <td className="num-col">
                    <strong>{check.actual_value != null ? check.actual_value.toFixed(1) : '—'}</strong>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

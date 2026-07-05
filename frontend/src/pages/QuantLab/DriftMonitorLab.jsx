import React, { useEffect, useState } from 'react';
import { getDriftMonitor, getDriftAlerts } from '../../api/labApi';

export default function DriftMonitorLab() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);

  const loadHistory = async () => {
    try {
      const res = await getDriftAlerts();
      setHistory(res.data || []);
    } catch (err) {
      console.error('Failed to load drift alert log history:', err);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getDriftMonitor();
      setData(res.data);
      await loadHistory();
    } catch (err) {
      console.error(err);
      setError('Failed to execute drift monitoring check.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: '800' }}>🛡️ Score & Model Drift Monitor</h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            Detect statistical shifts in recommendation sub-scores by auditing recent 30-day score distribution averages against baseline histories.
          </p>
        </div>
        <button
          onClick={handleRun}
          className="btn-primary"
          style={{ padding: '10px 20px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
          disabled={loading}
        >
          {loading ? 'Running Audit...' : '🔄 Trigger Drift Audit'}
        </button>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px', marginBottom: '20px' }}>
          ⚠️ {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <div className="spinner" style={{ margin: '0 auto 16px auto', border: '4px solid rgba(255,255,255,0.1)', borderTop: '4px solid var(--accent-primary)', borderRadius: '50%', width: '40px', height: '40px', animation: 'spin 1s linear infinite' }}></div>
          <p style={{ color: 'var(--text-secondary)' }}>Auditing database scoring history tables and computing standard deviation shifts...</p>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '24px',
          alignItems: 'start'
        }}>
          {/* Left Side: Current Audit Results */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {data ? (
              <>
                {/* Drift Summary Alert Box */}
                <div style={{
                  padding: '20px',
                  background: data.drift_detected ? 'rgba(239, 68, 68, 0.06)' : 'rgba(16, 185, 129, 0.06)',
                  border: `1px solid ${data.drift_detected ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)'}`,
                  borderRadius: 'var(--radius-lg)'
                }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '800', color: data.drift_detected ? '#ef4444' : '#10b981', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                    {data.drift_detected ? '⚠️ STATISTICAL SCORE DRIFT DETECTED' : '✅ SCORING STABILIZED'}
                  </h3>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '6px', margin: 0 }}>
                    {data.drift_detected 
                      ? 'Deviation score shifted beyond baseline threshold limits. Model recalibration is recommended.'
                      : 'Recent 30-day scores are statistically consistent with baseline averages.'}
                  </p>
                </div>

                {/* Active Alerts List */}
                {data.alerts?.length > 0 && (
                  <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#ef4444', marginBottom: '12px' }}>Active Threshold Violations</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {data.alerts.map((alert, idx) => (
                        <div key={idx} style={{ padding: '12px', background: 'rgba(239,68,68,0.02)', borderLeft: '3px solid #ef4444', borderRadius: '4px', fontSize: '13px' }}>
                          <strong>{alert.name.toUpperCase()}</strong>: {alert.message}
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                            Threshold: {alert.threshold} SD · Current Deviation: {alert.val.toFixed(2)} SD
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Comparison Grid */}
                {data.metrics && (
                  <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                    <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '16px' }}>Scoring Divergence Audit</h3>
                    <div style={{ overflowX: 'auto' }}>
                      <table className="data-table" style={{ width: '100%' }}>
                        <thead>
                          <tr>
                            <th>Scoring Engine</th>
                            <th style={{ textAlign: 'center' }}>Baseline Mean</th>
                            <th style={{ textAlign: 'center' }}>Recent 30D Mean</th>
                            <th style={{ textAlign: 'center' }}>Divergence (SD)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(data.metrics).map(([key, val]) => (
                            <tr key={key}>
                              <td><strong>{key.toUpperCase()} SCORE</strong></td>
                              <td style={{ textAlign: 'center', fontFamily: 'monospace' }}>{val.baseline_mean}</td>
                              <td style={{ textAlign: 'center', fontFamily: 'monospace' }}>{val.recent_mean}</td>
                              <td style={{ textAlign: 'center', fontFamily: 'monospace', fontWeight: '700', color: val.deviation_std > 0.20 ? '#ef4444' : '#10b981' }}>
                                {val.deviation_std} SD
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="card" style={{ padding: '40px', textAlign: 'center', border: '1px dashed var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <p style={{ color: 'var(--text-secondary)' }}>Click "Trigger Drift Audit" to execute statistical shift checks.</p>
              </div>
            )}
          </div>

          {/* Right Side: Drift Alert History Log */}
          <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
            <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '12px' }}>Logged Alert History</h3>
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '16px' }}>Persistent alerts registry from SQLite database.</p>
            {history.length === 0 ? (
              <div style={{ color: 'var(--text-secondary)', fontSize: '13px', textAlign: 'center', padding: '30px' }}>No logged alerts in database history.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '550px', overflowY: 'auto' }}>
                {history.map((h) => (
                  <div
                    key={h.id}
                    style={{
                      padding: '12px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-primary)',
                      background: 'rgba(255,255,255,0.02)',
                      fontSize: '12.5px'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{
                        padding: '2px 6px',
                        background: h.alert_type === 'composite' ? 'rgba(99,102,241,0.1)' : 'rgba(245,158,11,0.1)',
                        border: `1px solid ${h.alert_type === 'composite' ? 'rgba(99,102,241,0.2)' : 'rgba(245,158,11,0.2)'}`,
                        color: h.alert_type === 'composite' ? '#818cf8' : '#f59e0b',
                        fontSize: '10px',
                        fontWeight: '700',
                        borderRadius: '4px'
                      }}>
                        {h.alert_type.toUpperCase()}
                      </span>
                      <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>{h.recorded_at}</span>
                    </div>
                    <div style={{ color: 'var(--text-primary)', fontWeight: '600', marginBottom: '4px' }}>
                      {h.metric_name} (Deviation: {h.current_value.toFixed(2)} SD)
                    </div>
                    <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '12px' }}>{h.message}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useEffect, useState } from 'react';
import {
  populateAuditQueue,
  processValidations,
  getValidationDashboard,
  getSymbolValidation,
  getValidationTrend
} from '../../api/labApi';
import ChartPanel from './shared/ChartPanel';

const HORIZONS = ['1', '5', '10', '20', '30', '90', '180', '365'];
const RATINGS = ['STRONG BUY', 'BUY', 'HOLD', 'SELL', 'STRONG SELL'];

export default function RecommendationValidation() {
  const [dashboard, setDashboard] = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [actionMessage, setActionMessage] = useState('');
  const [error, setError] = useState(null);
  
  // Search symbol states
  const [searchSymbol, setSearchSymbol] = useState('');
  const [symbolAudits, setSymbolAudits] = useState([]);
  const [symbolLoading, setSymbolLoading] = useState(false);
  
  // Batch size state
  const [batchSize, setBatchSize] = useState(100);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const resDash = await getValidationDashboard();
      setDashboard(resDash.data);

      const resTrend = await getValidationTrend();
      setTrendData(resTrend.data);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch recommendation validation metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handlePopulate = async () => {
    setActionMessage('');
    setError(null);
    try {
      const res = await populateAuditQueue();
      setActionMessage(`Queue populated! Added ${res.data?.added || 0} pending validations.`);
      loadDashboardData();
    } catch (err) {
      console.error(err);
      setError('Failed to populate validation audit queue.');
    }
  };

  const handleProcess = async () => {
    setActionMessage('');
    setError(null);
    setProcessing(true);
    try {
      const res = await processValidations({ batch_size: batchSize });
      setActionMessage(`Background processing started for ${batchSize} rows. Wait a few seconds and refresh.`);
      setTimeout(() => {
        setProcessing(false);
        loadDashboardData();
      }, 3000);
    } catch (err) {
      console.error(err);
      setError('Failed to start recommendation validation processing.');
      setProcessing(false);
    }
  };

  const handleSearchSymbol = async (e) => {
    e.preventDefault();
    if (!searchSymbol) return;
    setSymbolLoading(true);
    setSymbolAudits([]);
    try {
      const res = await getSymbolValidation(searchSymbol);
      setSymbolAudits(res.data || []);
    } catch (err) {
      console.error(err);
      setError(`Failed to fetch audit data for symbol ${searchSymbol}`);
    } finally {
      setSymbolLoading(false);
    }
  };

  // Convert trend data for ChartPanel
  const getTrendChart = () => {
    if (!trendData || trendData.length === 0) return [];
    return [{
      key: 'accuracy_trend',
      title: 'Recommendation Accuracy Trend (%)',
      type: 'line',
      data: trendData,
      xKey: 'month',
      yKeys: ['accuracy_pct'],
      colors: ['#10b981'],
    }];
  };

  // Cell color based on accuracy
  const getCellBg = (val) => {
    if (val === null || val === undefined) return 'rgba(255,255,255,0.02)';
    if (val >= 75) return 'rgba(16, 185, 129, 0.25)'; // bright green
    if (val >= 60) return 'rgba(16, 185, 129, 0.15)'; // light green
    if (val >= 50) return 'rgba(245, 158, 11, 0.15)';  // orange
    return 'rgba(239, 68, 68, 0.15)'; // red
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: '800' }}>✅ Recommendation Validation & Audit Lab</h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            Examine the accuracy and realized forward returns of historical BUY, SELL, and HOLD recommendations.
          </p>
        </div>
        <button
          onClick={loadDashboardData}
          className="btn-secondary"
          style={{ padding: '8px 14px', borderRadius: '6px', cursor: 'pointer' }}
          disabled={loading}
        >
          🔄 Refresh Dashboard
        </button>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px', marginBottom: '20px' }}>
          ⚠️ {error}
        </div>
      )}

      {actionMessage && (
        <div style={{ padding: '12px 16px', background: 'rgba(59,130,246,0.1)', color: '#3b82f6', border: '1px solid rgba(59,130,246,0.2)', borderRadius: '6px', marginBottom: '20px' }}>
          ℹ️ {actionMessage}
        </div>
      )}

      {/* Control Queue Panel */}
      <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)', marginBottom: '24px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '16px' }}>Audit Queue Management</h3>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '24px',
          alignItems: 'end'
        }}>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Step 1: Scan & Queue Recommendations</div>
            <button
              onClick={handlePopulate}
              className="btn-secondary"
              style={{ padding: '10px 16px', borderRadius: '6px', cursor: 'pointer', background: 'rgba(255,255,255,0.03)' }}
              disabled={loading}
            >
              📂 Queue Pending Historical Runs
            </button>
          </div>

          <div style={{ borderLeft: '1px solid var(--border-primary)', height: '50px', display: 'none', '@media (min-width: 768px)': { display: 'block' } }}></div>

          <div style={{ flex: 1, minWidth: '280px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Step 2: Validate realizing return horizons in background</div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                type="number"
                className="input"
                style={{ width: '100px', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={batchSize}
                onChange={(e) => setBatchSize(parseInt(e.target.value) || 50)}
                placeholder="Batch Size"
              />
              <button
                onClick={handleProcess}
                className="btn-primary"
                style={{ padding: '10px 16px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
                disabled={processing || loading}
              >
                {processing ? 'Calculating Return Horizons...' : '🚀 Process Queue (Fetch Prices)'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {loading && !dashboard ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <div className="spinner" style={{ margin: '0 auto 16px auto', border: '4px solid rgba(255,255,255,0.1)', borderTop: '4px solid var(--accent-primary)', borderRadius: '50%', width: '40px', height: '40px', animation: 'spin 1s linear infinite' }}></div>
          <p style={{ color: 'var(--text-secondary)' }}>Loading audit dashboard...</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Main Matrix Heatmap */}
          <div className="card" style={{ padding: '24px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700' }}>Horizon Accuracy Heatmap Matrix (%)</h3>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Total Audited Predictions: <strong>{dashboard?.total_validated || 0}</strong>
              </span>
            </div>
            
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ padding: '12px', border: '1px solid var(--border-primary)', textAlign: 'left' }}>Rating Class</th>
                    {HORIZONS.map((h) => (
                      <th key={h} style={{ padding: '12px', border: '1px solid var(--border-primary)', textAlign: 'center' }}>
                        {h}D Horizon
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {RATINGS.map((rating) => {
                    const rowData = dashboard?.by_rating?.[rating] || {};
                    return (
                      <tr key={rating}>
                        <td style={{ padding: '12px', border: '1px solid var(--border-primary)', fontWeight: 'bold' }}>
                          {rating}
                        </td>
                        {HORIZONS.map((h) => {
                          const cell = rowData[h];
                          const hasData = cell && cell.total > 0;
                          return (
                            <td
                              key={h}
                              style={{
                                padding: '12px',
                                border: '1px solid var(--border-primary)',
                                textAlign: 'center',
                                background: hasData ? getCellBg(cell.accuracy_pct) : 'rgba(255,255,255,0.01)',
                                cursor: 'help'
                              }}
                              title={hasData ? `Validated ${cell.correct}/${cell.total} rows. Avg Ret: ${cell.avg_return_pct?.toFixed(2)}%` : 'No samples'}
                            >
                              {hasData ? (
                                <div>
                                  <div style={{ fontSize: '14px', fontWeight: '700', color: '#fff' }}>{cell.accuracy_pct}%</div>
                                  <div style={{ fontSize: '10px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                                    n={cell.total}
                                  </div>
                                </div>
                              ) : (
                                <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>—</span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Lower layout - Trend Line Chart & Symbol Lookup */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '24px',
            alignItems: 'start'
          }}>
            {/* Accuracy Trend */}
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Monthly Accuracy Calibration Trend</h3>
              {trendData.length === 0 ? (
                <div className="card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  No historical trend timeline available. Execute more queue batch calculations.
                </div>
              ) : (
                <ChartPanel charts={getTrendChart()} />
              )}
            </div>

            {/* Single Symbol Audit Lookup */}
            <div className="card" style={{ padding: '24px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '8px' }}>Symbol-Level Recommendation Audits</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '16px' }}>
                Query a specific ticker to audit all past recommendations, forward horizons, and outcomes.
              </p>
              
              <form onSubmit={handleSearchSymbol} style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                <input
                  type="text"
                  className="input"
                  style={{ flex: 1, padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff', textTransform: 'uppercase' }}
                  value={searchSymbol}
                  onChange={(e) => setSearchSymbol(e.target.value.toUpperCase())}
                  placeholder="e.g. RELIANCE, TCS, INFY"
                />
                <button type="submit" className="btn-secondary" style={{ padding: '10px 16px', borderRadius: '6px', cursor: 'pointer' }}>
                  {symbolLoading ? 'Searching...' : '🔍 Search'}
                </button>
              </form>

              {symbolLoading ? (
                <div style={{ textAlign: 'center', padding: '20px' }}>
                  <div className="spinner" style={{ margin: '0 auto 8px auto', border: '3px solid rgba(255,255,255,0.1)', borderTop: '3px solid var(--accent-primary)', borderRadius: '50%', width: '24px', height: '24px', animation: 'spin 1s linear infinite' }}></div>
                </div>
              ) : symbolAudits.length > 0 ? (
                <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                  <table className="data-table" style={{ width: '100%', fontSize: '12px' }}>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Rec.</th>
                        <th style={{ textAlign: 'center' }}>Horizon</th>
                        <th style={{ textAlign: 'center' }}>Realized Ret.</th>
                        <th style={{ textAlign: 'center' }}>Outcome</th>
                      </tr>
                    </thead>
                    <tbody>
                      {symbolAudits.map((aud) => (
                        <tr key={aud.id}>
                          <td>{aud.analyzed_at?.split(' ')?.[0] || aud.analyzed_at}</td>
                          <td>
                            <span style={{
                              fontWeight: '600',
                              color: aud.rating.includes('BUY') ? '#10b981' : (aud.rating.includes('SELL') ? '#ef4444' : '#f59e0b')
                            }}>
                              {aud.rating}
                            </span>
                          </td>
                          <td style={{ textAlign: 'center' }}>{aud.horizon_days}D</td>
                          <td style={{ textAlign: 'center', color: aud.forward_return >= 0 ? '#10b981' : '#ef4444' }}>
                            {aud.forward_return !== null ? `${aud.forward_return.toFixed(2)}%` : '—'}
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            {aud.validated === null ? (
                              <span style={{ color: 'var(--text-muted)' }}>Pending</span>
                            ) : (
                              <span style={{ fontWeight: '700', color: aud.validated ? '#10b981' : '#ef4444' }}>
                                {aud.validated ? 'PASS' : 'FAIL'}
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : searchSymbol ? (
                <div style={{ color: 'var(--text-secondary)', fontSize: '13px', textAlign: 'center', padding: '20px 0' }}>
                  No historical audits found for ticker "{searchSymbol}".
                </div>
              ) : null}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}

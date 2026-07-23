import React, { useEffect, useState } from 'react';
import { getFullFeatureAnalysis } from '../../api/labApi';
import ChartPanel from './shared/ChartPanel';
import LabWorkflowGuide from '../../components/common/LabWorkflowGuide';

export default function FeatureLab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('vif');

  const loadAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getFullFeatureAnalysis();
      setData(res.data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to fetch feature analysis data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalysis();
  }, []);

  // Format charts for ChartPanel
  const getMIChart = () => {
    if (!data?.mutual_information?.mutual_information) return [];
    return [{
      key: 'mi_chart',
      title: 'Mutual Information with Target',
      type: 'bar',
      data: data.mutual_information.mutual_information,
      xKey: 'feature',
      yKeys: ['mi'],
      colors: ['#3b82f6'],
    }];
  };

  const getImportanceChart = () => {
    if (!data?.importance?.importance) return [];
    return [{
      key: 'importance_chart',
      title: 'Permutation Feature Importance Ranks',
      type: 'bar',
      data: data.importance.importance,
      xKey: 'feature',
      yKeys: ['importance'],
      colors: ['#10b981'],
    }];
  };

  const getShapChart = () => {
    if (!data?.shap_proxy?.shap_values) return [];
    const chartData = Object.entries(data.shap_proxy.shap_values).map(([feature, val]) => ({
      feature,
      shap: val
    }));
    return [{
      key: 'shap_chart',
      title: 'Linear SHAP Proxy Values (Marginal Contribution)',
      type: 'bar',
      data: chartData,
      xKey: 'feature',
      yKeys: ['shap'],
      colors: ['#8b5cf6'],
    }];
  };

  const getDriftCharts = () => {
    if (!data?.drift?.drift) return [];
    return data.drift.drift.map((item) => ({
      key: `drift_${item.feature}`,
      title: `${item.feature.replace('_', ' ').toUpperCase()} Drift`,
      type: 'line',
      data: item.monthly_means,
      xKey: 'month',
      yKeys: ['mean'],
      colors: [item.drift_detected ? '#ef4444' : '#10b981'],
    }));
  };

  // Build a matrix for the correlation matrix heatmap visual
  const renderCorrelationMatrix = () => {
    if (!data?.correlation?.correlation_flat) return null;
    const flat = data.correlation.correlation_flat;
    const features = data.correlation.features;

    // Helper to get color shade based on correlation value
    const getHeatColor = (val) => {
      if (val === null || val === undefined) return 'rgba(255,255,255,0.02)';
      const abs = Math.abs(val);
      if (val > 0) {
        return `rgba(59, 130, 246, ${abs * 0.7})`; // Blue for positive
      } else {
        return `rgba(239, 68, 68, ${abs * 0.7})`; // Red for negative
      }
    };

    return (
      <div style={{ overflowX: 'auto', marginTop: '16px' }}>
        <table style={{ borderCollapse: 'collapse', margin: '0 auto', fontSize: '12px' }}>
          <thead>
            <tr>
              <th style={{ padding: '8px', border: '1px solid var(--border-primary)' }}></th>
              {features.map((f) => (
                <th key={f} style={{ padding: '8px', border: '1px solid var(--border-primary)', minWidth: '90px', fontSize: '10px', wordBreak: 'break-all' }}>
                  {f}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {features.map((fA) => (
              <tr key={fA}>
                <td style={{ padding: '8px', border: '1px solid var(--border-primary)', fontWeight: 'bold', fontSize: '10px' }}>
                  {fA}
                </td>
                {features.map((fB) => {
                  const match = flat.find((item) => item.feature_a === fA && item.feature_b === fB);
                  const corrVal = match ? match.correlation : (fA === fB ? 1.0 : null);
                  return (
                    <td
                      key={fB}
                      style={{
                        padding: '12px',
                        border: '1px solid var(--border-primary)',
                        textAlign: 'center',
                        background: getHeatColor(corrVal),
                        color: Math.abs(corrVal || 0) > 0.4 ? '#fff' : 'var(--text-secondary)',
                        fontWeight: '600'
                      }}
                    >
                      {corrVal !== null ? corrVal.toFixed(2) : '—'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: '800' }}>🧬 Feature Selection & Analysis Lab</h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            Examine multicollinearity, drift patterns, statistical importance, and SHAP contributions of engine input scores.
          </p>
        </div>
        <button
          onClick={loadAnalysis}
          className="btn-primary"
          style={{ padding: '10px 16px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
          disabled={loading}
        >
          {loading ? 'Analyzing...' : '🔄 Run Full Feature Analysis'}
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
          <p style={{ color: 'var(--text-secondary)' }}>Computing VIF, Drift, SHAP, MI, and Permutation Importance values...</p>
        </div>
      ) : data ? (
        <div className="quant-lab-split-grid responsive-split-grid" style={{ display: 'grid', gridTemplateColumns: '250px 1fr', gap: '24px', alignItems: 'start' }}>
          {/* Menu */}
          <div className="card" style={{ padding: '16px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
            <h2 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '12px', letterSpacing: '0.5px' }}>
              Analysis Modules
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <button onClick={() => setActiveTab('vif')} className={`tab-btn-vertical ${activeTab === 'vif' ? 'active' : ''}`} style={{ textAlign: 'left', padding: '10px 12px', background: activeTab === 'vif' ? 'rgba(255,255,255,0.05)' : 'none', border: 'none', borderRadius: '6px', cursor: 'pointer', color: activeTab === 'vif' ? 'var(--accent-primary)' : 'var(--text-primary)', fontWeight: activeTab === 'vif' ? '600' : 'normal' }}>
                💥 Multicollinearity (VIF)
              </button>
              <button onClick={() => setActiveTab('importance')} className={`tab-btn-vertical ${activeTab === 'importance' ? 'active' : ''}`} style={{ textAlign: 'left', padding: '10px 12px', background: activeTab === 'importance' ? 'rgba(255,255,255,0.05)' : 'none', border: 'none', borderRadius: '6px', cursor: 'pointer', color: activeTab === 'importance' ? 'var(--accent-primary)' : 'var(--text-primary)', fontWeight: activeTab === 'importance' ? '600' : 'normal' }}>
                📊 Feature Importance & MI
              </button>
              <button onClick={() => setActiveTab('correlation')} className={`tab-btn-vertical ${activeTab === 'correlation' ? 'active' : ''}`} style={{ textAlign: 'left', padding: '10px 12px', background: activeTab === 'correlation' ? 'rgba(255,255,255,0.05)' : 'none', border: 'none', borderRadius: '6px', cursor: 'pointer', color: activeTab === 'correlation' ? 'var(--accent-primary)' : 'var(--text-primary)', fontWeight: activeTab === 'correlation' ? '600' : 'normal' }}>
                🔥 Pearson Correlation
              </button>
              <button onClick={() => setActiveTab('shap')} className={`tab-btn-vertical ${activeTab === 'shap' ? 'active' : ''}`} style={{ textAlign: 'left', padding: '10px 12px', background: activeTab === 'shap' ? 'rgba(255,255,255,0.05)' : 'none', border: 'none', borderRadius: '6px', cursor: 'pointer', color: activeTab === 'shap' ? 'var(--accent-primary)' : 'var(--text-primary)', fontWeight: activeTab === 'shap' ? '600' : 'normal' }}>
                ⚖️ Linear SHAP Proxy
              </button>
              <button onClick={() => setActiveTab('drift')} className={`tab-btn-vertical ${activeTab === 'drift' ? 'active' : ''}`} style={{ textAlign: 'left', padding: '10px 12px', background: activeTab === 'drift' ? 'rgba(255,255,255,0.05)' : 'none', border: 'none', borderRadius: '6px', cursor: 'pointer', color: activeTab === 'drift' ? 'var(--accent-primary)' : 'var(--text-primary)', fontWeight: activeTab === 'drift' ? '600' : 'normal' }}>
                🌊 Score Drift Tracking
              </button>
              <button onClick={() => setActiveTab('redundancy')} className={`tab-btn-vertical ${activeTab === 'redundancy' ? 'active' : ''}`} style={{ textAlign: 'left', padding: '10px 12px', background: activeTab === 'redundancy' ? 'rgba(255,255,255,0.05)' : 'none', border: 'none', borderRadius: '6px', cursor: 'pointer', color: activeTab === 'redundancy' ? 'var(--accent-primary)' : 'var(--text-primary)', fontWeight: activeTab === 'redundancy' ? '600' : 'normal' }}>
                👥 Redundancy & Stability
              </button>
            </div>
          </div>

          {/* Results Content */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            
            {activeTab === 'vif' && (
              <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '8px' }}>Variance Inflation Factor (VIF)</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '16px' }}>
                  VIF estimates the severity of multicollinearity in OLS regression. VIF &gt; 5 indicates moderate multicollinearity, VIF &gt; 10 suggests high redundancy where features can be fully predicted from other features.
                </p>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table" style={{ width: '100%' }}>
                    <thead>
                      <tr>
                        <th>Feature Score</th>
                        <th>VIF Score</th>
                        <th>Multicollinearity Risk</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.vif?.vif?.map((v) => (
                        <tr key={v.feature}>
                          <td><strong>{v.feature}</strong></td>
                          <td>{v.vif !== null ? v.vif.toFixed(2) : '—'}</td>
                          <td>
                            <span style={{
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: '600',
                              background: v.risk === 'High' ? 'rgba(239,68,68,0.1)' : (v.risk === 'Moderate' ? 'rgba(245,158,11,0.1)' : 'rgba(16,185,129,0.1)'),
                              color: v.risk === 'High' ? '#ef4444' : (v.risk === 'Moderate' ? '#f59e0b' : '#10b981')
                            }}>
                              {v.risk}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'importance' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Mutual Information (Non-Linear Association)</h3>
                  <ChartPanel charts={getMIChart()} />
                </div>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Permutation Importance (Score Drop test)</h3>
                  <ChartPanel charts={getImportanceChart()} />
                </div>
              </div>
            )}

            {activeTab === 'correlation' && (
              <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '8px' }}>Pearson Correlation Matrix Heatmap</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '16px' }}>
                  Identifies linear relationships between scores. Blue represents positive correlation, red represents negative correlation.
                </p>
                {renderCorrelationMatrix()}
              </div>
            )}

            {activeTab === 'shap' && (
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Linear SHAP Proxy</h3>
                <ChartPanel charts={getShapChart()} />
                <p style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '12px', fontStyle: 'italic' }}>
                  *SHAP values represent average marginal contribution of scores pushing the final Composite Score away from its universe mean.
                </p>
              </div>
            )}

            {activeTab === 'drift' && (
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Feature Drift Over Historical Analysis Months</h3>
                <ChartPanel charts={getDriftCharts()} />
              </div>
            )}

            {activeTab === 'redundancy' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Feature Redundancy Groups</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '16px' }}>
                    Clustered variables where absolute Pearson correlation exceeds <strong>{data.redundancy?.threshold || 0.85}</strong>. High correlation suggests one score can substitute another.
                  </p>
                  {data.redundancy?.groups?.length === 0 ? (
                    <div style={{ color: '#10b981', fontSize: '13px', padding: '12px', border: '1px dashed rgba(16,185,129,0.3)', borderRadius: '6px', background: 'rgba(16,185,129,0.05)' }}>
                      ✅ No redundant feature clusters detected above the threshold. All variables carry distinct information.
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {data.redundancy?.groups?.map((g, idx) => (
                        <div key={idx} style={{ padding: '12px', border: '1px solid var(--border-primary)', borderRadius: '6px', background: 'rgba(255,255,255,0.01)' }}>
                          <span style={{ fontSize: '13px', fontWeight: '600', color: '#f59e0b' }}>Redundant Group #{idx + 1}</span>
                          <div style={{ marginTop: '6px', fontSize: '13px' }}>
                            Features: <strong>{g.features.join(', ')}</strong>
                          </div>
                          <div style={{ marginTop: '4px', fontSize: '12px', color: 'var(--text-muted)' }}>
                            Max Absolute Correlation: <strong>{g.max_correlation.toFixed(4)}</strong>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Feature Stability Metrics</h3>
                  <div style={{ overflowX: 'auto' }}>
                    <table className="data-table" style={{ width: '100%' }}>
                      <thead>
                        <tr>
                          <th>Feature</th>
                          <th style={{ textAlign: 'center' }}>Mean</th>
                          <th style={{ textAlign: 'center' }}>Std Dev</th>
                          <th style={{ textAlign: 'center' }}>Min</th>
                          <th style={{ textAlign: 'center' }}>Max</th>
                          <th style={{ textAlign: 'center' }}>Coeff. of Variation (CV)</th>
                          <th style={{ textAlign: 'center' }}>Stability Class</th>
                          <th style={{ textAlign: 'center' }}>Nulls</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.stability?.stability?.map((s) => (
                          <tr key={s.feature}>
                            <td><strong>{s.feature}</strong></td>
                            <td style={{ textAlign: 'center' }}>{s.mean.toFixed(2)}</td>
                            <td style={{ textAlign: 'center' }}>{s.std.toFixed(2)}</td>
                            <td style={{ textAlign: 'center' }}>{s.min.toFixed(2)}</td>
                            <td style={{ textAlign: 'center' }}>{s.max.toFixed(2)}</td>
                            <td style={{ textAlign: 'center' }}>{s.cv.toFixed(4)}</td>
                            <td style={{ textAlign: 'center' }}>
                              <span style={{
                                padding: '2px 8px',
                                borderRadius: '4px',
                                fontSize: '11px',
                                fontWeight: '600',
                                background: s.stability === 'High' ? 'rgba(16,185,129,0.1)' : (s.stability === 'Medium' ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)'),
                                color: s.stability === 'High' ? '#10b981' : (s.stability === 'Medium' ? '#f59e0b' : '#ef4444')
                              }}>
                                {s.stability}
                              </span>
                            </td>
                            <td style={{ textAlign: 'center' }}>{s.null_count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: '40px', textAlign: 'center', border: '1px dashed var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>No analysis computed yet.</p>
          <button onClick={loadAnalysis} className="btn-primary" style={{ padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}>
            Run Selection & Drift Analysis
          </button>
        </div>
      )}
    </div>
  );
}

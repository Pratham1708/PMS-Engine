import React, { useState } from 'react';
import { validateEngine, getEngineResult } from '../../api/labApi';
import useExperiment from './shared/useExperiment';
import ExperimentProgress from './shared/ExperimentProgress';
import MetricsGrid from './shared/MetricsGrid';
import ChartPanel from './shared/ChartPanel';

import LabWorkflowGuide from '../../components/common/LabWorkflowGuide';

export default function EngineValidationLab() {
  const [horizon, setHorizon] = useState('1M');
  const vHook = useExperiment(validateEngine, getEngineResult, getEngineResult);

  const handleValidate = () => {
    vHook.run({ horizon });
  };

  const getMonotonicityChart = () => {
    if (!vHook.result?.rating_monotonicity_chart) return [];
    return [
      {
        key: 'monotonicity',
        title: 'Rating Monotonicity (Forward Returns by Rating)',
        type: 'bar',
        data: vHook.result.rating_monotonicity_chart,
        xKey: 'rating',
        yKeys: 'avg_return',
        colors: ['#3b82f6'],
      }
    ];
  };

  const getDistributionCharts = () => {
    if (!vHook.result?.score_distributions) return [];
    
    return Object.entries(vHook.result.score_distributions).map(([scoreCol, dist]) => {
      return {
        key: `${scoreCol}_dist`,
        title: `${scoreCol.replace(/([A-Z])/g, ' $1').trim()}`,
        type: 'bar',
        data: dist.histogram || [],
        xKey: 'label',
        yKeys: 'count',
        colors: ['#6366f1'],
      };
    });
  };

  const scoreColumns = [
    'TechnicalScore',
    'FundamentalScore',
    'MLScore',
    'GRUScore',
    'ReliabilityScore',
    'CompositeScoreV2',
    'Confidence',
  ];

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>🧪 Scoring Engine Validation Laboratory</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Assess the predictive power and accuracy of individual score pipelines relative to subsequent returns.
        </p>
      </div>

      <LabWorkflowGuide
        title="Engine Score Validation"
        description="Audit predictive rank correlation (IC, Rank IC) and score distribution histograms for Technical, Fundamental, and Composite scores."
        icon="🧪"
        steps={[
          { title: '1. Choose Horizon', desc: 'Select forward return window (1M).' },
          { title: '2. Execute Validation', desc: 'Click Validate Engine Predictive Power to run scoring audit.' },
          { title: '3. Review Deciles', desc: 'Inspect score decile return monotonicity and Information Coefficient.' },
          { title: '4. Check Score Distributions', desc: 'Review histograms across Technical, Fundamental, ML, and Composite scores.' }
        ]}
      />

      <div style={{
        display: 'grid',
        gridTemplateColumns: '300px 1fr',
        gap: '24px',
        alignItems: 'start'
      }}>
        {/* Settings Card */}
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px' }}>
            Settings
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Forward Returns Horizon</label>
              <select
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={horizon}
                onChange={(e) => setHorizon(e.target.value)}
              >
                <option value="1M">1 Month (21 trading days)</option>
                <option value="3M">3 Months (63 trading days)</option>
                <option value="6M">6 Months (126 trading days)</option>
              </select>
            </div>
            <button onClick={handleValidate} className="btn-primary" style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}>
              ▶ Validate Scoring Engine
            </button>
          </div>
        </div>

        {/* Results view */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <ExperimentProgress
            status={vHook.status}
            elapsedTime={vHook.elapsedTime}
            error={vHook.error}
            onReset={vHook.reset}
          />

          {vHook.status === 'complete' && vHook.result && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
              
              {/* Score Validation Cards */}
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Scoring Pipeline Accuracies</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
                  {scoreColumns.map((scoreCol) => {
                    const validation = vHook.result.score_validations?.[scoreCol] || {};
                    return (
                      <div key={scoreCol} className="card" style={{
                        padding: '16px',
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border-primary)',
                        borderRadius: 'var(--radius-md)',
                        position: 'relative'
                      }}>
                        <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '12px', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '6px' }}>
                          {scoreCol.replace(/([A-Z])/g, ' $1').trim()}
                        </h4>
                        
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Information Coefficient:</span>
                            <span style={{ fontWeight: '700', fontFamily: 'monospace', color: validation.significant ? '#10b981' : '#f59e0b' }}>
                              {validation.ic !== null ? validation.ic.toFixed(4) : 'N/A'}
                            </span>
                          </div>
                          
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Hit Rate (Sign Agreement):</span>
                            <span style={{ fontWeight: '700', fontFamily: 'monospace' }}>
                              {validation.hit_rate !== null ? `${(validation.hit_rate * 100).toFixed(1)}%` : 'N/A'}
                            </span>
                          </div>

                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>t-statistic:</span>
                            <span style={{ fontWeight: '700', fontFamily: 'monospace' }}>
                              {validation.t_stat !== null ? validation.t_stat.toFixed(3) : 'N/A'}
                            </span>
                          </div>

                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Quartile Return Spread:</span>
                            <span style={{ fontWeight: '700', fontFamily: 'monospace', color: '#3b82f6' }}>
                              {validation.quartile_spread !== null ? `${(validation.quartile_spread * 100).toFixed(2)}%` : 'N/A'}
                            </span>
                          </div>
                        </div>

                        {validation.significant && (
                          <span style={{
                            position: 'absolute',
                            top: '12px',
                            right: '16px',
                            fontSize: '9px',
                            fontWeight: '800',
                            padding: '2px 6px',
                            background: 'rgba(16,185,129,0.12)',
                            color: '#10b981',
                            border: '1px solid rgba(16,185,129,0.3)',
                            borderRadius: '4px',
                            textTransform: 'uppercase'
                          }}>
                            Significant
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Rating Monotonicity Section */}
              {vHook.result.rating_monotonicity_chart?.length > 0 && (
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Final Rating Monotonicity Check</h3>
                  <div style={{ marginBottom: '12px' }}>
                    {vHook.result.score_validations?.FinalRating?.monotonicity ? (
                      <div className="lab-research-warning" style={{ background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.3)', color: '#10b981' }}>
                        <span>✓</span>
                        <div>
                          <strong>Monotonicity Holds:</strong> Realized returns follow a strict downward trajectory relative to risk levels (STRONG BUY &gt; BUY &gt; HOLD &gt; SELL &gt; STRONG SELL). Monotonicity validation is successful.
                        </div>
                      </div>
                    ) : (
                      <div className="lab-research-warning">
                        <span>⚠</span>
                        <div>
                          <strong>Monotonicity Deficit:</strong> The realized returns do not perfectly align in descending order across the rating hierarchy. Audit parameters or check for score weight overrides.
                        </div>
                      </div>
                    )}
                  </div>
                  <ChartPanel charts={getMonotonicityChart()} />
                </div>
              )}

              {/* Distribution Charts */}
              {Object.keys(vHook.result.score_distributions || {}).length > 0 && (
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Score Histograms (Universe Distributions)</h3>
                  <ChartPanel charts={getDistributionCharts()} />
                </div>
              )}

            </div>
          )}
        </div>
      </div>
    </div>
  );
}


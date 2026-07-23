import React, { useState } from 'react';
import { compareModels, getModelResult } from '../../api/labApi';
import useExperiment from './shared/useExperiment';
import ExperimentProgress from './shared/ExperimentProgress';
import MetricsGrid from './shared/MetricsGrid';
import ChartPanel from './shared/ChartPanel';

import LabWorkflowGuide from '../../components/common/LabWorkflowGuide';

export default function ModelLab() {
  const [horizonBars, setHorizonBars] = useState(21);
  const mHook = useExperiment(compareModels, getModelResult, getModelResult);

  const handleCompare = () => {
    mHook.run({ horizon_bars: horizonBars });
  };

  const getCalibrationCharts = () => {
    if (!mHook.result?.details) return [];
    
    return Object.entries(mHook.result.details).map(([mname, mdetails]) => {
      const chartData = mdetails.charts?.calibration || [];
      return {
        key: `${mname}_calibration`,
        title: `${mname.toUpperCase()} Calibration`,
        type: 'line',
        data: chartData,
        xKey: 'predicted_prob',
        yKeys: ['actual_freq', 'perfect'],
        colors: ['#3b82f6', '#475569'],
      };
    });
  };

  const getStabilityCharts = () => {
    if (!mHook.result?.details) return [];
    
    // Compile monthly stability into a single line chart with multiple series
    const allTrends = [];
    const models = Object.keys(mHook.result.details);
    const monthsSet = new Set();
    
    // Gather all unique months
    models.forEach((m) => {
      const trend = mHook.result.details[m].charts?.stability || [];
      trend.forEach((t) => {
        if (t.month) monthsSet.add(t.month);
      });
    });

    Array.from(monthsSet).sort().forEach((month) => {
      const row = { month };
      models.forEach((m) => {
        const trend = mHook.result.details[m].charts?.stability || [];
        const match = trend.find((t) => t.month === month);
        row[m] = match ? match.ic : 0.0;
      });
      allTrends.push(row);
    });

    return [
      {
        key: 'model_stability',
        title: 'Rolling Monthly Information Coefficient (IC) Stability',
        type: 'line',
        data: allTrends,
        xKey: 'month',
        yKeys: models,
        colors: ['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'],
      }
    ];
  };

  const getRegimePerformanceCharts = () => {
    if (!mHook.result?.details) return [];
    
    // Compile regime performance comparison
    const models = Object.keys(mHook.result.details);
    const regimeData = [];
    const regimesSet = new Set();

    models.forEach((m) => {
      const reg = mHook.result.details[m].charts?.regime_performance || [];
      reg.forEach((r) => {
        if (r.regime) regimesSet.add(r.regime);
      });
    });

    Array.from(regimesSet).forEach((regime) => {
      const row = { regime };
      models.forEach((m) => {
        const reg = mHook.result.details[m].charts?.regime_performance || [];
        const match = reg.find((r) => r.regime === regime);
        row[m] = match ? match.ic : 0.0;
      });
      regimeData.push(row);
    });

    return [
      {
        key: 'regime_perf',
        title: 'Model Rank Correlation (IC) by Market Regime',
        type: 'bar',
        data: regimeData,
        xKey: 'regime',
        yKeys: models,
        colors: ['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'],
      }
    ];
  };

  const getImportanceChart = () => {
    if (!mHook.result?.feature_importance_chart) return [];
    return [
      {
        key: 'importance',
        title: 'Permutation Feature Importance Ranks',
        type: 'bar',
        data: mHook.result.feature_importance_chart,
        xKey: 'feature',
        yKeys: 'importance',
        colors: ['#8b5cf6'],
      }
    ];
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>🤖 Model Comparison Lab</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Evaluate XGBoost, LightGBM, Random Forest, and Ridge for calibration quality, IC stability, and SHAP importances.
        </p>
      </div>

      <LabWorkflowGuide
        title="Model Research Lab"
        description="Compare ML model calibration, rolling IC stability, and feature importances across prediction horizons."
        icon="🤖"
        steps={[
          { title: '1. Select Prediction Horizon', desc: 'Choose target horizon in trading bars (default 21 bars / 1 Month).' },
          { title: '2. Run Model Comparison', desc: 'Click Run Side-by-Side Model Comparison to launch multi-model evaluation.' },
          { title: '3. Compare Metrics', desc: 'Compare Information Coefficient (IC), Hit Rate, and T-Stats across models.' },
          { title: '4. Inspect Calibration', desc: 'Verify model predicted probabilities match actual positive return frequencies.' }
        ]}
      />

      <div className="quant-lab-split-grid">
        {/* Settings */}
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px' }}>
            Settings
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Forward Horizon (Trading Bars)</label>
              <input
                type="number"
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={horizonBars}
                onChange={(e) => setHorizonBars(parseInt(e.target.value) || 21)}
              />
            </div>
            <button onClick={handleCompare} className="btn-primary" style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}>
              ▶ Compare All Models
            </button>
          </div>
        </div>

        {/* Outputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <ExperimentProgress
            status={mHook.status}
            elapsedTime={mHook.elapsedTime}
            error={mHook.error}
            onReset={mHook.reset}
          />

          {mHook.status === 'complete' && mHook.result && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
              
              {/* Models Matrix Table */}
              <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Model Comparison Matrix</h3>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table" style={{ width: '100%' }}>
                    <thead>
                      <tr>
                        <th>Model Label</th>
                        <th>Category</th>
                        <th style={{ textAlign: 'center' }}>Rank IC</th>
                        <th style={{ textAlign: 'center' }}>Hit Rate</th>
                        <th style={{ textAlign: 'center' }}>t-stat</th>
                        <th style={{ textAlign: 'center' }}>Significant</th>
                        <th style={{ textAlign: 'center' }}>Mean Score</th>
                        <th style={{ textAlign: 'center' }}>Score Std</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.values(mHook.result.comparison?.models || {}).map((m) => (
                        <tr key={m.model}>
                          <td><strong>{m.label}</strong></td>
                          <td>{m.category}</td>
                          <td style={{ textAlign: 'center', fontWeight: '700', color: m.significant ? '#10b981' : '#f59e0b' }}>
                            {m.ic !== null ? m.ic.toFixed(4) : 'N/A'}
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            {m.hit_rate !== null ? `${(m.hit_rate * 100).toFixed(1)}%` : 'N/A'}
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            {m.t_stat !== null ? m.t_stat.toFixed(2) : '—'}
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            {m.significant ? 'Yes' : 'No'}
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            {m.score_mean !== null ? m.score_mean.toFixed(2) : '—'}
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            {m.score_std !== null ? m.score_std.toFixed(2) : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Stability Tab */}
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Rolling Stability over Historical Analyses</h3>
                <ChartPanel charts={getStabilityCharts()} />
              </div>

              {/* Regime performance comparison */}
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Performance under Market Regimes</h3>
                <ChartPanel charts={getRegimePerformanceCharts()} />
              </div>

              {/* Permutation feature importance */}
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Permutation Feature Importance</h3>
                <ChartPanel charts={getImportanceChart()} />
              </div>

              {/* Calibration Diagrams */}
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Model Calibration diagram (Reliability Diagrams)</h3>
                <ChartPanel charts={getCalibrationCharts()} />
              </div>

            </div>
          )}
        </div>
      </div>
    </div>
  );
}


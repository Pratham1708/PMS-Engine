import { useState, useEffect } from 'react';
import { fetchScannerSummary } from '../api/stocks';
import StatCard from '../components/common/StatCard';
import LoadingSpinner from '../components/common/LoadingSpinner';

const PIPELINE_STEPS = [
  { title: 'Data Collection', desc: 'Historical OHLCV data for Nifty 50 via Yahoo Finance' },
  { title: 'Feature Engineering', desc: 'EMA20/50/200, RSI14, MACD, MACD_HIST, relative features' },
  { title: 'Technical Engine', desc: 'TechnicalScore from -100 to +100 based on trend + momentum' },
  { title: 'Random Forest', desc: '500-tree classifier with balanced class weights' },
  { title: 'XGBoost', desc: 'Gradient boosting with sample weight balancing' },
  { title: 'LightGBM', desc: '700-estimator model with leaf-wise growth' },
  { title: 'GRU Deep Learning', desc: '30-day sequences → HOLD / LONG / SHORT probabilities' },
  { title: 'HybridMLScore', desc: '60% Ensemble ML + 40% GRU Score blending' },
  { title: 'CompositeScoreV2', desc: '35% Technical + 30% HybridML + 20% ExpReturn + 15% Reliability' },
  { title: 'Rating Engine', desc: 'Quantile-based: P90→STRONG BUY, P70→BUY, P30→SELL, P10→STRONG SELL' },
  { title: 'Confidence Engine', desc: 'abs(CompositeScore) capped at 100' },
  { title: 'Portfolio Construction', desc: 'Conviction-weighted allocation for STRONG BUY + BUY' },
];

const MODELS = [
  { name: 'Random Forest', file: 'rf_5class.pkl', details: '500 trees, max_depth=12, balanced weights' },
  { name: 'XGBoost', file: 'xgb_5class.pkl', details: 'Gradient boosted trees, sample-weighted' },
  { name: 'LightGBM', file: 'lgbm_5class.pkl', details: '700 estimators, lr=0.03, 63 leaves' },
  { name: 'GRU Network', file: 'best_gru.keras', details: 'GRU(128)→GRU(64)→Dense(32)→Dense(3), 30-step sequences' },
];

const SCORE_RANGES = [
  { name: 'TechnicalScore', range: '-100 to +100', desc: 'Trend + momentum analysis' },
  { name: 'MLScore', range: '-100 to +100', desc: 'LONG_prob - SHORT_prob from ensemble' },
  { name: 'GRUScore', range: '-100 to +100', desc: 'LONG_prob*100 - SHORT_prob*100' },
  { name: 'CompositeScoreV2', range: 'Weighted sum', desc: 'Multi-factor composite' },
  { name: 'ReliabilityScore', range: '50 to 80', desc: 'Win-rate based reliability' },
  { name: 'Confidence', range: '0 to 100', desc: 'abs(Composite), capped' },
];

export default function SystemOverview() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchScannerSummary()
      .then((res) => setSummary(res.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="fade-in">
      {/* Universe Stats */}
      {summary && (
        <div className="stats-grid page-section">
          <StatCard label="Universe" value="Nifty 50" sub={`${summary.total_stocks} stocks`} />
          <StatCard label="Avg Technical" value={summary.avg_technical.toFixed(2)} />
          <StatCard label="Avg ML Score" value={summary.avg_ml.toFixed(2)} />
          <StatCard label="Avg GRU Score" value={summary.avg_gru.toFixed(2)} />
          <StatCard label="Avg Reliability" value={summary.avg_reliability.toFixed(0)} />
        </div>
      )}

      {/* Pipeline */}
      <div className="page-section">
        <div className="section-header">
          <h2 className="section-title">Scoring Pipeline</h2>
        </div>
        {PIPELINE_STEPS.map((step, i) => (
          <div key={i}>
            <div className="pipeline-step">
              <div className="pipeline-step-number">{i + 1}</div>
              <div className="pipeline-step-content">
                <h4>{step.title}</h4>
                <p>{step.desc}</p>
              </div>
            </div>
            {i < PIPELINE_STEPS.length - 1 && (
              <div className="pipeline-arrow">↓</div>
            )}
          </div>
        ))}
      </div>

      {/* Models */}
      <div className="page-section">
        <div className="section-header">
          <h2 className="section-title">Trained Models</h2>
        </div>
        <div className="info-grid">
          {MODELS.map((m) => (
            <div key={m.name} className="info-item">
              <div className="info-item-label">{m.name}</div>
              <div className="info-item-value" style={{ fontSize: '14px', marginBottom: '4px' }}>
                {m.file}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                {m.details}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Score Ranges */}
      <div className="page-section">
        <div className="section-header">
          <h2 className="section-title">Scoring Dimensions</h2>
        </div>
        <div className="card table-container" style={{ padding: 0 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Score</th>
                <th>Range</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {SCORE_RANGES.map((s) => (
                <tr key={s.name} style={{ cursor: 'default' }}>
                  <td><span className="symbol">{s.name}</span></td>
                  <td style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>{s.range}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>{s.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Version Info */}
      <div className="card page-section">
        <div className="card-title">System Info</div>
        <div className="info-grid">
          <div className="info-item">
            <div className="info-item-label">Version</div>
            <div className="info-item-value">1.0.0</div>
          </div>
          <div className="info-item">
            <div className="info-item-label">Phase</div>
            <div className="info-item-value">Phase 11 — Production</div>
          </div>
          <div className="info-item">
            <div className="info-item-label">Data Source</div>
            <div className="info-item-value" style={{ fontSize: '13px' }}>final_institutional_scanner.csv</div>
          </div>
          <div className="info-item">
            <div className="info-item-label">Author</div>
            <div className="info-item-value">Pratham Jindal</div>
          </div>
        </div>
      </div>
    </div>
  );
}

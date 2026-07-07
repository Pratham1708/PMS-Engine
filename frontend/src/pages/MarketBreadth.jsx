import { useState, useEffect } from 'react';
import { fetchLatestBreadth, fetchSnapshotStatus } from '../api/stocks';
import LoadingSpinner from '../components/common/LoadingSpinner';

const REGIME_CONFIG = {
  Bullish: { color: '#10b981', bg: 'rgba(16,185,129,0.12)', icon: '📈' },
  Bearish: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)',  icon: '📉' },
  Mixed:   { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', icon: '🔀' },
  Neutral: { color: '#6b7280', bg: 'rgba(107,114,128,0.1)', icon: '➡️' },
};

export default function MarketBreadth() {
  const [breadth, setBreadth] = useState(null);
  const [snapshotDate, setSnapshotDate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [breadthRes, statusRes] = await Promise.all([
          fetchLatestBreadth(),
          fetchSnapshotStatus(),
        ]);
        setBreadth(breadthRes.data);
        setSnapshotDate(statusRes.data?.latest_snapshot?.snapshot_date);
      } catch (err) {
        setError('No snapshot market breadth data available. Generate a snapshot first.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="page-error">{error}</div>;
  if (!breadth) return <div className="page-empty">No market breadth data found.</div>;

  const regime = REGIME_CONFIG[breadth.market_regime] || REGIME_CONFIG.Neutral;
  const total = breadth.total_stocks || 1;
  const advPct = (breadth.advancing_stocks / total) * 100;
  const decPct = (breadth.declining_stocks / total) * 100;
  const uncPct = (breadth.unchanged_stocks / total) * 100;

  const totalVol = (breadth.advance_volume || 0) + (breadth.decline_volume || 0) || 1;
  const advVolPct = ((breadth.advance_volume || 0) / totalVol) * 100;
  const decVolPct = ((breadth.decline_volume || 0) / totalVol) * 100;

  return (
    <div className="breadth-page">
      <div className="breadth-header">
        <h1 className="breadth-title">📈 Market Breadth Indicators</h1>
        {snapshotDate && <span className="breadth-date">Snapshot Date: {snapshotDate}</span>}
        <p className="breadth-subtitle">
          Universe-wide technical health, trend participation, and institutional regime classification.
        </p>
      </div>

      <div className="breadth-grid-top">
        {/* Market Regime Card */}
        <div className="breadth-card regime-card" style={{ '--accent-color': regime.color, backgroundColor: regime.bg }}>
          <div className="regime-icon">{regime.icon}</div>
          <div className="regime-value">{breadth.market_regime}</div>
          <div className="regime-label">Classified Market Regime</div>
          <div className="regime-desc">
            Based on stock advancing/declining ratios and score distributions across all 50 index constituents.
          </div>
        </div>

        {/* Core Breadth Stats */}
        <div className="breadth-card stats-card">
          <h3>Advance / Decline Ratio</h3>
          <div className="ad-ratio-value">{breadth.advance_decline_ratio?.toFixed(2) || '—'}</div>
          <div className="ad-bar">
            <div className="ad-bar-fill ad-bar-fill--adv" style={{ width: `${advPct}%` }} title={`Advancing: ${breadth.advancing_stocks}`} />
            <div className="ad-bar-fill ad-bar-fill--unc" style={{ width: `${uncPct}%` }} title={`Unchanged: ${breadth.unchanged_stocks}`} />
            <div className="ad-bar-fill ad-bar-fill--dec" style={{ width: `${decPct}%` }} title={`Declining: ${breadth.declining_stocks}`} />
          </div>
          <div className="ad-legend">
            <span className="legend-item text-green">🟢 {breadth.advancing_stocks} Advancing ({advPct.toFixed(0)}%)</span>
            <span className="legend-item text-gray">⚪ {breadth.unchanged_stocks} Unchanged ({uncPct.toFixed(0)}%)</span>
            <span className="legend-item text-red">🔴 {breadth.declining_stocks} Declining ({decPct.toFixed(0)}%)</span>
          </div>
        </div>

        {/* Volume Breadth */}
        <div className="breadth-card stats-card">
          <h3>Advance / Decline Volume</h3>
          <div className="vol-bar">
            <div className="ad-bar-fill ad-bar-fill--adv" style={{ width: `${advVolPct}%` }} title={`Advance Volume: ${breadth.advance_volume}`} />
            <div className="ad-bar-fill ad-bar-fill--dec" style={{ width: `${decVolPct}%` }} title={`Decline Volume: ${breadth.decline_volume}`} />
          </div>
          <div className="ad-legend">
            <span className="legend-item text-green">🟢 Adv Vol: {(breadth.advance_volume / 1000000).toFixed(1)}M ({advVolPct.toFixed(0)}%)</span>
            <span className="legend-item text-red">🔴 Dec Vol: {(breadth.decline_volume / 1000000).toFixed(1)}M ({decVolPct.toFixed(0)}%)</span>
          </div>
        </div>
      </div>

      <div className="breadth-section-title">📊 Trend Participation (Moving Averages)</div>

      <div className="breadth-grid-bottom">
        {/* EMA 20 Card */}
        <div className="breadth-card ema-card">
          <div className="ema-title">Above 20 EMA (Short-term)</div>
          <div className="ema-value text-green">{breadth.pct_above_ema20?.toFixed(1)}%</div>
          <div className="ema-sub">{breadth.stocks_above_ema20} of {total} stocks trading above their 20-day exponential moving average.</div>
          <div className="ema-progress">
            <div className="ema-progress-fill bg-green" style={{ width: `${breadth.pct_above_ema20}%` }} />
          </div>
        </div>

        {/* EMA 50 Card */}
        <div className="breadth-card ema-card">
          <div className="ema-title">Above 50 EMA (Medium-term)</div>
          <div className="ema-value text-blue">{breadth.pct_above_ema50?.toFixed(1)}%</div>
          <div className="ema-sub">{breadth.stocks_above_ema50} of {total} stocks trading above their 50-day exponential moving average.</div>
          <div className="ema-progress">
            <div className="ema-progress-fill bg-blue" style={{ width: `${breadth.pct_above_ema50}%` }} />
          </div>
        </div>

        {/* EMA 200 Card */}
        <div className="breadth-card ema-card">
          <div className="ema-title">Above 200 EMA (Long-term)</div>
          <div className="ema-value text-purple">{breadth.pct_above_ema200?.toFixed(1)}%</div>
          <div className="ema-sub">{breadth.stocks_above_ema200} of {total} stocks trading above their 200-day exponential moving average.</div>
          <div className="ema-progress">
            <div className="ema-progress-fill bg-purple" style={{ width: `${breadth.pct_above_ema200}%` }} />
          </div>
        </div>
      </div>

      <div className="breadth-grid-mid">
        <div className="breadth-card stats-card">
          <h3>52-Week Extreme Levels</h3>
          <div className="extreme-grid">
            <div className="extreme-item">
              <span className="extreme-icon">🚀</span>
              <div className="extreme-val text-green">{breadth.week52_high_count || 0}</div>
              <div className="extreme-label">Near 52-Week High</div>
            </div>
            <div className="extreme-item">
              <span className="extreme-icon">⚠️</span>
              <div className="extreme-val text-red">{breadth.week52_low_count || 0}</div>
              <div className="extreme-label">Near 52-Week Low</div>
            </div>
          </div>
        </div>

        <div className="breadth-card stats-card">
          <h3>Composite & Momentum Averages</h3>
          <div className="extreme-grid">
            <div className="extreme-item">
              <div className="extreme-val text-purple">{breadth.avg_composite?.toFixed(1) || '—'}</div>
              <div className="extreme-label">Avg Composite Score</div>
            </div>
            <div className="extreme-item">
              <div className="extreme-val text-blue">{breadth.avg_momentum?.toFixed(1) || '—'}</div>
              <div className="extreme-label">Avg Momentum Score</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

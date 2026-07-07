import { useState, useEffect } from 'react';
import { fetchLatestSectors, fetchSnapshotStatus } from '../api/stocks';
import LoadingSpinner from '../components/common/LoadingSpinner';

const RATING_COLORS = {
  'STRONG BUY': '#10b981',
  'BUY':        '#3b82f6',
  'HOLD':       '#f59e0b',
  'SELL':       '#f97316',
  'STRONG SELL':'#ef4444',
};

export default function SectorSnapshot() {
  const [sectors, setSectors] = useState([]);
  const [snapshotDate, setSnapshotDate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [sectorRes, statusRes] = await Promise.all([
          fetchLatestSectors(),
          fetchSnapshotStatus(),
        ]);
        setSectors(sectorRes.data || []);
        setSnapshotDate(statusRes.data?.latest_snapshot?.snapshot_date);
      } catch (err) {
        setError('No snapshot sector data available. Generate a snapshot first.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="page-error">{error}</div>;
  if (!sectors.length) return <div className="page-empty">No sector data available.</div>;

  return (
    <div className="sectors-page">
      <div className="sectors-header">
        <h1 className="sectors-title">🏢 Sector Snapshot Averages</h1>
        {snapshotDate && <span className="sectors-date">Snapshot Date: {snapshotDate}</span>}
        <p className="sectors-subtitle">
          Aggregated quantitative scoring, rating distribution, and momentum rankings across market sectors.
        </p>
      </div>

      <div className="sectors-grid">
        {sectors.map((sec) => (
          <div key={sec.sector} className="sector-card">
            <div className="sector-card-header">
              <span className="sector-rank">Rank #{sec.sector_rank || '—'}</span>
              <h3 className="sector-name">{sec.sector}</h3>
            </div>
            
            <div className="sector-stats-grid">
              <div className="sec-stat-item">
                <span className="sec-stat-label">Composite</span>
                <span className="sec-stat-val text-purple">{sec.avg_composite?.toFixed(1) || '—'}</span>
              </div>
              <div className="sec-stat-item">
                <span className="sec-stat-label">Confidence</span>
                <span className="sec-stat-val text-yellow">{sec.avg_confidence?.toFixed(0) || '—'}%</span>
              </div>
              <div className="sec-stat-item">
                <span className="sec-stat-label">Technical</span>
                <span className="sec-stat-val text-green">{sec.avg_technical?.toFixed(1) || '—'}</span>
              </div>
              <div className="sec-stat-item">
                <span className="sec-stat-label">Momentum</span>
                <span className="sec-stat-val text-blue">{sec.avg_momentum?.toFixed(1) || '—'}</span>
              </div>
            </div>

            <div className="sector-rating-bar-wrap">
              <div className="sector-rating-bar-title">
                <span>Rating Distribution ({sec.stock_count} stocks)</span>
                <span className="text-green">{sec.bullish_pct?.toFixed(0)}% Bullish</span>
              </div>
              <div className="sector-rating-bar">
                {sec.strong_buy_count > 0 && <div className="sec-bar-seg" style={{ width: `${(sec.strong_buy_count / sec.stock_count) * 100}%`, background: RATING_COLORS['STRONG BUY'] }} title={`Strong Buy: ${sec.strong_buy_count}`} />}
                {sec.buy_count > 0 && <div className="sec-bar-seg" style={{ width: `${(sec.buy_count / sec.stock_count) * 100}%`, background: RATING_COLORS['BUY'] }} title={`Buy: ${sec.buy_count}`} />}
                {sec.hold_count > 0 && <div className="sec-bar-seg" style={{ width: `${(sec.hold_count / sec.stock_count) * 100}%`, background: RATING_COLORS['HOLD'] }} title={`Hold: ${sec.hold_count}`} />}
                {sec.sell_count > 0 && <div className="sec-bar-seg" style={{ width: `${(sec.sell_count / sec.stock_count) * 100}%`, background: RATING_COLORS['SELL'] }} title={`Sell: ${sec.sell_count}`} />}
                {sec.strong_sell_count > 0 && <div className="sec-bar-seg" style={{ width: `${(sec.strong_sell_count / sec.stock_count) * 100}%`, background: RATING_COLORS['STRONG SELL'] }} title={`Strong Sell: ${sec.strong_sell_count}`} />}
              </div>
            </div>

            <div className="sector-leaders">
              <div className="leader-row">
                <span className="leader-label">Top Leader:</span>
                <span className="leader-sym text-green">{sec.top_stock?.replace('.NS', '') || '—'}</span>
              </div>
              <div className="leader-row">
                <span className="leader-label">Weakest:</span>
                <span className="leader-sym text-red">{sec.weakest_stock?.replace('.NS', '') || '—'}</span>
              </div>
              {sec.avg_daily_chg_pct != null && (
                <div className="leader-row">
                  <span className="leader-label">Avg Return:</span>
                  <span className={`leader-val ${sec.avg_daily_chg_pct >= 0 ? 'text-green' : 'text-red'}`}>
                    {sec.avg_daily_chg_pct >= 0 ? '+' : ''}{sec.avg_daily_chg_pct.toFixed(2)}%
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

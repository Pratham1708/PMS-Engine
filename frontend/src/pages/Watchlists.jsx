import { useState, useEffect } from 'react';
import { fetchLatestWatchlists, fetchSnapshotStatus } from '../api/stocks';

const WATCHLIST_META = {
  top_opportunities: { icon: '⭐', desc: 'Highest composite score stocks rated BUY or better', accent: '#10b981' },
  high_conviction:   { icon: '💎', desc: 'Confidence ≥80% rated BUY or better', accent: '#3b82f6' },
  momentum:          { icon: '🚀', desc: 'Top momentum leaders by technical score', accent: '#8b5cf6' },
  quality:           { icon: '🏆', desc: 'High reliability and confidence stocks', accent: '#f59e0b' },
  breakout:          { icon: '📈', desc: 'Near 52-week highs with strong momentum', accent: '#06b6d4' },
  recovery:          { icon: '🔄', desc: 'Improving stocks showing recovery signals', accent: '#84cc16' },
  value:             { icon: '💰', desc: 'Strong fundamentals and high composite', accent: '#a855f7' },
  growth:            { icon: '🌱', desc: 'Strong ML growth signals', accent: '#22c55e' },
  turnaround:        { icon: '🔁', desc: 'Strong GRU reversal signals', accent: '#f97316' },
  undervalued:       { icon: '💡', desc: 'HOLD stocks with re-rating potential', accent: '#0ea5e9' },
  overvalued:        { icon: '⚠️', desc: 'Candidates for reduction', accent: '#ef4444' },
  low_risk:          { icon: '🛡️', desc: 'High confidence BUY+ stocks', accent: '#14b8a6' },
  high_risk:         { icon: '⚡', desc: 'High return potential, speculative', accent: '#fb923c' },
  swing_trades:      { icon: '🎯', desc: 'Short-term technical momentum plays', accent: '#e879f9' },
  long_term:         { icon: '🏗️', desc: 'Core portfolio holdings', accent: '#38bdf8' },
  dividend:          { icon: '💸', desc: 'Stable income-generating stocks', accent: '#34d399' },
};

export default function Watchlists() {
  const [watchlists, setWatchlists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState(null);
  const [error, setError] = useState(null);
  const [snapshotDate, setSnapshotDate] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [wlRes, statusRes] = await Promise.all([
          fetchLatestWatchlists(),
          fetchSnapshotStatus(),
        ]);
        setWatchlists(wlRes.data || []);
        setSnapshotDate(statusRes.data?.latest_snapshot?.snapshot_date);
        if (wlRes.data?.length > 0) setActive(wlRes.data[0].watchlist_name);
      } catch {
        setError('No snapshot data available. Generate a snapshot first.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <div className="page-loading">Loading watchlists…</div>;
  if (error) return <div className="page-error">{error}</div>;
  if (!watchlists.length) return (
    <div className="page-empty">
      <p>No watchlists available. Generate a snapshot to populate them.</p>
    </div>
  );

  const activeWl = watchlists.find(w => w.watchlist_name === active);

  return (
    <div className="wl-page">
      <div className="wl-header">
        <h1 className="wl-title">📋 Smart Watchlists</h1>
        {snapshotDate && <span className="wl-date">Snapshot: {snapshotDate}</span>}
        <p className="wl-subtitle">
          16 automatically curated watchlists from today's official research snapshot.
          Updated with every published snapshot.
        </p>
      </div>

      <div className="wl-layout">
        {/* Sidebar */}
        <div className="wl-sidebar">
          {watchlists.map(wl => {
            const meta = WATCHLIST_META[wl.watchlist_name] || { icon: '📋', accent: '#6b7280' };
            return (
              <button
                key={wl.watchlist_name}
                className={`wl-sidebar-item ${active === wl.watchlist_name ? 'wl-sidebar-item--active' : ''}`}
                style={{ '--accent': meta.accent }}
                onClick={() => setActive(wl.watchlist_name)}
              >
                <span className="wl-sidebar-icon">{meta.icon}</span>
                <span className="wl-sidebar-name">{wl.display_name}</span>
                <span className="wl-sidebar-count">{wl.stocks?.length || 0}</span>
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="wl-content">
          {activeWl && (() => {
            const meta = WATCHLIST_META[activeWl.watchlist_name] || { icon: '📋', desc: '', accent: '#3b82f6' };
            return (
              <>
                <div className="wl-content-header" style={{ '--accent': meta.accent }}>
                  <div className="wl-content-title-row">
                    <span className="wl-content-icon">{meta.icon}</span>
                    <h2 className="wl-content-title">{activeWl.display_name}</h2>
                  </div>
                  <p className="wl-content-desc">{activeWl.description || meta.desc}</p>
                </div>

                <div className="wl-cards-grid">
                  {activeWl.stocks?.length > 0 ? (
                    activeWl.stocks.map(stock => (
                      <div key={stock.symbol} className="wl-stock-card" style={{ '--accent': meta.accent }}>
                        <div className="wl-stock-rank">#{stock.rank_in_list}</div>
                        <div className="wl-stock-sym">{stock.symbol?.replace('.NS', '')}</div>
                        {stock.score_used != null && (
                          <div className="wl-stock-score">{stock.score_used.toFixed(1)}</div>
                        )}
                        {stock.reason && (
                          <div className="wl-stock-reason">{stock.reason}</div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="wl-empty-list">No stocks match this watchlist's criteria today.</div>
                  )}
                </div>
              </>
            );
          })()}
        </div>
      </div>
    </div>
  );
}

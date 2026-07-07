import { useState, useEffect } from 'react';
import { fetchLatestChanges, fetchSnapshotStatus } from '../api/stocks';
import LoadingSpinner from '../components/common/LoadingSpinner';

const RATING_COLORS = {
  'STRONG BUY': '#10b981',
  'BUY':        '#3b82f6',
  'HOLD':       '#f59e0b',
  'SELL':       '#f97316',
  'STRONG SELL':'#ef4444',
};

const CHANGE_LABELS = {
  UPGRADE:         { label: 'Rating Upgrade ⬆️', class: 'badge-pos' },
  DOWNGRADE:       { label: 'Rating Downgrade ⬇️', class: 'badge-neg' },
  NEW_BUY:         { label: 'New Buy Signal 🆕', class: 'badge-pos' },
  NEW_SELL:        { label: 'New Sell Signal 🔻', class: 'badge-neg' },
  COMPOSITE_UP:    { label: 'Composite Score Up ↑', class: 'badge-pos' },
  COMPOSITE_DOWN:  { label: 'Composite Score Down ↓', class: 'badge-neg' },
  CONFIDENCE_UP:   { label: 'Confidence Up ↑', class: 'badge-pos' },
  CONFIDENCE_DOWN: { label: 'Confidence Down ↓', class: 'badge-neg' },
};

export default function WhatsChanged() {
  const [changes, setChanges] = useState([]);
  const [snapshotDate, setSnapshotDate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [typeFilter, setTypeFilter] = useState('ALL');

  useEffect(() => {
    const load = async () => {
      try {
        const [changesRes, statusRes] = await Promise.all([
          fetchLatestChanges(typeFilter === 'ALL' ? null : typeFilter),
          fetchSnapshotStatus(),
        ]);
        setChanges(changesRes.data || []);
        setSnapshotDate(statusRes.data?.latest_snapshot?.snapshot_date);
      } catch (err) {
        setError('No snapshot comparison data available. Generate a snapshot first.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [typeFilter]);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="page-error">{error}</div>;

  return (
    <div className="changes-page">
      <div className="changes-header">
        <h1 className="changes-title">🔄 Daily Recommendation Changes</h1>
        {snapshotDate && <span className="changes-date">Snapshot Date: {snapshotDate}</span>}
        <p className="changes-subtitle">
          Track rating upgrades, downgrades, new signal entries, and score changes from the previous official session.
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="changes-filters">
        {['ALL', 'UPGRADE', 'DOWNGRADE', 'NEW_BUY', 'COMPOSITE_UP', 'COMPOSITE_DOWN'].map((f) => (
          <button
            key={f}
            className={`filter-tab-btn ${typeFilter === f ? 'filter-tab-btn--active' : ''}`}
            onClick={() => setTypeFilter(f)}
          >
            {f === 'ALL' ? 'All Changes' : f.replace('_', ' ').title || f}
          </button>
        ))}
      </div>

      {changes.length > 0 ? (
        <div className="changes-list-card">
          <table className="changes-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Change Type</th>
                <th>Previous Rating</th>
                <th>New Rating</th>
                <th className="num-col">Composite Diff</th>
                <th className="num-col">Confidence Diff</th>
                <th>Primary Driver</th>
                <th>Secondary Driver</th>
              </tr>
            </thead>
            <tbody>
              {changes.map((c) => {
                const badge = CHANGE_LABELS[c.change_type] || { label: c.change_type, class: 'badge-neutral' };
                return (
                  <tr key={c.symbol}>
                    <td className="change-sym"><strong>{c.symbol?.replace('.NS', '')}</strong></td>
                    <td>
                      <span className={`change-badge ${badge.class}`}>{badge.label}</span>
                    </td>
                    <td>
                      {c.prev_rating ? (
                        <span className="rating-mini-pill" style={{ background: RATING_COLORS[c.prev_rating] + '12', color: RATING_COLORS[c.prev_rating] }}>
                          {c.prev_rating}
                        </span>
                      ) : '—'}
                    </td>
                    <td>
                      <span className="rating-mini-pill" style={{ background: RATING_COLORS[c.new_rating] + '12', color: RATING_COLORS[c.new_rating] }}>
                        {c.new_rating}
                      </span>
                    </td>
                    <td className={`num-col ${c.composite_diff > 0 ? 'text-green' : c.composite_diff < 0 ? 'text-red' : ''}`}>
                      {c.composite_diff > 0 ? '+' : ''}{c.composite_diff?.toFixed(1) || '—'}
                    </td>
                    <td className={`num-col ${c.confidence_diff > 0 ? 'text-green' : c.confidence_diff < 0 ? 'text-red' : ''}`}>
                      {c.confidence_diff > 0 ? '+' : ''}{c.confidence_diff?.toFixed(0) || '0'}%
                    </td>
                    <td className="driver-cell">{c.primary_driver || '—'}</td>
                    <td className="driver-cell">{c.secondary_driver || '—'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="page-empty">No changes found matching the filter for today's snapshot.</div>
      )}
    </div>
  );
}

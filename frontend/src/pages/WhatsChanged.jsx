import { useState, useEffect } from 'react';
import { fetchCompareSnapshots, fetchSnapshotStatus } from '../api/stocks';
import LoadingSpinner from '../components/common/LoadingSpinner';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
  ReferenceLine,
  ComposedChart
} from 'recharts';

const RATING_COLORS = {
  'STRONG BUY': '#10b981',
  'BUY':        '#3b82f6',
  'HOLD':       '#f59e0b',
  'SELL':       '#f97316',
  'STRONG SELL':'#ef4444',
};

const TRANSITION_BADGES = {
  UPGRADE: { label: 'Upgrade ⬆️', class: 'badge-upgrade' },
  DOWNGRADE: { label: 'Downgrade ⬇️', class: 'badge-downgrade' },
  NEW_BUY: { label: 'New Buy Signal 🆕', class: 'badge-new-buy' },
  NEW_SELL: { label: 'New Sell Signal 🔻', class: 'badge-new-sell' },
  NEW_IN_UNIVERSE: { label: 'New Listing 🌐', class: 'badge-new-universe' },
  UNCHANGED: { label: 'Unchanged ➡️', class: 'badge-unchanged' }
};

export default function WhatsChanged() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('ALL'); // 'ALL' | 'UPGRADES' | 'DOWNGRADES' | 'UNCHANGED'

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Load compare snapshots for previous vs latest official snapshot
      const res = await fetchCompareSnapshots('previous', 'latest');
      setData(res.data);
    } catch (err) {
      console.error('Failed to load recommendation changes data:', err);
      setError(
        err.response?.data?.detail || 
        'No snapshot comparison data available. Ensure at least two snapshots exist in the registry.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) {
    return (
      <div className="page-error-container" style={{ padding: '40px', textAlign: 'center' }}>
        <div className="compare-error-alert" style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', padding: '16px', borderRadius: '8px', maxWidth: '600px', margin: '0 auto' }}>
          <h4>⚠️ Historical Intelligence Unavailable</h4>
          <p style={{ marginTop: '8px', fontSize: '14px' }}>{error}</p>
          <button onClick={loadData} className="compare-submit-btn" style={{ marginTop: '16px', padding: '8px 16px', cursor: 'pointer' }}>
            Retry Load
          </button>
        </div>
      </div>
    );
  }

  const { comparison_metadata, portfolio_summary, sector_summary, recommendation_summary, stock_deltas, visualizations } = data;

  // Filter stock deltas based on selected tab
  const filteredDeltas = stock_deltas.filter(sd => {
    if (activeTab === 'ALL') return true;
    if (activeTab === 'UPGRADES') return sd.transition_type === 'UPGRADE' || sd.transition_type === 'NEW_BUY';
    if (activeTab === 'DOWNGRADES') return sd.transition_type === 'DOWNGRADE' || sd.transition_type === 'NEW_SELL';
    if (activeTab === 'UNCHANGED') return sd.transition_type === 'UNCHANGED';
    return true;
  });

  // Export report payload as JSON
  const handleExport = () => {
    const jsonStr = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(data, null, 2))}`;
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute('href', jsonStr);
    dlAnchor.setAttribute('download', `recommendation_changes_${comparison_metadata.date1}_vs_${comparison_metadata.date2}.json`);
    document.body.appendChild(dlAnchor);
    dlAnchor.click();
    dlAnchor.remove();
  };

  return (
    <div className="changes-page" style={{ padding: '24px', color: '#f9fafb', background: '#0a0e17' }}>
      
      {/* Mismatch Warning Banner */}
      {comparison_metadata.version_warnings && comparison_metadata.version_warnings.length > 0 && (
        <div className="warning-banner" style={{ background: 'rgba(245, 158, 11, 0.15)', border: '1px solid #f59e0b', borderRadius: '8px', padding: '12px 16px', marginBottom: '24px', fontSize: '13px', color: '#fbe5c9' }}>
          <strong>⚠️ Warning: Snapshot Pipeline Version Mismatch Detected</strong>
          <ul style={{ marginLeft: '20px', marginTop: '6px' }}>
            {comparison_metadata.version_warnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
          <span style={{ fontSize: '11px', display: 'block', marginTop: '8px', color: '#f59e0b' }}>
            Score differences might reflect formula updates rather than pure market adjustments.
          </span>
        </div>
      )}

      {/* Page Header */}
      <div className="changes-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px' }}>
        <div>
          <h1 className="changes-title" style={{ fontSize: '28px', fontWeight: '800', letterSpacing: '-0.5px' }}>
            🔄 Recommendation Change Intelligence
          </h1>
          <p className="changes-subtitle" style={{ color: '#9ca3af', marginTop: '4px' }}>
            Daily rating movements, delta tracking, and structured explanation drivers.
          </p>
          <div style={{ display: 'inline-flex', alignItems: 'center', background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.2)', padding: '6px 12px', borderRadius: '20px', fontSize: '13px', color: '#a5b4fc', marginTop: '12px', fontWeight: '500' }}>
            📅 Session: {comparison_metadata.date1} ➡️ {comparison_metadata.date2} (Official Runs)
          </div>
        </div>
        <button 
          onClick={handleExport}
          className="btn-action"
          style={{ background: 'rgba(31, 41, 55, 0.8)', border: '1px solid rgba(55, 65, 81, 0.8)', color: '#f9fafb', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', transition: 'all 0.2s', fontSize: '13px', fontWeight: '500' }}
        >
          📥 Export Comparison JSON
        </button>
      </div>

      {/* Portfolio highlights grid */}
      <div className="comparison-metrics-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 180px), 1fr))', gap: '16px', marginBottom: '32px' }}>
        <div className="comp-metric-card" style={{ background: 'rgba(17, 24, 39, 0.7)', border: '1px solid rgba(55, 65, 81, 0.5)', padding: '20px', borderRadius: '12px', display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Upgrades</span>
          <span style={{ fontSize: '32px', fontWeight: '800', color: '#10b981', marginTop: '8px' }}>
            {portfolio_summary.upgrades} <span style={{ fontSize: '16px', fontWeight: '500' }}>stocks</span>
          </span>
        </div>
        <div className="comp-metric-card" style={{ background: 'rgba(17, 24, 39, 0.7)', border: '1px solid rgba(55, 65, 81, 0.5)', padding: '20px', borderRadius: '12px', display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Downgrades</span>
          <span style={{ fontSize: '32px', fontWeight: '800', color: '#ef4444', marginTop: '8px' }}>
            {portfolio_summary.downgrades} <span style={{ fontSize: '16px', fontWeight: '500' }}>stocks</span>
          </span>
        </div>
        <div className="comp-metric-card" style={{ background: 'rgba(17, 24, 39, 0.7)', border: '1px solid rgba(55, 65, 81, 0.5)', padding: '20px', borderRadius: '12px', display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Unchanged</span>
          <span style={{ fontSize: '32px', fontWeight: '800', color: '#9ca3af', marginTop: '8px' }}>
            {portfolio_summary.unchanged} <span style={{ fontSize: '16px', fontWeight: '500' }}>stocks</span>
          </span>
        </div>
        <div className="comp-metric-card" style={{ background: 'rgba(17, 24, 39, 0.7)', border: '1px solid rgba(55, 65, 81, 0.5)', padding: '20px', borderRadius: '12px', display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Avg Composite Shift</span>
          <span style={{ fontSize: '32px', fontWeight: '800', color: portfolio_summary.avg_composite_change >= 0 ? '#10b981' : '#ef4444', marginTop: '8px' }}>
            {portfolio_summary.avg_composite_change >= 0 ? '+' : ''}{portfolio_summary.avg_composite_change.toFixed(2)}
          </span>
        </div>
        <div className="comp-metric-card" style={{ background: 'rgba(17, 24, 39, 0.7)', border: '1px solid rgba(55, 65, 81, 0.5)', padding: '20px', borderRadius: '12px', display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Avg Technical Shift</span>
          <span style={{ fontSize: '32px', fontWeight: '800', color: portfolio_summary.avg_technical_change >= 0 ? '#10b981' : '#ef4444', marginTop: '8px' }}>
            {portfolio_summary.avg_technical_change >= 0 ? '+' : ''}{portfolio_summary.avg_technical_change.toFixed(2)}
          </span>
        </div>
      </div>

      <div className="responsive-grid-400" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px', marginBottom: '32px' }}>
        <div className="chart-card" style={{ background: 'rgba(17, 24, 39, 0.6)', border: '1px solid rgba(55, 65, 81, 0.4)', borderRadius: '16px', padding: '20px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>📉 Composite Score Waterfall contribution</h3>
          <div style={{ width: '100%', height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={visualizations.waterfall}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(55, 65, 81, 0.3)" />
                <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: '11px' }} />
                <YAxis tick={{ fill: '#9ca3af', fontSize: '11px' }} />
                <Tooltip />
                <ReferenceLine y={0} stroke="#9ca3af" />
                <Bar dataKey="value">
                  {visualizations.waterfall.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.value >= 0 ? '#10b981' : '#ef4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Transition Matrix Grid */}
        <div className="chart-card" style={{ background: 'rgba(17, 24, 39, 0.6)', border: '1px solid rgba(55, 65, 81, 0.4)', borderRadius: '16px', padding: '20px', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>🔀 Recommendation Transition Matrix</h3>
          <div className="table-scroll-container" style={{ flex: 1 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'center' }}>
              <thead>
                <tr>
                  <th style={{ padding: '8px', color: '#9ca3af', borderBottom: '1px solid rgba(55, 65, 81, 0.5)' }}>From \ To</th>
                  {Object.keys(recommendation_summary.matrix).map((k) => (
                    <th key={k} style={{ padding: '8px', color: '#9ca3af', borderBottom: '1px solid rgba(55, 65, 81, 0.5)', fontWeight: 'bold' }}>{k.split(' ')[0]}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.keys(recommendation_summary.matrix).map((fromKey) => (
                  <tr key={fromKey}>
                    <td style={{ padding: '10px 8px', textAlign: 'left', fontWeight: '700', borderBottom: '1px solid rgba(55, 65, 81, 0.3)' }}>{fromKey}</td>
                    {Object.keys(recommendation_summary.matrix[fromKey]).map((toKey) => {
                      const val = recommendation_summary.matrix[fromKey][toKey];
                      const isDiagonal = fromKey === toKey;
                      const hasValue = val > 0;
                      let bg = 'transparent';
                      let color = '#9ca3af';
                      if (hasValue) {
                        if (isDiagonal) {
                          bg = 'rgba(55, 65, 81, 0.4)';
                          color = '#f9fafb';
                        } else {
                          const isUpgrade = Object.keys(recommendation_summary.matrix).indexOf(toKey) > Object.keys(recommendation_summary.matrix).indexOf(fromKey);
                          bg = isUpgrade ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.25)';
                          color = isUpgrade ? '#34d399' : '#f87171';
                        }
                      }
                      return (
                        <td 
                          key={toKey} 
                          style={{ 
                            padding: '10px 8px', 
                            background: bg, 
                            color: color, 
                            fontWeight: hasValue ? 'bold' : 'normal',
                            borderBottom: '1px solid rgba(55, 65, 81, 0.3)',
                            fontSize: '13px'
                          }}
                        >
                          {val}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Sector Intelligence & Movers Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px', marginBottom: '32px' }}>
        
        {/* Sector Intelligence Highlights */}
        <div className="card" style={{ background: 'rgba(17, 24, 39, 0.6)', border: '1px solid rgba(55, 65, 81, 0.4)', borderRadius: '16px', padding: '20px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>⚡ Sector Intelligence</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '10px', borderBottom: '1px solid rgba(55, 65, 81, 0.3)' }}>
              <span style={{ color: '#9ca3af' }}>Best Performing Sector</span>
              <strong style={{ color: '#10b981' }}>{sector_summary.best_sector || '—'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '10px', borderBottom: '1px solid rgba(55, 65, 81, 0.3)' }}>
              <span style={{ color: '#9ca3af' }}>Worst Performing Sector</span>
              <strong style={{ color: '#ef4444' }}>{sector_summary.worst_sector || '—'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '10px', borderBottom: '1px solid rgba(55, 65, 81, 0.3)' }}>
              <span style={{ color: '#9ca3af' }}>Most Upgraded Sector</span>
              <strong style={{ color: '#6366f1' }}>{sector_summary.most_upgrades || 'None'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '10px', borderBottom: '1px solid rgba(55, 65, 81, 0.3)' }}>
              <span style={{ color: '#9ca3af' }}>Largest Momentum Gain</span>
              <strong style={{ color: '#34d399' }}>{sector_summary.largest_momentum_gain || 'None'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#9ca3af' }}>Largest Risk Reduction</span>
              <strong style={{ color: '#3b82f6' }}>{sector_summary.largest_risk_reduction || 'None'}</strong>
            </div>
          </div>
        </div>

        {/* Top Movers (Movers & Losers) */}
        <div className="card" style={{ background: 'rgba(17, 24, 39, 0.6)', border: '1px solid rgba(55, 65, 81, 0.4)', borderRadius: '16px', padding: '20px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>🚀 Strongest Score Movers</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
            <thead>
              <tr>
                <th style={{ padding: '6px 8px', color: '#9ca3af', borderBottom: '1px solid rgba(55, 65, 81, 0.4)' }}>Symbol</th>
                <th style={{ padding: '6px 8px', color: '#9ca3af', borderBottom: '1px solid rgba(55, 65, 81, 0.4)' }}>Rating Shift</th>
                <th style={{ padding: '6px 8px', color: '#9ca3af', borderBottom: '1px solid rgba(55, 65, 81, 0.4)', textAlign: 'right' }}>Composite Delta</th>
              </tr>
            </thead>
            <tbody>
              {portfolio_summary.strongest_improving.map((sd) => (
                <tr key={sd.symbol}>
                  <td style={{ padding: '8px', borderBottom: '1px solid rgba(55, 65, 81, 0.2)' }}>
                    <strong>{sd.symbol.replace('.NS', '')}</strong>
                  </td>
                  <td style={{ padding: '8px', borderBottom: '1px solid rgba(55, 65, 81, 0.2)' }}>
                    {sd.prev_rating} ➡️ {sd.new_rating}
                  </td>
                  <td style={{ padding: '8px', borderBottom: '1px solid rgba(55, 65, 81, 0.2)', textAlign: 'right', fontWeight: 'bold', color: '#10b981' }}>
                    +{sd.score_changes.composite_score.delta}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Top Losers */}
        <div className="card" style={{ background: 'rgba(17, 24, 39, 0.6)', border: '1px solid rgba(55, 65, 81, 0.4)', borderRadius: '16px', padding: '20px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>📉 Largest Score Deteriorations</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
            <thead>
              <tr>
                <th style={{ padding: '6px 8px', color: '#9ca3af', borderBottom: '1px solid rgba(55, 65, 81, 0.4)' }}>Symbol</th>
                <th style={{ padding: '6px 8px', color: '#9ca3af', borderBottom: '1px solid rgba(55, 65, 81, 0.4)' }}>Rating Shift</th>
                <th style={{ padding: '6px 8px', color: '#9ca3af', borderBottom: '1px solid rgba(55, 65, 81, 0.4)', textAlign: 'right' }}>Composite Delta</th>
              </tr>
            </thead>
            <tbody>
              {portfolio_summary.largest_deteriorating.map((sd) => (
                <tr key={sd.symbol}>
                  <td style={{ padding: '8px', borderBottom: '1px solid rgba(55, 65, 81, 0.2)' }}>
                    <strong>{sd.symbol.replace('.NS', '')}</strong>
                  </td>
                  <td style={{ padding: '8px', borderBottom: '1px solid rgba(55, 65, 81, 0.2)' }}>
                    {sd.prev_rating} ➡️ {sd.new_rating}
                  </td>
                  <td style={{ padding: '8px', borderBottom: '1px solid rgba(55, 65, 81, 0.2)', textAlign: 'right', fontWeight: 'bold', color: '#ef4444' }}>
                    {sd.score_changes.composite_score.delta}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Changes Details List Table */}
      <div className="changes-list-card" style={{ background: 'rgba(17, 24, 39, 0.6)', border: '1px solid rgba(55, 65, 81, 0.4)', borderRadius: '16px', padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '800' }}>📄 Recommendation Transition Ledger</h3>
          <div style={{ display: 'flex', gap: '8px' }}>
            {['ALL', 'UPGRADES', 'DOWNGRADES', 'UNCHANGED'].map((tab) => (
              <button
                key={tab}
                className={`filter-tab-btn ${activeTab === tab ? 'filter-tab-btn--active' : ''}`}
                onClick={() => setActiveTab(tab)}
                style={{
                  background: activeTab === tab ? '#6366f1' : 'rgba(31, 41, 55, 0.6)',
                  border: '1px solid rgba(55, 65, 81, 0.5)',
                  color: '#f9fafb',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  fontWeight: '600'
                }}
              >
                {tab.charAt(0) + tab.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
        </div>

        {filteredDeltas.length > 0 ? (
          <div className="table-container" style={{ overflowX: 'auto' }}>
            <table className="changes-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid rgba(55, 65, 81, 0.6)' }}>
                  <th style={{ padding: '12px 8px', color: '#9ca3af' }}>Symbol</th>
                  <th style={{ padding: '12px 8px', color: '#9ca3af' }}>Transition</th>
                  <th style={{ padding: '12px 8px', color: '#9ca3af' }}>Rating Path</th>
                  <th style={{ padding: '12px 8px', color: '#9ca3af', textAlign: 'right' }}>Composite Shift</th>
                  <th style={{ padding: '12px 8px', color: '#9ca3af', textAlign: 'right' }}>Technical Shift</th>
                  <th style={{ padding: '12px 8px', color: '#9ca3af', textAlign: 'right' }}>Expected Return Change</th>
                  <th style={{ padding: '12px 8px', color: '#9ca3af', paddingLeft: '24px' }}>Main Contributing Factors</th>
                </tr>
              </thead>
              <tbody>
                {filteredDeltas.map((sd) => {
                  const badge = TRANSITION_BADGES[sd.transition_type] || { label: sd.transition_type, class: '' };
                  const compDelta = sd.score_changes.composite_score?.delta || 0;
                  const techDelta = sd.score_changes.technical_score?.delta || 0;
                  const retDelta = sd.score_changes.expected_return?.delta || 0;
                  
                  return (
                    <tr key={sd.symbol} style={{ borderBottom: '1px solid rgba(55, 65, 81, 0.3)' }}>
                      <td style={{ padding: '16px 8px' }}>
                        <strong>{sd.symbol.replace('.NS', '')}</strong>
                        <span style={{ display: 'block', fontSize: '11px', color: '#9ca3af' }}>{sd.company_name}</span>
                      </td>
                      <td style={{ padding: '16px 8px' }}>
                        <span className={`change-badge ${badge.class}`} style={{ display: 'inline-block', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '700' }}>
                          {badge.label}
                        </span>
                      </td>
                      <td style={{ padding: '16px 8px' }}>
                        {sd.prev_rating ? (
                          <span className="rating-mini-pill" style={{ background: RATING_COLORS[sd.prev_rating] + '15', color: RATING_COLORS[sd.prev_rating], padding: '2px 6px', borderRadius: '4px', fontWeight: '700', fontSize: '11px' }}>
                            {sd.prev_rating}
                          </span>
                        ) : '—'}
                        <span style={{ margin: '0 6px', color: '#9ca3af' }}>➡️</span>
                        <span className="rating-mini-pill" style={{ background: RATING_COLORS[sd.new_rating] + '15', color: RATING_COLORS[sd.new_rating], padding: '2px 6px', borderRadius: '4px', fontWeight: '700', fontSize: '11px' }}>
                          {sd.new_rating}
                        </span>
                      </td>
                      <td style={{ padding: '16px 8px', textAlign: 'right', fontWeight: 'bold', color: compDelta > 0 ? '#10b981' : compDelta < 0 ? '#ef4444' : '#9ca3af' }}>
                        {compDelta > 0 ? '+' : ''}{compDelta.toFixed(1)}
                      </td>
                      <td style={{ padding: '16px 8px', textAlign: 'right', color: techDelta > 0 ? '#10b981' : techDelta < 0 ? '#ef4444' : '#9ca3af' }}>
                        {techDelta > 0 ? '+' : ''}{techDelta.toFixed(1)}
                      </td>
                      <td style={{ padding: '16px 8px', textAlign: 'right', color: retDelta > 0 ? '#10b981' : retDelta < 0 ? '#ef4444' : '#9ca3af' }}>
                        {retDelta > 0 ? '+' : ''}{retDelta.toFixed(2)}%
                      </td>
                      <td style={{ padding: '16px 8px', paddingLeft: '24px' }}>
                        {sd.drivers && sd.drivers.length > 0 ? (
                          <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '12px', color: '#d1d5db', listStyleType: 'square' }}>
                            {sd.drivers.map((d, index) => (
                              <li key={index} style={{ marginBottom: '4px' }}>
                                <strong>{d.feature}</strong>: {d.change} ({d.prev_value} ➡️ {d.curr_value})
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <span style={{ color: '#6b7280', fontStyle: 'italic' }}>No significant indicators changed.</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="page-empty" style={{ textAlign: 'center', padding: '40px', color: '#9ca3af' }}>
            No stock recommendation transitions match the active tab filter.
          </div>
        )}
      </div>
    </div>
  );
}

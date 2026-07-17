import React, { useState, useEffect } from 'react';
import { fetchSnapshotDates, fetchCompareSnapshots } from '../api/stocks';
import LoadingSpinner from '../components/common/LoadingSpinner';

const RATING_COLORS = {
  'STRONG BUY': '#10b981',
  'BUY':        '#3b82f6',
  'HOLD':       '#f59e0b',
  'SELL':       '#f97316',
  'STRONG SELL':'#ef4444',
};

export default function HistoricalSnapshots() {
  const [dates, setDates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Tab control: 'DROPDOWN' | 'UUID'
  const [compareMode, setCompareMode] = useState('DROPDOWN');
  
  // Selections for dropdown compare
  const [date1, setDate1] = useState('');
  const [date2, setDate2] = useState('');
  
  // Selections for UUID compare
  const [uuid1, setUuid1] = useState('');
  const [uuid2, setUuid2] = useState('');

  const [comparing, setComparing] = useState(false);
  const [comparison, setComparison] = useState(null);
  const [compError, setCompError] = useState(null);

  // Accordion state for expanded stock detail rows
  const [expandedStocks, setExpandedStocks] = useState(new Set());

  const loadDates = async () => {
    try {
      const res = await fetchSnapshotDates();
      const items = res.data?.dates || [];
      setDates(items);
      if (items.length >= 2) {
        setDate1(items[1].snapshot_date);
        setDate2(items[0].snapshot_date);
      } else if (items.length >= 1) {
        setDate1(items[0].snapshot_date);
      }
    } catch (err) {
      setError('Failed to load snapshot archive registry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDates();
  }, []);

  const handleCompare = async (bSel, tSel) => {
    const sel1 = bSel || (compareMode === 'DROPDOWN' ? date1 : uuid1);
    const sel2 = tSel || (compareMode === 'DROPDOWN' ? date2 : uuid2);

    if (!sel1 || !sel2) {
      setCompError('Please select or specify both baseline and comparison targets.');
      return;
    }

    setComparing(true);
    setCompError(null);
    setComparison(null);
    setExpandedStocks(new Set());
    
    try {
      const res = await fetchCompareSnapshots(sel1, sel2);
      setComparison(res.data);
    } catch (err) {
      console.error(err);
      setCompError(
        err.response?.data?.detail || 
        'Comparison failed. Ensure both snapshots exist and are fully completed.'
      );
    } finally {
      setComparing(false);
    }
  };

  const handleQuickCompareLatest = () => {
    handleCompare('previous', 'latest');
  };

  const toggleStockAccordion = (symbol) => {
    setExpandedStocks((prev) => {
      const next = new Set(prev);
      if (next.has(symbol)) {
        next.delete(symbol);
      } else {
        next.add(symbol);
      }
      return next;
    });
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="page-error">{error}</div>;

  return (
    <div className="history-page" style={{ padding: '24px', color: '#f9fafb', background: '#0a0e17' }}>
      <div className="history-header" style={{ marginBottom: '32px' }}>
        <h1 className="history-title" style={{ fontSize: '28px', fontWeight: '800' }}>
          📚 Research Snapshot Archive & Compare
        </h1>
        <p className="history-subtitle" style={{ color: '#9ca3af', marginTop: '4px' }}>
          Query, validate, and compare historical daily snapshots and execution registries.
        </p>
      </div>

      {/* Comparison Workspace */}
      <div className="compare-panel-card" style={{ background: 'rgba(17, 24, 39, 0.7)', border: '1px solid rgba(55, 65, 81, 0.6)', borderRadius: '16px', padding: '24px', marginBottom: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '700' }}>⚖️ Compare Snapshot Runs</h3>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setCompareMode('DROPDOWN')}
              className={`filter-tab-btn ${compareMode === 'DROPDOWN' ? 'filter-tab-btn--active' : ''}`}
              style={{ background: compareMode === 'DROPDOWN' ? '#6366f1' : 'transparent', border: '1px solid rgba(55, 65, 81, 0.5)', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', color: '#f9fafb', fontSize: '12px', fontWeight: '600' }}
            >
              Select Dates
            </button>
            <button
              onClick={() => setCompareMode('UUID')}
              className={`filter-tab-btn ${compareMode === 'UUID' ? 'filter-tab-btn--active' : ''}`}
              style={{ background: compareMode === 'UUID' ? '#6366f1' : 'transparent', border: '1px solid rgba(55, 65, 81, 0.5)', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', color: '#f9fafb', fontSize: '12px', fontWeight: '600' }}
            >
              Specify UUIDs
            </button>
            <button
              onClick={handleQuickCompareLatest}
              className="compare-quick-btn"
              style={{ background: 'rgba(16, 185, 129, 0.2)', border: '1px solid rgba(16, 185, 129, 0.4)', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', color: '#34d399', fontSize: '12px', fontWeight: '700' }}
            >
              ⚡ Latest vs Previous
            </button>
          </div>
        </div>

        {compareMode === 'DROPDOWN' ? (
          <div className="compare-form-row" style={{ display: 'flex', gap: '16px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div className="compare-form-grp" style={{ flex: 1, minWidth: '200px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '600' }}>Baseline Date (Date 1)</label>
              <select 
                value={date1} 
                onChange={(e) => setDate1(e.target.value)}
                style={{ background: '#111827', border: '1px solid rgba(55, 65, 81, 0.8)', color: '#f9fafb', padding: '10px', borderRadius: '6px', fontSize: '13px' }}
              >
                <option value="">Select baseline date...</option>
                {dates.map((d) => (
                  <option key={d.snapshot_id + '-1'} value={d.snapshot_date}>
                    {d.snapshot_date} ({d.is_official ? 'Official' : 'Live'}) — {d.stocks_processed} stocks
                  </option>
                ))}
              </select>
            </div>
            <div className="compare-arrow" style={{ paddingBottom: '10px', fontSize: '20px', color: '#9ca3af' }}>➡️</div>
            <div className="compare-form-grp" style={{ flex: 1, minWidth: '200px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '600' }}>Comparison Date (Date 2)</label>
              <select 
                value={date2} 
                onChange={(e) => setDate2(e.target.value)}
                style={{ background: '#111827', border: '1px solid rgba(55, 65, 81, 0.8)', color: '#f9fafb', padding: '10px', borderRadius: '6px', fontSize: '13px' }}
              >
                <option value="">Select comparison date...</option>
                {dates.map((d) => (
                  <option key={d.snapshot_id + '-2'} value={d.snapshot_date}>
                    {d.snapshot_date} ({d.is_official ? 'Official' : 'Live'}) — {d.stocks_processed} stocks
                  </option>
                ))}
              </select>
            </div>
            <button
              className={`compare-submit-btn ${comparing ? 'compare-submit-btn--busy' : ''}`}
              onClick={() => handleCompare()}
              disabled={comparing}
              style={{ background: '#4f46e5', border: 'none', color: '#f9fafb', padding: '11px 24px', borderRadius: '6px', fontSize: '14px', fontWeight: '700', cursor: 'pointer', transition: 'all 0.2s' }}
            >
              {comparing ? 'Comparing…' : 'Run Comparison'}
            </button>
          </div>
        ) : (
          <div className="compare-form-row" style={{ display: 'flex', gap: '16px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div className="compare-form-grp" style={{ flex: 1, minWidth: '240px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '600' }}>Baseline Snapshot UUID</label>
              <input 
                type="text" 
                value={uuid1} 
                onChange={(e) => setUuid1(e.target.value)}
                placeholder="Enter baseline snapshot UUID..."
                style={{ background: '#111827', border: '1px solid rgba(55, 65, 81, 0.8)', color: '#f9fafb', padding: '10px', borderRadius: '6px', fontSize: '13px' }}
              />
            </div>
            <div className="compare-arrow" style={{ paddingBottom: '10px', fontSize: '20px', color: '#9ca3af' }}>➡️</div>
            <div className="compare-form-grp" style={{ flex: 1, minWidth: '240px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '600' }}>Comparison Snapshot UUID</label>
              <input 
                type="text" 
                value={uuid2} 
                onChange={(e) => setUuid2(e.target.value)}
                placeholder="Enter comparison snapshot UUID..."
                style={{ background: '#111827', border: '1px solid rgba(55, 65, 81, 0.8)', color: '#f9fafb', padding: '10px', borderRadius: '6px', fontSize: '13px' }}
              />
            </div>
            <button
              className="compare-submit-btn"
              onClick={() => handleCompare()}
              disabled={comparing}
              style={{ background: '#4f46e5', border: 'none', color: '#f9fafb', padding: '11px 24px', borderRadius: '6px', fontSize: '14px', fontWeight: '700', cursor: 'pointer' }}
            >
              {comparing ? 'Comparing…' : 'Run Comparison'}
            </button>
          </div>
        )}

        {compError && (
          <div className="compare-error-alert" style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px', padding: '12px', marginTop: '16px', fontSize: '13px' }}>
            ⚠️ {compError}
          </div>
        )}
      </div>

      {/* Comparison Details Panel */}
      {comparison && (
        <div className="comparison-results" style={{ marginBottom: '40px' }}>
          
          {/* Mismatch warnings */}
          {comparison.comparison_metadata.version_warnings && comparison.comparison_metadata.version_warnings.length > 0 && (
            <div className="warning-banner" style={{ background: 'rgba(245, 158, 11, 0.12)', border: '1px solid rgba(245, 158, 11, 0.4)', borderRadius: '8px', padding: '12px 16px', marginBottom: '24px', fontSize: '13px', color: '#fbe5c9' }}>
              <strong>⚠️ Pipeline Version Mismatch Flagged</strong>
              <ul style={{ marginLeft: '20px', marginTop: '6px' }}>
                {comparison.comparison_metadata.version_warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          <h2 className="comparison-results-title" style={{ fontSize: '20px', fontWeight: '800', marginBottom: '20px' }}>
            ⚖️ Comparison Report: {comparison.comparison_metadata.date1} vs {comparison.comparison_metadata.date2}
          </h2>

          {/* Metrics summary cards */}
          <div className="comparison-metrics-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '32px' }}>
            <div className="comp-metric-card" style={{ background: 'rgba(17, 24, 39, 0.6)', border: '1px solid rgba(55, 65, 81, 0.4)', padding: '16px', borderRadius: '10px' }}>
              <span style={{ fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase', fontWeight: '600' }}>Upgrades / Downgrades</span>
              <span style={{ fontSize: '24px', fontWeight: '800', display: 'block', marginTop: '4px' }}>
                🟢 {comparison.portfolio_summary.upgrades} / 🔴 {comparison.portfolio_summary.downgrades}
              </span>
            </div>
            <div className="comp-metric-card" style={{ background: 'rgba(17, 24, 39, 0.6)', border: '1px solid rgba(55, 65, 81, 0.4)', padding: '16px', borderRadius: '10px' }}>
              <span style={{ fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase', fontWeight: '600' }}>Avg Composite Delta</span>
              <span style={{ fontSize: '24px', fontWeight: '800', display: 'block', marginTop: '4px', color: comparison.portfolio_summary.avg_composite_change >= 0 ? '#10b981' : '#ef4444' }}>
                {comparison.portfolio_summary.avg_composite_change >= 0 ? '+' : ''}{comparison.portfolio_summary.avg_composite_change.toFixed(2)}
              </span>
            </div>
            <div className="comp-metric-card" style={{ background: 'rgba(17, 24, 39, 0.6)', border: '1px solid rgba(55, 65, 81, 0.4)', padding: '16px', borderRadius: '10px' }}>
              <span style={{ fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase', fontWeight: '600' }}>Best Performing Sector</span>
              <span style={{ fontSize: '18px', fontWeight: '800', display: 'block', marginTop: '8px', color: '#10b981' }}>
                🏢 {comparison.sector_summary.best_sector || '—'}
              </span>
            </div>
            <div className="comp-metric-card" style={{ background: 'rgba(17, 24, 39, 0.6)', border: '1px solid rgba(55, 65, 81, 0.4)', padding: '16px', borderRadius: '10px' }}>
              <span style={{ fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase', fontWeight: '600' }}>Most Upgrades Sector</span>
              <span style={{ fontSize: '18px', fontWeight: '800', display: 'block', marginTop: '8px', color: '#6366f1' }}>
                ⚡ {comparison.sector_summary.most_upgrades || 'None'}
              </span>
            </div>
          </div>

          {/* Stock Accordion Table */}
          <div className="compare-stock-changes-card" style={{ background: 'rgba(17, 24, 39, 0.6)', border: '1px solid rgba(55, 65, 81, 0.4)', borderRadius: '16px', padding: '20px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>
              📋 Detailed Stock-Level Score Deltas ({comparison.stock_deltas.length} Stocks)
            </h3>
            
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid rgba(55, 65, 81, 0.6)' }}>
                    <th style={{ padding: '12px 8px', color: '#9ca3af' }}>Symbol</th>
                    <th style={{ padding: '12px 8px', color: '#9ca3af' }}>Sector</th>
                    <th style={{ padding: '12px 8px', color: '#9ca3af' }}>Rating Shift</th>
                    <th style={{ padding: '12px 8px', color: '#9ca3af', textAlign: 'right' }}>Composite Shift</th>
                    <th style={{ padding: '12px 8px', color: '#9ca3af', textAlign: 'right' }}>Technical Shift</th>
                    <th style={{ padding: '12px 8px', color: '#9ca3af', textAlign: 'right' }}>Expected Return Change</th>
                    <th style={{ padding: '12px 8px', color: '#9ca3af', textAlign: 'center' }}>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.stock_deltas.map((sd) => {
                    const isExpanded = expandedStocks.has(sd.symbol);
                    const comp = sd.score_changes.composite_score;
                    const tech = sd.score_changes.technical_score;
                    const ret = sd.score_changes.expected_return;
                    
                    return (
                      <React.Fragment key={sd.symbol}>
                        {/* Summary Header Row */}
                        <tr 
                          onClick={() => toggleStockAccordion(sd.symbol)}
                          style={{ borderBottom: '1px solid rgba(55, 65, 81, 0.2)', cursor: 'pointer', background: isExpanded ? 'rgba(99, 102, 241, 0.05)' : 'transparent' }}
                          className="accordion-row-hover"
                        >
                          <td style={{ padding: '14px 8px' }}>
                            <strong>{sd.symbol.replace('.NS', '')}</strong>
                            <span style={{ display: 'block', fontSize: '11px', color: '#9ca3af' }}>{sd.company_name}</span>
                          </td>
                          <td style={{ padding: '14px 8px', color: '#d1d5db' }}>{sd.sector}</td>
                          <td style={{ padding: '14px 8px' }}>
                            {sd.prev_rating ? (
                              <span className="rating-mini-pill" style={{ background: RATING_COLORS[sd.prev_rating] + '12', color: RATING_COLORS[sd.prev_rating], padding: '2px 6px', borderRadius: '4px', fontSize: '11px', fontWeight: '700' }}>
                                {sd.prev_rating}
                              </span>
                            ) : '—'}
                            <span style={{ margin: '0 6px', color: '#6b7280' }}>➡️</span>
                            {sd.new_rating ? (
                              <span className="rating-mini-pill" style={{ background: RATING_COLORS[sd.new_rating] + '12', color: RATING_COLORS[sd.new_rating], padding: '2px 6px', borderRadius: '4px', fontSize: '11px', fontWeight: '700' }}>
                                {sd.new_rating}
                              </span>
                            ) : '—'}
                          </td>
                          <td style={{ padding: '14px 8px', textAlign: 'right', fontWeight: 'bold', color: comp?.delta > 0 ? '#10b981' : comp?.delta < 0 ? '#ef4444' : '#9ca3af' }}>
                            {comp ? `${comp.delta > 0 ? '+' : ''}${comp.delta.toFixed(1)}` : '—'}
                          </td>
                          <td style={{ padding: '14px 8px', textAlign: 'right', color: tech?.delta > 0 ? '#10b981' : tech?.delta < 0 ? '#ef4444' : '#9ca3af' }}>
                            {tech ? `${tech.delta > 0 ? '+' : ''}${tech.delta.toFixed(1)}` : '—'}
                          </td>
                          <td style={{ padding: '14px 8px', textAlign: 'right', color: ret?.delta > 0 ? '#10b981' : ret?.delta < 0 ? '#ef4444' : '#9ca3af' }}>
                            {ret ? `${ret.delta > 0 ? '+' : ''}${ret.delta.toFixed(2)}%` : '—'}
                          </td>
                          <td style={{ padding: '14px 8px', textAlign: 'center', color: '#6366f1', fontWeight: 'bold', fontSize: '16px' }}>
                            {isExpanded ? '▲' : '▼'}
                          </td>
                        </tr>
                        
                        {/* Expanded details row */}
                        {isExpanded && (
                          <tr>
                            <td colSpan="7" style={{ padding: '20px', background: 'rgba(17, 24, 39, 0.4)', borderBottom: '1px solid rgba(55, 65, 81, 0.3)' }}>
                              
                              {/* 13 side-by-side score values */}
                              <h4 style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>
                                📊 Detailed Score Comparison Metrics
                              </h4>
                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px', marginBottom: '20px' }}>
                                {Object.keys(sd.score_changes).map((scoreName) => {
                                  const sChg = sd.score_changes[scoreName];
                                  const display = scoreName.replace(/_/g, ' ').toUpperCase();
                                  
                                  return (
                                    <div key={scoreName} style={{ background: '#111827', padding: '10px 12px', borderRadius: '6px', border: '1px solid rgba(55, 65, 81, 0.3)' }}>
                                      <span style={{ fontSize: '10px', color: '#9ca3af', display: 'block' }}>{display}</span>
                                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '6px' }}>
                                        <span style={{ fontSize: '12px', color: '#d1d5db' }}>{sChg.prev?.toFixed(1) || '—'} ➡️ {sChg.curr?.toFixed(1) || '—'}</span>
                                        <span style={{ fontSize: '12px', fontWeight: 'bold', color: sChg.delta > 0 ? '#10b981' : sChg.delta < 0 ? '#ef4444' : '#9ca3af' }}>
                                          {sChg.delta > 0 ? '+' : ''}{sChg.delta.toFixed(1)}
                                        </span>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>

                              {/* Structured drivers explanation list */}
                              <h4 style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>
                                💡 Contributing Technical Crossovers & Drivers
                              </h4>
                              {sd.drivers && sd.drivers.length > 0 ? (
                                <div style={{ background: '#111827', borderRadius: '8px', padding: '12px 16px', border: '1px solid rgba(55, 65, 81, 0.3)' }}>
                                  <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '13px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                    {sd.drivers.map((d, index) => (
                                      <li key={index} style={{ color: '#e5e7eb' }}>
                                        <span style={{ color: '#818cf8', fontWeight: '600' }}>{d.feature}</span> changed: {d.change} (Value: {d.prev_value} ➡️ {d.curr_value}). Effect: <span style={{ color: d.effect === 'positive' ? '#10b981' : '#ef4444', fontWeight: 'bold' }}>{d.effect}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              ) : (
                                <p style={{ fontSize: '12px', color: '#6b7280', fontStyle: 'italic', margin: 0 }}>
                                  No notable technical crossovers or significant indicator shifts recorded for this period.
                                </p>
                              )}
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      )}

      {/* History Archive Table */}
      <div className="archive-section">
        <h2 style={{ fontSize: '20px', fontWeight: '800', marginBottom: '16px' }}>📁 Snapshot Registry Archive</h2>
        {dates.length > 0 ? (
          <div className="archive-card" style={{ background: 'rgba(17, 24, 39, 0.6)', border: '1px solid rgba(55, 65, 81, 0.4)', borderRadius: '16px', padding: '20px' }}>
            <table className="archive-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid rgba(55, 65, 81, 0.5)' }}>
                  <th style={{ padding: '10px 8px', color: '#9ca3af' }}>Market Date</th>
                  <th style={{ padding: '10px 8px', color: '#9ca3af' }}>Status</th>
                  <th style={{ padding: '10px 8px', color: '#9ca3af', textAlign: 'right' }}>Processed Stocks</th>
                  <th style={{ padding: '10px 8px', color: '#9ca3af', textAlign: 'right' }}>Failed Stocks</th>
                  <th style={{ padding: '10px 8px', color: '#9ca3af', textAlign: 'right' }}>Quality Score</th>
                  <th style={{ padding: '10px 8px', color: '#9ca3af', textAlign: 'right' }}>Duration</th>
                  <th style={{ padding: '10px 8px', color: '#9ca3af', paddingLeft: '16px' }}>Generated At (IST)</th>
                </tr>
              </thead>
              <tbody>
                {dates.map((d) => (
                  <tr key={d.snapshot_id} style={{ borderBottom: '1px solid rgba(55, 65, 81, 0.2)' }}>
                    <td style={{ padding: '12px 8px' }}>
                      <strong>{d.snapshot_date}</strong>
                      {!d.is_official && <span className="archive-badge-live" style={{ marginLeft: '8px', padding: '2px 6px', background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', borderRadius: '4px', fontSize: '10px', fontWeight: 'bold' }}>Live</span>}
                    </td>
                    <td style={{ padding: '12px 8px' }}>
                      <span className={`status-pill status-pill--${d.status}`} style={{ fontSize: '11px', textTransform: 'capitalize' }}>
                        {d.status?.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td style={{ padding: '12px 8px', textAlign: 'right' }}>{d.stocks_processed}</td>
                    <td style={{ padding: '12px 8px', textAlign: 'right', color: '#ef4444' }}>{d.stocks_failed}</td>
                    <td style={{ padding: '12px 8px', textAlign: 'right' }}>
                      <strong>{d.validation_score != null ? `${d.validation_score.toFixed(0)}/100` : '—'}</strong>
                    </td>
                    <td style={{ padding: '12px 8px', textAlign: 'right' }}>{d.pipeline_duration_sec?.toFixed(0) || '—'}s</td>
                    <td style={{ padding: '12px 8px', paddingLeft: '16px', color: '#9ca3af' }}>
                      {d.generated_at ? new Date(d.generated_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="page-empty" style={{ padding: '40px', textAlign: 'center', color: '#9ca3af' }}>
            No historical snapshots registered. Trigger a run to generate a snapshot.
          </div>
        )}
      </div>
    </div>
  );
}

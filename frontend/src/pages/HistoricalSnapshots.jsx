import { useState, useEffect } from 'react';
import { fetchSnapshotDates, fetchCompareSnapshots } from '../api/stocks';
import LoadingSpinner from '../components/common/LoadingSpinner';

const REGIME_CONFIG = {
  Bullish: { color: '#10b981', icon: '📈' },
  Bearish: { color: '#ef4444', icon: '📉' },
  Mixed:   { color: '#f59e0b', icon: '🔀' },
  Neutral: { color: '#6b7280', icon: '➡️' },
};

export default function HistoricalSnapshots() {
  const [dates, setDates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Selection for comparison
  const [date1, setDate1] = useState('');
  const [date2, setDate2] = useState('');
  const [comparing, setComparing] = useState(false);
  const [comparison, setComparison] = useState(null);
  const [compError, setCompError] = useState(null);

  useEffect(() => {
    const load = async () => {
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
        setError('Failed to load snapshot archive list.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleCompare = async () => {
    if (!date1 || !date2) {
      setCompError('Please select both dates to compare.');
      return;
    }
    setComparing(true);
    setCompError(null);
    setComparison(null);
    try {
      const res = await fetchCompareSnapshots(date1, date2);
      setComparison(res.data);
    } catch (err) {
      setCompError('Comparison failed. Ensure both snapshots are fully generated.');
    } finally {
      setComparing(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="page-error">{error}</div>;

  return (
    <div className="history-page">
      <div className="history-header">
        <h1 className="history-title">📚 Research Snapshot Archive & Compare</h1>
        <p className="history-subtitle">
          Browse historical session snapshots, validation reports, and execute side-by-side comparisons of engine runs.
        </p>
      </div>

      {/* Compare Panel */}
      <div className="compare-panel-card">
        <h3>🔍 Run Snapshot Comparison</h3>
        <div className="compare-form-row">
          <div className="compare-form-grp">
            <label>Baseline Date (Date 1)</label>
            <select value={date1} onChange={(e) => setDate1(e.target.value)}>
              <option value="">Select baseline date...</option>
              {dates.map((d) => (
                <option key={d.snapshot_id + '-1'} value={d.snapshot_date}>
                  {d.snapshot_date} ({d.is_official ? 'Official' : 'Live'})
                </option>
              ))}
            </select>
          </div>
          <div className="compare-arrow">➡️</div>
          <div className="compare-form-grp">
            <label>Comparison Date (Date 2)</label>
            <select value={date2} onChange={(e) => setDate2(e.target.value)}>
              <option value="">Select comparison date...</option>
              {dates.map((d) => (
                <option key={d.snapshot_id + '-2'} value={d.snapshot_date}>
                  {d.snapshot_date} ({d.is_official ? 'Official' : 'Live'})
                </option>
              ))}
            </select>
          </div>
          <button
            className={`compare-submit-btn ${comparing ? 'compare-submit-btn--busy' : ''}`}
            onClick={handleCompare}
            disabled={comparing}
          >
            {comparing ? 'Comparing…' : 'Compare Snapshots'}
          </button>
        </div>
        {compError && <div className="compare-error-alert">{compError}</div>}
      </div>

      {/* Comparison Results */}
      {comparison && (
        <div className="comparison-results">
          <h2 className="comparison-results-title">
            ⚖️ Comparison: {comparison.date1} vs {comparison.date2}
          </h2>

          <div className="comparison-metrics-grid">
            <div className="comp-metric-card">
              <span className="comp-metric-label">Regime Shift</span>
              <span className="comp-metric-val">
                {comparison.regime_change || 'No Regime Shift'}
              </span>
            </div>
            <div className="comp-metric-card">
              <span className="comp-metric-label">Avg Composite Delta</span>
              <span className={`comp-metric-val ${comparison.composite_delta >= 0 ? 'text-green' : 'text-red'}`}>
                {comparison.composite_delta >= 0 ? '+' : ''}
                {comparison.composite_delta?.toFixed(2) || '0.00'}
              </span>
            </div>
            <div className="comp-metric-card">
              <span className="comp-metric-label">Avg Confidence Delta</span>
              <span className={`comp-metric-val ${comparison.confidence_delta >= 0 ? 'text-green' : 'text-red'}`}>
                {comparison.confidence_delta >= 0 ? '+' : ''}
                {comparison.confidence_delta?.toFixed(2) || '0.00'}%
              </span>
            </div>
          </div>

          {/* Upgrades & Downgrades List */}
          <div className="compare-stock-changes-card">
            <h3>📈 Stock Changes ({comparison.stock_changes?.length || 0} changes)</h3>
            {comparison.stock_changes?.length > 0 ? (
              <div className="compare-table-wrap">
                <table className="compare-table">
                  <thead>
                    <tr>
                      <th>Symbol</th>
                      <th>Rating Shift</th>
                      <th className="num-col">Composite Delta</th>
                      <th className="num-col">Confidence Delta</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparison.stock_changes.map((sc) => (
                      <tr key={sc.symbol}>
                        <td><strong>{sc.symbol?.replace('.NS', '')}</strong></td>
                        <td>
                          {sc.prev_rating} ➡️ {sc.new_rating}
                        </td>
                        <td className={`num-col ${sc.composite_diff >= 0 ? 'text-green' : 'text-red'}`}>
                          {sc.composite_diff >= 0 ? '+' : ''}{sc.composite_diff?.toFixed(1)}
                        </td>
                        <td className={`num-col ${sc.confidence_diff >= 0 ? 'text-green' : 'text-red'}`}>
                          {sc.confidence_diff >= 0 ? '+' : ''}{sc.confidence_diff?.toFixed(0)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="compare-empty-state">No stock rating or score changes between these dates.</div>
            )}
          </div>
        </div>
      )}

      {/* History Archive Table */}
      <div className="archive-section">
        <h2>📁 Historical Execution Registry</h2>
        {dates.length > 0 ? (
          <div className="archive-card">
            <table className="archive-table">
              <thead>
                <tr>
                  <th>Market Date</th>
                  <th>Status</th>
                  <th className="num-col">Stocks Ok</th>
                  <th className="num-col">Stocks Failed</th>
                  <th className="num-col">Validation Score</th>
                  <th className="num-col">Duration</th>
                  <th>Generated At (IST)</th>
                </tr>
              </thead>
              <tbody>
                {dates.map((d) => (
                  <tr key={d.snapshot_id}>
                    <td>
                      <strong>{d.snapshot_date}</strong>
                      {!d.is_official && <span className="archive-badge-live">Live</span>}
                    </td>
                    <td>
                      <span className={`status-pill status-pill--${d.status}`}>
                        {d.status?.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="num-col">{d.stocks_processed}</td>
                    <td className="num-col text-red">{d.stocks_failed}</td>
                    <td className="num-col">
                      <strong>{d.validation_score != null ? `${d.validation_score.toFixed(0)}/100` : '—'}</strong>
                    </td>
                    <td className="num-col">{d.pipeline_duration_sec?.toFixed(0) || '—'}s</td>
                    <td>{d.generated_at ? new Date(d.generated_at).toLocaleString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="page-empty">No historical snapshots registered. Run a snapshot generation run.</div>
        )}
      </div>
    </div>
  );
}

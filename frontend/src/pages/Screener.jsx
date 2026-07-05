import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchStocks } from '../api/stocks';
import RatingBadge from '../components/common/RatingBadge';
import ConfidenceBar from '../components/common/ConfidenceBar';
import LoadingSpinner from '../components/common/LoadingSpinner';

const RATINGS = ['All', 'STRONG BUY', 'BUY', 'HOLD', 'SELL', 'STRONG SELL'];

const SORTABLE_COLUMNS = [
  { key: 'Symbol', label: 'Symbol' },
  { key: 'FinalRating', label: 'Rating' },
  { key: 'Confidence', label: 'Confidence' },
  { key: 'CompositeScoreV2', label: 'Composite' },
  { key: 'TechnicalScore', label: 'Technical' },
  { key: 'MLScore', label: 'ML Score' },
  { key: 'GRUScore', label: 'GRU Score' },
  { key: 'ReliabilityScore', label: 'Reliability' },
  { key: 'Sector', label: 'Sector' },
];

function scoreColor(val) {
  if (val > 0) return '#10b981';
  if (val < 0) return '#ef4444';
  return '#6b7280';
}

export default function Screener() {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [ratingFilter, setRatingFilter] = useState('All');
  const [sortKey, setSortKey] = useState('CompositeScoreV2');
  const [sortOrder, setSortOrder] = useState('desc');
  const navigate = useNavigate();

  useEffect(() => {
    fetchStocks().then((res) => {
      setStocks(res.data);
      setLoading(false);
    });
  }, []);

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  };

  const filtered = useMemo(() => {
    let result = [...stocks];

    if (search) {
      const term = search.toUpperCase();
      result = result.filter((s) => s.Symbol.toUpperCase().includes(term));
    }

    if (ratingFilter !== 'All') {
      result = result.filter((s) => s.FinalRating === ratingFilter);
    }

    result.sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (typeof aVal === 'string') {
        return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }
      return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
    });

    return result;
  }, [stocks, search, ratingFilter, sortKey, sortOrder]);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="fade-in">
      {/* Controls */}
      <div className="page-section" style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
        <input
          className="header-search"
          placeholder="Search symbol..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: '240px' }}
        />
        <div className="filter-chips">
          {RATINGS.map((r) => (
            <button
              key={r}
              className={`filter-chip ${ratingFilter === r ? 'active' : ''}`}
              onClick={() => setRatingFilter(r)}
            >
              {r}
            </button>
          ))}
        </div>
        <span style={{ marginLeft: 'auto', fontSize: '13px', color: 'var(--text-muted)' }}>
          {filtered.length} stocks
        </span>
      </div>

      {/* Table */}
      <div className="card table-container" style={{ padding: 0 }}>
        <table className="data-table">
          <thead>
            <tr>
              {SORTABLE_COLUMNS.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className={sortKey === col.key ? 'sorted' : ''}
                >
                  {col.label}
                  {sortKey === col.key && (
                    <span style={{ marginLeft: '4px' }}>
                      {sortOrder === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((stock) => (
              <tr
                key={stock.Symbol}
                onClick={() => navigate(`/stock/${encodeURIComponent(stock.Symbol)}`)}
              >
                <td><span className="symbol">{stock.Symbol}</span></td>
                <td><RatingBadge rating={stock.FinalRating} /></td>
                <td style={{ minWidth: '160px' }}>
                  <ConfidenceBar value={stock.Confidence} />
                </td>
                <td style={{ color: scoreColor(stock.CompositeScoreV2), fontWeight: 600 }}>
                  {stock.CompositeScoreV2.toFixed(2)}
                </td>
                <td style={{ color: scoreColor(stock.TechnicalScore), fontWeight: 600 }}>
                  {stock.TechnicalScore.toFixed(2)}
                </td>
                <td style={{ color: scoreColor(stock.MLScore), fontWeight: 600 }}>
                  {stock.MLScore.toFixed(2)}
                </td>
                <td style={{ color: scoreColor(stock.GRUScore), fontWeight: 600 }}>
                  {stock.GRUScore.toFixed(2)}
                </td>
                <td>{stock.ReliabilityScore.toFixed(0)}</td>
                <td style={{ color: 'var(--text-muted)' }}>{stock.Sector}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';
import { fetchStocks, fetchRatingsDistribution, fetchScannerSummary } from '../api/stocks';
import RatingBadge from '../components/common/RatingBadge';
import ConfidenceBar from '../components/common/ConfidenceBar';
import LoadingSpinner from '../components/common/LoadingSpinner';

const RATINGS = ['All', 'STRONG BUY', 'BUY', 'HOLD', 'SELL', 'STRONG SELL'];

const RATING_COLORS = {
  'STRONG BUY': '#10b981',
  'BUY': '#34d399',
  'HOLD': '#f59e0b',
  'SELL': '#f97316',
  'STRONG SELL': '#ef4444',
};

export default function MarketOverview() {
  const [stocks, setStocks] = useState([]);
  const [marketStats, setMarketStats] = useState(null);
  const [dist, setDist] = useState(null);
  const [scannerSummary, setScannerSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Table filters/sorting
  const [search, setSearch] = useState('');
  const [ratingFilter, setRatingFilter] = useState('All');
  const [sortKey, setSortKey] = useState('CompositeScoreV2');
  const [sortOrder, setSortOrder] = useState('desc');
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      fetchStocks(),
      client.get('/market/overview'),
      fetchRatingsDistribution(),
      fetchScannerSummary()
    ])
      .then(([stocksRes, marketRes, distRes, summaryRes]) => {
        setStocks(stocksRes.data || []);
        setMarketStats(marketRes.data || null);
        setDist(distRes.data || null);
        setScannerSummary(summaryRes.data || null);
      })
      .catch((err) => console.error('Failed to fetch market data', err))
      .finally(() => setLoading(false));
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

  const distItems = [
    { label: 'STRONG BUY', count: dist?.strong_buy || 0, color: RATING_COLORS['STRONG BUY'] },
    { label: 'BUY', count: dist?.buy || 0, color: RATING_COLORS['BUY'] },
    { label: 'HOLD', count: dist?.hold || 0, color: RATING_COLORS['HOLD'] },
    { label: 'SELL', count: dist?.sell || 0, color: RATING_COLORS['SELL'] },
    { label: 'STRONG SELL', count: dist?.strong_sell || 0, color: RATING_COLORS['STRONG SELL'] },
  ];

  const maxCount = Math.max(...distItems.map(d => d.count), 1);

  // Compute market breadth
  const totalStocks = stocks.length || 1;
  const bullishCount = (dist?.strong_buy || 0) + (dist?.buy || 0);
  const bearishCount = (dist?.sell || 0) + (dist?.strong_sell || 0);
  const neutralCount = dist?.hold || 0;

  const bullishPct = (bullishCount / totalStocks) * 100;
  const bearishPct = (bearishCount / totalStocks) * 100;
  const neutralPct = (neutralCount / totalStocks) * 100;

  return (
    <div className="fade-in">
      {/* Hero Stats */}
      <div className="reports-hero" style={{ marginBottom: '24px', padding: '24px', borderRadius: '12px' }}>
        <h1 className="reports-hero-title" style={{ fontSize: '24px' }}>📈 Nifty 50 Market Overview</h1>
        <p className="reports-hero-subtitle" style={{ fontSize: '14px', marginTop: '4px' }}>
          Universe-wide statistics, breadth distribution, and core rating parameters.
        </p>
      </div>

      {/* Snapshot Cards */}
      {marketStats && scannerSummary && (
        <div className="stats-grid" style={{ marginBottom: '32px' }}>
          <div className="stat-card card">
            <span className="stat-label">Daily Avg Return</span>
            <div className="stat-value" style={{ color: marketStats.average_daily_change_pct >= 0 ? '#10b981' : '#ef4444' }}>
              {marketStats.average_daily_change_pct > 0 ? '+' : ''}{marketStats.average_daily_change_pct.toFixed(2)}%
            </div>
            <span className="stat-sub text-muted">Equal-Weighted Change</span>
          </div>

          <div className="stat-card card">
            <span className="stat-label">Total Volume</span>
            <div className="stat-value text-white">
              {(marketStats.total_volume / 1000000).toFixed(1)}M
            </div>
            <span className="stat-sub text-muted">Daily Volume Traded</span>
          </div>

          <div className="stat-card card">
            <span className="stat-label">Avg Composite Score</span>
            <div className="stat-value text-white">
              {scannerSummary.avg_composite.toFixed(2)}
            </div>
            <span className="stat-sub text-muted">Range: {scannerSummary.min_composite.toFixed(1)} to {scannerSummary.max_composite.toFixed(1)}</span>
          </div>

          <div className="stat-card card">
            <span className="stat-label">Market Breadth Ratio</span>
            <div style={{ display: 'flex', gap: '8px', marginTop: '12px', alignItems: 'center' }}>
              <span style={{ color: '#10b981', fontWeight: 700 }}>{bullishCount} B</span>
              <span className="text-muted">/</span>
              <span style={{ color: '#f59e0b', fontWeight: 700 }}>{neutralCount} H</span>
              <span className="text-muted">/</span>
              <span style={{ color: '#ef4444', fontWeight: 700 }}>{bearishCount} S</span>
            </div>
            <span className="stat-sub text-muted">Buys vs Holds vs Sells</span>
          </div>
        </div>
      )}

      {/* Breadth Bar & Ratings Distribution */}
      <div className="two-col" style={{ marginBottom: '32px' }}>
        {/* Breadth Analysis */}
        <div className="card" style={{ padding: '20px' }}>
          <h2 className="card-title" style={{ marginBottom: '16px' }}>📊 Nifty 50 Market Breadth</h2>
          <div className="gru-probs-bar" style={{ height: '28px', borderRadius: '6px', overflow: 'hidden', display: 'flex' }}>
            <div style={{ width: `${bullishPct}%`, background: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '12px', fontWeight: 'bold' }}>
              {bullishPct > 10 ? `Bullish: ${bullishPct.toFixed(0)}%` : ''}
            </div>
            <div style={{ width: `${neutralPct}%`, background: '#f59e0b', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '12px', fontWeight: 'bold' }}>
              {neutralPct > 10 ? `Neutral: ${neutralPct.toFixed(0)}%` : ''}
            </div>
            <div style={{ width: `${bearishPct}%`, background: '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '12px', fontWeight: 'bold' }}>
              {bearishPct > 10 ? `Bearish: ${bearishPct.toFixed(0)}%` : ''}
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px', fontSize: '13px' }}>
            <span style={{ color: '#10b981', fontWeight: 600 }}>🟢 Bullish (STRONG BUY/BUY): {bullishCount}</span>
            <span style={{ color: '#f59e0b', fontWeight: 600 }}>🟡 Neutral (HOLD): {neutralCount}</span>
            <span style={{ color: '#ef4444', fontWeight: 600 }}>🔴 Bearish (SELL/STRONG SELL): {bearishCount}</span>
          </div>
        </div>

        {/* Rating Distribution */}
        <div className="card" style={{ padding: '20px' }}>
          <h2 className="card-title" style={{ marginBottom: '16px' }}>⭐ Rating Distribution</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {distItems.map((item) => (
              <div key={item.label} className="distribution-row" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span className="distribution-label" style={{ color: item.color, width: '110px', fontSize: '12px', fontWeight: 700 }}>
                  {item.label}
                </span>
                <div className="distribution-bar-track" style={{ flex: 1, background: 'rgba(255,255,255,0.05)', height: '16px', borderRadius: '4px', overflow: 'hidden' }}>
                  <div
                    className="distribution-bar-fill"
                    style={{
                      width: `${(item.count / maxCount) * 100}%`,
                      backgroundColor: item.color,
                      height: '100%',
                      minWidth: item.count > 0 ? '20px' : '0',
                      transition: 'width 0.5s ease-out',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'flex-end',
                      paddingRight: '6px',
                      color: '#000',
                      fontSize: '10px',
                      fontWeight: 800
                    }}
                  >
                    {item.count > 0 ? item.count : ''}
                  </div>
                </div>
                <span style={{ color: item.color, fontWeight: 700, width: '20px', textAlign: 'right', fontSize: '12px' }}>
                  {item.count}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Gainers & Losers */}
      {marketStats && (
        <div className="two-col" style={{ marginBottom: '32px' }}>
          {/* Top Gainers */}
          <div className="card" style={{ padding: '20px' }}>
            <h3 className="card-title" style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>🚀</span> Top Gainers Today
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '12px' }}>
              {marketStats.top_gainers.map((g) => (
                <div key={g.symbol} className="stock-list-item" onClick={() => navigate(`/stock/${encodeURIComponent(g.symbol)}`)} style={{ padding: '10px', borderRadius: '6px', background: 'rgba(16,185,129,0.03)', display: 'flex', justifyContent: 'space-between', cursor: 'pointer' }}>
                  <span className="symbol">{g.symbol}</span>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 700 }}>₹{g.current_price.toFixed(2)}</div>
                    <span style={{ color: '#10b981', fontWeight: 600, fontSize: '12px' }}>+{g.daily_change_pct.toFixed(2)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Top Losers */}
          <div className="card" style={{ padding: '20px' }}>
            <h3 className="card-title" style={{ color: '#ef4444', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>📉</span> Top Losers Today
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '12px' }}>
              {marketStats.top_losers.map((l) => (
                <div key={l.symbol} className="stock-list-item" onClick={() => navigate(`/stock/${encodeURIComponent(l.symbol)}`)} style={{ padding: '10px', borderRadius: '6px', background: 'rgba(239,68,68,0.03)', display: 'flex', justifyContent: 'space-between', cursor: 'pointer' }}>
                  <span className="symbol">{l.symbol}</span>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 700 }}>₹{l.current_price.toFixed(2)}</div>
                    <span style={{ color: '#ef4444', fontWeight: 600, fontSize: '12px' }}>{l.daily_change_pct.toFixed(2)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Full Screener Table (the only page allowed to show all Nifty 50 stocks) */}
      <div className="card" style={{ padding: '20px' }}>
        <h2 className="card-title" style={{ marginBottom: '8px' }}>🔍 Full Universe Stock Screener</h2>
        <p className="text-muted text-sm" style={{ marginBottom: '16px' }}>Complete rating and score index of the Nifty 50 universe. Sort and filter below.</p>

        {/* Controls */}
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '16px' }}>
          <input
            className="header-search"
            placeholder="Search symbol..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: '200px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: '6px' }}
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
            Showing {filtered.length} of {stocks.length} stocks
          </span>
        </div>

        {/* Table */}
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('Symbol')} className={sortKey === 'Symbol' ? 'sorted' : ''}>Symbol</th>
                <th onClick={() => handleSort('FinalRating')} className={sortKey === 'FinalRating' ? 'sorted' : ''}>Rating</th>
                <th onClick={() => handleSort('Confidence')} className={sortKey === 'Confidence' ? 'sorted' : ''}>Confidence</th>
                <th onClick={() => handleSort('CompositeScoreV2')} className={sortKey === 'CompositeScoreV2' ? 'sorted' : ''}>Composite</th>
                <th onClick={() => handleSort('TechnicalScore')} className={sortKey === 'TechnicalScore' ? 'sorted' : ''}>Technical</th>
                <th onClick={() => handleSort('MLScore')} className={sortKey === 'MLScore' ? 'sorted' : ''}>ML Score</th>
                <th onClick={() => handleSort('GRUScore')} className={sortKey === 'GRUScore' ? 'sorted' : ''}>GRU Score</th>
                <th onClick={() => handleSort('ReliabilityScore')} className={sortKey === 'ReliabilityScore' ? 'sorted' : ''}>Reliability</th>
                <th onClick={() => handleSort('Sector')} className={sortKey === 'Sector' ? 'sorted' : ''}>Sector</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((stock) => (
                <tr
                  key={stock.Symbol}
                  onClick={() => navigate(`/stock/${encodeURIComponent(stock.Symbol)}`)}
                  style={{ cursor: 'pointer' }}
                >
                  <td><span className="symbol">{stock.Symbol}</span></td>
                  <td><RatingBadge rating={stock.FinalRating} /></td>
                  <td style={{ minWidth: '140px' }}>
                    <ConfidenceBar value={stock.Confidence} />
                  </td>
                  <td style={{ fontWeight: 600, color: stock.CompositeScoreV2 > 0 ? '#10b981' : '#ef4444' }}>
                    {stock.CompositeScoreV2.toFixed(2)}
                  </td>
                  <td style={{ fontWeight: 600 }}>{stock.TechnicalScore.toFixed(1)}</td>
                  <td style={{ fontWeight: 600 }}>{stock.MLScore.toFixed(1)}</td>
                  <td style={{ fontWeight: 600 }}>{stock.GRUScore.toFixed(1)}</td>
                  <td>{stock.ReliabilityScore.toFixed(0)}</td>
                  <td style={{ color: 'var(--text-muted)' }}>{stock.Sector}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

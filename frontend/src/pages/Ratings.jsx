import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchRatingsDistribution, fetchStocks } from '../api/stocks';
import RatingBadge from '../components/common/RatingBadge';
import ConfidenceBar from '../components/common/ConfidenceBar';
import LoadingSpinner from '../components/common/LoadingSpinner';

const RATING_ORDER = ['STRONG BUY', 'BUY', 'HOLD', 'SELL', 'STRONG SELL'];

const RATING_COLORS = {
  'STRONG BUY': '#10b981',
  'BUY': '#34d399',
  'HOLD': '#f59e0b',
  'SELL': '#f97316',
  'STRONG SELL': '#ef4444',
};

const DIST_KEYS = {
  'STRONG BUY': 'strong_buy',
  'BUY': 'buy',
  'HOLD': 'hold',
  'SELL': 'sell',
  'STRONG SELL': 'strong_sell',
};

export default function Ratings() {
  const [dist, setDist] = useState(null);
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([fetchRatingsDistribution(), fetchStocks()])
      .then(([distRes, stocksRes]) => {
        setDist(distRes.data);
        setStocks(stocksRes.data);
      })
      .finally(() => setLoading(false));
  }, []);

  const grouped = useMemo(() => {
    const groups = {};
    RATING_ORDER.forEach((r) => { groups[r] = []; });
    stocks.forEach((s) => {
      if (groups[s.FinalRating]) {
        groups[s.FinalRating].push(s);
      }
    });
    // Sort each group by composite desc
    Object.values(groups).forEach((arr) =>
      arr.sort((a, b) => b.CompositeScoreV2 - a.CompositeScoreV2)
    );
    return groups;
  }, [stocks]);

  if (loading) return <LoadingSpinner />;

  const maxCount = dist
    ? Math.max(...Object.values(dist), 1)
    : 1;

  return (
    <div className="fade-in">
      {/* Distribution */}
      <div className="card page-section">
        <div className="card-title">Rating Distribution</div>
        {RATING_ORDER.map((rating) => {
          const count = dist?.[DIST_KEYS[rating]] || 0;
          return (
            <div key={rating} className="distribution-row">
              <span className="distribution-label" style={{ color: RATING_COLORS[rating] }}>
                {rating}
              </span>
              <div className="distribution-bar-track">
                <div
                  className="distribution-bar-fill"
                  style={{
                    width: `${(count / maxCount) * 100}%`,
                    backgroundColor: RATING_COLORS[rating],
                    minWidth: count > 0 ? '40px' : '0',
                  }}
                >
                  {count}
                </div>
              </div>
              <span className="distribution-count" style={{ color: RATING_COLORS[rating] }}>
                {count}
              </span>
            </div>
          );
        })}
      </div>

      {/* Grouped Stocks */}
      {RATING_ORDER.map((rating) => (
        <div key={rating} className="rating-group">
          <div className="rating-group-header">
            <RatingBadge rating={rating} large />
            <span className="rating-group-count">
              {grouped[rating]?.length || 0} stocks
            </span>
          </div>
          <div className="rating-group-stocks">
            {grouped[rating]?.map((stock) => (
              <div
                key={stock.Symbol}
                className="rating-stock-card"
                onClick={() => navigate(`/stock/${encodeURIComponent(stock.Symbol)}`)}
              >
                <div className="stock-symbol">{stock.Symbol}</div>
                <ConfidenceBar value={stock.Confidence} />
                <div className="stock-composite" style={{
                  color: stock.CompositeScoreV2 >= 0 ? '#10b981' : '#ef4444',
                }}>
                  Composite: {stock.CompositeScoreV2 > 0 ? '+' : ''}{stock.CompositeScoreV2.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

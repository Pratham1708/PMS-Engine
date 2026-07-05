import { useState } from 'react';
import { fetchPortfolio } from '../api/stocks';
import RatingBadge from '../components/common/RatingBadge';
import ConfidenceBar from '../components/common/ConfidenceBar';
import StatCard from '../components/common/StatCard';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const COLORS = [
  '#6366f1', '#818cf8', '#a78bfa', '#c4b5fd', '#10b981',
  '#34d399', '#6ee7b7', '#f59e0b', '#fbbf24', '#fcd34d',
  '#fb923c', '#f97316', '#ef4444', '#f87171', '#fca5a5',
];

const formatINR = (val) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(val);

function confidenceColor(val) {
  if (val >= 80) return '#10b981';
  if (val >= 60) return '#f59e0b';
  return '#ef4444';
}

export default function Portfolio() {
  const [capital, setCapital] = useState(1000000);
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleBuild = () => {
    if (capital <= 0) return;
    setLoading(true);
    fetchPortfolio(capital)
      .then((res) => setPortfolio(res.data))
      .finally(() => setLoading(false));
  };

  const chartData = portfolio?.stocks.map((s) => ({
    name: s.Symbol,
    value: parseFloat(s.Weight.toFixed(2)),
  })) || [];

  return (
    <div className="fade-in">
      {/* Capital Input */}
      <div className="card page-section">
        <div className="card-title">Investment Capital</div>
        <div className="capital-input-group">
          <span className="capital-prefix">₹</span>
          <input
            className="capital-input"
            type="number"
            value={capital}
            onChange={(e) => setCapital(Number(e.target.value))}
            min="0"
            step="100000"
          />
          <button className="btn btn-primary" onClick={handleBuild}>
            Build Portfolio
          </button>
        </div>
        <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Portfolio allocates only to STRONG BUY and BUY rated stocks using conviction-weighted methodology.
        </div>
      </div>

      {loading && <LoadingSpinner />}

      {portfolio && !loading && (
        <>
          {/* Metrics */}
          <div className="stats-grid">
            <StatCard label="Capital" value={formatINR(portfolio.capital)} />
            <StatCard label="Stocks Selected" value={portfolio.total_stocks} color="#6366f1" />
            <StatCard
              label="Avg Confidence"
              value={portfolio.avg_confidence.toFixed(1)}
              color={confidenceColor(portfolio.avg_confidence)}
            />
            <StatCard
              label="Avg Composite"
              value={portfolio.avg_composite.toFixed(2)}
              color="#10b981"
            />
          </div>

          <div className="two-col page-section">
            {/* Allocation Table */}
            <div className="card" style={{ padding: 0, overflow: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Rating</th>
                    <th>Weight %</th>
                    <th>Amount</th>
                    <th>Confidence</th>
                    <th>Composite</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolio.stocks.map((s) => (
                    <tr key={s.Symbol}>
                      <td><span className="symbol">{s.Symbol}</span></td>
                      <td><RatingBadge rating={s.FinalRating} /></td>
                      <td style={{ fontWeight: 700 }}>{s.Weight.toFixed(2)}%</td>
                      <td style={{ fontWeight: 600 }}>{formatINR(s.Amount)}</td>
                      <td style={{ minWidth: '140px' }}>
                        <ConfidenceBar value={s.Confidence} />
                      </td>
                      <td style={{ color: s.CompositeScoreV2 >= 0 ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                        {s.CompositeScoreV2.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Donut Chart */}
            <div className="card">
              <div className="card-title">Weight Distribution</div>
              <div className="portfolio-chart-container">
                <ResponsiveContainer width="100%" height={360}>
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={80}
                      outerRadius={140}
                      dataKey="value"
                      stroke="rgba(0,0,0,0.3)"
                      strokeWidth={2}
                    >
                      {chartData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: '#1f2937',
                        border: '1px solid rgba(55,65,81,0.5)',
                        borderRadius: '8px',
                        color: '#f9fafb',
                        fontSize: '13px',
                      }}
                      formatter={(value) => [`${value.toFixed(2)}%`, 'Weight']}
                    />
                    <Legend
                      wrapperStyle={{ fontSize: '12px', color: '#9ca3af' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

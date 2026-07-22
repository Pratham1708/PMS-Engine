import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchMyStocks, fetchRecentAnalysis, runAnalysis } from '../api/stocks';
import RatingBadge from '../components/common/RatingBadge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { ResponsiveGrid } from '../components/layout/ResponsiveLayoutEngine';

function statusColor(status) {
  switch (status) {
    case 'Fresh': return '#10b981'; // Green
    case 'Recent': return '#3b82f6'; // Blue
    case 'Aging': return '#f59e0b'; // Orange
    case 'Stale': return '#ef4444'; // Red
    default: return '#9ca3af'; // Grey
  }
}

export default function Dashboard() {
  const [myStocks, setMyStocks] = useState([]);
  const [recentAnalysis, setRecentAnalysis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [spinningSymbols, setSpinningSymbols] = useState(new Set());
  const navigate = useNavigate();

  const loadData = () => {
    return Promise.all([fetchMyStocks(), fetchRecentAnalysis()])
      .then(([myRes, recentRes]) => {
        setMyStocks(myRes.data || []);
        setRecentAnalysis(recentRes.data || []);
      })
      .catch((err) => console.error('Failed to load dashboard data', err));
  };

  useEffect(() => {
    loadData().finally(() => setLoading(false));
  }, []);

  const handleReAnalyze = async (symbol, e) => {
    e.stopPropagation();
    
    setSpinningSymbols((prev) => {
      const next = new Set(prev);
      next.add(symbol.toUpperCase());
      return next;
    });

    try {
      await runAnalysis(symbol);
      await loadData();
    } catch (err) {
      console.error('Re-analysis failed', err);
      alert(`Re-analysis failed for ${symbol}`);
    } finally {
      setSpinningSymbols((prev) => {
        const next = new Set(prev);
        next.delete(symbol.toUpperCase());
        return next;
      });
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="fade-in">
      <div className="reports-hero" style={{ marginBottom: '24px', padding: 'var(--card-padding)', borderRadius: 'var(--radius-md)' }}>
        <h1 className="reports-hero-title" style={{ fontSize: 'var(--font-size-h2)' }}>📊 Dashboard Signals Cache</h1>
        <p className="reports-hero-subtitle" style={{ fontSize: 'var(--font-size-body)', marginTop: '4px' }}>
          Real-time cache viewer presenting the last known intelligence outputs from the PMS Engine.
        </p>
      </div>

      <ResponsiveGrid cols={{ desktop: 2, tablet: 1, mobile: 1 }} gap="var(--spacing-md)">
        {/* Tracked Stock Signals */}
        <div className="card" style={{ padding: 'var(--card-padding)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 className="card-title" style={{ margin: 0, fontSize: '1.1rem' }}>⭐ My Stocks Last Signals</h2>
            <span className="text-muted text-sm">{myStocks.length} Tracked</span>
          </div>

          {myStocks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
              <p>No stocks currently in your research universe.</p>
              <button 
                className="btn btn-primary touch-target-44" 
                style={{ marginTop: '16px' }}
                onClick={() => navigate('/search')}
              >
                🔍 Search & Track Stocks
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {myStocks.map((stock) => {
                const isSpinning = spinningSymbols.has(stock.symbol.toUpperCase());
                return (
                  <div 
                    key={stock.symbol} 
                    className="stock-list-item"
                    onClick={() => navigate(`/stock/${encodeURIComponent(stock.symbol)}`)}
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '12px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'rgba(255,255,255,0.03)',
                      cursor: 'pointer',
                      gap: '8px'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '15px', color: '#fff' }}>{stock.symbol}</div>
                      {stock.current_price !== null && (
                        <div className="text-sm text-muted">₹{stock.current_price.toFixed(2)}</div>
                      )}
                    </div>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <RatingBadge rating={stock.rating} />
                      <button
                        className="btn btn-secondary text-xs font-semibold touch-target-44"
                        style={{ padding: '4px 10px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                        disabled={isSpinning}
                        onClick={(e) => handleReAnalyze(stock.symbol, e)}
                      >
                        {isSpinning ? '⏳' : '▶ Re-Analyze'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Recent Analysis Runs */}
        <div className="card" style={{ padding: 'var(--card-padding)' }}>
          <h2 className="card-title" style={{ marginBottom: '16px', fontSize: '1.1rem' }}>⏱️ Recently Analyzed Stocks</h2>
          
          {recentAnalysis.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
              <p>No recent analysis logs found in SQLite cache.</p>
              <p className="text-xs" style={{ marginTop: '8px' }}>Open any stock and run the PMS rating algorithm to build your cache history.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {recentAnalysis.map((run) => {
                const isSpinning = spinningSymbols.has(run.symbol.toUpperCase());
                return (
                  <div 
                    key={run.symbol}
                    className="stock-list-item"
                    onClick={() => navigate(`/stock/${encodeURIComponent(run.symbol)}`)}
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '12px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'rgba(255,255,255,0.03)',
                      cursor: 'pointer',
                      gap: '8px'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '15px', color: '#fff' }}>{run.symbol}</div>
                      {run.current_price !== null && (
                        <div className="text-sm text-muted">₹{run.current_price.toFixed(2)}</div>
                      )}
                    </div>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <RatingBadge rating={run.rating} />
                      <button
                        className="btn btn-secondary text-xs font-semibold touch-target-44"
                        style={{ padding: '4px 10px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                        disabled={isSpinning}
                        onClick={(e) => handleReAnalyze(run.symbol, e)}
                      >
                        {isSpinning ? '⏳' : '▶ Re-Analyze'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </ResponsiveGrid>
    </div>
  );
}

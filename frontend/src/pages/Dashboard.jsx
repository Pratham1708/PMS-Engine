import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchMyStocks, fetchRecentAnalysis, runAnalysis } from '../api/stocks';
import RatingBadge from '../components/common/RatingBadge';
import LoadingSpinner from '../components/common/LoadingSpinner';

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
    
    // Add to loading set
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
      // Remove from loading set
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
      <div className="reports-hero" style={{ marginBottom: '24px', padding: '24px', borderRadius: '12px' }}>
        <h1 className="reports-hero-title" style={{ fontSize: '24px' }}>📊 Dashboard Signals Cache</h1>
        <p className="reports-hero-subtitle" style={{ fontSize: '14px', marginTop: '4px' }}>
          Real-time cache viewer presenting the last known intelligence outputs from the PMS Engine.
        </p>
      </div>

      <div className="two-col">
        {/* Tracked Stock Signals */}
        <div className="card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 className="card-title" style={{ margin: 0 }}>⭐ My Stocks Last Signals</h2>
            <span className="text-muted text-sm">{myStocks.length} Tracked</span>
          </div>

          {myStocks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
              <p>No stocks currently in your research universe.</p>
              <button 
                className="btn btn-primary" 
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
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      padding: '12px',
                      borderRadius: '8px',
                      background: 'rgba(255,255,255,0.03)',
                      cursor: 'pointer',
                      transition: 'transform 0.2s'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.transform = 'translateX(4px)'}
                    onMouseLeave={(e) => e.currentTarget.style.transform = 'none'}
                  >
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '16px', color: '#fff' }}>{stock.symbol}</div>
                      <div className="text-sm text-muted">{stock.sector}</div>
                    </div>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                        {stock.last_rating === 'Not Analyzed' ? (
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px' }}>
                            NOT ANALYZED
                          </span>
                        ) : (
                          <>
                            <RatingBadge rating={stock.last_rating} />
                            {stock.last_confidence !== null && (
                              <span className="text-xs text-muted" style={{ fontWeight: 600 }}>
                                Conf: {stock.last_confidence.toFixed(1)}%
                              </span>
                            )}
                          </>
                        )}
                      </div>

                      {stock.analyzed_at ? (
                        <div className="text-xs text-muted" style={{ minWidth: '100px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                          <span className="badge-status" style={{ 
                            background: `${statusColor(stock.last_status)}20`, 
                            color: statusColor(stock.last_status),
                            border: `1px solid ${statusColor(stock.last_status)}40`,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontWeight: 'bold',
                            fontSize: '10px',
                            marginBottom: '4px'
                          }}>
                            {stock.last_status.toUpperCase()}
                          </span>
                          <span style={{ fontSize: '10px' }}>{stock.analyzed_at.split(' ')[0]}</span>
                        </div>
                      ) : (
                        <div className="text-xs text-muted" style={{ minWidth: '100px', textAlign: 'right' }}>
                          <span className="badge-status" style={{ 
                            background: 'rgba(239,68,68,0.1)', 
                            color: '#ef4444',
                            border: '1px solid rgba(239,68,68,0.2)',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontWeight: 'bold',
                            fontSize: '10px'
                          }}>
                            STALE
                          </span>
                        </div>
                      )}

                      <button
                        className="btn btn-secondary text-xs font-semibold"
                        style={{ padding: '6px 10px', height: '32px', display: 'flex', alignItems: 'center', minWidth: '95px', justifyContent: 'center' }}
                        disabled={isSpinning}
                        onClick={(e) => handleReAnalyze(stock.symbol, e)}
                      >
                        {isSpinning ? '⏳ Running...' : '▶ Re-Analyze'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Recent Analysis Runs */}
        <div className="card" style={{ padding: '20px' }}>
          <h2 className="card-title" style={{ marginBottom: '16px' }}>⏱️ Recently Analyzed Stocks</h2>
          
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
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '12px',
                      borderRadius: '8px',
                      background: 'rgba(255,255,255,0.03)',
                      cursor: 'pointer',
                      transition: 'transform 0.2s'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.transform = 'translateX(4px)'}
                    onMouseLeave={(e) => e.currentTarget.style.transform = 'none'}
                  >
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '15px', color: '#fff' }}>{run.symbol}</div>
                      {run.current_price !== null && (
                        <div className="text-sm text-muted">₹{run.current_price.toFixed(2)}</div>
                      )}
                    </div>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                        <RatingBadge rating={run.rating} />
                        <span className="text-xs text-muted" style={{ fontWeight: 500 }}>
                          Comp: {run.composite_score.toFixed(2)}
                        </span>
                      </div>

                      <div className="text-xs text-muted" style={{ minWidth: '100px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                        <span className="badge-status" style={{ 
                          background: `${statusColor(run.status)}20`, 
                          color: statusColor(run.status),
                          border: `1px solid ${statusColor(run.status)}40`,
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontWeight: 'bold',
                          fontSize: '10px',
                          marginBottom: '4px'
                        }}>
                          {run.status.toUpperCase()}
                        </span>
                        <span style={{ fontSize: '10px' }}>{run.analyzed_at.split(' ')[0]}</span>
                      </div>

                      <button
                        className="btn btn-secondary text-xs font-semibold"
                        style={{ padding: '6px 10px', height: '32px', display: 'flex', alignItems: 'center', minWidth: '95px', justifyContent: 'center' }}
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
      </div>
    </div>
  );
}

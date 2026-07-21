import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchResearchWorkspace, addToMyStocks, deleteFromMyStocks, runAnalysis } from '../api/stocks';
import RatingBadge from '../components/common/RatingBadge';
import StatCard from '../components/common/StatCard';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { getReportDownloadUrl } from '../api/reports';

function statusColor(status) {
  switch (status) {
    case 'Fresh': return '#10b981'; // Green
    case 'Recent': return '#3b82f6'; // Blue
    case 'Aging': return '#f59e0b'; // Orange
    case 'Stale': return '#ef4444'; // Red
    default: return '#9ca3af'; // Grey
  }
}

export default function ResearchWorkspace() {
  const [workspace, setWorkspace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quickSymbol, setQuickSymbol] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [spinningSymbols, setSpinningSymbols] = useState(new Set());
  const navigate = useNavigate();

  const loadWorkspace = () => {
    return fetchResearchWorkspace()
      .then((res) => {
        setWorkspace(res.data);
        setError(null);
      })
      .catch((err) => console.error('Failed to load workspace data', err));
  };

  useEffect(() => {
    loadWorkspace().finally(() => setLoading(false));
  }, []);

  const handleQuickAdd = async (e) => {
    e.preventDefault();
    if (!quickSymbol) return;
    setError(null);
    setSuccess(null);

    const formatted = quickSymbol.trim().toUpperCase().replace(/\.NS$/i, '');

    try {
      await addToMyStocks(formatted);
      setSuccess(`Successfully added ${formatted} to tracked universe!`);
      setQuickSymbol('');
      await loadWorkspace();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to add symbol ${formatted}. Verify it belongs to Nifty 50.`);
      setTimeout(() => setError(null), 4000);
    }
  };

  const handleRemove = async (symbol, e) => {
    e.stopPropagation();
    try {
      await deleteFromMyStocks(symbol);
      await loadWorkspace();
    } catch (err) {
      console.error('Failed to remove stock', err);
    }
  };

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
      await loadWorkspace();
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
  if (!workspace) return <div>Failed to load workspace</div>;

  const { my_stocks, recent_analysis, saved_reports, universe_stats } = workspace;

  return (
    <div className="fade-in">
      {/* Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 className="stock-title" style={{ margin: 0, fontSize: '28px' }}>🏠 Research Workspace</h1>
          <p className="text-muted" style={{ marginTop: '4px' }}>AI-Powered Personalized Stock Intelligence Hub</p>
        </div>
        <span className="text-muted text-sm font-semibold">Institutional Grade • Auditable Inputs Only</span>
      </div>

      {/* Universe Stats Banner */}
      <div className="stats-grid" style={{ marginBottom: '32px' }}>
        <StatCard label="My Tracked Stocks" value={universe_stats.my_stocks_count} sub="Custom Universe Size" color="#6366f1" />
        <StatCard label="Nifty 50 Universe" value={universe_stats.total_universe} sub="Active Scanner Coverage" />
        <StatCard label="Workspace Analysis Coverage" value={`${universe_stats.analyzed_universe_count} / ${universe_stats.total_universe}`} sub="Stocks Analyzed in DB" color="#10b981" />
      </div>

      {/* Quick Tracking Widget */}
      <div className="card" style={{ marginBottom: '32px', padding: '20px' }}>
        <h3 className="card-title" style={{ marginBottom: '8px' }}>➕ Quick Track Ticker</h3>
        <p className="text-muted text-sm" style={{ marginBottom: '16px' }}>Add any Nifty 50 ticker symbol (e.g. RELIANCE, TCS, INFY) to track it in your custom workspace.</p>
        
        <form onSubmit={handleQuickAdd} style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            className="header-search"
            placeholder="e.g. RELIANCE"
            value={quickSymbol}
            onChange={(e) => setQuickSymbol(e.target.value)}
            style={{ width: '240px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: '6px' }}
          />
          <button type="submit" className="btn btn-primary" style={{ height: '40px' }}>
            Track Stock
          </button>
          
          {success && <span style={{ color: '#10b981', marginLeft: '12px', fontWeight: 600, fontSize: '14px' }}>✓ {success}</span>}
          {error && <span style={{ color: '#ef4444', marginLeft: '12px', fontWeight: 600, fontSize: '14px' }}>⚠️ {error}</span>}
        </form>
      </div>

      {/* Custom Universe List */}
      <div className="card" style={{ marginBottom: '32px', padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 className="card-title" style={{ margin: 0 }}>⭐ Tracked Stocks Universe (My Stocks)</h2>
          <button className="btn btn-secondary" onClick={() => navigate('/search')}>
            🔍 Search Tickers
          </button>
        </div>

        {my_stocks.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📁</div>
            <p style={{ fontSize: '16px', fontWeight: 600 }}>Your workspace is currently empty</p>
            <p className="text-sm" style={{ marginTop: '4px', marginBottom: '20px' }}>Track stocks using the quick add widget above or search the Nifty 50 database.</p>
            <button className="btn btn-primary" onClick={() => navigate('/search')}>
              🔍 Browse Nifty 50 Universe
            </button>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Sector</th>
                  <th>Live Price</th>
                  <th>Day Change</th>
                  <th>Last Rating</th>
                  <th>Last Confidence</th>
                  <th>Freshness</th>
                  <th>Last Analysis Time</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {my_stocks.map((stock) => {
                  const isSpinning = spinningSymbols.has(stock.symbol.toUpperCase());
                  return (
                    <tr 
                      key={stock.symbol}
                      onClick={() => navigate(`/stock/${encodeURIComponent(stock.symbol)}`)}
                      style={{ cursor: 'pointer' }}
                    >
                      <td><span className="symbol">{stock.symbol}</span></td>
                      <td style={{ color: 'var(--text-muted)' }}>{stock.sector}</td>
                      <td style={{ fontWeight: 600 }}>
                        {stock.current_price !== null ? `₹${stock.current_price.toFixed(2)}` : '—'}
                      </td>
                      <td style={{ 
                        fontWeight: 600, 
                        color: stock.daily_change_pct > 0 ? '#10b981' : stock.daily_change_pct < 0 ? '#ef4444' : 'var(--text-muted)'
                      }}>
                        {stock.daily_change_pct !== null ? `${stock.daily_change_pct > 0 ? '+' : ''}${stock.daily_change_pct.toFixed(2)}%` : '—'}
                      </td>
                      <td>
                        {stock.last_rating === 'Not Analyzed' ? (
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px' }}>
                            Not Analyzed
                          </span>
                        ) : (
                          <RatingBadge rating={stock.last_rating} />
                        )}
                      </td>
                      <td style={{ fontWeight: 600 }}>
                        {stock.last_confidence !== null ? `${stock.last_confidence.toFixed(1)}%` : '—'}
                      </td>
                      <td>
                        <span className="badge-status" style={{ 
                          background: `${statusColor(stock.last_status)}15`, 
                          color: statusColor(stock.last_status),
                          border: `1px solid ${statusColor(stock.last_status)}30`,
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontWeight: 'bold',
                          fontSize: '11px'
                        }}>
                          {stock.last_status}
                        </span>
                      </td>
                      <td className="text-sm text-muted">
                        {stock.analyzed_at ? stock.analyzed_at : 'No analysis run yet'}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                          <button
                            className="btn btn-secondary text-sm"
                            style={{ padding: '4px 10px', display: 'flex', alignItems: 'center', minWidth: '105px', justifyContent: 'center' }}
                            disabled={isSpinning}
                            onClick={(e) => handleReAnalyze(stock.symbol, e)}
                          >
                            {isSpinning ? '⏳ Running...' : '▶ Re-Analyze'}
                          </button>
                          <button 
                            className="btn btn-back text-sm" 
                            style={{ padding: '4px 8px', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)' }}
                            onClick={(e) => handleRemove(stock.symbol, e)}
                          >
                            Untrack
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Two columns: Recent analysis log & Generated research reports */}
      <div className="two-col">
        {/* Workspace Recent Analyses */}
        <div className="card" style={{ padding: '20px' }}>
          <h2 className="card-title" style={{ marginBottom: '16px' }}>⏱️ Recent Workspace Runs</h2>
          
          {recent_analysis.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--text-muted)' }}>
              <p>No analysis records found.</p>
              <p className="text-xs" style={{ marginTop: '4px' }}>Manual stock analyses you run will show up here.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {recent_analysis.map((run) => (
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
                    background: 'rgba(255,255,255,0.02)',
                    cursor: 'pointer'
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '15px', color: '#fff' }}>{run.symbol}</div>
                    <div className="text-xs text-muted">{run.sector}</div>
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
                        background: `${statusColor(run.status)}15`, 
                        color: statusColor(run.status),
                        border: `1px solid ${statusColor(run.status)}30`,
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
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Saved Research Reports */}
        <div className="card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 className="card-title" style={{ margin: 0 }}>📄 Saved PDF Reports</h2>
            <button className="btn btn-secondary text-sm" onClick={() => navigate('/reports')}>
              View All
            </button>
          </div>
          
          {saved_reports.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--text-muted)' }}>
              <p>No reports generated yet.</p>
              <p className="text-xs" style={{ marginTop: '4px' }}>Go to the Reports page to generate PDF research briefs.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {saved_reports.map((report) => (
                <div 
                  key={report.report_id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '12px',
                    borderRadius: '8px',
                    background: 'rgba(255,255,255,0.02)'
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '14px', color: '#fff' }}>
                      {report.type === 'stock' ? `📈 ${report.report_id.split('_')[1]}` : report.type === 'portfolio' ? '💼 Portfolio' : '🌐 Market'}
                    </div>
                    <div className="text-xs text-muted">
                      {new Date(report.generated_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                    </div>
                  </div>
                  
                  {report.has_pdf && (
                    <a 
                      href={getReportDownloadUrl(report.report_id, 'pdf')}
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="btn btn-secondary text-sm"
                      style={{ padding: '4px 10px', textDecoration: 'none' }}
                    >
                      📥 PDF
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

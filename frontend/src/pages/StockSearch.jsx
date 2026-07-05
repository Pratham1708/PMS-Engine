import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchStocks, addToMyStocks, fetchMyStocks } from '../api/stocks';

export default function StockSearch() {
  const [stocks, setStocks] = useState([]);
  const [myStockSymbols, setMyStockSymbols] = useState(new Set());
  const [search, setSearch] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const navigate = useNavigate();

  // Load user workspace tracking list once
  useEffect(() => {
    fetchMyStocks()
      .then((myStocksRes) => {
        const symbols = new Set(
          (myStocksRes.data || []).map((s) => s.symbol.toUpperCase())
        );
        setMyStockSymbols(symbols);
      })
      .catch((err) => console.error('Failed to load tracked workspace symbols', err));
  }, []);

  // Fetch stocks dynamically from API based on search input
  useEffect(() => {
    fetchStocks(search ? { search } : {})
      .then((res) => {
        setStocks(res.data || []);
      })
      .catch((err) => console.error('Failed to fetch stock search results', err));
  }, [search]);

  const handleTrack = async (symbol, e) => {
    e.stopPropagation();
    try {
      await addToMyStocks(symbol);
      setSuccessMsg(`Successfully tracked ${symbol}!`);
      // Reload tracked list
      const myStocksRes = await fetchMyStocks();
      const symbols = new Set(
        (myStocksRes.data || []).map((s) => s.symbol.toUpperCase())
      );
      setMyStockSymbols(symbols);
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (err) {
      console.error('Failed to track stock', err);
    }
  };

  return (
    <div className="fade-in">
      <div className="reports-hero" style={{ marginBottom: '24px', padding: '24px', borderRadius: '12px' }}>
        <h1 className="reports-hero-title" style={{ fontSize: '24px' }}>🔍 Stock Universe</h1>
        <p className="reports-hero-subtitle" style={{ fontSize: '14px', marginTop: '4px' }}>
          Explore the expanded universe of 100+ Indian equities. Track tickers to your workspace, or select a symbol to view profile details and generate a progressive research report.
        </p>
      </div>

      {successMsg && (
        <div style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid #10b981', color: '#10b981', padding: '12px', borderRadius: '6px', marginBottom: '20px', fontWeight: 600 }}>
          ✓ {successMsg}
        </div>
      )}

      {/* Search Bar */}
      <div className="card" style={{ padding: '16px', marginBottom: '24px', display: 'flex', gap: '12px', alignItems: 'center' }}>
        <span style={{ fontSize: '20px' }}>🔍</span>
        <input
          className="header-search"
          placeholder="Search by ticker symbol or sector..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ 
            flex: 1, 
            background: 'none', 
            border: 'none', 
            fontSize: '16px', 
            color: '#fff', 
            outline: 'none',
            padding: '4px 0' 
          }}
        />
        <span className="text-muted text-sm">{stocks.length} stocks found</span>
      </div>

      {/* Grid of covered stocks */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', 
        gap: '16px' 
      }}>
        {stocks.map((stock) => {
          const isTracked = myStockSymbols.has(stock.Symbol.toUpperCase());
          const isNotAnalyzed = stock.FinalRating === 'Not Analyzed';
          
          return (
            <div
              key={stock.Symbol}
              className="card stock-list-item"
              onClick={() => navigate(`/stock/${encodeURIComponent(stock.Symbol)}`)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'stretch',
                padding: '16px',
                borderRadius: '8px',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid var(--border-color)',
                cursor: 'pointer',
                margin: 0,
                transition: 'transform 0.2s, background-color 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.06)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'none';
                e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.03)';
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <div>
                  <div style={{ fontWeight: 800, fontSize: '18px', color: '#fff' }}>{stock.Symbol}</div>
                  <div className="text-xs text-muted" style={{ marginTop: '2px' }}>Sector: {stock.Sector}</div>
                </div>
                {isNotAnalyzed ? (
                  <span className="badge-not-analyzed" style={{ alignSelf: 'flex-start' }}>NOT ANALYZED</span>
                ) : (
                  stock.CurrentPrice !== null && (
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontWeight: 700, fontSize: '15px' }}>₹{stock.CurrentPrice.toFixed(2)}</div>
                      {stock.DailyChangePct !== null && (
                        <div className="text-xs" style={{ 
                          fontWeight: 600, 
                          color: stock.DailyChangePct > 0 ? '#10b981' : stock.DailyChangePct < 0 ? '#ef4444' : 'var(--text-muted)'
                        }}>
                          {stock.DailyChangePct > 0 ? '+' : ''}{stock.DailyChangePct.toFixed(2)}%
                        </div>
                      )}
                    </div>
                  )
                )}
              </div>

              <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                <button 
                  className="btn btn-primary text-sm" 
                  style={{ flex: 1, padding: '6px 12px' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/stock/${encodeURIComponent(stock.Symbol)}`);
                  }}
                >
                  🔬 Research
                </button>
                <button
                  className={`btn ${isTracked ? 'btn-secondary' : 'btn-back'} text-sm`}
                  style={{ 
                    flex: 1, 
                    padding: '6px 12px',
                    borderColor: isTracked ? 'transparent' : 'rgba(255,255,255,0.15)'
                  }}
                  disabled={isTracked}
                  onClick={(e) => handleTrack(stock.Symbol, e)}
                >
                  {isTracked ? '⭐ Tracking' : '＋ Track'}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {stocks.length === 0 && (
        <div style={{ textAlign: 'center', padding: '64px', color: 'var(--text-muted)' }}>
          <p style={{ fontSize: '16px' }}>No matching stocks found for "{search}"</p>
          <p className="text-xs" style={{ marginTop: '8px' }}>Ensure you are searching for covered NSE symbols (e.g. RELIANCE, ZOMATO, PAYTM).</p>
        </div>
      )}
    </div>
  );
}

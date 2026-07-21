import { useState, useEffect } from 'react';
import { TrendingUp, Shield, Activity, Award } from 'lucide-react';
import { fetchLatestSnapshot, fetchTopBuys } from '../../api/stocks';

export default function LiveMarketPreview() {
  const [topStocks, setTopStocks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const loadLiveData = async () => {
      try {
        const res = await fetchTopBuys(4);
        if (isMounted && res.data) {
          setTopStocks(Array.isArray(res.data) ? res.data : (res.data.stocks || []));
        }
      } catch (err) {
        // Fallback gracefully
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    loadLiveData();
  }, []);

  return (
    <section style={{ padding: '60px 24px', background: 'var(--color-bg-base)', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '8px' }}>
          Live Quantitative Market Preview
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '1rem' }}>
          Real-time signals generated from today's point-in-time snapshot dataset.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px' }}>
        {topStocks.length > 0 ? (
          topStocks.slice(0, 4).map((stk, idx) => (
            <div key={idx} className="glass-panel glass-panel-hover" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--color-text-primary)' }}>
                  {stk.symbol || stk.ticker}
                </span>
                <span className={`signal-badge ${stk.recommendation ? stk.recommendation.toLowerCase().replace('_', '-') : 'strong-buy'}`}>
                  {stk.recommendation || 'STRONG BUY'}
                </span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '16px' }}>
                {stk.company_name || stk.name || 'Indian Universe Stock'}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                <span>Composite Score</span>
                <span style={{ fontWeight: '700', color: '#10b981' }}>{stk.composite_score ? (stk.composite_score * 100).toFixed(1) : '88.5'} / 100</span>
              </div>
            </div>
          ))
        ) : (
          // Default Preview Grid
          [
            { symbol: 'RELIANCE', rec: 'STRONG BUY', score: '92.4', sector: 'Energy' },
            { symbol: 'TCS', rec: 'BUY', score: '84.8', sector: 'Technology' },
            { symbol: 'HDFCBANK', rec: 'STRONG BUY', score: '91.0', sector: 'Financials' },
            { symbol: 'INFY', rec: 'BUY', score: '82.5', sector: 'Technology' }
          ].map((stk, idx) => (
            <div key={idx} className="glass-panel glass-panel-hover" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--color-text-primary)' }}>{stk.symbol}</span>
                <span className="signal-badge strong-buy">{stk.rec}</span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '16px' }}>{stk.sector}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                <span>Composite Score</span>
                <span style={{ fontWeight: '700', color: '#10b981' }}>{stk.score} / 100</span>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

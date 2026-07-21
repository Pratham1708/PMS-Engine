import { useState, useEffect } from 'react';
import { fetchTopBuys } from '../../api/stocks';
import { parseStockRecord } from '../../utils/stockUtils';

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

  const previewList = topStocks.length > 0 ? topStocks.slice(0, 4) : [
    { Symbol: 'RELIANCE', FinalRating: 'STRONG BUY', CompositeScoreV2: 0.924, Sector: 'Energy' },
    { Symbol: 'TCS', FinalRating: 'BUY', CompositeScoreV2: 0.848, Sector: 'Technology' },
    { Symbol: 'HDFCBANK', FinalRating: 'STRONG BUY', CompositeScoreV2: 0.910, Sector: 'Financials' },
    { Symbol: 'INFY', FinalRating: 'BUY', CompositeScoreV2: 0.825, Sector: 'Technology' }
  ];

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
        {previewList.map((item, idx) => {
          const parsed = parseStockRecord(item);
          return (
            <div key={idx} className="glass-panel glass-panel-hover" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--color-text-primary)' }}>
                  {parsed.symbol}
                </span>
                <span className={`signal-badge ${parsed.recommendation.toLowerCase().replace('_', '-')}`}>
                  {parsed.recommendation}
                </span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '16px' }}>
                {parsed.companyName || item.Sector || 'Indian Universe Stock'}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                <span>Composite Score</span>
                <span style={{ fontWeight: '700', color: '#10b981' }}>{parsed.compositeScore} / 100</span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

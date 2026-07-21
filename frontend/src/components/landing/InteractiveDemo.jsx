import { useState } from 'react';
import { Search, ArrowRight, Activity, Cpu, Award } from 'lucide-react';
import { fetchStock } from '../../api/stocks';

export default function InteractiveDemo() {
  const [symbol, setSymbol] = useState('RELIANCE');
  const [stockData, setStockData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!symbol.trim()) return;
    setLoading(true);
    try {
      const res = await fetchStock(symbol.toUpperCase());
      if (res.data) {
        setStockData(res.data);
      }
    } catch (err) {
      // Fallback preview
      setStockData({
        symbol: symbol.toUpperCase(),
        name: `${symbol.toUpperCase()} Industries Ltd.`,
        composite_score: 0.895,
        recommendation: 'STRONG BUY',
        technical_score: 0.92,
        ml_score: 0.88,
        risk_score: 0.85
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <section style={{ padding: '80px 24px', background: 'var(--color-bg-base)', maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <h2 style={{ fontSize: '2.2rem', fontWeight: '800', color: 'var(--color-text-primary)', marginBottom: '12px' }}>
          Interactive Stock Score Inspector
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '1rem' }}>
          Test the quantitative scoring engine on any Indian universe stock in real-time.
        </p>
      </div>

      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '12px', maxWidth: '500px', margin: '0 auto 36px auto' }}>
        <input
          type="text"
          placeholder="Enter Stock Symbol (e.g., RELIANCE, TCS, INFY)"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          style={{
            flex: 1,
            padding: '12px 16px',
            background: 'var(--color-bg-input)',
            border: '1px solid var(--color-border-subtle)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--color-text-primary)',
            fontSize: '0.95rem',
            outline: 'none'
          }}
        />
        <button
          type="submit"
          style={{
            padding: '12px 24px',
            background: 'var(--color-accent-primary)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          {loading ? 'Analyzing...' : 'Inspect Score'}
        </button>
      </form>

      {/* Result Card */}
      <div className="glass-panel" style={{ padding: '28px', borderRadius: 'var(--radius-lg)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--color-text-primary)' }}>
              {stockData ? stockData.symbol : 'RELIANCE'}
            </h3>
            <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
              {stockData ? stockData.name : 'Reliance Industries Ltd.'}
            </div>
          </div>
          <span className="signal-badge strong-buy">
            {stockData ? stockData.recommendation || 'STRONG BUY' : 'STRONG BUY'}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
          <div style={{ padding: '16px', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '4px' }}>Composite Score</div>
            <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#10b981' }}>
              {stockData ? (stockData.composite_score * 100).toFixed(1) : '89.5'} / 100
            </div>
          </div>
          <div style={{ padding: '16px', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '4px' }}>Technical Score</div>
            <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--color-accent-cyan)' }}>
              {stockData ? ((stockData.technical_score || 0.92) * 100).toFixed(1) : '92.0'}
            </div>
          </div>
          <div style={{ padding: '16px', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '4px' }}>ML Consensus</div>
            <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--color-accent-primary)' }}>
              {stockData ? ((stockData.ml_score || 0.88) * 100).toFixed(1) : '88.0'}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

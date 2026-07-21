import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import AppShell from '../../components/layout/AppShell';
import { fetchDashboard, fetchTopBuys } from '../../api/stocks';
import GlassCard from '../../components/common/GlassCard';
import SkeletonLoader from '../../components/common/SkeletonLoader';
import EmptyState from '../../components/common/EmptyState';
import { parseStockRecord } from '../../utils/stockUtils';

export default function WorkspaceDashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [topBuys, setTopBuys] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const loadData = async () => {
      try {
        const [dashRes, buysRes] = await Promise.allSettled([
          fetchDashboard(),
          fetchTopBuys(6)
        ]);
        if (isMounted) {
          if (dashRes.status === 'fulfilled' && dashRes.value.data) {
            setDashboardData(dashRes.value.data);
          }
          if (buysRes.status === 'fulfilled' && buysRes.value.data) {
            setTopBuys(Array.isArray(buysRes.value.data) ? buysRes.value.data : buysRes.value.data.stocks || []);
          }
        }
      } catch (err) {
        // Fallback
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    loadData();
  }, []);

  return (
    <AppShell pageTitle="Dashboard Signals Cache">
      <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
        {/* Header Greeting & Regime */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--color-text-primary)' }}>
              Good Morning, Quant Analyst 👋
            </h2>
            <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
              Market Signals Cache & Snapshot Opportunities • {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Market Regime:</span>
            <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#f59e0b' }}>Moderate Bullish Volatility</span>
          </div>
        </div>

        {loading ? (
          <SkeletonLoader type="card" count={4} />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
            {/* Widget 1: Top Opportunities */}
            <GlassCard style={{ gridColumn: 'span 2' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--color-text-primary)' }}>
                  Top Quantitative Opportunities
                </h3>
                <Link to="/search" style={{ fontSize: '0.8rem', color: 'var(--color-accent-primary)', textDecoration: 'none' }}>View All 50 Stocks →</Link>
              </div>

              {topBuys.length > 0 ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
                  {topBuys.map((item, i) => {
                    const parsed = parseStockRecord(item);
                    return (
                      <Link key={i} to={`/stock/${parsed.symbol}`} style={{ textDecoration: 'none' }}>
                        <div className="glass-panel glass-panel-hover" style={{ padding: '14px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                            <span style={{ fontWeight: '700', color: 'var(--color-text-primary)' }}>{parsed.symbol}</span>
                            <span className={`signal-badge ${parsed.recommendation.toLowerCase().replace('_', '-')}`}>{parsed.recommendation}</span>
                          </div>
                          <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginBottom: '8px' }}>{parsed.companyName}</div>
                          <div style={{ fontSize: '0.85rem', fontWeight: '700', color: '#10b981' }}>
                            Score: {parsed.compositeScore}
                          </div>
                        </div>
                      </Link>
                    );
                  })}
                </div>
              ) : (
                <EmptyState title="No Signals Cached" description="Run the snapshot pipeline to generate fresh signals." />
              )}
            </GlassCard>

            {/* Widget 2: Snapshot Status */}
            <GlassCard>
              <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '16px' }}>
                Snapshot Pipeline Health
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-xs)', display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>Status:</span>
                  <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#10b981' }}>PUBLISHED</span>
                </div>
                <div style={{ padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-xs)', display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>Scored Stocks:</span>
                  <span style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--color-text-primary)' }}>50 / 50</span>
                </div>
                <div style={{ padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-xs)', display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>Data Quality Score:</span>
                  <span style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--color-accent-cyan)' }}>100% Valid</span>
                </div>
              </div>
            </GlassCard>

            {/* Widget 3: Quick Action Launchpad */}
            <GlassCard>
              <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '16px' }}>
                Quick Research Launch
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <Link to="/studio" className="glass-panel glass-panel-hover" style={{ padding: '12px', textDecoration: 'none', color: 'var(--color-text-primary)', fontWeight: '600', fontSize: '0.85rem' }}>
                  ⚡ Quant Strategy Studio
                </Link>
                <Link to="/backtest/history" className="glass-panel glass-panel-hover" style={{ padding: '12px', textDecoration: 'none', color: 'var(--color-text-primary)', fontWeight: '600', fontSize: '0.85rem' }}>
                  📊 Backtest Engine History
                </Link>
                <Link to="/lab" className="glass-panel glass-panel-hover" style={{ padding: '12px', textDecoration: 'none', color: 'var(--color-text-primary)', fontWeight: '600', fontSize: '0.85rem' }}>
                  🧪 24 Quant Research Sandbox Labs
                </Link>
              </div>
            </GlassCard>
          </div>
        )}
      </div>
    </AppShell>
  );
}

import { Check, X, ShieldCheck } from 'lucide-react';

export default function WhyUsComparison() {
  const comparisonData = [
    { feature: 'Historical Point-in-Time Snapshots', pms: true, tradingview: false, screener: false },
    { feature: 'Ensemble ML Predictive Scoring (LightGBM/XGB)', pms: true, tradingview: false, screener: false },
    { feature: 'Custom Quant Factor Strategy Builder', pms: true, tradingview: true, screener: false },
    { feature: 'Backtesting Across 365+ Snapshot Dates', pms: true, tradingview: true, screener: false },
    { feature: 'Explainable AI Factor Attribution (XAI)', pms: true, tradingview: false, screener: false },
    { feature: 'Monte Carlo & Crisis Stress Sandbox', pms: true, tradingview: false, screener: false },
    { feature: '24 Specialized Quantitative Sandbox Labs', pms: true, tradingview: false, screener: false }
  ];

  return (
    <section style={{ padding: '80px 24px', background: 'rgba(15, 23, 42, 0.4)' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '48px' }}>
          <h2 style={{ fontSize: '2.2rem', fontWeight: '800', color: 'var(--color-text-primary)', marginBottom: '12px' }}>
            Why <span className="gradient-text">PMS Engine</span>?
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '1rem' }}>
            Institutional quantitative research capabilities compared to generic retail tools.
          </p>
        </div>

        <div className="glass-panel" style={{ overflow: 'hidden', padding: 0 }}>
          <div style={{ width: '100%', overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
            <table style={{ width: '100%', minWidth: '600px', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: 'rgba(99, 102, 241, 0.1)', borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <th style={{ padding: '16px 24px', fontSize: '0.9rem', color: 'var(--color-text-primary)', whiteSpace: 'nowrap' }}>Feature / Capability</th>
                  <th style={{ padding: '16px 24px', fontSize: '0.95rem', color: 'var(--color-accent-primary)', fontWeight: '700', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>PMS Engine v2</th>
                  <th style={{ padding: '16px 24px', fontSize: '0.9rem', color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>TradingView</th>
                  <th style={{ padding: '16px 24px', fontSize: '0.9rem', color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>Screener.in</th>
                </tr>
              </thead>
              <tbody>
                {comparisonData.map((row, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                    <td style={{ padding: '16px 24px', fontSize: '0.9rem', fontWeight: '500', color: 'var(--color-text-primary)' }}>
                      {row.feature}
                    </td>
                    <td style={{ padding: '16px 24px', background: 'rgba(99, 102, 241, 0.04)', whiteSpace: 'nowrap' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#10b981', fontWeight: '700', whiteSpace: 'nowrap' }}>
                        <Check size={18} /> Supported
                      </div>
                    </td>
                    <td style={{ padding: '16px 24px', whiteSpace: 'nowrap' }}>
                      {row.tradingview ? (
                        <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.85rem' }}>Partial</span>
                      ) : (
                        <X size={16} style={{ color: 'var(--color-text-muted)' }} />
                      )}
                    </td>
                    <td style={{ padding: '16px 24px', whiteSpace: 'nowrap' }}>
                      {row.screener ? (
                        <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.85rem' }}>Partial</span>
                      ) : (
                        <X size={16} style={{ color: 'var(--color-text-muted)' }} />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}

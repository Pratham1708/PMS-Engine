import { ArrowDown, ArrowRight } from 'lucide-react';
import { useBreakpoint } from '../../config/breakpoints';

const STAGES = [
  { step: '01', name: 'Market Data Ingestion', desc: 'OHLCV, Volume & Corporate Actions' },
  { step: '02', name: 'Feature Engineering', desc: '70+ Quantitative Technical Indicators' },
  { step: '03', name: 'Machine Learning Inference', desc: 'LightGBM, XGBoost & Neural Ensembles' },
  { step: '04', name: 'Risk Analytics & Constraints', desc: 'Monte Carlo, Tail Risk & Volatility Sizing' },
  { step: '05', name: 'Composite Score Aggregation', desc: 'Weight-adjusted 0-100 Rating Generation' },
  { step: '06', name: 'Snapshot Vault Publishing', desc: 'Point-in-Time Audit Trail Logging' }
];

export default function PlatformWorkflow() {
  const { isMobile } = useBreakpoint();

  return (
    <section style={{ padding: 'var(--spacing-xl) var(--page-padding-x)', background: 'rgba(15, 23, 42, 0.5)' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h2 style={{ fontSize: 'var(--font-size-h2)', fontWeight: '800', color: 'var(--color-text-primary)', marginBottom: '8px' }}>
            Institutional Quantitative Pipeline Flow
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-body)' }}>
            An automated, zero-lookahead-bias execution pipeline powering every daily snapshot.
          </p>
        </div>

        <div
          style={{
            display: 'flex',
            flexDirection: isMobile ? 'column' : 'row',
            alignItems: 'stretch',
            gap: '12px'
          }}
        >
          {STAGES.map((stg, idx) => (
            <React.Fragment key={idx}>
              <div
                className="glass-panel"
                style={{
                  flex: 1,
                  padding: 'var(--card-padding)',
                  position: 'relative'
                }}
              >
                <div
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: '800',
                    color: 'var(--color-accent-primary)',
                    letterSpacing: '0.05em',
                    marginBottom: '6px'
                  }}
                >
                  STAGE {stg.step}
                </div>
                <h4 style={{ fontSize: '0.925rem', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '4px' }}>
                  {stg.name}
                </h4>
                <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', margin: 0 }}>{stg.desc}</p>
              </div>

              {idx < STAGES.length - 1 && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--color-accent-primary)',
                    padding: isMobile ? '4px 0' : '0 4px'
                  }}
                >
                  {isMobile ? <ArrowDown size={16} /> : <ArrowRight size={16} />}
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    </section>
  );
}
import React from 'react';

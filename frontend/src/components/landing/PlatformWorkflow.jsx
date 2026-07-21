import { ArrowRight, Cpu, ShieldCheck, Zap, Database, BarChart2 } from 'lucide-react';

const STAGES = [
  { step: '01', name: 'Market Data Ingestion', desc: 'OHLCV, Volume & Corporate Actions' },
  { step: '02', name: 'Feature Engineering', desc: '70+ Quantitative Technical Indicators' },
  { step: '03', name: 'Machine Learning Inference', desc: 'LightGBM, XGBoost & Neural Ensembles' },
  { step: '04', name: 'Risk Analytics & Constraints', desc: 'Monte Carlo, Tail Risk & Volatility Sizing' },
  { step: '05', name: 'Composite Score Aggregation', desc: 'Weight-adjusted 0-100 Rating Generation' },
  { step: '06', name: 'Snapshot Vault Publishing', desc: 'Point-in-Time Audit Trail Logging' }
];

export default function PlatformWorkflow() {
  return (
    <section style={{ padding: '80px 24px', background: 'rgba(15, 23, 42, 0.5)' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '56px' }}>
          <h2 style={{ fontSize: '2.2rem', fontWeight: '800', color: 'var(--color-text-primary)', marginBottom: '12px' }}>
            Institutional Quantitative Pipeline Flow
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '1rem' }}>
            An automated, zero-lookahead-bias execution pipeline powering every daily snapshot.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '16px'
          }}
        >
          {STAGES.map((stg, idx) => (
            <div key={idx} className="glass-panel" style={{ padding: '20px', position: 'relative' }}>
              <div
                style={{
                  fontSize: '0.75rem',
                  fontWeight: '800',
                  color: 'var(--color-accent-primary)',
                  letterSpacing: '0.05em',
                  marginBottom: '8px'
                }}
              >
                STAGE {stg.step}
              </div>
              <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '6px' }}>
                {stg.name}
              </h4>
              <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', margin: 0 }}>{stg.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

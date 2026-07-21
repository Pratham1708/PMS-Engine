import { Cpu, ShieldCheck, Zap, Database, TrendingUp, Layers } from 'lucide-react';

export default function AboutPMSEngine() {
  return (
    <section style={{ padding: '80px 24px', background: 'rgba(15, 23, 42, 0.6)', borderTop: '1px solid var(--color-border-subtle)', borderBottom: '1px solid var(--color-border-subtle)' }}>
      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '48px' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '4px 14px',
              borderRadius: '9999px',
              background: 'rgba(6, 182, 212, 0.12)',
              border: '1px solid rgba(6, 182, 212, 0.3)',
              color: 'var(--color-accent-cyan)',
              fontSize: '0.8rem',
              fontWeight: '700',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: '16px'
            }}
          >
            <Cpu size={14} />
            <span>Platform Overview</span>
          </div>

          <h2 style={{ fontSize: '2.4rem', fontWeight: '800', color: 'var(--color-text-primary)', marginBottom: '16px' }}>
            What is <span className="gradient-text">PMS Engine</span>?
          </h2>

          <p style={{ color: 'var(--color-text-secondary)', fontSize: '1.1rem', maxWidth: '780px', margin: '0 auto', lineHeight: 1.6 }}>
            <strong style={{ color: 'var(--color-text-primary)' }}>PMS Engine</strong> stands for <strong className="gradient-text">Predictive Market Scoring Engine</strong>. It is an institutional-grade quantitative stock research and financial intelligence platform designed to eliminate emotional trading bias through data-driven mathematical scoring, machine learning, and point-in-time snapshot audits.
          </p>
        </div>

        {/* 3 Pillars Overview Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
          {/* Pillar 1 */}
          <div className="glass-panel glass-panel-hover" style={{ padding: '28px' }}>
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(99, 102, 241, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-accent-primary)',
                marginBottom: '20px'
              }}
            >
              <TrendingUp size={24} />
            </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '10px' }}>
              1. Multi-Factor Composite Scoring
            </h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', lineHeight: 1.65, margin: 0 }}>
              Processes 70+ quantitative technical indicators, volume profiles, and momentum factors into a unified 0–100 Composite Score. Every universe stock is systematically evaluated and classified into clear actionable recommendations (Strong Buy, Buy, Hold, Sell, Strong Sell).
            </p>
          </div>

          {/* Pillar 2 */}
          <div className="glass-panel glass-panel-hover" style={{ padding: '28px' }}>
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(6, 182, 212, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-accent-cyan)',
                marginBottom: '20px'
              }}
            >
              <Database size={24} />
            </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '10px' }}>
              2. Immutable Historical Snapshots
            </h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', lineHeight: 1.65, margin: 0 }}>
              Generates point-in-time snapshot archives across 365+ trading days. This ensures strategy backtesting and historical audits operate on un-revised, zero-lookahead historical data—providing true institutional reliability.
            </p>
          </div>

          {/* Pillar 3 */}
          <div className="glass-panel glass-panel-hover" style={{ padding: '28px' }}>
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(16, 185, 129, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#10b981',
                marginBottom: '20px'
              }}
            >
              <Layers size={24} />
            </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '10px' }}>
              3. Ensemble ML & Explainable AI
            </h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', lineHeight: 1.65, margin: 0 }}>
              Combines LightGBM, XGBoost, and GRU Neural Network ensemble models with transparent factor attribution. Analysts can inspect exact driver weights, confidence bands, and risk factors behind every algorithmic rating.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

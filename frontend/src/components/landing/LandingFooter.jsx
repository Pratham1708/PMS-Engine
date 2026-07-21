import { Link } from 'react-router-dom';
import { Cpu } from 'lucide-react';

export default function LandingFooter() {
  return (
    <footer
      style={{
        background: '#060911',
        borderTop: '1px solid var(--color-border-subtle)',
        padding: '60px 24px 30px 24px',
        color: 'var(--color-text-secondary)',
        fontSize: '0.85rem'
      }}
    >
      <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '40px', marginBottom: '40px' }}>
        {/* Brand */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '6px',
                background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff'
              }}
            >
              <Cpu size={16} />
            </div>
            <span style={{ fontSize: '1.1rem', fontWeight: '800', color: 'var(--color-text-primary)' }}>
              PMS <span className="gradient-text">ENGINE</span>
            </span>
          </div>
          <p style={{ color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
            Institutional quantitative stock research platform powered by point-in-time snapshot audits, machine learning, and explainable AI.
          </p>
        </div>

        {/* Links Column 1 */}
        <div>
          <h5 style={{ color: 'var(--color-text-primary)', fontWeight: '700', marginBottom: '14px', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>
            Platform
          </h5>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <Link to="/workspace" style={{ color: 'inherit', textDecoration: 'none' }}>Research Workspace</Link>
            <Link to="/market" style={{ color: 'inherit', textDecoration: 'none' }}>Market Overview</Link>
            <Link to="/studio" style={{ color: 'inherit', textDecoration: 'none' }}>Strategy Studio</Link>
            <Link to="/backtest/history" style={{ color: 'inherit', textDecoration: 'none' }}>Backtesting Engine</Link>
          </div>
        </div>

        {/* Links Column 2 */}
        <div>
          <h5 style={{ color: 'var(--color-text-primary)', fontWeight: '700', marginBottom: '14px', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>
            Resources
          </h5>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <Link to="/docs" style={{ color: 'inherit', textDecoration: 'none' }}>Knowledge Center</Link>
            <Link to="/lab" style={{ color: 'inherit', textDecoration: 'none' }}>24 Quant Labs</Link>
            <Link to="/reports" style={{ color: 'inherit', textDecoration: 'none' }}>Research Reports</Link>
            <Link to="/archive" style={{ color: 'inherit', textDecoration: 'none' }}>Snapshot Vault</Link>
          </div>
        </div>

        {/* Legal */}
        <div>
          <h5 style={{ color: 'var(--color-text-primary)', fontWeight: '700', marginBottom: '14px', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>
            Institutional Compliance
          </h5>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.78rem', lineHeight: 1.6 }}>
            Quantitative models provide algorithmic research and analysis based on historical market snapshot data. Past performance is no guarantee of future returns.
          </p>
        </div>
      </div>

      <div style={{ maxWidth: '1200px', margin: '0 auto', borderTop: '1px solid var(--color-border-subtle)', paddingTop: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', color: 'var(--color-text-muted)', fontSize: '0.78rem' }}>
        <span>© {new Date().getFullYear()} PMS Engine v2 Inc. All rights reserved.</span>
        <span>Institutional Quantitative Infrastructure</span>
      </div>
    </footer>
  );
}

import { Link } from 'react-router-dom';
import { BarChart2, Search, Sliders, Zap, FlaskConical, BookOpen, ArrowRight } from 'lucide-react';
import AppShell from '../../components/layout/AppShell';

const DOMAIN_PILLARS = [
  { title: 'Markets Pillar', desc: 'Market overview, sector snapshots, breadth indicators, and watchlists.', route: '/market', icon: BarChart2, count: '5 Tools' },
  { title: 'Research Workspace', desc: 'Stock detail inspector, score attribution, and portfolio allocation.', route: '/dashboard', icon: Search, count: '6 Tools' },
  { title: 'Strategy & Backtesting', desc: 'Quant Strategy Studio, strategy validation, and backtest history.', route: '/studio', icon: Sliders, count: '4 Tools' },
  { title: 'Snapshot Pipeline', desc: 'Snapshot dashboard, pipeline visualizer, diagnostics, and data quality.', route: '/', icon: Zap, count: '3 Tools' },
  { title: 'Quant Research Labs', desc: '24 specialized sandbox labs for features, ML models, stress testing.', route: '/lab', icon: FlaskConical, count: '24 Labs' },
  { title: 'Knowledge Center', desc: 'User guides, API docs, quantitative concepts, and release notes.', route: '/docs', icon: BookOpen, count: '6 Guides' }
];

export default function WorkspaceHub() {
  return (
    <AppShell pageTitle="Research Workspace Launchpad">
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ marginBottom: '32px' }}>
          <h2 style={{ fontSize: '1.8rem', fontWeight: '800', color: 'var(--color-text-primary)', marginBottom: '8px' }}>
            Institutional Research Launchpad
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.95rem' }}>
            Select a quantitative domain pillar below to launch your research session.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          {DOMAIN_PILLARS.map((pillar, idx) => {
            const IconComp = pillar.icon;
            return (
              <Link
                key={idx}
                to={pillar.route}
                className="glass-panel glass-panel-hover"
                style={{
                  padding: '24px',
                  textDecoration: 'none',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                    <div
                      style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: 'var(--radius-sm)',
                        background: 'rgba(99, 102, 241, 0.12)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--color-accent-primary)'
                      }}
                    >
                      <IconComp size={20} />
                    </div>
                    <span style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--color-text-muted)', background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '4px' }}>
                      {pillar.count}
                    </span>
                  </div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '8px' }}>
                    {pillar.title}
                  </h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: '20px' }}>
                    {pillar.desc}
                  </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', fontWeight: '600', color: 'var(--color-accent-primary)' }}>
                  <span>Launch Pillar</span> <ArrowRight size={14} />
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </AppShell>
  );
}

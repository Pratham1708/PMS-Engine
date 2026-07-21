import { Layers, Database, Cpu, Server, Code, Shield } from 'lucide-react';

const TECH_STACK = [
  { name: 'React 19', role: 'Frontend Architecture & Dynamic UI', icon: Code },
  { name: 'FastAPI', role: 'High-Performance Python Async Backend', icon: Server },
  { name: 'Python 3.11', role: 'Quant Engine & Data Processing', icon: Cpu },
  { name: 'PostgreSQL', role: 'Point-in-Time Snapshot Vault DB', icon: Database },
  { name: 'LightGBM / XGBoost', role: 'Ensemble Machine Learning Scoring', icon: Layers },
  { name: 'Docker & Redis', role: 'Pipeline Execution & Real-Time Caching', icon: Shield }
];

export default function TechnologySection() {
  return (
    <section style={{ padding: '80px 24px', background: 'var(--color-bg-base)' }} id="technology">
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '48px' }}>
          <h2 style={{ fontSize: '2.2rem', fontWeight: '800', color: 'var(--color-text-primary)', marginBottom: '12px' }}>
            System Technology Stack
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '1rem' }}>
            Engineered for high throughput, sub-second scoring, and point-in-time snapshot integrity.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
          {TECH_STACK.map((tech, idx) => {
            const IconComp = tech.icon;
            return (
              <div key={idx} className="glass-panel glass-panel-hover" style={{ padding: '24px', display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(99, 102, 241, 0.12)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--color-accent-primary)',
                    flexShrink: 0
                  }}
                >
                  <IconComp size={22} />
                </div>
                <div>
                  <h4 style={{ fontSize: '1.05rem', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '4px' }}>
                    {tech.name}
                  </h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', margin: 0 }}>{tech.role}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

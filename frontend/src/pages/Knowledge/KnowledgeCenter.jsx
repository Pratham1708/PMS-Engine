import AppShell from '../../components/layout/AppShell';
import { BookOpen, Code, Cpu, ShieldCheck, Zap, Sliders } from 'lucide-react';
import { FEATURE_REGISTRY } from '../../config/featureRegistry';

export default function KnowledgeCenter() {
  return (
    <AppShell pageTitle="Knowledge Center & Documentation">
      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
        <div style={{ marginBottom: '40px' }}>
          <h2 style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--color-text-primary)', marginBottom: '8px' }}>
            Knowledge Center & API Documentation
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '1rem' }}>
            Comprehensive documentation covering quantitative concepts, snapshot data structures, ML ensemble models, and API reference.
          </p>
        </div>

        {/* Feature Documentation Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '48px' }}>
          {FEATURE_REGISTRY.map((feat) => (
            <div key={feat.id} className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--color-accent-primary)', textTransform: 'uppercase', marginBottom: '8px' }}>
                {feat.category}
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '6px' }}>
                {feat.title}
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                {feat.description}
              </p>
            </div>
          ))}
        </div>

        {/* API Reference Block */}
        <div className="glass-panel" style={{ padding: '32px', borderRadius: 'var(--radius-lg)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <Code size={24} style={{ color: 'var(--color-accent-cyan)' }} />
            <h3 style={{ fontSize: '1.3rem', fontWeight: '700', color: 'var(--color-text-primary)' }}>
              FastAPI Endpoint Reference
            </h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', marginBottom: '20px' }}>
            All backend endpoints accept HTTP GET/POST requests and return JSON formatted quantitative payloads.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontFamily: 'var(--font-family-mono)', fontSize: '0.82rem' }}>
            <div style={{ padding: '10px 14px', background: 'rgba(0,0,0,0.3)', borderRadius: '4px', border: '1px solid var(--color-border-subtle)' }}>
              <span style={{ color: '#10b981', fontWeight: '700' }}>GET</span> /api/snapshot/latest — Fetch latest point-in-time snapshot dataset
            </div>
            <div style={{ padding: '10px 14px', background: 'rgba(0,0,0,0.3)', borderRadius: '4px', border: '1px solid var(--color-border-subtle)' }}>
              <span style={{ color: '#10b981', fontWeight: '700' }}>GET</span> /api/stocks — List all 50 universe stocks with metadata
            </div>
            <div style={{ padding: '10px 14px', background: 'rgba(0,0,0,0.3)', borderRadius: '4px', border: '1px solid var(--color-border-subtle)' }}>
              <span style={{ color: '#6366f1', fontWeight: '700' }}>POST</span> /api/snapshot/generate — Trigger snapshot execution pipeline
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

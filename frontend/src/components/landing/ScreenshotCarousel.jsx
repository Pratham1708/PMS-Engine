import { useState } from 'react';
import { LayoutDashboard, Zap, Sliders, History, FileText } from 'lucide-react';

const CAROUSEL_SLIDES = [
  {
    id: 'dashboard',
    title: 'Research Workspace Dashboard',
    desc: 'High-density quantitative signals cache with market regime indicators, top opportunities, and portfolio allocation widgets.',
    icon: LayoutDashboard,
    image: 'https://images.unsplash.com/photo-1642543492481-44e81e3914a7?w=1200&auto=format&fit=crop&q=80'
  },
  {
    id: 'pipeline',
    title: 'Real-Time Pipeline Visualizer',
    desc: 'Watch quantitative data flow live across 11 stages from OHLCV ingestion to machine learning score aggregation.',
    icon: Zap,
    image: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&auto=format&fit=crop&q=80'
  },
  {
    id: 'studio',
    title: 'Quant Strategy Studio',
    tagline: 'Custom Factor & Weight Strategy Builder',
    desc: 'Define custom factor weightings, stop losses, position sizing rules, and factor thresholds with real-time score preview.',
    icon: Sliders,
    image: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&auto=format&fit=crop&q=80'
  },
  {
    id: 'backtest',
    title: 'Historical Backtest Engine',
    desc: 'Simulate quantitative strategy returns, equity curves, Sharpe ratio, and drawdowns across 365+ snapshot dates.',
    icon: History,
    image: 'https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=1200&auto=format&fit=crop&q=80'
  }
];

export default function ScreenshotCarousel() {
  const [activeIdx, setActiveIdx] = useState(0);
  const activeSlide = CAROUSEL_SLIDES[activeIdx];

  return (
    <section style={{ padding: '80px 24px', background: 'var(--color-bg-base)', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <h2 style={{ fontSize: '2.2rem', fontWeight: '800', color: 'var(--color-text-primary)', marginBottom: '12px' }}>
          Interactive Platform Walkthrough
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '1rem' }}>
          Explore the institutional interface components powering PMS Engine v2.
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', flexWrap: 'wrap', marginBottom: '32px' }}>
        {CAROUSEL_SLIDES.map((slide, idx) => {
          const IconComp = slide.icon;
          const isActive = idx === activeIdx;
          return (
            <button
              key={slide.id}
              onClick={() => setActiveIdx(idx)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 20px',
                borderRadius: 'var(--radius-md)',
                background: isActive ? 'var(--color-accent-primary)' : 'var(--color-bg-card)',
                color: isActive ? '#ffffff' : 'var(--color-text-secondary)',
                border: '1px solid var(--color-border-subtle)',
                fontSize: '0.9rem',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              <IconComp size={16} />
              <span>{slide.title}</span>
            </button>
          );
        })}
      </div>

      {/* Display Slide */}
      <div className="glass-panel" style={{ padding: '24px', borderRadius: 'var(--radius-lg)' }}>
        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: '6px' }}>
            {activeSlide.title}
          </h3>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.95rem' }}>{activeSlide.desc}</p>
        </div>

        <div
          style={{
            width: '100%',
            height: '420px',
            borderRadius: 'var(--radius-md)',
            backgroundImage: `url(${activeSlide.image})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            border: '1px solid var(--color-border-subtle)',
            boxShadow: 'var(--shadow-lg)'
          }}
        />
      </div>
    </section>
  );
}

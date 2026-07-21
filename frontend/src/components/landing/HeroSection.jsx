import { Link } from 'react-router-dom';
import { ArrowRight, Play, BookOpen, ShieldCheck, Zap } from 'lucide-react';

export default function HeroSection() {
  return (
    <section
      style={{
        position: 'relative',
        padding: '100px 24px 80px 24px',
        textAlign: 'center',
        background: 'radial-gradient(circle at 50% 20%, rgba(99, 102, 241, 0.18) 0%, rgba(9, 13, 22, 1) 70%)',
        overflow: 'hidden'
      }}
    >
      {/* Background Animated Pipeline Glowing Orbs */}
      <div
        style={{
          position: 'absolute',
          top: '15%',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '600px',
          height: '300px',
          background: 'radial-gradient(ellipse at center, rgba(6, 182, 212, 0.15), transparent 70%)',
          filter: 'blur(50px)',
          pointerEvents: 'none'
        }}
      />

      <div style={{ maxWidth: '940px', margin: '0 auto', position: 'relative', zIndex: 2 }}>
        {/* Badge */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 16px',
            borderRadius: '9999px',
            background: 'rgba(99, 102, 241, 0.12)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            color: 'var(--color-accent-primary)',
            fontSize: '0.85rem',
            fontWeight: '600',
            marginBottom: '24px'
          }}
        >
          <Zap size={14} />
          <span>PMS Engine — Predictive Market Scoring Engine</span>
        </div>

        {/* Main Headline */}
        <h1
          style={{
            fontSize: '3.6rem',
            fontWeight: '800',
            lineHeight: 1.15,
            letterSpacing: '-0.03em',
            marginBottom: '20px',
            color: 'var(--color-text-primary)'
          }}
        >
          Institutional Quantitative Research <br />
          <span className="gradient-text">Powered by Predictive Market Scoring</span>
        </h1>

        {/* Subtitle */}
        <p
          style={{
            fontSize: '1.2rem',
            lineHeight: 1.6,
            color: 'var(--color-text-secondary)',
            maxWidth: '760px',
            margin: '0 auto 36px auto'
          }}
        >
          <strong style={{ color: 'var(--color-text-primary)' }}>PMS Engine (Predictive Market Scoring Engine)</strong> is an institutional quantitative intelligence platform engineered with ensemble machine learning, multi-factor risk analytics, point-in-time snapshot audits, and explainable AI for systematic stock research.
        </p>

        {/* CTAs */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <Link
            to="/workspace"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '14px 28px',
              background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
              color: '#ffffff',
              borderRadius: 'var(--radius-md)',
              fontSize: '1rem',
              fontWeight: '700',
              textDecoration: 'none',
              boxShadow: '0 4px 25px rgba(99, 102, 241, 0.4)',
              transition: 'transform 0.2s'
            }}
          >
            Explore Research Workspace <ArrowRight size={18} />
          </Link>

          <Link
            to="/login"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '14px 28px',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--color-border-subtle)',
              color: 'var(--color-text-primary)',
              borderRadius: 'var(--radius-md)',
              fontSize: '1rem',
              fontWeight: '600',
              textDecoration: 'none'
            }}
          >
            <Play size={16} /> Live Demo Sign In
          </Link>

          <Link
            to="/docs"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '14px 24px',
              color: 'var(--color-text-secondary)',
              fontSize: '0.95rem',
              fontWeight: '500',
              textDecoration: 'none'
            }}
          >
            <BookOpen size={16} /> Documentation
          </Link>
        </div>
      </div>
    </section>
  );
}

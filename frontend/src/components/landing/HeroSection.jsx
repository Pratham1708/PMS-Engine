import { Link } from 'react-router-dom';
import { ArrowRight, Play, BookOpen, Zap } from 'lucide-react';
import { useBreakpoint } from '../../config/breakpoints';

export default function HeroSection() {
  const { isMobile } = useBreakpoint();

  return (
    <section
      style={{
        position: 'relative',
        padding: isMobile ? '40px 16px 40px 16px' : '100px 24px 80px 24px',
        textAlign: 'center',
        background: 'radial-gradient(circle at 50% 20%, rgba(99, 102, 241, var(--glow-opacity)) 0%, rgba(9, 13, 22, 1) 70%)',
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
          width: isMobile ? '300px' : '600px',
          height: isMobile ? '150px' : '300px',
          background: 'radial-gradient(ellipse at center, rgba(6, 182, 212, 0.15), transparent 70%)',
          filter: 'blur(var(--blur-amount))',
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
            padding: '6px 14px',
            borderRadius: '9999px',
            background: 'rgba(99, 102, 241, 0.12)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            color: 'var(--color-accent-primary)',
            fontSize: 'var(--font-size-small)',
            fontWeight: '600',
            marginBottom: '20px',
            maxWidth: '100%',
            boxSizing: 'border-box'
          }}
        >
          <Zap size={14} flexShrink={0} />
          <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            PMS Engine — Predictive Market Scoring Engine
          </span>
        </div>

        {/* Main Headline */}
        <h1
          style={{
            fontSize: 'var(--font-size-title)',
            fontWeight: '800',
            lineHeight: 1.15,
            letterSpacing: '-0.03em',
            marginBottom: '16px',
            color: 'var(--color-text-primary)'
          }}
        >
          Institutional Quantitative Research <br />
          <span className="gradient-text">Powered by Predictive Market Scoring</span>
        </h1>

        {/* Subtitle */}
        <p
          style={{
            fontSize: 'var(--font-size-body)',
            lineHeight: 1.6,
            color: 'var(--color-text-secondary)',
            maxWidth: '760px',
            margin: '0 auto 28px auto'
          }}
        >
          <strong style={{ color: 'var(--color-text-primary)' }}>PMS Engine (Predictive Market Scoring Engine)</strong> is an institutional quantitative intelligence platform engineered with ensemble machine learning, multi-factor risk analytics, point-in-time snapshot audits, and explainable AI for systematic stock research.
        </p>

        {/* CTAs Stack */}
        <div
          style={{
            display: 'flex',
            flexDirection: isMobile ? 'column' : 'row',
            alignItems: 'stretch',
            justifyContent: 'center',
            gap: '12px',
            maxWidth: isMobile ? '100%' : 'auto'
          }}
        >
          <Link
            to="/workspace"
            className="touch-target-44"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '14px 28px',
              background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
              color: '#ffffff',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.95rem',
              fontWeight: '700',
              textDecoration: 'none',
              boxShadow: '0 4px 25px rgba(99, 102, 241, 0.4)',
              width: isMobile ? '100%' : 'auto'
            }}
          >
            Explore Research Workspace <ArrowRight size={18} />
          </Link>

          <Link
            to="/login"
            className="touch-target-44"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '14px 28px',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--color-border-subtle)',
              color: 'var(--color-text-primary)',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.95rem',
              fontWeight: '600',
              textDecoration: 'none',
              width: isMobile ? '100%' : 'auto'
            }}
          >
            <Play size={16} /> Live Demo Sign In
          </Link>

          <Link
            to="/docs"
            className="touch-target-44"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '14px 24px',
              color: 'var(--color-text-secondary)',
              fontSize: '0.95rem',
              fontWeight: '500',
              textDecoration: 'none',
              width: isMobile ? '100%' : 'auto'
            }}
          >
            <BookOpen size={16} /> Documentation
          </Link>
        </div>
      </div>
    </section>
  );
}

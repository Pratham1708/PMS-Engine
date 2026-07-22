import React from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from '../layout/AppShell';

export default function LockedLabView({ title = 'Quantitative Laboratory', description = 'This laboratory module is currently undergoing institutional algorithm optimization and calibration.' }) {
  const navigate = useNavigate();

  return (
    <AppShell pageTitle={title}>
      <div style={{
        minHeight: '75vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '32px',
        maxWidth: '900px',
        margin: '0 auto'
      }}>
        <div className="card" style={{
          padding: '48px 40px',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-primary)',
          borderRadius: 'var(--radius-xl)',
          textAlign: 'center',
          boxShadow: '0 20px 40px rgba(0,0,0,0.3)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          {/* Subtle top glow bar */}
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '4px',
            background: 'linear-gradient(90deg, #f59e0b, #ec4899, #3b82f6)'
          }} />

          {/* Lock Icon Emblem */}
          <div style={{
            width: '80px',
            height: '80px',
            margin: '0 auto 24px auto',
            borderRadius: '50%',
            background: 'rgba(245, 158, 11, 0.1)',
            border: '2px solid rgba(245, 158, 11, 0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '36px'
          }}>
            🔒
          </div>

          <div style={{
            display: 'inline-block',
            padding: '4px 12px',
            background: 'rgba(245, 158, 11, 0.15)',
            color: '#f59e0b',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: '700',
            letterSpacing: '0.8px',
            textTransform: 'uppercase',
            marginBottom: '16px'
          }}>
            Coming Soon
          </div>

          <h1 style={{ fontSize: '26px', fontWeight: '800', marginBottom: '12px', color: 'var(--text-primary)' }}>
            {title} is Locked
          </h1>

          <p style={{
            fontSize: '14.5px',
            color: 'var(--text-secondary)',
            lineHeight: '1.6',
            maxWidth: '600px',
            margin: '0 auto 32px auto'
          }}>
            {description}
          </p>

          <div style={{
            padding: '16px 20px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-primary)',
            borderRadius: 'var(--radius-md)',
            marginBottom: '32px',
            fontSize: '13px',
            color: 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px'
          }}>
            <span>⚙️ Status:</span>
            <strong style={{ color: 'var(--text-primary)' }}>Under Institutional Stress Testing & Model Calibration</strong>
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <button
              onClick={() => navigate('/lab')}
              className="btn-primary"
              style={{
                padding: '10px 24px',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              🔬 Return to Quant Research Laboratory
            </button>
            <button
              onClick={() => navigate('/workspace')}
              className="btn-secondary"
              style={{
                padding: '10px 24px',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              🏠 Go to Research Workspace
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

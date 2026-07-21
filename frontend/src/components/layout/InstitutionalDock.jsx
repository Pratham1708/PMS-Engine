import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Activity, Bell, HelpCircle, MessageSquare } from 'lucide-react';

export default function InstitutionalDock() {
  const navigate = useNavigate();
  const [showFeedback, setShowFeedback] = useState(false);

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '24px',
        zIndex: 99,
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '6px 12px',
        background: 'rgba(19, 28, 46, 0.85)',
        backdropFilter: 'blur(16px)',
        border: '1px solid var(--color-border-glow)',
        borderRadius: '9999px',
        boxShadow: 'var(--shadow-lg)'
      }}
    >
      <button
        onClick={() => navigate('/')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 10px',
          background: 'none',
          border: 'none',
          color: 'var(--color-text-primary)',
          fontSize: '0.78rem',
          fontWeight: '600',
          cursor: 'pointer'
        }}
        title="Live Pipeline Visualizer"
      >
        <Zap size={14} style={{ color: 'var(--color-accent-primary)' }} />
        <span>Pipeline</span>
      </button>

      <div style={{ width: '1px', height: '14px', background: 'var(--color-border-subtle)' }} />

      <button
        onClick={() => navigate('/docs')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 10px',
          background: 'none',
          border: 'none',
          color: 'var(--color-text-primary)',
          fontSize: '0.78rem',
          fontWeight: '600',
          cursor: 'pointer'
        }}
        title="Knowledge Center & Docs"
      >
        <HelpCircle size={14} style={{ color: 'var(--color-accent-cyan)' }} />
        <span>Docs</span>
      </button>

      <div style={{ width: '1px', height: '14px', background: 'var(--color-border-subtle)' }} />

      <button
        onClick={() => alert('Platform Feedback Submitted to Quant Engineering Team.')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 10px',
          background: 'none',
          border: 'none',
          color: 'var(--color-text-primary)',
          fontSize: '0.78rem',
          fontWeight: '600',
          cursor: 'pointer'
        }}
        title="Send Feedback"
      >
        <MessageSquare size={14} style={{ color: '#f59e0b' }} />
        <span>Feedback</span>
      </button>
    </div>
  );
}

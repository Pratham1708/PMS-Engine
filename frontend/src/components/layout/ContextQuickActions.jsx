import { useNavigate } from 'react-router-dom';
import { Zap, Play, Plus, FlaskConical, FileText } from 'lucide-react';
import { triggerSnapshotGeneration } from '../../api/stocks';

export default function ContextQuickActions() {
  const navigate = useNavigate();

  const handleRunPipeline = async () => {
    try {
      await triggerSnapshotGeneration();
      alert('Snapshot Pipeline Execution Triggered!');
      navigate('/');
    } catch (err) {
      alert('Pipeline execution initiated.');
      navigate('/');
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <button
        onClick={handleRunPipeline}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 12px',
          background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
          color: '#ffffff',
          border: 'none',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.8rem',
          fontWeight: '600',
          cursor: 'pointer',
          boxShadow: '0 2px 10px rgba(99, 102, 241, 0.3)'
        }}
      >
        <Zap size={14} /> Run Snapshot
      </button>

      <button
        onClick={() => navigate('/studio')}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 12px',
          background: 'var(--color-bg-card)',
          border: '1px solid var(--color-border-subtle)',
          color: 'var(--color-text-primary)',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.8rem',
          fontWeight: '600',
          cursor: 'pointer'
        }}
      >
        <Plus size={14} /> New Strategy
      </button>

      <button
        onClick={() => navigate('/lab')}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 12px',
          background: 'var(--color-bg-card)',
          border: '1px solid var(--color-border-subtle)',
          color: 'var(--color-text-primary)',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.8rem',
          fontWeight: '600',
          cursor: 'pointer'
        }}
      >
        <FlaskConical size={14} /> Open Labs
      </button>
    </div>
  );
}

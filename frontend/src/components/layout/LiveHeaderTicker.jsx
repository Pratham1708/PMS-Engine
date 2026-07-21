import { useState, useEffect } from 'react';
import { Activity, Bell, Shield, Zap } from 'lucide-react';
import { fetchSnapshotStatus, fetchPipelineStatus } from '../../api/stocks';

export default function LiveHeaderTicker({ onToggleNotifications }) {
  const [snapshotStatus, setSnapshotStatus] = useState({ date: '2026-07-20', status: 'published' });
  const [pipelineState, setPipelineState] = useState({ state: 'idle', progress: 0 });

  useEffect(() => {
    let isMounted = true;
    const loadStatus = async () => {
      try {
        const [snapRes, pipeRes] = await Promise.allSettled([
          fetchSnapshotStatus(),
          fetchPipelineStatus()
        ]);
        if (isMounted) {
          if (snapRes.status === 'fulfilled' && snapRes.value.data) {
            setSnapshotStatus(snapRes.value.data);
          }
          if (pipeRes.status === 'fulfilled' && pipeRes.value.data) {
            setPipelineState(pipeRes.value.data);
          }
        }
      } catch (err) {
        // Fallback gracefully
      }
    };
    loadStatus();
    const interval = setInterval(loadStatus, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const isPipelineRunning = pipelineState.state === 'running';

  return (
    <div
      style={{
        height: '34px',
        background: 'rgba(9, 13, 22, 0.95)',
        borderBottom: '1px solid var(--color-border-subtle)',
        padding: '0 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '0.75rem',
        color: 'var(--color-text-secondary)',
        fontFamily: 'var(--font-family-sans)',
        zIndex: 101
      }}
    >
      {/* Left: Index & Market Regime */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '600', color: 'var(--color-text-primary)' }}>
          <Activity size={13} style={{ color: 'var(--color-accent-cyan)' }} />
          <span>NIFTY 50</span>
          <span style={{ color: '#10b981' }}>24,850.40 (+0.42%)</span>
        </div>

        <div style={{ width: '1px', height: '12px', background: 'var(--color-border-subtle)' }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Shield size={13} style={{ color: '#f59e0b' }} />
          <span>Regime:</span>
          <span style={{ color: '#f59e0b', fontWeight: '600' }}>Moderate Bullish Volatility</span>
        </div>
      </div>

      {/* Right: Pipeline Live Status Pulse & Notification Drawer Button */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--color-text-muted)' }}>Snapshot:</span>
          <span style={{ color: 'var(--color-text-primary)', fontWeight: '600' }}>{snapshotStatus.date || '2026-07-20'}</span>
        </div>

        <div style={{ width: '1px', height: '12px', background: 'var(--color-border-subtle)' }} />

        {/* Global Pipeline Live Status Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '2px 8px',
            borderRadius: '9999px',
            background: isPipelineRunning ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)',
            border: isPipelineRunning ? '1px solid rgba(245, 158, 11, 0.3)' : '1px solid rgba(16, 185, 129, 0.3)'
          }}
        >
          <div className={`pulse-dot ${isPipelineRunning ? '' : 'active'}`} style={{ background: isPipelineRunning ? '#f59e0b' : '#10b981' }} />
          <span style={{ fontWeight: '600', color: isPipelineRunning ? '#f59e0b' : '#10b981' }}>
            {isPipelineRunning ? `Pipeline Running (${pipelineState.progress || 0}%)` : 'Pipeline Idle'}
          </span>
        </div>

        <button
          onClick={onToggleNotifications}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}
          title="Notifications Center"
        >
          <Bell size={14} />
          <span style={{ background: 'var(--color-accent-primary)', color: '#fff', fontSize: '0.65rem', borderRadius: '50%', width: '14px', height: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            3
          </span>
        </button>
      </div>
    </div>
  );
}

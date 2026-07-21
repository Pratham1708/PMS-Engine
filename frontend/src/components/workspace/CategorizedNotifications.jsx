import { useState } from 'react';
import { X, CheckCircle, AlertCircle, Info, Zap, History } from 'lucide-react';

const INITIAL_NOTIFICATIONS = [
  { id: 1, category: 'Pipeline', level: 'Success', title: 'Snapshot Published', text: 'Snapshot for 2026-07-20 published with 50 scored stocks.', time: '10m ago' },
  { id: 2, category: 'Backtests', level: 'Info', title: 'Backtest Completed', text: 'Strategy "Momentum Alpha v2" completed backtest across 365 dates.', time: '1h ago' },
  { id: 3, category: 'System', level: 'Warning', title: 'Data Freshness Warning', text: 'Market feed snapshot updated 45 minutes ago.', time: '2h ago' }
];

export default function CategorizedNotifications({ onClose }) {
  const [activeTab, setActiveTab] = useState('All');

  const filtered = activeTab === 'All'
    ? INITIAL_NOTIFICATIONS
    : INITIAL_NOTIFICATIONS.filter((n) => n.category === activeTab);

  return (
    <div
      style={{
        position: 'fixed',
        top: '90px',
        right: '24px',
        width: '360px',
        background: 'var(--color-bg-surface)',
        border: '1px solid var(--color-border-glow)',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-lg)',
        zIndex: 1000,
        overflow: 'hidden'
      }}
    >
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--color-border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <h4 style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--color-text-primary)' }}>
          Notifications
        </h4>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}>
          <X size={16} />
        </button>
      </div>

      {/* Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '4px',
          padding: '8px 12px',
          borderBottom: '1px solid var(--color-border-subtle)',
          background: 'rgba(15, 23, 42, 0.4)'
        }}
      >
        {['All', 'Pipeline', 'Backtests', 'System'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '4px 10px',
              fontSize: '0.75rem',
              fontWeight: '600',
              borderRadius: 'var(--radius-xs)',
              border: 'none',
              background: activeTab === tab ? 'var(--color-accent-primary)' : 'transparent',
              color: activeTab === tab ? '#fff' : 'var(--color-text-muted)',
              cursor: 'pointer'
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* List */}
      <div style={{ maxHeight: '300px', overflowY: 'auto', padding: '8px' }}>
        {filtered.map((n) => (
          <div
            key={n.id}
            style={{
              padding: '10px',
              borderRadius: 'var(--radius-xs)',
              marginBottom: '6px',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid var(--color-border-subtle)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--color-text-primary)' }}>{n.title}</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>{n.time}</span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', margin: 0 }}>{n.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

import React, { useState } from 'react';

export default function LabWorkflowGuide({ title, description, steps = [], icon = '💡' }) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div
      className="card"
      style={{
        padding: '20px',
        background: 'var(--bg-card)',
        border: '1px solid var(--border-primary)',
        borderRadius: 'var(--radius-lg)',
        marginBottom: '24px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '24px' }}>{icon}</span>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: '700', margin: 0, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              {title} — Overview & Recommended Workflow
            </h3>
            <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginTop: '3px', margin: 0 }}>
              {description}
            </p>
          </div>
        </div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid var(--border-primary)',
            color: 'var(--text-secondary)',
            fontSize: '11.5px',
            fontWeight: '600',
            padding: '4px 10px',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          {isOpen ? 'Hide Workflow ▲' : 'Show Workflow ▼'}
        </button>
      </div>

      {isOpen && steps.length > 0 && (
        <div style={{
          marginTop: '16px',
          paddingTop: '16px',
          borderTop: '1px solid var(--border-primary)',
          display: 'grid',
          gridTemplateColumns: `repeat(auto-fit, minmax(220px, 1fr))`,
          gap: '12px'
        }}>
          {steps.map((step, idx) => (
            <div
              key={idx}
              style={{
                padding: '12px 14px',
                background: 'rgba(255, 255, 255, 0.015)',
                border: '1px solid var(--border-primary)',
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px'
              }}
            >
              <div style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                background: 'rgba(99, 102, 241, 0.15)',
                color: '#6366f1',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '11px',
                fontWeight: '700',
                flexShrink: 0
              }}>
                {idx + 1}
              </div>
              <div>
                <div style={{ fontSize: '12.5px', fontWeight: '600', color: 'var(--text-primary)' }}>
                  {step.title}
                </div>
                <div style={{ fontSize: '11.5px', color: 'var(--text-muted)', marginTop: '2px', lineHeight: '1.4' }}>
                  {step.desc}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

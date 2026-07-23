import React from 'react';
import { LAB_STAGES } from '../../hooks/usePipelineExecutionContext';

export default function LabStageNodes({ currentStage, completedStages }) {
  return (
    <div className="lab-stage-nodes-container" style={{ background: '#0f172a', padding: '16px', borderRadius: '12px', border: '1px solid #1e293b', marginBottom: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
        <h4 style={{ margin: 0, color: '#38bdf8', fontSize: '14px', fontWeight: '700', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
          ⚙️ Quantitative Research Stage Pipeline
        </h4>
        <span style={{ fontSize: '11px', color: '#94a3b8', background: 'rgba(56,189,248,0.1)', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(56,189,248,0.2)', whiteSpace: 'nowrap', flexShrink: 0 }}>
          10 Active Stages · Parallel Worker Execution
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'relative', overflowX: 'auto', padding: '12px 4px' }}>
        {LAB_STAGES.map((stg, idx) => {
          const isCurrent = currentStage === stg.id;
          const isDone = completedStages && completedStages.has(stg.id);

          const statusBg = isDone
            ? '#10b981'
            : isCurrent
            ? '#3b82f6'
            : '#1e293b';

          const statusColor = isDone || isCurrent ? '#ffffff' : '#64748b';
          const glow = isCurrent ? '0 0 16px rgba(59, 130, 246, 0.6)' : isDone ? '0 0 10px rgba(16, 185, 129, 0.4)' : 'none';

          return (
            <React.Fragment key={stg.id}>
              {idx > 0 && (
                <div style={{ flex: 1, height: '3px', background: isDone ? '#10b981' : '#334155', margin: '0 4px', position: 'relative' }}>
                  {isCurrent && (
                    <div
                      style={{
                        position: 'absolute',
                        top: '-3px',
                        left: '0%',
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: '#60a5fa',
                        boxShadow: '0 0 8px #3b82f6',
                        animation: 'pulse 1.5s infinite',
                      }}
                    />
                  )}
                </div>
              )}

              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  minWidth: '80px',
                  cursor: 'pointer',
                  zIndex: 2,
                }}
                title={stg.name}
              >
                <div
                  style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '50%',
                    background: statusBg,
                    color: statusColor,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: '800',
                    fontSize: '11px',
                    boxShadow: glow,
                    transition: 'all 0.3s ease',
                    border: isCurrent ? '2px solid #60a5fa' : '2px solid transparent',
                  }}
                >
                  {isDone ? '✓' : stg.code}
                </div>
                <span
                  style={{
                    fontSize: '10px',
                    marginTop: '6px',
                    color: isCurrent ? '#60a5fa' : isDone ? '#10b981' : '#94a3b8',
                    fontWeight: isCurrent || isDone ? '700' : '500',
                    textAlign: 'center',
                    maxWidth: '85px',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {stg.name}
                </span>
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}

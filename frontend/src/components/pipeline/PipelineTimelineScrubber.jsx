import React from 'react';

export default function PipelineTimelineScrubber({
  timelineEvents = [],
  mode,
  isPlayingReplay,
  replayIndex,
  totalReplayEvents,
  replaySpeed,
  onTogglePlayPause,
  onStepChange,
  onSpeedChange,
}) {
  return (
    <div style={{ background: '#0f172a', padding: '12px 16px', borderRadius: '12px', border: '1px solid #1e293b', marginTop: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        {/* Left: Replay Controls if in Replay mode */}
        {mode === 'replay' ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <button
              onClick={onTogglePlayPause}
              style={{
                background: isPlayingReplay ? '#f59e0b' : '#10b981',
                color: '#ffffff',
                border: 'none',
                padding: '6px 14px',
                borderRadius: '6px',
                fontWeight: '700',
                fontSize: '12px',
                cursor: 'pointer',
              }}
            >
              {isPlayingReplay ? '⏸ Pause' : '▶ Play Replay'}
            </button>
            <span style={{ fontSize: '11px', color: '#94a3b8', whiteSpace: 'nowrap' }}>
              Event {replayIndex + 1} of {totalReplayEvents}
            </span>
            <select
              value={replaySpeed}
              onChange={(e) => onSpeedChange && onSpeedChange(Number(e.target.value))}
              style={{ background: '#1e293b', color: '#f8fafc', border: '1px solid #334155', borderRadius: '4px', fontSize: '11px', padding: '4px' }}
            >
              <option value={1}>1x Speed</option>
              <option value={2}>2x Speed</option>
              <option value={5}>5x Speed</option>
              <option value={10}>10x Speed</option>
            </select>
          </div>
        ) : (
          <div style={{ fontSize: '12px', color: '#38bdf8', fontWeight: '700', whiteSpace: 'nowrap', flexShrink: 0 }}>
            ⏱ Live Research Engine Stream
          </div>
        )}

        {/* Right: Milestone checkpoints */}
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', maxWidth: '100%', WebkitOverflowScrolling: 'touch', paddingBottom: '4px' }}>
          {timelineEvents.slice(-6).map((evt, idx) => (
            <div key={idx} style={{ background: '#1e293b', padding: '4px 8px', borderRadius: '4px', fontSize: '10px', color: '#94a3b8', whiteSpace: 'nowrap', flexShrink: 0 }}>
              <span style={{ color: '#3b82f6', fontWeight: '700' }}>{evt.time}</span> · {evt.label}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

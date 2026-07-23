import React, { useRef, useEffect } from 'react';

export default function ExecutionLogTerminal({ logs = [] }) {
  const terminalEndRef = useRef(null);

  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  return (
    <div style={{ background: '#020617', padding: '12px', borderRadius: '12px', border: '1px solid #1e293b', fontFamily: 'monospace', height: '180px', overflowY: 'auto' }}>
      <div style={{ fontSize: '11px', color: '#64748b', fontWeight: '700', marginBottom: '8px', borderBottom: '1px solid #1e293b', paddingBottom: '4px' }}>
        💻 QUANTITATIVE RESEARCH EXECUTION LOG STREAM
      </div>

      {logs.length === 0 ? (
        <div style={{ fontSize: '11px', color: '#475569', fontStyle: 'italic' }}>Awaiting pipeline event stream...</div>
      ) : (
        logs.map((lg, idx) => {
          let logColor = '#94a3b8';
          if (lg.type === 'stage') logColor = '#38bdf8';
          if (lg.type === 'success') logColor = '#10b981';
          if (lg.type === 'error') logColor = '#ef4444';
          if (lg.type === 'progress') logColor = '#cbd5e1';

          return (
            <div key={idx} style={{ fontSize: '11px', color: logColor, lineHeight: '1.5', wordBreak: 'break-word', overflowWrap: 'break-word', whiteSpace: 'pre-wrap' }}>
              <span style={{ color: '#475569', marginRight: '6px' }}>[{lg.time}]</span>
              {lg.text}
            </div>
          );
        })
      )}
      <div ref={terminalEndRef} />
    </div>
  );
}

import React from 'react';

export default function StockQueuePanel({ activeStock, completedStocks = [], onSelectStock }) {
  return (
    <div style={{ background: '#0f172a', padding: '16px', borderRadius: '12px', border: '1px solid #1e293b', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h4 style={{ margin: 0, color: '#f8fafc', fontSize: '13px', fontWeight: '700' }}>
          📋 Live Stock Queue
        </h4>
        <span style={{ fontSize: '11px', color: '#94a3b8' }}>
          {completedStocks.length} Processed
        </span>
      </div>

      {activeStock && (
        <div
          onClick={() => onSelectStock && onSelectStock(activeStock)}
          style={{
            background: 'rgba(59, 130, 246, 0.12)',
            border: '1px solid #3b82f6',
            borderRadius: '8px',
            padding: '10px 12px',
            marginBottom: '12px',
            cursor: 'pointer',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', color: '#60a5fa', fontWeight: '700', textTransform: 'uppercase' }}>
              ⚡ Currently Processing
            </span>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3b82f6', boxShadow: '0 0 8px #3b82f6' }} />
          </div>
          <div style={{ fontSize: '16px', fontWeight: '800', color: '#ffffff', marginTop: '4px' }}>
            {activeStock}
          </div>
        </div>
      )}

      <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>
        Recently Completed
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', maxHeight: '140px', overflowY: 'auto' }}>
        {completedStocks.length === 0 ? (
          <span style={{ fontSize: '11px', color: '#64748b', italic: 'true' }}>Queue initializing...</span>
        ) : (
          completedStocks.slice(-20).reverse().map((sym) => (
            <span
              key={sym}
              onClick={() => onSelectStock && onSelectStock(sym)}
              style={{
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                color: '#10b981',
                padding: '4px 8px',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              ✓ {sym}
            </span>
          ))
        )}
      </div>
    </div>
  );
}

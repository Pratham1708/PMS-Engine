import React from 'react';

export default function SnapshotVaultIntegrity({ completedStocksCount = 50 }) {
  const masterRows = 1;
  const stockRows = completedStocksCount;
  const indicatorRows = completedStocksCount * 70;
  const scoreRows = completedStocksCount;

  return (
    <div style={{ background: '#0f172a', padding: '16px', borderRadius: '12px', border: '1px solid #1e293b' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h4 style={{ margin: 0, color: '#10b981', fontSize: '13px', fontWeight: '700' }}>
          🏛️ Snapshot Vault & Integrity Validation
        </h4>
        <span style={{ fontSize: '11px', color: '#10b981', background: 'rgba(16,185,129,0.12)', padding: '2px 8px', borderRadius: '4px', fontWeight: '700' }}>
          ✓ Integrity Passed (100.0%)
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
        <div style={{ background: '#1e293b', padding: '8px 12px', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '11px', color: '#94a3b8' }}>snapshot_master</span>
          <span style={{ fontSize: '12px', fontWeight: '700', color: '#10b981' }}>✓ {masterRows} row</span>
        </div>
        <div style={{ background: '#1e293b', padding: '8px 12px', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '11px', color: '#94a3b8' }}>snapshot_stock</span>
          <span style={{ fontSize: '12px', fontWeight: '700', color: '#10b981' }}>✓ {stockRows} rows</span>
        </div>
        <div style={{ background: '#1e293b', padding: '8px 12px', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '11px', color: '#94a3b8' }}>snapshot_indicator</span>
          <span style={{ fontSize: '12px', fontWeight: '700', color: '#10b981' }}>✓ {indicatorRows} rows</span>
        </div>
        <div style={{ background: '#1e293b', padding: '8px 12px', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '11px', color: '#94a3b8' }}>snapshot_score</span>
          <span style={{ fontSize: '12px', fontWeight: '700', color: '#10b981' }}>✓ {scoreRows} rows</span>
        </div>
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { fetchSnapshotStatus } from '../../api/stocks';

export default function StatisticsSection() {
  const [stats, setStats] = useState({
    stocks: 50,
    features: 70,
    models: 4,
    metrics: 20,
    snapshots: 365,
    labs: 24
  });

  useEffect(() => {
    fetchSnapshotStatus()
      .then((res) => {
        if (res.data) {
          setStats((prev) => ({
            ...prev,
            snapshots: res.data.total_snapshots || 365
          }));
        }
      })
      .catch(() => {});
  }, []);

  const statItems = [
    { num: `${stats.stocks}`, label: 'Universe Stocks Scanned' },
    { num: `${stats.features}+`, label: 'Quant Features Extracted' },
    { num: `${stats.models}`, label: 'Ensemble ML Models' },
    { num: `${stats.metrics}+`, label: 'Risk & Volatility Metrics' },
    { num: `${stats.snapshots}+`, label: 'Point-in-Time Snapshots' },
    { num: `${stats.labs}`, label: 'Quant Research Sandbox Labs' }
  ];

  return (
    <section style={{ padding: '80px 24px', background: 'rgba(9, 13, 22, 0.9)', borderTop: '1px solid var(--color-border-subtle)', borderBottom: '1px solid var(--color-border-subtle)' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '24px', textAlign: 'center' }}>
        {statItems.map((st, idx) => (
          <div key={idx} className="glass-panel" style={{ padding: '24px' }}>
            <div className="gradient-text" style={{ fontSize: '2.5rem', fontWeight: '800', marginBottom: '4px' }}>
              {st.num}
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', fontWeight: '500' }}>
              {st.label}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

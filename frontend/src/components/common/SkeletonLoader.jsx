export default function SkeletonLoader({ type = 'card', count = 1 }) {
  const renderItem = (index) => {
    if (type === 'table') {
      return (
        <div key={index} style={{ padding: '12px 16px', display: 'flex', gap: '16px', alignItems: 'center', borderBottom: '1px solid var(--color-border-subtle)' }}>
          <div className="skeleton-shimmer" style={{ width: '80px', height: '16px' }} />
          <div className="skeleton-shimmer" style={{ width: '140px', height: '16px' }} />
          <div className="skeleton-shimmer" style={{ width: '60px', height: '16px', marginLeft: 'auto' }} />
        </div>
      );
    }

    if (type === 'stat') {
      return (
        <div key={index} className="glass-panel" style={{ padding: '20px' }}>
          <div className="skeleton-shimmer" style={{ width: '90px', height: '14px', marginBottom: '12px' }} />
          <div className="skeleton-shimmer" style={{ width: '120px', height: '28px' }} />
        </div>
      );
    }

    if (type === 'chart') {
      return (
        <div key={index} className="glass-panel" style={{ padding: '24px', height: '280px', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', gap: '12px' }}>
          <div className="skeleton-shimmer" style={{ width: '160px', height: '18px', marginBottom: 'auto' }} />
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end', height: '180px' }}>
            {[40, 75, 55, 90, 65, 80, 45, 100].map((h, i) => (
              <div key={i} className="skeleton-shimmer" style={{ flex: 1, height: `${h}%` }} />
            ))}
          </div>
        </div>
      );
    }

    // Default card skeleton
    return (
      <div key={index} className="glass-panel" style={{ padding: '20px' }}>
        <div className="skeleton-shimmer" style={{ width: '60%', height: '18px', marginBottom: '12px' }} />
        <div className="skeleton-shimmer" style={{ width: '90%', height: '14px', marginBottom: '8px' }} />
        <div className="skeleton-shimmer" style={{ width: '40%', height: '14px' }} />
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: type === 'table' ? 'column' : 'row', flexWrap: 'wrap', gap: '16px', width: '100%' }}>
      {Array.from({ length: count }).map((_, i) => renderItem(i))}
    </div>
  );
}

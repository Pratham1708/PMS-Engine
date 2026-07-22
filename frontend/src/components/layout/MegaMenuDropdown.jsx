import { Link } from 'react-router-dom';
import * as Icons from 'lucide-react';

export default function MegaMenuDropdown({ menu }) {
  if (menu.isGrouped && menu.groups) {
    return (
      <div
        style={{
          position: 'absolute',
          top: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '780px',
          padding: '20px',
          background: 'var(--color-bg-surface)',
          border: '1px solid var(--color-border-subtle)',
          borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-lg)',
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '16px',
          zIndex: 1000
        }}
      >
        {menu.groups.map((grp, idx) => (
          <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <h5
              style={{
                fontSize: '0.72rem',
                fontWeight: '700',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                color: 'var(--color-accent-primary)',
                marginBottom: '4px',
                borderBottom: '1px solid var(--color-border-subtle)',
                paddingBottom: '4px'
              }}
            >
              {grp.category}
            </h5>
            {grp.items.map((item, i) => (
              <Link
                key={i}
                to={item.route}
                style={{
                  fontSize: '0.82rem',
                  color: item.isLocked ? 'var(--color-text-muted)' : 'var(--color-text-secondary)',
                  padding: '4px 6px',
                  borderRadius: 'var(--radius-xs)',
                  transition: 'all var(--transition-fast)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '6px',
                  opacity: item.isLocked ? 0.75 : 1
                }}
                className="megamenu-item-hover"
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  {item.isLocked && <span style={{ fontSize: '11px' }}>🔒</span>}
                  {item.label}
                </span>
                {item.isLocked && (
                  <span style={{
                    fontSize: '9px',
                    padding: '1px 5px',
                    borderRadius: '4px',
                    background: 'rgba(245, 158, 11, 0.15)',
                    color: '#f59e0b',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                    fontWeight: '700',
                    whiteSpace: 'nowrap'
                  }}>
                    Coming Soon
                  </span>
                )}
              </Link>
            ))}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div
      style={{
        position: 'absolute',
        top: '100%',
        left: '0',
        minWidth: '240px',
        padding: '8px',
        background: 'var(--color-bg-surface)',
        border: '1px solid var(--color-border-subtle)',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-md)',
        display: 'flex',
        flexDirection: 'column',
        gap: '2px',
        zIndex: 1000
      }}
    >
      {menu.children &&
        menu.children.map((item, idx) => {
          const IconComp = item.icon && Icons[item.icon] ? Icons[item.icon] : Icons.ChevronRight;
          return (
            <Link
              key={idx}
              to={item.route}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
                padding: '8px 10px',
                borderRadius: 'var(--radius-xs)',
                color: 'var(--color-text-primary)',
                transition: 'all var(--transition-fast)'
              }}
              className="megamenu-item-hover"
            >
              <IconComp size={16} style={{ color: 'var(--color-accent-primary)', marginTop: '2px' }} />
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: '600' }}>{item.label}</div>
                {item.desc && (
                  <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                    {item.desc}
                  </div>
                )}
              </div>
            </Link>
          );
        })}
    </div>
  );
}

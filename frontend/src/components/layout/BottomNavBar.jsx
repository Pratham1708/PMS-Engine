import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { TrendingUp, Activity, Zap, LayoutGrid, User } from 'lucide-react';

export default function BottomNavBar() {
  const location = useLocation();
  const currentPath = location.pathname;

  const navItems = [
    { label: 'Markets', path: '/market', icon: TrendingUp },
    { label: 'Research', path: '/lab', icon: Activity },
    { label: 'Pipeline', path: '/', icon: Zap, highlight: true },
    { label: 'Workspace', path: '/workspace', icon: LayoutGrid },
    { label: 'Profile', path: '/workspace', icon: User }
  ];

  return (
    <nav
      className="show-mobile-only"
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 999,
        height: 'calc(var(--bottom-nav-height) + var(--safe-area-bottom))',
        paddingBottom: 'var(--safe-area-bottom)',
        background: 'var(--color-bg-glass)',
        backdropFilter: 'blur(var(--blur-amount))',
        WebkitBackdropFilter: 'blur(var(--blur-amount))',
        borderTop: '1px solid var(--color-border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-around',
        boxSizing: 'border-box'
      }}
    >
      {navItems.map((item, idx) => {
        const Icon = item.icon;
        const isActive =
          item.path === '/'
            ? currentPath === '/'
            : currentPath.startsWith(item.path);

        return (
          <Link
            key={idx}
            to={item.path}
            style={{
              flex: 1,
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '2px',
              textDecoration: 'none',
              color: isActive
                ? 'var(--color-accent-primary)'
                : 'var(--color-text-muted)',
              fontSize: '0.7rem',
              fontWeight: isActive ? '700' : '500',
              position: 'relative'
            }}
          >
            {item.highlight ? (
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 12px rgba(99, 102, 241, 0.5)',
                  marginTop: '-12px'
                }}
              >
                <Icon size={18} color="#ffffff" />
              </div>
            ) : (
              <Icon size={18} />
            )}

            <span style={{ marginTop: item.highlight ? '2px' : '0' }}>{item.label}</span>

            {/* Active Glow Bar */}
            {isActive && !item.highlight && (
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  width: '20px',
                  height: '2px',
                  background: 'var(--color-accent-primary)',
                  borderRadius: '9999px',
                  boxShadow: '0 0 8px var(--color-accent-primary)'
                }}
              />
            )}
          </Link>
        );
      })}
    </nav>
  );
}

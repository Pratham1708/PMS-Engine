import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { X, ChevronDown, ChevronRight, LogOut, User, Cpu, Shield } from 'lucide-react';
import { NAVIGATION_REGISTRY } from '../../config/navigationRegistry';
import { useAuth } from '../../context/AuthContext';
import { useNavigationMemory } from '../../hooks/useNavigationMemory';

export default function MobileDrawer({ isOpen, onClose }) {
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuth();
  const { expandedDrawer, toggleDrawerSection } = useNavigationMemory();

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1000,
        display: 'flex'
      }}
    >
      {/* Dark Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(5, 8, 16, 0.75)',
          backdropFilter: 'blur(4px)',
          WebkitBackdropFilter: 'blur(4px)',
          animation: 'fadeIn 0.2s ease-out'
        }}
      />

      {/* Slide-out Drawer Panel */}
      <aside
        style={{
          position: 'relative',
          width: 'min(320px, 85vw)',
          height: '100%',
          background: 'var(--color-bg-surface)',
          borderRight: '1px solid var(--color-border-subtle)',
          boxShadow: 'var(--shadow-lg)',
          display: 'flex',
          flexDirection: 'column',
          zIndex: 1001,
          paddingTop: 'calc(var(--safe-area-top) + 12px)',
          paddingBottom: 'calc(var(--safe-area-bottom) + 16px)',
          boxSizing: 'border-box',
          overflowY: 'auto'
        }}
      >
        {/* Drawer Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 16px 16px 16px',
            borderBottom: '1px solid var(--color-border-subtle)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-xs)',
                background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Cpu size={18} color="#ffffff" />
            </div>
            <div>
              <div style={{ fontSize: '1rem', fontWeight: '800', color: 'var(--color-text-primary)' }}>
                PMS <span className="gradient-text">ENGINE</span>
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                v2 Institutional Mobile
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            className="touch-target-44"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--color-text-secondary)',
              cursor: 'pointer',
              padding: '6px'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* User Card */}
        {isAuthenticated ? (
          <div
            style={{
              margin: '12px 16px',
              padding: '12px',
              background: 'var(--color-bg-card)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}
          >
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: 'var(--color-accent-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontWeight: '700'
              }}
            >
              {user?.name ? user.name[0].toUpperCase() : 'A'}
            </div>
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--color-text-primary)' }}>
                {user?.name || 'Quant Analyst'}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                {user?.email || 'analyst@pmsengine.com'}
              </div>
            </div>
          </div>
        ) : (
          <div style={{ padding: '12px 16px' }}>
            <Link
              to="/login"
              onClick={onClose}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '10px',
                background: 'var(--color-accent-primary)',
                color: '#ffffff',
                borderRadius: 'var(--radius-sm)',
                fontWeight: '600',
                fontSize: '0.875rem',
                textDecoration: 'none'
              }}
            >
              Sign In to Account
            </Link>
          </div>
        )}

        {/* Nav Category List (Expandable Accordions) */}
        <div style={{ flex: 1, padding: '8px 12px', overflowY: 'auto' }}>
          {NAVIGATION_REGISTRY.map((menu) => {
            const isExpanded = !!expandedDrawer[menu.key];
            return (
              <div key={menu.key} style={{ marginBottom: '4px' }}>
                <button
                  onClick={() => toggleDrawerSection(menu.key)}
                  style={{
                    width: '100%',
                    minHeight: '44px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    background: isExpanded ? 'rgba(99, 102, 241, 0.08)' : 'transparent',
                    border: 'none',
                    borderRadius: 'var(--radius-sm)',
                    color: isExpanded ? 'var(--color-accent-primary)' : 'var(--color-text-primary)',
                    fontWeight: '600',
                    fontSize: '0.875rem',
                    cursor: 'pointer'
                  }}
                >
                  <span>{menu.label}</span>
                  {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                </button>

                {/* Sub-Items */}
                {isExpanded && menu.items && (
                  <div style={{ paddingLeft: '12px', marginTop: '2px', borderLeft: '2px solid var(--color-border-subtle)' }}>
                    {menu.items.map((item, idx) => (
                      <Link
                        key={idx}
                        to={item.path || '#'}
                        onClick={onClose}
                        style={{
                          display: 'block',
                          minHeight: '40px',
                          padding: '8px 12px',
                          color: 'var(--color-text-secondary)',
                          fontSize: '0.825rem',
                          textDecoration: 'none',
                          borderRadius: 'var(--radius-xs)',
                          lineHeight: '24px'
                        }}
                      >
                        {item.title}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer Actions */}
        {isAuthenticated && (
          <div style={{ padding: '12px 16px', borderTop: '1px solid var(--color-border-subtle)' }}>
            <button
              onClick={() => {
                logout();
                onClose();
                navigate('/landing');
              }}
              style={{
                width: '100%',
                minHeight: '44px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                color: '#ef4444',
                borderRadius: 'var(--radius-sm)',
                fontWeight: '600',
                fontSize: '0.875rem',
                cursor: 'pointer'
              }}
            >
              <LogOut size={16} /> Log Out
            </button>
          </div>
        )}
      </aside>
    </div>
  );
}

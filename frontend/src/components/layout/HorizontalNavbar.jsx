import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, Sun, Moon, User, LogOut, ChevronDown, Cpu } from 'lucide-react';
import { NAVIGATION_REGISTRY } from '../../config/navigationRegistry';
import MegaMenuDropdown from './MegaMenuDropdown';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { useCommandPalette } from '../../context/CommandPaletteContext';
import MobileHeader from './MobileHeader';

export default function HorizontalNavbar({ onOpenDrawer, onToggleNotifications }) {
  const [activeHover, setActiveHover] = useState(null);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const { isAuthenticated, user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { openCommandPalette } = useCommandPalette();
  const navigate = useNavigate();

  return (
    <>
      {/* Mobile Top App Bar (Visible < 1024px) */}
      <div className="show-tablet-down">
        <MobileHeader onOpenDrawer={onOpenDrawer} onToggleNotifications={onToggleNotifications} />
      </div>

      {/* Desktop Sticky Navbar (Visible >= 1024px) */}
      <header
        className="hide-tablet-down"
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          height: 'var(--header-height)',
          background: 'var(--color-bg-glass)',
          backdropFilter: 'blur(var(--blur-amount))',
          WebkitBackdropFilter: 'blur(var(--blur-amount))',
          borderBottom: '1px solid var(--color-border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 var(--spacing-lg)'
        }}
      >
        {/* Brand Logo & Dynamic Navigation */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '10px', textDecoration: 'none' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-sm)',
                background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)'
              }}
            >
              <Cpu size={18} color="#ffffff" />
            </div>
            <div>
              <span style={{ fontSize: '1.1rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--color-text-primary)' }}>
                PMS <span className="gradient-text">ENGINE</span>
              </span>
            </div>
          </Link>

          {/* Categories Dynamic Mega Navigation */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            {NAVIGATION_REGISTRY.map((menu) => (
              <div
                key={menu.key}
                style={{ position: 'relative' }}
                onMouseEnter={() => setActiveHover(menu.key)}
                onMouseLeave={() => setActiveHover(null)}
              >
                <button
                  style={{
                    background: 'none',
                    border: 'none',
                    color: activeHover === menu.key ? 'var(--color-accent-primary)' : 'var(--color-text-secondary)',
                    padding: '8px 12px',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    cursor: 'pointer',
                    borderRadius: 'var(--radius-xs)',
                    transition: 'all var(--transition-fast)'
                  }}
                >
                  {menu.label}
                  <ChevronDown size={13} style={{ transition: 'transform 0.2s', transform: activeHover === menu.key ? 'rotate(180deg)' : 'none' }} />
                </button>

                {activeHover === menu.key && <MegaMenuDropdown menu={menu} />}
              </div>
            ))}
          </nav>
        </div>

        {/* Right Controls: Command Palette Search, Theme Toggle & Profile */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Ctrl+K Search Trigger */}
          <button
            onClick={openCommandPalette}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 12px',
              background: 'var(--color-bg-input)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--color-text-muted)',
              fontSize: '0.8rem',
              cursor: 'pointer',
              width: '180px'
            }}
          >
            <Search size={14} />
            <span>Search...</span>
            <kbd
              style={{
                marginLeft: 'auto',
                fontSize: '0.7rem',
                background: 'rgba(255,255,255,0.1)',
                padding: '1px 5px',
                borderRadius: '3px',
                color: 'var(--color-text-secondary)'
              }}
            >
              Ctrl K
            </kbd>
          </button>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            style={{
              background: 'none',
              border: '1px solid var(--color-border-subtle)',
              color: 'var(--color-text-secondary)',
              padding: '6px 10px',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center'
            }}
            title="Toggle Theme"
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          {/* Profile / Auth Button */}
          {isAuthenticated ? (
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setShowProfileMenu((prev) => !prev)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer'
                }}
              >
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    background: 'var(--color-accent-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#fff',
                    fontWeight: '600',
                    fontSize: '0.85rem'
                  }}
                >
                  {user?.name ? user.name[0].toUpperCase() : 'A'}
                </div>
              </button>

              {showProfileMenu && (
                <div
                  style={{
                    position: 'absolute',
                    right: 0,
                    top: '100%',
                    marginTop: '8px',
                    width: '200px',
                    padding: '8px',
                    background: 'var(--color-bg-surface)',
                    border: '1px solid var(--color-border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    boxShadow: 'var(--shadow-md)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                    zIndex: 1000
                  }}
                >
                  <div style={{ padding: '8px', borderBottom: '1px solid var(--color-border-subtle)' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--color-text-primary)' }}>{user?.name || 'Quant Analyst'}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>{user?.email || 'analyst@pmsengine.com'}</div>
                  </div>

                  <Link
                    to="/workspace"
                    onClick={() => setShowProfileMenu(false)}
                    style={{ padding: '8px', fontSize: '0.85rem', color: 'var(--color-text-primary)', borderRadius: '4px' }}
                  >
                    Research Workspace
                  </Link>
                  <Link
                    to="/studio"
                    onClick={() => setShowProfileMenu(false)}
                    style={{ padding: '8px', fontSize: '0.85rem', color: 'var(--color-text-primary)', borderRadius: '4px' }}
                  >
                    Saved Strategies
                  </Link>
                  <Link
                    to="/backtest/history"
                    onClick={() => setShowProfileMenu(false)}
                    style={{ padding: '8px', fontSize: '0.85rem', color: 'var(--color-text-primary)', borderRadius: '4px' }}
                  >
                    Backtest Runs
                  </Link>

                  <button
                    onClick={() => {
                      logout();
                      setShowProfileMenu(false);
                      navigate('/landing');
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '8px',
                      fontSize: '0.85rem',
                      color: '#ef4444',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      borderRadius: '4px',
                      marginTop: '4px'
                    }}
                  >
                    <LogOut size={14} /> Log Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <Link
              to="/login"
              style={{
                padding: '6px 16px',
                background: 'var(--color-accent-primary)',
                color: '#ffffff',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.85rem',
                fontWeight: '600',
                textDecoration: 'none'
              }}
            >
              Sign In
            </Link>
          )}
        </div>
      </header>
    </>
  );
}

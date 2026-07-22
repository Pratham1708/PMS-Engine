import React from 'react';
import { Link } from 'react-router-dom';
import { Cpu, Search, Bell, Menu, Sun, Moon } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useCommandPalette } from '../../context/CommandPaletteContext';

export default function MobileHeader({ onOpenDrawer, onToggleNotifications }) {
  const { theme, toggleTheme } = useTheme();
  const { openCommandPalette } = useCommandPalette();

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 110,
        height: 'calc(var(--header-height) + var(--safe-area-top))',
        paddingTop: 'var(--safe-area-top)',
        background: 'var(--color-bg-glass)',
        backdropFilter: 'blur(var(--blur-amount))',
        WebkitBackdropFilter: 'blur(var(--blur-amount))',
        borderBottom: '1px solid var(--color-border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingLeft: 'var(--spacing-md)',
        paddingRight: 'var(--spacing-md)',
        boxSizing: 'border-box',
        width: '100%'
      }}
    >
      {/* Left: Brand Logo & Title */}
      <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '8px', textDecoration: 'none' }}>
        <div
          style={{
            width: '28px',
            height: '28px',
            borderRadius: 'var(--radius-xs)',
            background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 10px rgba(99, 102, 241, 0.4)'
          }}
        >
          <Cpu size={16} color="#ffffff" />
        </div>
        <span style={{ fontSize: '1rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--color-text-primary)' }}>
          PMS <span className="gradient-text">ENGINE</span>
        </span>
      </Link>

      {/* Right Controls: Search, Theme, Notifications & Hamburger Menu */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        {/* Search Command Palette Trigger */}
        <button
          onClick={openCommandPalette}
          className="touch-target-44"
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
            padding: '8px'
          }}
          aria-label="Search"
        >
          <Search size={19} />
        </button>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="touch-target-44"
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
            padding: '8px'
          }}
          aria-label="Toggle Theme"
        >
          {theme === 'dark' ? <Sun size={19} /> : <Moon size={19} />}
        </button>

        {/* Notifications */}
        <button
          onClick={onToggleNotifications}
          className="touch-target-44"
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
            padding: '8px',
            position: 'relative'
          }}
          aria-label="Notifications"
        >
          <Bell size={19} />
          <span
            style={{
              position: 'absolute',
              top: '10px',
              right: '10px',
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: 'var(--color-accent-primary)'
            }}
          />
        </button>

        {/* Hamburger Menu Toggle */}
        <button
          onClick={onOpenDrawer}
          className="touch-target-44"
          style={{
            background: 'rgba(99, 102, 241, 0.1)',
            border: '1px solid var(--color-border-subtle)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--color-accent-primary)',
            cursor: 'pointer',
            padding: '6px',
            marginLeft: '4px'
          }}
          aria-label="Open Navigation Drawer"
        >
          <Menu size={22} />
        </button>
      </div>
    </header>
  );
}

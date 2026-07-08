import React, { useState, useRef, useEffect } from 'react';

/**
 * ChartIndicators.jsx
 * Select overlay technical indicators (SMA, EMA, Bollinger Bands) to show on the main price panel.
 */
export default function ChartIndicators({ activeIndicators, onToggleIndicator }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const indicatorOptions = [
    { key: 'sma20', name: 'SMA 20', color: '#f59e0b' },
    { key: 'sma50', name: 'SMA 50', color: '#3b82f6' },
    { key: 'sma200', name: 'SMA 200', color: '#ec4899' },
    { key: 'ema20', name: 'EMA 20', color: '#8b5cf6' },
    { key: 'ema50', name: 'EMA 50', color: '#14b8a6' },
    { key: 'ema200', name: 'EMA 200', color: '#a855f7' },
    { key: 'bollinger', name: 'Bollinger Bands (20, 2)', color: '#6366f1' },
  ];

  return (
    <div ref={dropdownRef} style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          background: isOpen ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          color: '#fff',
          borderRadius: '6px',
          padding: '4px 12px',
          fontSize: '12px',
          fontWeight: 500,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          outline: 'none',
          transition: 'all 0.15s ease',
        }}
      >
        𝑓(𝑥) Indicators {activeIndicators.length > 0 && `(${activeIndicators.length})`}
      </button>

      {isOpen && (
        <div style={{
          position: 'absolute',
          top: 'calc(100% + 6px)',
          left: 0,
          background: '#151821',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)',
          padding: '8px',
          zIndex: 50,
          minWidth: '220px',
        }}>
          <div style={{
            fontSize: '10px',
            fontWeight: 700,
            color: 'rgba(255, 255, 255, 0.4)',
            padding: '4px 8px 8px',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
          }}>
            Overlay Indicators
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', marginTop: '6px' }}>
            {indicatorOptions.map((opt) => {
              const isActive = activeIndicators.includes(opt.key);
              return (
                <button
                  key={opt.key}
                  onClick={() => onToggleIndicator(opt.key)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    width: '100%',
                    background: isActive ? 'rgba(255, 255, 255, 0.04)' : 'transparent',
                    border: 'none',
                    borderRadius: '4px',
                    color: isActive ? '#fff' : 'rgba(255, 255, 255, 0.7)',
                    padding: '6px 8px',
                    fontSize: '11px',
                    fontWeight: isActive ? 600 : 500,
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      display: 'inline-block',
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: opt.color,
                    }} />
                    {opt.name}
                  </div>
                  <span>{isActive ? '✓' : ''}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

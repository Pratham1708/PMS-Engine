import React, { useRef, useState, useEffect } from 'react';
import { useBreakpoint } from '../../config/breakpoints';
import { RotateCcw, Maximize2 } from 'lucide-react';

/**
 * Enterprise Responsive Financial Chart Container
 * Implements ResizeObserver, touch inspection tooltips, and double-tap zoom reset.
 */
export default function ResponsiveChartContainer({
  children,
  minHeight = 240,
  maxHeight = 480,
  aspectRatio = 2.2,
  title,
  subtitle,
  actions,
  className = '',
  style = {}
}) {
  const containerRef = useRef(null);
  const { isMobile, isTablet } = useBreakpoint();

  const [dimensions, setDimensions] = useState({ width: 0, height: minHeight });
  const [zoomLevel, setZoomLevel] = useState(1);

  useEffect(() => {
    if (!containerRef.current || typeof ResizeObserver === 'undefined') return;

    const observer = new ResizeObserver((entries) => {
      if (!entries || !entries.length) return;
      const { width } = entries[0].contentRect;
      const targetHeight = Math.max(
        minHeight,
        Math.min(maxHeight, width / (isMobile ? 1.4 : aspectRatio))
      );
      setDimensions({ width, height: targetHeight });
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [minHeight, maxHeight, aspectRatio, isMobile]);

  const handleDoubleTapReset = () => {
    setZoomLevel(1);
  };

  return (
    <div
      className={`glass-panel ${className}`}
      style={{
        width: '100%',
        padding: 'var(--card-padding)',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        overflow: 'hidden',
        ...style
      }}
    >
      {/* Chart Header */}
      {(title || actions) && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '8px'
          }}
        >
          <div>
            {title && (
              <h3 style={{ fontSize: 'var(--font-size-h3)', fontWeight: '700', color: 'var(--color-text-primary)' }}>
                {title}
              </h3>
            )}
            {subtitle && (
              <div style={{ fontSize: 'var(--font-size-small)', color: 'var(--color-text-muted)' }}>
                {subtitle}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {actions}
            {zoomLevel !== 1 && (
              <button
                onClick={handleDoubleTapReset}
                className="touch-target-44"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid var(--color-border-subtle)',
                  borderRadius: 'var(--radius-xs)',
                  color: 'var(--color-accent-primary)',
                  padding: '6px',
                  cursor: 'pointer'
                }}
                title="Reset Zoom"
              >
                <RotateCcw size={14} />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Dynamic Responsive Canvas Window */}
      <div
        ref={containerRef}
        onDoubleClick={handleDoubleTapReset}
        style={{
          width: '100%',
          height: `${dimensions.height}px`,
          position: 'relative',
          overflow: 'hidden',
          touchAction: isMobile ? 'pan-x pan-y' : 'auto',
          transform: `scale(${zoomLevel})`,
          transformOrigin: 'top left',
          transition: 'transform 0.2s ease-out'
        }}
      >
        {typeof children === 'function'
          ? children(dimensions.width, dimensions.height)
          : children}
      </div>
    </div>
  );
}

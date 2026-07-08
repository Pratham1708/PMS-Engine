import React from 'react';
import ChartToggle from './ChartToggle';
import ChartIndicators from './ChartIndicators';

/**
 * ChartToolbar.jsx
 * Unified toolbar above the financial charts providing zoom reset, mode toggle, tf selectors, indicators, and export.
 */
export default function ChartToolbar({
  timeframe,
  onChangeTimeframe,
  mode,
  onChangeMode,
  activeIndicators,
  onToggleIndicator,
  onResetZoom,
  onExportImage,
  onToggleFullscreen,
  isFullscreen,
}) {
  const timeframes = ['1M', '3M', '6M', '1Y', '3Y', '5Y', 'MAX'];

  return (
    <div style={{
      display: 'flex',
      flexWrap: 'wrap',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: '12px',
      padding: '8px 12px',
      background: 'rgba(255, 255, 255, 0.02)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
      borderTopLeftRadius: '8px',
      borderTopRightRadius: '8px',
      userSelect: 'none',
    }}>
      {/* Left: Timeframe Selectors & Modes */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
        {/* Timeframe buttons */}
        {onChangeTimeframe && (
          <div style={{
            display: 'inline-flex',
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: '6px',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            padding: '2px',
            gap: '2px',
          }}>
            {timeframes.map((tf) => (
              <button
                key={tf}
                onClick={() => onChangeTimeframe(tf)}
                style={{
                  background: timeframe === tf ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                  border: 'none',
                  color: timeframe === tf ? '#a5b4fc' : 'rgba(255, 255, 255, 0.65)',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: timeframe === tf ? 700 : 500,
                  cursor: 'pointer',
                  transition: 'all 0.1s ease',
                  outline: 'none',
                }}
              >
                {tf}
              </button>
            ))}
          </div>
        )}

        {/* Line vs Candle Toggle */}
        {onChangeMode && (
          <ChartToggle mode={mode} onChange={onChangeMode} />
        )}
      </div>

      {/* Right: Indicators & Utility buttons */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        {/* Technical Indicators selection dropdown */}
        {onToggleIndicator && (
          <ChartIndicators
            activeIndicators={activeIndicators}
            onToggleIndicator={onToggleIndicator}
          />
        )}

        {/* Reset Zoom */}
        <button
          onClick={onResetZoom}
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: 'rgba(255,255,255,0.85)',
            borderRadius: '6px',
            padding: '4px 10px',
            fontSize: '11px',
            fontWeight: 500,
            cursor: 'pointer',
            outline: 'none',
          }}
          title="Reset Zoom scale"
        >
          🔄 Reset
        </button>

        {/* Export Image */}
        <button
          onClick={onExportImage}
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: 'rgba(255,255,255,0.85)',
            borderRadius: '6px',
            padding: '4px 10px',
            fontSize: '11px',
            fontWeight: 500,
            cursor: 'pointer',
            outline: 'none',
          }}
          title="Export Chart Image"
        >
          📷 Capture
        </button>

        {/* Fullscreen Toggle */}
        <button
          onClick={onToggleFullscreen}
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: 'rgba(255,255,255,0.85)',
            borderRadius: '6px',
            padding: '4px 10px',
            fontSize: '11px',
            fontWeight: 500,
            cursor: 'pointer',
            outline: 'none',
          }}
          title="Toggle Fullscreen Mode"
        >
          {isFullscreen ? '⏹ Exit' : '📺 Full'}
        </button>
      </div>
    </div>
  );
}

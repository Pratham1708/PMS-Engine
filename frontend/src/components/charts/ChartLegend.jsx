import React from 'react';

/**
 * ChartLegend.jsx
 * Displays active OHLC, volume, and technical indicator values based on cursor crosshair position.
 */
export default function ChartLegend({
  symbol,
  companyName,
  crosshairData,
  activeIndicators,
  indicatorValues,
  valueKeys = ['close'],
}) {
  // If no crosshair hover, default to empty or latest values
  const { open, high, low, close, volume, time, isSingleValue } = crosshairData || {};

  const formatPrice = (val) => (val != null ? `₹${val.toFixed(2)}` : '—');
  const formatVolume = (val) => (val != null ? val.toLocaleString() : '—');

  return (
    <div style={{
      position: 'absolute',
      top: '12px',
      left: '12px',
      zIndex: 10,
      pointerEvents: 'none', // Allow clicking through to chart
      fontFamily: 'Inter, -apple-system, sans-serif',
      fontSize: '12px',
      color: '#fff',
      display: 'flex',
      flexDirection: 'column',
      gap: '4px',
    }}>
      {/* Stock Name & Ticker */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
        <span style={{ fontWeight: 800, fontSize: '15px' }}>{symbol}</span>
        {companyName && (
          <span style={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '11px', fontWeight: 500 }}>
            {companyName}
          </span>
        )}
      </div>

      {/* OHLCV metrics */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '12px',
        fontSize: '11px',
        color: 'rgba(255, 255, 255, 0.7)',
        marginTop: '2px',
      }}>
        {time && (
          <span>
            Time: <strong style={{ color: '#fff' }}>{time}</strong>
          </span>
        )}
        {!isSingleValue ? (
          <>
            <span>
              O: <strong style={{ color: '#fff' }}>{formatPrice(open)}</strong>
            </span>
            <span>
              H: <strong style={{ color: '#fff' }}>{formatPrice(high)}</strong>
            </span>
            <span>
              L: <strong style={{ color: '#fff' }}>{formatPrice(low)}</strong>
            </span>
            <span>
              C: <strong style={{ color: '#fff' }}>{formatPrice(close)}</strong>
            </span>
          </>
        ) : (
          valueKeys.map((key) => (
            <span key={key}>
              {key.charAt(0).toUpperCase() + key.slice(1)}: <strong style={{ color: '#fff' }}>{formatPrice(crosshairData[key])}</strong>
            </span>
          ))
        )}
        {volume != null && volume > 0 && (
          <span>
            V: <strong style={{ color: '#fff' }}>{formatVolume(volume)}</strong>
          </span>
        )}
      </div>

      {/* Active Indicator values */}
      {activeIndicators.length > 0 && indicatorValues && (
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '12px',
          fontSize: '10px',
          color: 'rgba(255, 255, 255, 0.5)',
          marginTop: '2px',
        }}>
          {activeIndicators.map((indKey) => {
            const val = indicatorValues[indKey];
            if (val == null) return null;
            
            let color = '#fff';
            if (indKey === 'sma20') color = '#f59e0b';
            else if (indKey === 'sma50') color = '#3b82f6';
            else if (indKey === 'sma200') color = '#ec4899';
            else if (indKey === 'ema20') color = '#8b5cf6';
            else if (indKey === 'ema50') color = '#14b8a6';
            else if (indKey === 'ema200') color = '#a855f7';
            else if (indKey === 'bollinger') {
              const u = indicatorValues['bbUpper'];
              const l = indicatorValues['bbLower'];
              return (
                <span key={indKey}>
                  BB (20,2):{' '}
                  <strong style={{ color: '#6366f1' }}>
                    Basis={formatPrice(val)} U={formatPrice(u)} L={formatPrice(l)}
                  </strong>
                </span>
              );
            }

            return (
              <span key={indKey}>
                {indKey.toUpperCase()}: <strong style={{ color }}>{formatPrice(val)}</strong>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}

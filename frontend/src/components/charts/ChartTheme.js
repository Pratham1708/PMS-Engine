/**
 * ChartTheme.js
 * Color palettes and layout properties matching the PMS Engine institutional dark theme.
 */

export const ChartTheme = {
  // Chart container background
  background: '#0d0e12',
  
  // Grid line colors
  grid: {
    vertLines: 'rgba(42, 46, 57, 0.2)',
    horzLines: 'rgba(42, 46, 57, 0.2)',
  },

  // Axis and text labels
  text: {
    color: '#9ca3af', // Gray 400
    fontSize: 12,
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },

  // Crosshair line colors
  crosshair: {
    color: '#6366f1', // Indigo 500
    style: 1, // Dotted
  },

  // Price colors
  price: {
    upColor: '#10b981', // Emerald 500
    downColor: '#ef4444', // Red 500
    borderUpColor: '#10b981',
    borderDownColor: '#ef4444',
    wickUpColor: '#10b981',
    wickDownColor: '#ef4444',
    
    // Regular (Line/Area)
    lineColor: '#6366f1',
    topColor: 'rgba(99, 102, 241, 0.3)',
    bottomColor: 'rgba(99, 102, 241, 0.0)',
  },

  // Volume bar colors
  volume: {
    upColor: 'rgba(16, 185, 129, 0.35)',
    downColor: 'rgba(239, 68, 68, 0.35)',
  },

  // Technical indicator colors
  indicators: {
    sma20: '#f59e0b',  // Amber
    sma50: '#3b82f6',  // Blue
    sma200: '#ec4899', // Pink
    ema20: '#8b5cf6',  // Purple
    ema50: '#14b8a6',  // Teal
    ema200: '#a855f7', // Light purple
    bbUpper: '#6366f1',
    bbLower: '#6366f1',
    bbBasis: 'rgba(99, 102, 241, 0.5)',
    bbBackground: 'rgba(99, 102, 241, 0.05)',
  },

  // Markers styling
  markers: {
    'STRONG BUY': { color: '#10b981', symbol: '▲' },
    'BUY': { color: '#34d399', symbol: '▲' },
    'HOLD': { color: '#f59e0b', symbol: '■' },
    'SELL': { color: '#f87171', symbol: '▼' },
    'STRONG SELL': { color: '#ef4444', symbol: '▼' }
  }
};

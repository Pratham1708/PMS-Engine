/**
 * ChartUtils.js
 * Technical indicators and data mapping utility functions for the unified charting framework.
 */

/**
 * Format a Date string or Object into a YYYY-MM-DD format suitable for Lightweight Charts.
 */
export function formatChartTime(dateInput) {
  if (!dateInput) return '';
  const dateObj = new Date(dateInput);
  if (isNaN(dateObj.getTime())) return '';
  const year = dateObj.getFullYear();
  const month = String(dateObj.getMonth() + 1).padStart(2, '0');
  const day = String(dateObj.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Map backend raw data to standard Lightweight Charts format.
 * Sourced from yfinance or local SQLite schema.
 * Handles variations in property names (casing, etc.).
 */
export function mapOhlcvData(rawData) {
  if (!Array.isArray(rawData)) return [];
  
  return rawData
    .map((item) => {
      // Support multiple variants of property names from backend responses
      const timeStr = item.date || item.Date || item.time || item.timestamp;
      
      // Look for any alternative numeric key if standard OHLC keys are not available
      let fallbackVal = 0;
      for (const k of Object.keys(item)) {
        if (k !== 'date' && k !== 'Date' && k !== 'time' && k !== 'timestamp' && typeof item[k] === 'number') {
          fallbackVal = item[k];
          break;
        }
      }

      const openVal = item.open != null ? item.open : (item.Open != null ? item.Open : fallbackVal);
      const highVal = item.high != null ? item.high : (item.High != null ? item.High : fallbackVal);
      const lowVal = item.low != null ? item.low : (item.Low != null ? item.Low : fallbackVal);
      const closeVal = item.close != null ? item.close : (item.Close != null ? item.Close : (item.CurrentPrice != null ? item.CurrentPrice : fallbackVal));
      const volumeVal = item.volume != null ? item.volume : (item.Volume != null ? item.Volume : 0);

      const formattedTime = formatChartTime(timeStr);
      if (!formattedTime) return null;

      return {
        time: formattedTime,
        open: Number(openVal),
        high: Number(highVal),
        low: Number(lowVal),
        close: Number(closeVal),
        volume: Number(volumeVal),
        isSingleValue: (item.open == null && item.Open == null && item.high == null && item.High == null),
      };
    })
    .filter(Boolean)
    // Sort chronological ascending
    .sort((a, b) => a.time.localeCompare(b.time));
}

/**
 * Calculate Simple Moving Average (SMA)
 */
export function calculateSMA(data, period = 20) {
  const sma = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      continue;
    }
    let sum = 0;
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close;
    }
    sma.push({
      time: data[i].time,
      value: sum / period,
    });
  }
  return sma;
}

/**
 * Calculate Exponential Moving Average (EMA)
 */
export function calculateEMA(data, period = 20) {
  const ema = [];
  if (data.length === 0) return ema;

  const k = 2 / (period + 1);
  let prevEma = data[0].close;

  // Set initial seed to first value (or simple SMA if preferred)
  ema.push({
    time: data[0].time,
    value: prevEma,
  });

  for (let i = 1; i < data.length; i++) {
    const currentVal = data[i].close;
    const currentEma = currentVal * k + prevEma * (1 - k);
    ema.push({
      time: data[i].time,
      value: currentEma,
    });
    prevEma = currentEma;
  }
  
  // Filter to only match indexes after period has sufficient data
  return ema.filter((_, idx) => idx >= period - 1);
}

/**
 * Calculate Bollinger Bands (BB)
 * Returns { upper, basis, lower } series array
 */
export function calculateBollingerBands(data, period = 20, numStdDev = 2) {
  const upper = [];
  const basis = [];
  const lower = [];

  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      continue;
    }

    let sum = 0;
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close;
    }
    const mean = sum / period;

    let varianceSum = 0;
    for (let j = 0; j < period; j++) {
      varianceSum += Math.pow(data[i - j].close - mean, 2);
    }
    const stdDev = Math.sqrt(varianceSum / period);

    basis.push({ time: data[i].time, value: mean });
    upper.push({ time: data[i].time, value: mean + numStdDev * stdDev });
    lower.push({ time: data[i].time, value: mean - numStdDev * stdDev });
  }

  return { upper, basis, lower };
}

/**
 * Sync zoom and scroll across multiple chart instances
 */
export function syncCharts(charts) {
  if (!Array.isArray(charts) || charts.length <= 1) return;

  charts.forEach((chart, index) => {
    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (!range) return;
      charts.forEach((otherChart, otherIndex) => {
        if (index !== otherIndex) {
          otherChart.timeScale().setVisibleLogicalRange(range);
        }
      });
    });
  });
}

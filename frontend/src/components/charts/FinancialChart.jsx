import React, { useEffect, useRef, useState } from 'react';
import { createChart, AreaSeries, CandlestickSeries, LineSeries, HistogramSeries } from 'lightweight-charts';
import { ChartTheme } from './ChartTheme';
import {
  mapOhlcvData,
  calculateSMA,
  calculateEMA,
  calculateBollingerBands,
  formatChartTime,
} from './ChartUtils';
import ChartToolbar from './ChartToolbar';
import ChartLegend from './ChartLegend';

/**
 * FinancialChart.jsx
 * Unified institutional-grade charting component powered by TradingView Lightweight Charts.
 * Supports line/candle modes, synchronized volume, overlay indicators, custom markers with detailed tooltips,
 * fullscreen toggling, reset zoom, screenshot export, and handles standard data structure formats.
 */
export default function FinancialChart({
  symbol = 'CHART',
  companyName = '',
  rawData = [],
  recHistory = [], // [{ Date: '2026-07-01', Rating: 'STRONG BUY', CompositeScoreV2: 78.5, ... }]
  timeframe = '1Y',
  onChangeTimeframe,
  height = 420,
  valueKeys = ['close'], // Support multiple line overlays (like portfolio, benchmark, etc.)
  colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444'],
}) {
  const containerRef = useRef(null);
  const chartWrapperRef = useRef(null);
  const chartInstanceRef = useRef(null);
  
  // Series refs
  const priceSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const indicatorSeriesRefs = useRef({}); // { sma20: seriesInstance, ... }
  const extraSeriesRefs = useRef({}); // { benchmark: seriesInstance, ... }

  // States
  const [chartMode, setChartMode] = useState('line'); // 'line' | 'candlestick'
  const [activeIndicators, setActiveIndicators] = useState([]);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Data for legend overlay
  const [legendData, setLegendData] = useState(null);
  const [indicatorValues, setIndicatorValues] = useState({});
  const [tooltipInfo, setTooltipInfo] = useState(null); // { x, y, content }

  // Pre-process data
  const chartData = mapOhlcvData(rawData);

  // Check characteristics of the loaded series
  const isSingleValue = chartData.some((d) => d.isSingleValue);
  const activeMode = isSingleValue ? 'line' : chartMode;
  const hasVolume = chartData.some((d) => d.volume > 0);

  // Re-build or update chart on mode, data or indicators change
  useEffect(() => {
    if (!containerRef.current || chartData.length === 0) return;

    // 1. Create chart instance if missing
    if (!chartInstanceRef.current) {
      const chart = createChart(containerRef.current, {
        width: containerRef.current.clientWidth,
        height: height,
        layout: {
          background: { type: 'solid', color: ChartTheme.background },
          textColor: ChartTheme.text.color,
          fontSize: ChartTheme.text.fontSize,
          fontFamily: ChartTheme.text.fontFamily,
        },
        grid: {
          vertLines: { color: ChartTheme.grid.vertLines },
          horzLines: { color: ChartTheme.grid.horzLines },
        },
        crosshair: {
          mode: 1, // Magnet
          vertLine: {
            color: ChartTheme.crosshair.color,
            style: ChartTheme.crosshair.style,
          },
          horzLine: {
            color: ChartTheme.crosshair.color,
            style: ChartTheme.crosshair.style,
          },
        },
        timeScale: {
          borderColor: 'rgba(255, 255, 255, 0.08)',
          rightOffset: 12,
          barSpacing: 6,
        },
      });

      chartInstanceRef.current = chart;

      // Handle responsiveness
      const handleResize = () => {
        if (chartInstanceRef.current && containerRef.current) {
          chartInstanceRef.current.applyOptions({
            width: containerRef.current.clientWidth,
          });
        }
      };
      window.addEventListener('resize', handleResize);
      chartInstanceRef.current._cleanupResize = () => window.removeEventListener('resize', handleResize);

      // Default legend data to last element
      if (chartData.length > 0) {
        const lastBar = chartData[chartData.length - 1];
        setLegendData(lastBar);
      }
    }

    const chart = chartInstanceRef.current;

    // 2. Clear existing price & volume series
    if (priceSeriesRef.current) {
      try {
        chart.removeSeries(priceSeriesRef.current);
      } catch {}
      priceSeriesRef.current = null;
    }
    if (volumeSeriesRef.current) {
      try {
        chart.removeSeries(volumeSeriesRef.current);
      } catch {}
      volumeSeriesRef.current = null;
    }
    
    // Clear indicator series
    Object.values(indicatorSeriesRefs.current).forEach((series) => {
      try {
        chart.removeSeries(series);
      } catch {}
    });
    indicatorSeriesRefs.current = {};

    // Clear extra line series
    Object.values(extraSeriesRefs.current).forEach((series) => {
      try {
        chart.removeSeries(series);
      } catch {}
    });
    extraSeriesRefs.current = {};

    // 3. Add base price series (Line / Candle)
    if (activeMode === 'line') {
      const mainKey = valueKeys[0] || 'close';
      
      // Main series as Area
      priceSeriesRef.current = chart.addSeries(AreaSeries, {
        lineColor: colors[0] || ChartTheme.price.lineColor,
        topColor: colors[0] ? `${colors[0]}4d` : ChartTheme.price.topColor, // 30% opacity
        bottomColor: colors[0] ? `${colors[0]}00` : ChartTheme.price.bottomColor, // 0% opacity
        lineWidth: 2,
        priceFormat: { type: 'price', precision: 2, minMove: 0.01 },
      });
      priceSeriesRef.current.setData(
        chartData.map((d) => ({ time: d.time, value: d[mainKey] != null ? d[mainKey] : d.close }))
      );

      // Extra line overlays (for multi-series line charts)
      valueKeys.slice(1).forEach((key, idx) => {
        const lineCol = colors[idx + 1] || '#10b981';
        const lineSeries = chart.addSeries(LineSeries, {
          color: lineCol,
          lineWidth: 2,
          priceFormat: { type: 'price', precision: 2, minMove: 0.01 },
        });
        lineSeries.setData(
          chartData.map((d) => ({ time: d.time, value: d[key] != null ? d[key] : 0 }))
        );
        extraSeriesRefs.current[key] = lineSeries;
      });
    } else {
      priceSeriesRef.current = chart.addSeries(CandlestickSeries, {
        upColor: ChartTheme.price.upColor,
        downColor: ChartTheme.price.downColor,
        borderUpColor: ChartTheme.price.borderUpColor,
        borderDownColor: ChartTheme.price.borderDownColor,
        wickUpColor: ChartTheme.price.wickUpColor,
        wickDownColor: ChartTheme.price.wickDownColor,
        priceFormat: { type: 'price', precision: 2, minMove: 0.01 },
      });
      priceSeriesRef.current.setData(chartData);
    }

    // Configure main price scale margin
    priceSeriesRef.current.priceScale().applyOptions({
      scaleMargins: {
        top: 0.15,
        bottom: hasVolume ? 0.25 : 0.15, // Leaves 25% room at the bottom for Volume if volume exists
      },
    });

    // 4. Add Volume histogram series if present
    if (hasVolume) {
      volumeSeriesRef.current = chart.addSeries(HistogramSeries, {
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume', // Sits on its own scale overlay
      });

      volumeSeriesRef.current.setData(
        chartData.map((d) => {
          const color = d.close >= d.open ? ChartTheme.volume.upColor : ChartTheme.volume.downColor;
          return {
            time: d.time,
            value: d.volume,
            color,
          };
        })
      );

      // Apply scale margins to overlay volume at the bottom 20%
      chart.priceScale('volume').applyOptions({
        scaleMargins: {
          top: 0.8,
          bottom: 0,
        },
      });
    }

    // 5. Add technical indicators (skip if isSingleValue since they are for stock close prices)
    if (!isSingleValue) {
      activeIndicators.forEach((indKey) => {
        if (indKey === 'bollinger') {
          const { upper, basis, lower } = calculateBollingerBands(chartData);
          
          const upperSeries = chart.addSeries(LineSeries, {
            color: ChartTheme.indicators.bbUpper,
            lineWidth: 1,
            lineStyle: 2, // Dotted
          });
          upperSeries.setData(upper);
          indicatorSeriesRefs.current['bbUpper'] = upperSeries;

          const lowerSeries = chart.addSeries(LineSeries, {
            color: ChartTheme.indicators.bbLower,
            lineWidth: 1,
            lineStyle: 2,
          });
          lowerSeries.setData(lower);
          indicatorSeriesRefs.current['bbLower'] = lowerSeries;

          const basisSeries = chart.addSeries(LineSeries, {
            color: ChartTheme.indicators.bbBasis,
            lineWidth: 1,
          });
          basisSeries.setData(basis);
          indicatorSeriesRefs.current['bbBasis'] = basisSeries;
        } else {
          let values = [];
          let color = '#fff';
          if (indKey === 'sma20') {
            values = calculateSMA(chartData, 20);
            color = ChartTheme.indicators.sma20;
          } else if (indKey === 'sma50') {
            values = calculateSMA(chartData, 50);
            color = ChartTheme.indicators.sma50;
          } else if (indKey === 'sma200') {
            values = calculateSMA(chartData, 200);
            color = ChartTheme.indicators.sma200;
          } else if (indKey === 'ema20') {
            values = calculateEMA(chartData, 20);
            color = ChartTheme.indicators.ema20;
          } else if (indKey === 'ema50') {
            values = calculateEMA(chartData, 50);
            color = ChartTheme.indicators.ema50;
          } else if (indKey === 'ema200') {
            values = calculateEMA(chartData, 200);
            color = ChartTheme.indicators.ema200;
          }

          const series = chart.addSeries(LineSeries, {
            color,
            lineWidth: 1.5,
          });
          series.setData(values);
          indicatorSeriesRefs.current[indKey] = series;
        }
      });
    }

    // 6. Settle recommendation markers
    if (recHistory.length > 0 && priceSeriesRef.current) {
      const markers = recHistory
        .map((rec) => {
          const itemTime = rec.Date || rec.time || rec.timestamp || rec.analyzed_at;
          const formattedTime = formatChartTime(itemTime);
          
          // Only show markers that exist in our chart time series
          const exists = chartData.some((c) => c.time === formattedTime);
          if (!exists) return null;

          const rating = String(rec.FinalRating || rec.rating || 'HOLD').toUpperCase();
          const themeInfo = ChartTheme.markers[rating] || { color: '#f59e0b', symbol: '■' };
          
          const isBuy = rating.includes('BUY');
          const isSell = rating.includes('SELL');
          
          return {
            time: formattedTime,
            position: isBuy ? 'belowBar' : (isSell ? 'aboveBar' : 'inBar'),
            color: themeInfo.color,
            shape: isBuy ? 'arrowUp' : (isSell ? 'arrowDown' : 'square'),
            text: themeInfo.symbol,
            size: 1.2,
            id: formattedTime,
            recData: rec, // Save full payload inside the marker
          };
        })
        .filter(Boolean);

      try {
        priceSeriesRef.current.setMarkers(markers);
      } catch {}
    }

    // 7. Subscribe to crosshair movement
    chart.subscribeCrosshairMove((param) => {
      const currentIndicatorVals = {};
      
      if (!param || !param.time) {
        // Reset to last element values if crosshair leaves chart
        if (chartData.length > 0) {
          const lastBar = chartData[chartData.length - 1];
          const defaultLegend = { ...lastBar };
          valueKeys.forEach((key) => {
            defaultLegend[key] = lastBar[key] != null ? lastBar[key] : lastBar.close;
          });
          setLegendData(defaultLegend);
        }
        setIndicatorValues({});
        setTooltipInfo(null);
        return;
      }

      // Find price series value
      const pricePoint = param.seriesData.get(priceSeriesRef.current);
      const volumePoint = volumeSeriesRef.current ? param.seriesData.get(volumeSeriesRef.current) : null;

      if (pricePoint) {
        const timeStr = typeof param.time === 'string' ? param.time : formatChartTime(new Date(param.time));
        const newLegend = {
          time: timeStr,
          open: pricePoint.open || pricePoint.value,
          high: pricePoint.high || pricePoint.value,
          low: pricePoint.low || pricePoint.value,
          close: pricePoint.close || pricePoint.value,
          volume: volumePoint ? volumePoint.value : null,
          isSingleValue: isSingleValue,
        };

        // Populate multiple line series values
        valueKeys.forEach((key, idx) => {
          if (idx === 0) {
            newLegend[key] = pricePoint.value || pricePoint.close;
          } else {
            const series = extraSeriesRefs.current[key];
            if (series) {
              const pt = param.seriesData.get(series);
              newLegend[key] = pt ? pt.value : null;
            }
          }
        });

        setLegendData(newLegend);
      }

      // Populate indicator legend values
      Object.entries(indicatorSeriesRefs.current).forEach(([key, series]) => {
        const dataPoint = param.seriesData.get(series);
        if (dataPoint) {
          currentIndicatorVals[key] = dataPoint.value;
        }
      });
      setIndicatorValues(currentIndicatorVals);

      // Check recommendation tooltip hover
      if (recHistory.length > 0) {
        const hoveredTime = typeof param.time === 'string' ? param.time : formatChartTime(new Date(param.time));
        const matchedRec = recHistory.find((rec) => formatChartTime(rec.Date || rec.time || rec.timestamp || rec.analyzed_at) === hoveredTime);

        if (matchedRec) {
          const toolTipWidth = 240;
          const toolTipHeight = 180;
          
          const point = param.point;
          if (!point) return;
          
          let x = point.x + 15;
          let y = point.y + 15;
          
          const chartWidth = containerRef.current.clientWidth;
          const chartHeight = containerRef.current.clientHeight;
          
          if (x + toolTipWidth > chartWidth) {
            x = point.x - toolTipWidth - 15;
          }
          if (y + toolTipHeight > chartHeight) {
            y = point.y - toolTipHeight - 15;
          }

          setTooltipInfo({
            x,
            y,
            rec: matchedRec,
          });
        } else {
          setTooltipInfo(null);
        }
      }
    });

    chart.timeScale().fitContent();

  }, [activeMode, rawData, activeIndicators, recHistory, height, valueKeys, colors]);

  // Clean up chart on unmount
  useEffect(() => {
    return () => {
      if (chartInstanceRef.current) {
        if (chartInstanceRef.current._cleanupResize) {
          chartInstanceRef.current._cleanupResize();
        }
        chartInstanceRef.current.remove();
        chartInstanceRef.current = null;
      }
    };
  }, []);

  // Toolbar Handlers
  const handleToggleIndicator = (key) => {
    setActiveIndicators((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  };

  const handleResetZoom = () => {
    if (chartInstanceRef.current) {
      chartInstanceRef.current.timeScale().fitContent();
    }
  };

  const handleExportImage = () => {
    if (!chartInstanceRef.current) return;
    const canvas = chartInstanceRef.current.takeScreenshot();
    if (canvas) {
      const dataUrl = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.download = `${symbol}_chart.png`;
      link.href = dataUrl;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const handleToggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // Keep responsive width during fullscreen transitions
  useEffect(() => {
    setTimeout(() => {
      if (chartInstanceRef.current && containerRef.current) {
        chartInstanceRef.current.applyOptions({
          width: containerRef.current.clientWidth,
          height: isFullscreen ? window.innerHeight - 100 : height,
        });
        chartInstanceRef.current.timeScale().fitContent();
      }
    }, 150);
  }, [isFullscreen]);

  if (rawData.length === 0) {
    return (
      <div className="card" style={{
        height: `${height}px`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--text-muted)',
        background: ChartTheme.background,
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '8px',
      }}>
        No historical chart data available for {symbol}
      </div>
    );
  }

  return (
    <div
      ref={chartWrapperRef}
      style={isFullscreen ? {
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 99999,
        background: '#0d0e12',
        display: 'flex',
        flexDirection: 'column',
        padding: '16px',
        boxSizing: 'border-box',
      } : {
        position: 'relative',
        background: '#0d0e12',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '8px',
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        boxSizing: 'border-box',
        overflow: 'hidden',
      }}
    >
      {/* Chart controls toolbar */}
      <ChartToolbar
        timeframe={timeframe}
        onChangeTimeframe={onChangeTimeframe}
        mode={activeMode}
        onChangeMode={isSingleValue ? null : setChartMode}
        activeIndicators={activeIndicators}
        onToggleIndicator={isSingleValue ? null : handleToggleIndicator}
        onResetZoom={handleResetZoom}
        onExportImage={handleExportImage}
        onToggleFullscreen={handleToggleFullscreen}
        isFullscreen={isFullscreen}
      />

      {/* Main chart rendering container */}
      <div style={{ position: 'relative', flex: 1, minHeight: isFullscreen ? '0' : `${height}px` }}>
        {/* Legendary float values */}
        <ChartLegend
          symbol={symbol.replace('.NS', '')}
          companyName={companyName}
          crosshairData={legendData}
          activeIndicators={activeIndicators}
          indicatorValues={indicatorValues}
          valueKeys={valueKeys}
        />

        {/* Lightweight Charts Canvas mount */}
        <div ref={containerRef} style={{ width: '100%', height: '100%' }} />

        {/* Floating marker popup tooltip */}
        {tooltipInfo && (
          <div style={{
            position: 'absolute',
            left: `${tooltipInfo.x}px`,
            top: `${tooltipInfo.y}px`,
            background: 'rgba(21, 24, 33, 0.95)',
            border: `1px solid ${ChartTheme.markers[String(tooltipInfo.rec.FinalRating || tooltipInfo.rec.rating || 'HOLD').toUpperCase()]?.color || '#6366f1'}`,
            borderRadius: '6px',
            padding: '10px 12px',
            color: '#fff',
            zIndex: 100,
            pointerEvents: 'none',
            fontSize: '11px',
            boxShadow: '0 8px 16px rgba(0,0,0,0.6)',
            width: '230px',
            display: 'flex',
            flexDirection: 'column',
            gap: '5px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong style={{
                color: ChartTheme.markers[String(tooltipInfo.rec.FinalRating || tooltipInfo.rec.rating || 'HOLD').toUpperCase()]?.color,
                fontSize: '13px',
                fontWeight: 800,
              }}>
                ▲ {tooltipInfo.rec.FinalRating || tooltipInfo.rec.rating || 'HOLD'}
              </strong>
              <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '9px' }}>
                {tooltipInfo.rec.Date || tooltipInfo.rec.time || tooltipInfo.rec.analyzed_at || '—'}
              </span>
            </div>
            
            <div style={{ height: '1px', background: 'rgba(255, 255, 255, 0.08)', margin: '2px 0' }} />

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
              <div>Composite: <strong style={{ color: '#fff' }}>{parseFloat(tooltipInfo.rec.CompositeScoreV2 || tooltipInfo.rec.composite_score || 0).toFixed(2)}</strong></div>
              <div>Confidence: <strong style={{ color: '#fff' }}>{parseFloat(tooltipInfo.rec.Confidence || tooltipInfo.rec.confidence || 0).toFixed(1)}%</strong></div>
              <div>Technical: <strong style={{ color: '#fff' }}>{parseFloat(tooltipInfo.rec.TechnicalScore || tooltipInfo.rec.technical_score || 0).toFixed(1)}</strong></div>
              <div>ML Forecast: <strong style={{ color: '#fff' }}>{parseFloat(tooltipInfo.rec.MLScore || tooltipInfo.rec.ml_score || 0).toFixed(1)}</strong></div>
            </div>

            {(tooltipInfo.rec.FinalRatingReason || tooltipInfo.rec.rating_reason) && (
              <div style={{ color: 'rgba(255, 255, 255, 0.7)', fontStyle: 'italic', marginTop: '4px', lineHeight: '1.4', fontSize: '10px' }}>
                "{tooltipInfo.rec.FinalRatingReason || tooltipInfo.rec.rating_reason}"
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

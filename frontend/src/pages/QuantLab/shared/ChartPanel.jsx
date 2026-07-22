import React, { useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import FinancialChart from '../../../components/charts/FinancialChart';

/**
 * Reusable tabbed Recharts dashboard panel.
 *
 * @param {Array} props.charts - Array of chart configurations:
 *   [
 *     {
 *       key: 'equity',
 *       title: 'Equity Curve',
 *       type: 'area', // line, area, bar, scatter
 *       data: [...],
 *       xKey: 'date',
 *       yKeys: ['portfolio', 'benchmark'], // or single string
 *       colors: ['#6366f1', '#9ca3af'],
 *     },
 *     ...
 *   ]
 */
export default function ChartPanel({ charts }) {
  const [activeTab, setActiveTab] = useState(charts?.[0]?.key || '');

  if (!charts || charts.length === 0) return null;

  const currentChart = charts.find((c) => c.key === activeTab) || charts[0];

  const renderChart = (c) => {
    if (!c.data || c.data.length === 0) {
      return (
        <div style={{
          height: '350px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-secondary)'
        }}>
          No data available for this chart.
        </div>
      );
    }

    const xKey = c.xKey || 'date';
    const yKeys = Array.isArray(c.yKeys) ? c.yKeys : [c.yKeys || 'value'];
    const colors = c.colors || ['#6366f1', '#10b981', '#f59e0b', '#ef4444'];

    switch (c.type) {
      case 'area':
      case 'line':
      default:
        return (
          <div style={{ width: '100%', height: '380px' }}>
            <FinancialChart
              symbol={c.title || 'Chart'}
              rawData={c.data}
              valueKeys={yKeys}
              colors={colors}
              height={340}
            />
          </div>
        );

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={c.data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey={xKey} stroke="var(--text-muted)" fontSize={11} tickLine={false} />
              <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{ background: '#111827', borderColor: 'var(--border-primary)', borderRadius: '6px' }}
                labelStyle={{ fontWeight: 'bold', color: 'var(--text-primary)' }}
              />
              <Legend verticalAlign="top" height={36} iconType="circle" />
              {yKeys.map((yK, i) => (
                <Bar key={yK} dataKey={yK} fill={colors[i]} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'scatter':
        return (
          <ResponsiveContainer width="100%" height={350}>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: -20 }}>
              <CartesianGrid stroke="rgba(255,255,255,0.05)" />
              <XAxis type="number" dataKey={xKey} name="Holding Days" stroke="var(--text-muted)" fontSize={11} unit="d" />
              <YAxis type="number" dataKey={yKeys[0]} name="Return" stroke="var(--text-muted)" fontSize={11} unit="%" />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{ background: '#111827', borderColor: 'var(--border-primary)', borderRadius: '6px' }}
              />
              <Legend verticalAlign="top" height={36} />
              <Scatter name="Trades" data={c.data} fill={colors[0]} />
            </ScatterChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
      <div className="lab-tabs" style={{
        display: 'flex',
        borderBottom: '1px solid var(--border-primary)',
        marginBottom: '15px',
        whiteSpace: 'nowrap',
      }}>
        {charts.map((c) => (
          <button
            key={c.key}
            onClick={() => setActiveTab(c.key)}
            className={`lab-tab ${activeTab === c.key ? 'active' : ''}`}
            style={{
              background: 'none',
              border: 'none',
              padding: '10px 16px',
              cursor: 'pointer',
              color: activeTab === c.key ? 'var(--accent-primary)' : 'var(--text-secondary)',
              borderBottom: activeTab === c.key ? '2px solid var(--accent-primary)' : '2px solid transparent',
              fontWeight: '500'
            }}
          >
            {c.title}
          </button>
        ))}
      </div>
      {currentChart.description && (
        <div style={{
          padding: '10px 14px',
          marginBottom: '14px',
          background: 'rgba(99, 102, 241, 0.08)',
          borderLeft: '3px solid var(--accent-primary)',
          borderRadius: '4px',
          fontSize: '12.5px',
          color: 'var(--text-secondary)',
          lineHeight: '1.4'
        }}>
          💡 <strong style={{ color: 'var(--text-primary)' }}>What this signifies:</strong> {currentChart.description}
        </div>
      )}
      <div style={{ padding: '10px 0' }}>
        {renderChart(currentChart)}
      </div>
    </div>
  );
}


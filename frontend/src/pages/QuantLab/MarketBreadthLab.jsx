import React, { useState } from 'react';
import { getMarketBreadth } from '../../api/labApi';
import ChartPanel from './shared/ChartPanel';
import MetricsGrid from './shared/MetricsGrid';

import LabWorkflowGuide from '../../components/common/LabWorkflowGuide';

export default function MarketBreadthLab() {
  const [period, setPeriod] = useState('6M');

  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getMarketBreadth(period);
      setData(res.data);
    } catch (err) {
      console.error(err);
      setError('Failed to compute market breadth index metrics.');
    } finally {
      setLoading(false);
    }
  };

  const getBreadthCharts = () => {
    if (!data?.timeline || data.timeline.length === 0) return [];
    return [
      {
        key: 'participation',
        title: 'Moving Average Participation (% Stocks Above 50D SMA)',
        type: 'area',
        data: data.timeline,
        xKey: 'date',
        yKeys: ['participation_pct'],
        colors: ['#10b981'],
      },
      {
        key: 'ad_ratio',
        title: 'Advance-Decline Ratio Timeline',
        type: 'line',
        data: data.timeline,
        xKey: 'date',
        yKeys: ['ad_ratio'],
        colors: ['#3b82f6'],
      },
      {
        key: 'highs_lows',
        title: '20-Day New Highs vs New Lows Count',
        type: 'bar',
        data: data.timeline,
        xKey: 'date',
        yKeys: ['new_highs', 'new_lows'],
        colors: ['#10b981', '#ef4444'],
      }
    ];
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>📈 Market Breadth & Participation Lab</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Analyze overall market health, Advance-Decline timeline, and the participation index (% of stocks above 50 SMA).
        </p>
      </div>

      <LabWorkflowGuide
        title="Market Breadth Lab"
        description="Monitor market participation dynamics using Advance/Decline ratios, net advances, and stocks above moving averages."
        icon="📈"
        steps={[
          { title: '1. Select Lookback Window', desc: 'Choose analysis window (3M, 6M, or 1Y).' },
          { title: '2. Compute Breadth', desc: 'Click Calculate Market Breadth to analyze constituent stock trends.' },
          { title: '3. Inspect A/D Line', desc: 'View the Advance/Decline trend timeline to identify market divergence.' },
          { title: '4. Analyze Participation', desc: 'Check whether market rallies are broad-based or driven by a narrow subset of stocks.' }
        ]}
      />

      <div style={{
        display: 'grid',
        gridTemplateColumns: '300px 1fr',
        gap: '24px',
        alignItems: 'start'
      }}>
        {/* Settings */}
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', borderBottom: '1px solid var(--border-primary)', paddingBottom: '8px' }}>
            Parameters
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Research Timeline</label>
              <select
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
              >
                <option value="3M">3 Months Window</option>
                <option value="6M">6 Months Window</option>
                <option value="1Y">1 Year Window</option>
              </select>
            </div>
            <button
              onClick={handleRun}
              className="btn-primary"
              style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
              disabled={loading}
            >
              {loading ? 'Calculating...' : '📈 Compute Market Breadth'}
            </button>
          </div>
        </div>

        {/* Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {error && (
            <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px' }}>
              ⚠️ {error}
            </div>
          )}

          {loading ? (
            <div style={{ textAlign: 'center', padding: '60px 0' }}>
              <div className="spinner" style={{ margin: '0 auto 16px auto', border: '4px solid rgba(255,255,255,0.1)', borderTop: '4px solid var(--accent-primary)', borderRadius: '50%', width: '40px', height: '40px', animation: 'spin 1s linear infinite' }}></div>
              <p style={{ color: 'var(--text-secondary)' }}>Calculating stock indicators and aggregating breadth statistics...</p>
            </div>
          ) : data ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              
              {/* Snapshot metrics */}
              <MetricsGrid
                metrics={{
                  'Current AD Ratio': data.current_ad_ratio,
                  'Participation (stocks above 50 SMA)': `${data.current_participation_pct}%`,
                  'New 20D Highs': data.current_new_highs,
                  'New 20D Lows': data.current_new_lows,
                }}
              />

              {/* Timeline charts */}
              {data.timeline?.length > 0 && (
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Breadth Indexes Timeline Analysis</h3>
                  <ChartPanel charts={getBreadthCharts()} />
                </div>
              )}
            </div>
          ) : (
            <div className="card" style={{ padding: '40px', textAlign: 'center', border: '1px dashed var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
              <p style={{ color: 'var(--text-secondary)' }}>Click "Compute Market Breadth" to trigger market breadth timeline compilation.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

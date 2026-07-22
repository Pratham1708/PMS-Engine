import React, { useEffect, useState } from 'react';
import { getSectorAnalysis, runSectorReturns, getSectorResult } from '../../api/labApi';
import useExperiment from './shared/useExperiment';
import ExperimentProgress from './shared/ExperimentProgress';
import ChartPanel from './shared/ChartPanel';
import LabWorkflowGuide from '../../components/common/LabWorkflowGuide';

export default function SectorLab() {
  const [staticAnalysis, setStaticAnalysis] = useState(null);
  const [loadingStatic, setLoadingStatic] = useState(false);
  const [period, setPeriod] = useState('1Y');

  // Custom experiment hook for running sector returns research
  const secHook = useExperiment(runSectorReturns, getSectorResult, getSectorResult);

  const loadStaticAnalysis = async () => {
    setLoadingStatic(true);
    try {
      const res = await getSectorAnalysis();
      setStaticAnalysis(res.data);
    } catch (err) {
      console.error('Failed to load static sector analysis:', err);
    } finally {
      setLoadingStatic(false);
    }
  };

  useEffect(() => {
    loadStaticAnalysis();
  }, []);

  const handleRunAnalysis = () => {
    secHook.run({ period });
  };

  // Format charts for ChartPanel
  const getCharts = () => {
    if (!secHook.result?.sector_returns) return [];

    const list = [];
    const retData = secHook.result.sector_returns || [];
    if (retData.length > 0) {
      list.push({
        key: 'returns',
        title: 'Sector Realized Returns (%)',
        type: 'bar',
        data: retData,
        xKey: 'sector',
        yKeys: ['return_pct'],
        colors: ['#10b981'],
      });
    }

    return list;
  };

  // Helper to color sector cells in correlation table
  const getHeatColor = (val) => {
    if (val === null || val === undefined) return 'rgba(255,255,255,0.02)';
    const abs = Math.abs(val);
    if (val > 0) {
      return `rgba(16, 185, 129, ${Math.min(0.6, abs)})`;
    } else {
      return `rgba(239, 68, 68, ${Math.min(0.6, abs)})`;
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>🏭 Sector Analysis & Momentum Rotation Lab</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Assess industry-level composite score clusters, map sector return correlations, and view rotation weights.
        </p>
      </div>

      <LabWorkflowGuide
        title="Sector Analysis Lab"
        description="Evaluate cross-sector relative return performance, sector momentum rotation signals, and inter-sector correlation matrices."
        icon="🗺️"
        steps={[
          { title: '1. Choose Assessment Period', desc: 'Select historical timeframe (e.g. 1Y, 3Y, or 5Y).' },
          { title: '2. Run Sector Analysis', desc: 'Click Run Sector Performance to compute relative sector returns vs NIFTY 50.' },
          { title: '3. Inspect Clusters & Returns', desc: 'Review top-performing sectors (e.g. NIFTY IT vs NIFTY BANK).' },
          { title: '4. Analyze Rotation & Correlation', desc: 'Examine inter-sector correlation heatmap to identify uncorrelated sector hedges.' }
        ]}
      />

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '24px',
        alignItems: 'start',
        marginBottom: '32px'
      }}>
        {/* Sector Scores Panel */}
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Sector Composite Score Clusters</h3>
          {loadingStatic ? (
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Loading clusters...</p>
          ) : staticAnalysis?.sector_scores ? (
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table" style={{ width: '100%', fontSize: '12px' }}>
                <thead>
                  <tr>
                    <th>Sector</th>
                    <th style={{ textAlign: 'center' }}>Avg Score</th>
                    <th style={{ textAlign: 'center' }}>Avg Tech</th>
                    <th style={{ textAlign: 'center' }}>Avg ML</th>
                    <th style={{ textAlign: 'center' }}>Avg GRU</th>
                    <th style={{ textAlign: 'center' }}>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(staticAnalysis.sector_scores).map(([sector, val]) => (
                    <tr key={sector}>
                      <td><strong>{sector}</strong></td>
                      <td style={{ textAlign: 'center', fontWeight: '700', color: '#3b82f6' }}>
                        {val.composite?.toFixed(1) || '—'}
                      </td>
                      <td style={{ textAlign: 'center' }}>{val.technical?.toFixed(1) || '—'}</td>
                      <td style={{ textAlign: 'center' }}>{val.ml?.toFixed(1) || '—'}</td>
                      <td style={{ textAlign: 'center' }}>{val.gru?.toFixed(1) || '—'}</td>
                      <td style={{ textAlign: 'center' }}>{val.count || 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>No cluster database available.</p>
          )}
        </div>

        {/* Sector Backtest Configuration */}
        <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Sector Returns & Rotation Research</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '20px' }}>
            Initiate a sector index return backtest and calculate momentum-based rotation parameters across available groups.
          </p>
          <div style={{ display: 'flex', gap: '15px', alignItems: 'end' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Returns Horizon Period</label>
              <select
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
              >
                <option value="1Y">1 Year Returns</option>
                <option value="3Y">3 Years Returns</option>
                <option value="5Y">5 Years Returns</option>
              </select>
            </div>
            <button
              onClick={handleRunAnalysis}
              className="btn-primary"
              style={{ padding: '10px 16px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
              disabled={secHook.status === 'running'}
            >
              🚀 Run Backtest
            </button>
          </div>
          
          <div style={{ marginTop: '20px' }}>
            <ExperimentProgress
              status={secHook.status}
              elapsedTime={secHook.elapsedTime}
              error={secHook.error}
              onReset={secHook.reset}
            />
          </div>
        </div>
      </div>

      {secHook.status === 'complete' && secHook.result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Charts */}
          <ChartPanel charts={getCharts()} />

          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '24px',
            alignItems: 'start'
          }}>
            {/* Correlation Heatmap */}
            {secHook.result.sector_correlation?.flat?.length > 0 && (
              <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Sector Return Correlations Heatmap</h3>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ borderCollapse: 'collapse', fontSize: '11px', margin: '0 auto' }}>
                    <thead>
                      <tr>
                        <th style={{ padding: '6px', border: '1px solid var(--border-primary)' }}></th>
                        {secHook.result.sector_correlation.sectors?.map((s) => (
                          <th key={s} style={{ padding: '6px', border: '1px solid var(--border-primary)', fontSize: '9px', minWidth: '70px', textTransform: 'capitalize' }}>
                            {s.split(' ')[0]}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {secHook.result.sector_correlation.sectors?.map((sA) => (
                        <tr key={sA}>
                          <td style={{ padding: '6px', border: '1px solid var(--border-primary)', fontWeight: 'bold', textTransform: 'capitalize' }}>
                            {sA.split(' ')[0]}
                          </td>
                          {secHook.result.sector_correlation.sectors?.map((sB) => {
                            const row = secHook.result.sector_correlation.flat.find(
                              (item) => item.sector_a === sA && item.sector_b === sB
                            );
                            const corrVal = row ? row.correlation : (sA === sB ? 1.0 : null);
                            return (
                              <td
                                key={sB}
                                style={{
                                  padding: '10px',
                                  border: '1px solid var(--border-primary)',
                                  textAlign: 'center',
                                  background: getHeatColor(corrVal),
                                  color: Math.abs(corrVal || 0) > 0.4 ? '#fff' : 'var(--text-secondary)',
                                  fontWeight: '600'
                                }}
                              >
                                {corrVal !== null ? corrVal.toFixed(2) : '—'}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Rotation Weights */}
            {secHook.result.sector_rotation?.length > 0 && (
              <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>Momentum Rotation Allocations</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '16px' }}>
                  Top recommended sector tickers based on combined return momentum signals.
                </p>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table" style={{ width: '100%' }}>
                    <thead>
                      <tr>
                        <th>Sector Target Name</th>
                        <th style={{ textAlign: 'center' }}>Allocation Signal</th>
                      </tr>
                    </thead>
                    <tbody>
                      {secHook.result.sector_rotation.map((rot, idx) => (
                        <tr key={idx}>
                          <td><strong>{rot.sector}</strong></td>
                          <td style={{ textAlign: 'center' }}>
                            <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'rgba(16,185,129,0.1)', color: '#10b981', fontWeight: '700' }}>
                              SELECTED
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  );
}

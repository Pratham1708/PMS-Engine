import React, { useState } from 'react';
import { getLiquidityResearch } from '../../api/labApi';
import MetricsGrid from './shared/MetricsGrid';

export default function LiquidityLab() {
  const [symbol, setSymbol] = useState('RELIANCE.NS');
  
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getLiquidityResearch(symbol);
      setData(res.data);
    } catch (err) {
      console.error(err);
      setError('Failed to audit ticker liquidity.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>💧 Liquidity & Suitability Auditor</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Audit stock liquidity, gap risk frequency, and market impact estimates (Amihud Illiquidity Score) to qualify assets for portfolio selection.
        </p>
      </div>

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
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Stock Symbol</label>
              <input
                type="text"
                className="input"
                style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              />
            </div>
            <button
              onClick={handleRun}
              className="btn-primary"
              style={{ width: '100%', padding: '10px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
              disabled={loading}
            >
              {loading ? 'Auditing...' : '💧 Audit Liquidity'}
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
              <p style={{ color: 'var(--text-secondary)' }}>Auditing yFinance volume matrices and gap ratios...</p>
            </div>
          ) : data ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              
              {/* Decision Banner */}
              <div style={{
                padding: '24px',
                background: data.decision === 'ACCEPT' ? 'rgba(16,185,129,0.06)' : 'rgba(239,68,68,0.06)',
                border: `1px solid ${data.decision === 'ACCEPT' ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
                borderRadius: 'var(--radius-lg)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div>
                  <h3 style={{ fontSize: '18px', fontWeight: '800', color: data.decision === 'ACCEPT' ? '#10b981' : '#ef4444', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {data.decision === 'ACCEPT' ? '✅ SUITABLE FOR PMS RECOMMENDATION' : '❌ REJECTED BY LIQUIDITY FILTERS'}
                  </h3>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    Ticker: <strong>{data.symbol}</strong> · Audited against ADV, Gap-Open frequency, and market impact limits.
                  </p>
                </div>
                <div style={{
                  fontSize: '14px',
                  fontWeight: '700',
                  padding: '6px 16px',
                  borderRadius: '20px',
                  background: data.decision === 'ACCEPT' ? '#10b981' : '#ef4444',
                  color: '#fff'
                }}>
                  {data.decision}
                </div>
              </div>

              {/* Reasons if Rejected */}
              {data.reasons && data.reasons.length > 0 && (
                <div className="card" style={{ padding: '20px', background: 'rgba(239,68,68,0.02)', border: '1px solid rgba(239,68,68,0.1)', borderRadius: 'var(--radius-lg)' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#ef4444', marginBottom: '12px' }}>Breached Threshold Violations</h4>
                  <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.7' }}>
                    {data.reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Metrics Grid */}
              <MetricsGrid
                metrics={{
                  'Average Daily Volume (ADV)': data.adv_inr,
                  'Gap Frequency (%)': `${data.gap_frequency}%`,
                  'Amihud Illiquidity (1e6 scale)': data.amihud_illiquidity,
                  'Annualized Volatility': `${data.annualized_volatility}%`,
                  'Turnover Ratio Proxy (Lakhs)': data.turnover_ratio_proxy,
                }}
              />
            </div>
          ) : (
            <div className="card" style={{ padding: '40px', textAlign: 'center', border: '1px dashed var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
              <p style={{ color: 'var(--text-secondary)' }}>Click "Audit Liquidity" to trigger suitability filters.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

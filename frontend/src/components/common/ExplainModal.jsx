import React, { useState, useEffect } from 'react';
import { fetchExplainScore } from '../../api/stocks';
import LoadingSpinner from './LoadingSpinner';
import SankeyFlow from '../charts/SankeyFlow';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  Legend,
  ReferenceLine
} from 'recharts';

export default function ExplainModal({ scoreType, symbol, defaultTab = 'why', onClose }) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchExplainScore(scoreType, symbol)
      .then((res) => {
        setData(res.data);
      })
      .catch((err) => {
        console.error('Failed to fetch explainability payload', err);
        setError('Failed to load explainability data. Please ensure the backend is active.');
      })
      .finally(() => setLoading(false));
  }, [scoreType, symbol]);

  if (loading) {
    return (
      <div className="explain-modal-backdrop" style={backdropStyle} onClick={onClose}>
        <div className="explain-modal-wrap" style={modalWrapStyle} onClick={(e) => e.stopPropagation()}>
          <div style={{ textAlign: 'center', padding: '60px' }}>
            <LoadingSpinner />
            <p style={{ marginTop: '16px', color: 'var(--text-muted)' }}>Loading Telemetry Explanations...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="explain-modal-backdrop" style={backdropStyle} onClick={onClose}>
        <div className="explain-modal-wrap" style={modalWrapStyle} onClick={(e) => e.stopPropagation()}>
          <div style={{ padding: '40px', textAlign: 'center' }}>
            <h3 style={{ color: '#ef4444' }}>⚠️ System Alert</h3>
            <p style={{ color: 'var(--text-muted)', marginTop: '8px' }}>{error || 'Data empty'}</p>
            <button className="btn btn-secondary" style={{ marginTop: '20px' }} onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    );
  }

  const scoreName = scoreType.charAt(0).toUpperCase() + scoreType.slice(1) + " Score";

  // Calculate past benchmark comparisons if historical context exists
  const history = data.historical_context || [];
  const currentVal = data.current_value;
  const prevVal = history.length > 1 ? history[1].value : null;
  const prev7dVal = history.length > 7 ? history[7].value : null;
  const prev30dVal = history.length > 29 ? history[29].value : null;

  // Custom tooltips for Recharts
  const CustomLineTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ background: '#0a1628', border: '1px solid rgba(255,255,255,0.1)', padding: '8px', borderRadius: '4px' }}>
          <p style={{ margin: 0, fontSize: '11px', color: '#94a3b8' }}>Date: {label}</p>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', fontWeight: 'bold', color: '#818cf8' }}>
            {scoreName}: {payload[0].value.toFixed(2)}
          </p>
        </div>
      );
    }
    return null;
  };

  const CustomBarTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{ background: '#0a1628', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '4px', maxWidth: '250px' }}>
          <p style={{ margin: 0, fontSize: '12px', fontWeight: 'bold', color: '#e2e8f0' }}>{data.name}</p>
          <p style={{ margin: '4px 0 0 0', fontSize: '11px', color: '#94a3b8' }}>
            Weight: {data.weight != null ? `${(data.weight * 100).toFixed(0)}%` : 'N/A'}
          </p>
          <p style={{ margin: '2px 0 0 0', fontSize: '11px', color: '#94a3b8' }}>
            Raw Score: {data.value != null ? data.value.toFixed(2) : 'N/A'}
          </p>
          <p style={{ margin: '4px 0 0 0', fontSize: '12px', fontWeight: 'bold', color: data.contribution > 0 ? '#10b981' : data.contribution < 0 ? '#ef4444' : '#fff' }}>
            Blended Impact: {data.contribution != null ? (data.contribution > 0 ? '+' : '') + data.contribution.toFixed(2) : 'Unavailable'}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="explain-modal-backdrop" style={backdropStyle} onClick={onClose}>
      <div className="explain-modal-wrap" style={modalWrapStyle} onClick={(e) => e.stopPropagation()}>
        
        {/* Header Block */}
        <div className="explain-modal-header" style={headerStyle}>
          <div>
            <span style={{ color: '#818cf8', fontSize: '11px', letterSpacing: '1.5px', fontWeight: 'bold', textTransform: 'uppercase' }}>
              PMS Engine Explainability Hub ({symbol || 'Global'})
            </span>
            <h2 style={{ color: '#fff', margin: '4px 0 0 0', fontSize: '22px', fontWeight: 'bold' }}>{scoreName} Methodology</h2>
          </div>
          <button style={closeBtnStyle} onClick={onClose}>&times;</button>
        </div>

        {/* Tab Controls */}
        <div className="explain-modal-tabs" style={tabsContainerStyle}>
          <button 
            style={activeTab === 'why' ? activeTabStyle : tabStyle} 
            onClick={() => setActiveTab('why')}
          >
            ⓘ Why This Score?
          </button>
          <button 
            style={activeTab === 'breakdown' ? activeTabStyle : tabStyle} 
            onClick={() => setActiveTab('breakdown')}
          >
            📊 Contribution Breakdown
          </button>
          <button 
            style={activeTab === 'trust' ? activeTabStyle : tabStyle} 
            onClick={() => setActiveTab('trust')}
          >
            🛡️ Can I Trust This Score?
          </button>
          <button 
            style={activeTab === 'methodology' ? activeTabStyle : tabStyle} 
            onClick={() => setActiveTab('methodology')}
          >
            📚 Methodology & References
          </button>
        </div>

        {/* Content Panel (Scrollable) */}
        <div className="explain-modal-body" style={bodyStyle}>
          
          {/* Tab 1: Why This Score? */}
          {activeTab === 'why' && (
            <div className="tab-pane fade-in">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px', marginBottom: '24px' }}>
                {/* Score Summary Card */}
                <div className="card" style={statCardStyle}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>CURRENT SCORE VALUE</span>
                  <div style={{ fontSize: '40px', fontWeight: 900, color: currentVal >= 0 ? '#10b981' : '#ef4444', margin: '8px 0' }}>
                    {currentVal > 0 && scoreType !== 'reliability' ? '+' : ''}{currentVal.toFixed(2)}
                  </div>
                  
                  {/* Historical contexts list */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '16px', fontSize: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '4px' }}>
                      <span className="text-muted">Previous Day</span>
                      <span style={{ color: '#fff', fontWeight: 'bold' }}>{prevVal !== null ? prevVal.toFixed(2) : '—'}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '4px' }}>
                      <span className="text-muted">7 Days Ago</span>
                      <span style={{ color: '#fff', fontWeight: 'bold' }}>{prev7dVal !== null ? prev7dVal.toFixed(2) : '—'}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span className="text-muted">30 Days Ago</span>
                      <span style={{ color: '#fff', fontWeight: 'bold' }}>{prev30dVal !== null ? prev30dVal.toFixed(2) : '—'}</span>
                    </div>
                  </div>
                </div>

                {/* Narrative Text */}
                <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                  <h4 style={{ color: '#fff', margin: '0 0 8px 0' }}>Dynamic Narrative Analysis</h4>
                  <p style={{ color: 'var(--text-muted)', fontSize: '14px', lineHeight: '1.6', margin: 0 }}>
                    {data.dynamic_explanation}
                  </p>
                </div>
              </div>

              {/* Sparkline Trend Chart */}
              {history.length > 0 && (
                <div className="card" style={{ padding: '16px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', marginBottom: '24px' }}>
                  <h4 style={{ color: '#fff', margin: '0 0 12px 0', fontSize: '14px' }}>Score Evolution Trend (Last 30 snapshots)</h4>
                  <div style={{ width: '100%', height: '140px' }}>
                    <ResponsiveContainer>
                      <LineChart data={[...history].reverse()} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="snapshot_date" stroke="#94a3b8" fontSize={9} />
                        <YAxis stroke="#94a3b8" fontSize={9} domain={['auto', 'auto']} />
                        <Tooltip content={<CustomLineTooltip />} />
                        <Line 
                          type="monotone" 
                          dataKey={scoreType === 'composite' ? 'composite_score' : `${scoreType}_score`} 
                          stroke="#818cf8" 
                          strokeWidth={2}
                          dot={false}
                          activeDot={{ r: 5 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Why Not? Box */}
              <div className="card" style={whyNotCardStyle}>
                <h4 style={{ color: '#fb7185', margin: '0 0 8px 0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span>❓</span> Why Not Rated Higher/Lower?
                </h4>
                <p style={{ margin: 0, fontSize: '13px', lineHeight: '1.6', color: '#fecdd3' }}>
                  {data.why_not}
                </p>
              </div>
            </div>
          )}

          {/* Tab 2: Breakdown */}
          {activeTab === 'breakdown' && (
            <div className="tab-pane fade-in">
              {scoreType === 'composite' ? (
                /* Sankey Flow for Composite */
                <SankeyFlow 
                  tech={data.current_values?.w_technical ? 0.0 : (data.current_contributions[0]?.value || 0.0)}
                  ml={data.current_values?.w_technical ? 0.0 : (data.current_contributions[1]?.value || 0.0)}
                  gru={data.current_values?.w_technical ? 0.0 : (data.current_contributions[2]?.value || 0.0)}
                  reliability={data.current_values?.w_technical ? 70.0 : (data.current_contributions[3]?.value || 70.0)}
                  wTech={data.current_values?.w_technical || 0.40}
                  wMl={data.current_values?.w_ml || 0.35}
                  wGru={data.current_values?.w_gru || 0.15}
                  wReliability={data.current_values?.w_reliability || 0.10}
                  composite={currentVal}
                />
              ) : (
                /* Standard Bar Chart for others */
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
                  
                  {/* Contributions Table */}
                  <div className="card" style={{ padding: '16px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                    <h4 style={{ color: '#fff', margin: '0 0 12px 0', fontSize: '14px' }}>Factor Inputs</h4>
                    
                    {data.current_contributions.length === 0 ? (
                      <div style={{ padding: '24px', textAlign: 'center', color: '#fb7185', background: 'rgba(239, 44, 44, 0.05)', borderRadius: '4px' }}>
                        ⚠️ Contribution currently unavailable. Calculated during live analysis only.
                      </div>
                    ) : (
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                        <thead>
                          <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-muted)' }}>
                            <th style={{ textAlign: 'left', padding: '8px' }}>Variable</th>
                            <th style={{ textAlign: 'right', padding: '8px' }}>Value</th>
                            <th style={{ textAlign: 'right', padding: '8px' }}>Blended Score</th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.current_contributions.map((con, idx) => (
                            <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                              <td style={{ padding: '8px', color: '#fff', fontWeight: 500 }}>{con.name}</td>
                              <td style={{ padding: '8px', textAlign: 'right', color: 'var(--text-muted)' }}>
                                {con.value !== null ? con.value.toFixed(2) : '—'}
                              </td>
                              <td style={{ 
                                padding: '8px', 
                                textAlign: 'right', 
                                fontWeight: 'bold',
                                color: con.contribution > 0 ? '#10b981' : con.contribution < 0 ? '#ef4444' : '#fff' 
                              }}>
                                {con.contribution !== null ? (con.contribution > 0 ? '+' : '') + con.contribution.toFixed(2) : '—'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>

                  {/* Contributions Visual Chart */}
                  {data.current_contributions.length > 0 && (
                    <div className="card" style={{ padding: '16px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                      <h4 style={{ color: '#fff', margin: '0 0 12px 0', fontSize: '14px' }}>Visual Attribution Waterfall</h4>
                      <div style={{ width: '100%', height: '200px' }}>
                        <ResponsiveContainer>
                          <BarChart data={data.current_contributions} layout="vertical" margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis type="number" stroke="#94a3b8" fontSize={9} />
                            <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={9} width={100} />
                            <Tooltip content={<CustomBarTooltip />} />
                            <ReferenceLine x={0} stroke="rgba(255,255,255,0.2)" />
                            <Bar dataKey="contribution">
                              {data.current_contributions.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.contribution >= 0 ? '#10b981' : '#ef4444'} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Recommendation Journey Sequence Block */}
              <div className="card" style={{ padding: '16px', background: 'rgba(5, 10, 20, 0.4)', border: '1px solid rgba(255, 255, 255, 0.05)', borderRadius: '8px', marginTop: '16px' }}>
                <h4 style={{ color: '#fff', margin: '0 0 12px 0', fontSize: '14px' }}>🛤️ Full Recommendation Journey</h4>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', overflowX: 'auto', paddingBottom: '8px' }}>
                  <div style={journeyStepStyle}>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>STEP 1</span>
                    <strong style={{ color: '#fff', fontSize: '12px' }}>Raw Market Data</strong>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Price & Volume Feeds</span>
                  </div>
                  <span style={{ color: 'var(--text-muted)' }}>➔</span>
                  <div style={journeyStepStyle}>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>STEP 2</span>
                    <strong style={{ color: '#fff', fontSize: '12px' }}>Indicators Derived</strong>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>RSI, MACD, EMAs</span>
                  </div>
                  <span style={{ color: 'var(--text-muted)' }}>➔</span>
                  <div style={journeyStepStyle}>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>STEP 3</span>
                    <strong style={{ color: '#fff', fontSize: '12px' }}>Modular Engines</strong>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Technical, ML, GRU</span>
                  </div>
                  <span style={{ color: 'var(--text-muted)' }}>➔</span>
                  <div style={journeyStepStyle}>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>STEP 4</span>
                    <strong style={{ color: '#fff', fontSize: '12px' }}>Composite blending</strong>
                    <span style={{ fontSize: '11px', color: '#10b981' }}>Score: {currentVal.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 3: Can I Trust This Score? */}
          {activeTab === 'trust' && (
            <div className="tab-pane fade-in">
              <h4 style={{ color: '#fff', margin: '0 0 16px 0' }}>🛡️ Quant Subsystem Trust Center</h4>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                {data.validation.map((v, i) => (
                  <div key={i} className="card" style={{ padding: '16px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{v.metric.toUpperCase()}</span>
                    <div style={{ fontSize: '20px', fontWeight: 900, color: '#818cf8', margin: '6px 0' }}>
                      {v.value}
                    </div>
                    <p style={{ margin: 0, fontSize: '11px', color: 'var(--text-muted)' }}>{v.description}</p>
                  </div>
                ))}
              </div>

              {/* Data Freshness Indicator Box */}
              <div className="card" style={{ padding: '16px', background: 'rgba(16, 185, 129, 0.02)', border: '1px solid rgba(16, 185, 129, 0.1)', borderRadius: '8px' }}>
                <h4 style={{ color: '#10b981', margin: '0 0 8px 0', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span>🟢</span> Telemetry Stream Freshness
                </h4>
                <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.6' }}>
                  All pricing, volumetric overlays, and technical components are synchronized directly with live NSE feeds. Ranks are calculated across the active 50-stock index universe to verify distribution stability.
                </p>
              </div>
            </div>
          )}

          {/* Tab 4: Methodology & References */}
          {activeTab === 'methodology' && (
            <div className="tab-pane fade-in">
              {/* Formula and Description */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
                
                {/* Method details */}
                <div>
                  <h4 style={{ color: '#fff', margin: '0 0 8px 0' }}>Mathematical Pipeline</h4>
                  <p style={{ color: 'var(--text-muted)', fontSize: '13px', lineHeight: '1.6' }}>
                    {data.purpose}
                  </p>
                  <div style={{ padding: '12px', background: 'rgba(255,255,255,0.02)', borderLeft: '3px solid #818cf8', borderRadius: '4px', marginTop: '12px' }}>
                    <code style={{ color: '#a5b4fc', fontSize: '12px' }}>{data.formula}</code>
                  </div>
                </div>

                {/* Score Limits */}
                <div className="card" style={{ padding: '16px', background: 'rgba(239, 44, 44, 0.01)', border: '1px solid rgba(239, 44, 44, 0.05)', borderRadius: '8px' }}>
                  <h4 style={{ color: '#f87171', margin: '0 0 8px 0' }}>Risk Caveats & Limitations</h4>
                  <ul style={{ margin: 0, paddingLeft: '20px', color: 'var(--text-muted)', fontSize: '12px', lineHeight: '1.6' }}>
                    {data.limitations.map((limit, idx) => (
                      <li key={idx} style={{ marginBottom: '6px' }}>{limit}</li>
                    ))}
                  </ul>
                </div>

              </div>

              {/* Research References */}
              <div className="card" style={{ padding: '16px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                <h4 style={{ color: '#fff', margin: '0 0 12px 0', fontSize: '14px' }}>Academic & Quantitative References</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {data.references.map((ref, idx) => (
                    <div key={idx} style={{ borderBottom: idx < data.references.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none', paddingBottom: '12px' }}>
                      <strong style={{ color: '#818cf8', fontSize: '13px' }}>{ref.paper} ({ref.year})</strong>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                        By <strong>{ref.author}</strong>
                      </div>
                      <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: 'var(--text-muted)' }}>
                        {ref.description}
                      </p>
                      {ref.link && (
                        <a href={ref.link} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-block', marginTop: '6px', fontSize: '11px', color: '#6366f1', textDecoration: 'none' }}>
                          Original Publication Link ↗
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}

// Inline Styles
const backdropStyle = {
  position: 'fixed',
  top: 0,
  left: 0,
  width: '100%',
  height: '100%',
  background: 'rgba(0, 0, 0, 0.7)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1100,
  backdropFilter: 'blur(8px)',
  animation: 'fadeIn 0.25s ease-out'
};

const modalWrapStyle = {
  width: '90%',
  maxWidth: '850px',
  maxHeight: '90%',
  background: 'rgba(10, 22, 40, 0.85)',
  border: '1px solid rgba(255, 255, 255, 0.08)',
  borderRadius: '12px',
  display: 'flex',
  flexDirection: 'column',
  boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
  overflow: 'hidden',
  backdropFilter: 'blur(20px)',
  animation: 'scaleUp 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)'
};

const headerStyle = {
  padding: '20px 24px',
  borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center'
};

const closeBtnStyle = {
  background: 'none',
  border: 'none',
  color: 'var(--text-muted)',
  fontSize: '28px',
  cursor: 'pointer',
  padding: '0 4px',
  lineHeight: 1
};

const tabsContainerStyle = {
  display: 'flex',
  borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
  padding: '0 12px',
  background: 'rgba(0, 0, 0, 0.2)'
};

const tabStyle = {
  background: 'none',
  border: 'none',
  borderBottom: '2px solid transparent',
  color: 'var(--text-muted)',
  padding: '12px 16px',
  fontSize: '13px',
  fontWeight: 'bold',
  cursor: 'pointer',
  transition: 'all 0.2s ease'
};

const activeTabStyle = {
  background: 'none',
  border: 'none',
  borderBottom: '2px solid #818cf8',
  color: '#818cf8',
  padding: '12px 16px',
  fontSize: '13px',
  fontWeight: 'bold',
  cursor: 'pointer'
};

const bodyStyle = {
  padding: '24px',
  overflowY: 'auto',
  flex: 1
};

const statCardStyle = {
  padding: '16px',
  background: 'rgba(255, 255, 255, 0.01)',
  border: '1px solid rgba(255, 255, 255, 0.05)',
  borderRadius: '8px',
  textAlign: 'center'
};

const whyNotCardStyle = {
  padding: '16px',
  background: 'rgba(244, 63, 94, 0.03)',
  border: '1px solid rgba(244, 63, 94, 0.1)',
  borderRadius: '8px'
};

const journeyStepStyle = {
  background: 'rgba(255, 255, 255, 0.02)',
  border: '1px solid rgba(255, 255, 255, 0.05)',
  borderRadius: '6px',
  padding: '10px 14px',
  minWidth: '110px',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  textAlign: 'center'
};

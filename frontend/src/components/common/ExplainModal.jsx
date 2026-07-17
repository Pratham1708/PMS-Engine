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
  const [expandedCats, setExpandedCats] = useState({});
  const [expandedFeats, setExpandedFeats] = useState({});

  const toggleCat = (catName) => {
    setExpandedCats(prev => ({ ...prev, [catName]: !prev[catName] }));
  };

  const toggleFeat = (featKey) => {
    setExpandedFeats(prev => ({ ...prev, [featKey]: !prev[featKey] }));
  };

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchExplainScore(scoreType, symbol)
      .then((res) => {
        console.log('[FRONTEND API DEBUG] Received explain payload:', res.data);
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

  const flatAttributions = (categories) => {
    if (!categories) return [];
    let list = [];
    categories.forEach(cat => {
      if (cat.features) {
        cat.features.forEach(f => {
          list.push({
            name: f.name,
            contribution: f.contribution,
            weight: f.weight
          });
        });
      }
    });
    return list.sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
  };

  const CustomAttributionTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      return (
        <div style={{ background: '#0a1628', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '4px', maxWidth: '280px' }}>
          <p style={{ margin: 0, fontSize: '12px', fontWeight: 'bold', color: '#e2e8f0' }}>{d.name}</p>
          <p style={{ margin: '4px 0 0 0', fontSize: '11px', color: '#94a3b8' }}>
            Weight: {(d.weight * 100).toFixed(1)}%
          </p>
          <p style={{ margin: '4px 0 0 0', fontSize: '12px', fontWeight: 'bold', color: d.contribution >= 0 ? '#10b981' : '#ef4444' }}>
            Attribution: {d.contribution >= 0 ? '+' : ''}{d.contribution.toFixed(2)} points
          </p>
        </div>
      );
    }
    return null;
  };

  const CustomCategoryTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      return (
        <div style={{ background: '#0a1628', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '4px' }}>
          <p style={{ margin: 0, fontSize: '12px', fontWeight: 'bold', color: '#e2e8f0' }}>{d.category}</p>
          <p style={{ margin: '4px 0 0 0', fontSize: '12px', fontWeight: 'bold', color: d.subtotal >= 0 ? '#10b981' : '#ef4444' }}>
            Subtotal: {d.subtotal >= 0 ? '+' : ''}{d.subtotal.toFixed(2)} points
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
            <div className="tab-pane fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              
              {scoreType === 'composite' ? (
                /* Sankey Flow for Composite */
                <SankeyFlow 
                  tech={data.current_values?.technical_score}
                  ml={data.current_values?.ml_score}
                  gru={data.current_values?.gru_score}
                  reliability={data.current_values?.reliability_score}
                  wTech={data.current_values?.w_technical}
                  wMl={data.current_values?.w_ml}
                  wGru={data.current_values?.w_gru}
                  wReliability={data.current_values?.w_reliability}
                  composite={currentVal}
                />
              ) : (
                /* Attribution Visualizations Side-by-Side */
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                  
                  {/* Chart 1: Feature Attribution Bars */}
                  <div className="card" style={chartCardStyle}>
                    <h4 style={chartTitleStyle}>Feature Impact Attribution</h4>
                    <div style={{ height: '240px' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={flatAttributions(data.feature_attributions)}
                          layout="vertical"
                          margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                          <XAxis type="number" stroke="#94a3b8" fontSize={10} />
                          <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={10} width={120} tickLine={false} />
                          <Tooltip content={<CustomAttributionTooltip />} />
                          <ReferenceLine x={0} stroke="rgba(255,255,255,0.2)" />
                          <Bar dataKey="contribution" radius={[0, 4, 4, 0]}>
                            {flatAttributions(data.feature_attributions).map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.contribution >= 0 ? '#10b981' : '#ef4444'} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Chart 2: Category subtotals */}
                  <div className="card" style={chartCardStyle}>
                    <h4 style={chartTitleStyle}>Category Attribution Subtotals</h4>
                    <div style={{ height: '240px' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={data.feature_attributions || []}
                          margin={{ top: 10, right: 10, left: -20, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                          <XAxis dataKey="category" stroke="#94a3b8" fontSize={9} tickLine={false} />
                          <YAxis stroke="#94a3b8" fontSize={10} />
                          <Tooltip content={<CustomCategoryTooltip />} />
                          <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" />
                          <Bar dataKey="subtotal" radius={[4, 4, 0, 0]}>
                            {(data.feature_attributions || []).map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.subtotal >= 0 ? '#818cf8' : '#fb7185'} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                </div>
              )}

              {/* Expandable Nesting Hierarchy Table */}
              <div className="card" style={{ padding: '20px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                <h4 style={{ color: '#fff', margin: '0 0 16px 0', fontSize: '15px', fontWeight: 'bold' }}>Factor Attribution Hierarchy</h4>
                
                {(!data.feature_attributions || data.feature_attributions.length === 0) ? (
                  <div style={{ padding: '24px', textAlign: 'center', color: '#fb7185', background: 'rgba(239, 44, 44, 0.05)', borderRadius: '4px' }}>
                    ⚠️ Nested attribution details are currently unavailable for this score snapshot.
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {data.feature_attributions.map((cat) => {
                      const isCatExpanded = !!expandedCats[cat.category];
                      return (
                        <div key={cat.category} style={{ border: '1px solid rgba(255,255,255,0.05)', borderRadius: '6px', overflow: 'hidden' }}>
                          
                          {/* Category Header Row */}
                          <div 
                            style={{ 
                              display: 'flex', 
                              justifyContent: 'space-between', 
                              alignItems: 'center', 
                              padding: '12px 16px', 
                              background: isCatExpanded ? 'rgba(129, 140, 248, 0.08)' : 'rgba(255,255,255,0.02)', 
                              cursor: 'pointer',
                              transition: 'background 0.2s'
                            }}
                            onClick={() => toggleCat(cat.category)}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                              <span style={{ color: '#818cf8', fontSize: '14px', fontWeight: 'bold' }}>
                                {isCatExpanded ? '▼' : '▶'}
                              </span>
                              <span style={{ color: '#fff', fontWeight: 600, fontSize: '13px' }}>{cat.category}</span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Subtotal Impact:</span>
                              <strong style={{ 
                                fontSize: '13px', 
                                color: cat.subtotal >= 0 ? '#10b981' : '#ef4444' 
                              }}>
                                {cat.subtotal >= 0 ? '+' : ''}{cat.subtotal.toFixed(2)}
                              </strong>
                            </div>
                          </div>

                          {/* Nested Features List */}
                          {isCatExpanded && (
                            <div style={{ background: 'rgba(0,0,0,0.1)', padding: '8px 12px' }}>
                              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                                <thead>
                                  <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', color: 'var(--text-muted)' }}>
                                    <th style={{ textAlign: 'left', padding: '6px 8px' }}>Factor Name</th>
                                    <th style={{ textAlign: 'right', padding: '6px 8px' }}>Current Value</th>
                                    <th style={{ textAlign: 'right', padding: '6px 8px' }}>Normalized</th>
                                    <th style={{ textAlign: 'right', padding: '6px 8px' }}>Weight</th>
                                    <th style={{ textAlign: 'right', padding: '6px 8px' }}>Contribution</th>
                                    <th style={{ textAlign: 'center', padding: '6px 8px' }}>Confidence</th>
                                    <th style={{ width: '100px' }}></th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {cat.features.map((feat) => {
                                    const isFeatExpanded = !!expandedFeats[feat.feature_key];
                                    return (
                                      <React.Fragment key={feat.feature_key}>
                                        <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                                          <td style={{ padding: '8px', color: '#fff', fontWeight: 500 }}>{feat.name}</td>
                                          <td style={{ padding: '8px', textAlign: 'right', color: 'var(--text-muted)' }}>{feat.current_value}</td>
                                          <td style={{ padding: '8px', textAlign: 'right', color: 'var(--text-muted)' }}>{feat.normalized_value >= 0 ? '+' : ''}{feat.normalized_value.toFixed(0)}</td>
                                          <td style={{ padding: '8px', textAlign: 'right', color: 'var(--text-muted)' }}>{(feat.weight * 100).toFixed(1)}%</td>
                                          <td style={{ 
                                            padding: '8px', 
                                            textAlign: 'right', 
                                            fontWeight: 'bold',
                                            color: feat.contribution > 0 ? '#10b981' : feat.contribution < 0 ? '#ef4444' : '#fff' 
                                          }}>
                                            {feat.contribution >= 0 ? '+' : ''}{feat.contribution.toFixed(2)}
                                          </td>
                                          <td style={{ padding: '8px', textAlign: 'center' }}>
                                            <span style={getConfBadgeStyle(feat.confidence)}>
                                              {feat.confidence}
                                            </span>
                                          </td>
                                          <td style={{ padding: '8px', textAlign: 'center' }}>
                                            <button 
                                              style={detailsBtnStyle}
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                toggleFeat(feat.feature_key);
                                              }}
                                            >
                                              {isFeatExpanded ? 'Hide Details ▲' : 'Details ▼'}
                                            </button>
                                          </td>
                                        </tr>

                                        {/* Dropdown Card for Feature Details */}
                                        {isFeatExpanded && (
                                          <tr>
                                            <td colSpan={7} style={{ padding: '12px 16px', background: 'rgba(0, 0, 0, 0.25)', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                                              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                                  <span style={dataSourceTagStyle}>{feat.metadata?.data_source || 'Telemetry'}</span>
                                                  <span style={{ color: '#fff', fontSize: '12px', fontWeight: 600 }}>{feat.explanation}</span>
                                                </div>
                                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '6px' }}>
                                                  <div style={detailBoxStyle}>
                                                    <strong style={detailHeaderStyle}>Mathematical Equations</strong>
                                                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                                                      Plain: {feat.metadata?.plain_formula || 'N/A'}
                                                    </div>
                                                    <div style={{ fontSize: '11px', color: '#a5b4fc', marginTop: '4px', fontFamily: 'monospace' }}>
                                                      LaTeX: {feat.metadata?.latex_formula || 'N/A'}
                                                    </div>
                                                  </div>
                                                  <div style={detailBoxStyle}>
                                                    <strong style={detailHeaderStyle}>Normalization Bounds</strong>
                                                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                                                      Method: {feat.metadata?.normalization?.method || 'N/A'} (Range: {feat.metadata?.normalization?.range || 'N/A'})
                                                    </div>
                                                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                                                      Logic: {feat.metadata?.normalization?.logic || 'N/A'}
                                                    </div>
                                                  </div>
                                                </div>
                                                <div style={{ ...detailBoxStyle, marginTop: '4px' }}>
                                                  <strong style={detailHeaderStyle}>Research Reference Citation</strong>
                                                  <div style={{ fontSize: '11px', color: '#818cf8', fontWeight: 600 }}>
                                                    {feat.metadata?.reference?.paper || 'PMS Standard Quantitative Guidelines'} ({feat.metadata?.reference?.year || 2026})
                                                  </div>
                                                  <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
                                                    Author: {feat.metadata?.reference?.author || 'PMS Team'}
                                                  </div>
                                                  {feat.metadata?.reference?.link && (
                                                    <a 
                                                      href={feat.metadata.reference.link} 
                                                      target="_blank" 
                                                      rel="noopener noreferrer" 
                                                      style={{ fontSize: '10px', color: '#6366f1', textDecoration: 'none', display: 'inline-block', marginTop: '4px' }}
                                                    >
                                                      Link to Publication ↗
                                                    </a>
                                                  )}
                                                </div>
                                              </div>
                                            </td>
                                          </tr>
                                        )}
                                      </React.Fragment>
                                    );
                                  })}
                                </tbody>
                              </table>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Recommendation Journey Sequence Block */}
              <div className="card" style={{ padding: '16px', background: 'rgba(5, 10, 20, 0.4)', border: '1px solid rgba(255, 255, 255, 0.05)', borderRadius: '8px' }}>
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

const chartCardStyle = {
  padding: '16px',
  background: 'rgba(255,255,255,0.01)',
  border: '1px solid rgba(255,255,255,0.05)',
  borderRadius: '8px'
};

const chartTitleStyle = {
  color: '#fff',
  margin: '0 0 12px 0',
  fontSize: '13px',
  fontWeight: 'bold',
  letterSpacing: '0.5px'
};

const detailsBtnStyle = {
  background: 'rgba(129, 140, 248, 0.1)',
  border: '1px solid rgba(129, 140, 248, 0.2)',
  color: '#a5b4fc',
  padding: '4px 8px',
  borderRadius: '4px',
  fontSize: '10px',
  cursor: 'pointer',
  whiteSpace: 'nowrap'
};

const getConfBadgeStyle = (conf) => {
  const isHigh = conf === 'High';
  const isMed = conf === 'Medium';
  return {
    background: isHigh ? 'rgba(16, 185, 129, 0.1)' : isMed ? 'rgba(245, 158, 11, 0.1)' : 'rgba(239, 44, 44, 0.1)',
    border: isHigh ? '1px solid rgba(16, 185, 129, 0.2)' : isMed ? '1px solid rgba(245, 158, 11, 0.2)' : '1px solid rgba(239, 44, 44, 0.2)',
    color: isHigh ? '#10b981' : isMed ? '#f59e0b' : '#ef4444',
    padding: '2px 6px',
    borderRadius: '4px',
    fontSize: '10px',
    fontWeight: 'bold'
  };
};

const dataSourceTagStyle = {
  background: 'rgba(255,255,255,0.05)',
  border: '1px solid rgba(255,255,255,0.1)',
  color: '#94a3b8',
  padding: '1px 6px',
  borderRadius: '4px',
  fontSize: '9px',
  textTransform: 'uppercase',
  fontWeight: 'bold'
};

const detailBoxStyle = {
  background: 'rgba(0,0,0,0.15)',
  border: '1px solid rgba(255,255,255,0.03)',
  borderRadius: '4px',
  padding: '8px 12px'
};

const detailHeaderStyle = {
  display: 'block',
  color: '#fff',
  fontSize: '10px',
  fontWeight: 'bold',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
  marginBottom: '4px'
};

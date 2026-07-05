/* eslint-disable react-hooks/refs, react-hooks/set-state-in-effect, react-hooks/exhaustive-deps, no-unused-vars */
import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  fetchStock, 
  fetchCompanyProfile, 
  fetchMyStocks, 
  addToMyStocks, 
  deleteFromMyStocks, 
  runAnalysis, 
  fetchAnalysisHistory 
} from '../api/stocks';
import {
  generateStockReport,
  getReportPreviewUrl,
  getReportDownloadUrl,
} from '../api/reports';
import RatingBadge from '../components/common/RatingBadge';
import ScoreBar from '../components/common/ScoreBar';
import ConfidenceBar from '../components/common/ConfidenceBar';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';

function confidenceColor(val) {
  if (val >= 80) return '#10b981';
  if (val >= 60) return '#f59e0b';
  return '#ef4444';
}

function statusColor(status) {
  switch (status) {
    case 'Fresh': return '#10b981'; // Green
    case 'Recent': return '#3b82f6'; // Blue
    case 'Aging': return '#f59e0b'; // Orange
    case 'Stale': return '#ef4444'; // Red
    default: return '#9ca3af'; // Grey
  }
}

function impactColor(impact) {
  if (impact === 'positive') return '#10b981';
  if (impact === 'negative') return '#ef4444';
  return '#9ca3af';
}

function impactLabel(impact) {
  if (impact === 'positive') return '▲ Positive';
  if (impact === 'negative') return '▼ Bearish';
  return '◆ Neutral';
}

// Inline ScoreCounter component for counting up score animations
function ScoreCounter({ value, duration = 800, decimals = 2, suffix = '' }) {
  const [displayVal, setDisplayVal] = useState(0);
  useEffect(() => {
    let start = 0;
    const end = parseFloat(value);
    if (isNaN(end)) {
      setDisplayVal(0);
      return;
    }
    const startTime = performance.now();
    let animationFrameId;
    
    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out quad
      const easeProgress = progress * (2 - progress);
      const current = start + easeProgress * (end - start);
      setDisplayVal(current);
      if (progress < 1) {
        animationFrameId = requestAnimationFrame(animate);
      } else {
        setDisplayVal(end);
      }
    };
    animationFrameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrameId);
  }, [value, duration]);
  
  return <span>{displayVal.toFixed(decimals)}{suffix}</span>;
}

export default function StockDetail() {
  const { symbol } = useParams();
  const navigate = useNavigate();

  // Data States
  const [stock, setStock] = useState(null);
  const [company, setCompany] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [historyLogs, setHistoryLogs] = useState([]);
  const [isTracked, setIsTracked] = useState(false);
  const [chartPeriod, setChartPeriod] = useState('1Y');

  // Status States
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState(false);

  // Analysis Flow States
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisCompleted, setAnalysisCompleted] = useState(false);
  const [analyzedStockData, setAnalyzedStockData] = useState(null);
  const [lastAnalysisId, setLastAnalysisId] = useState('');
  const [lastAnalysisTimestamp, setLastAnalysisTimestamp] = useState('');

  // Progressive Report States
  const [reportSections, setReportSections] = useState(Array(9).fill(false));
  const [isRevealing, setIsRevealing] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [generatedReportId, setGeneratedReportId] = useState(null);

  const handleGenerateReport = async () => {
    setIsGeneratingReport(true);
    try {
      const res = await generateStockReport(symbol);
      setGeneratedReportId(res.data.report_id);
    } catch (err) {
      console.error('Failed to generate report', err);
      alert('Failed to generate stock report.');
    } finally {
      setIsGeneratingReport(false);
    }
  };

  // Refs for auto-scrolling
  const sectionRefs = [
    useRef(null), // 1. Market Data
    useRef(null), // 2. Technical Engine
    useRef(null), // 3. ML Engine
    useRef(null), // 4. GRU Engine
    useRef(null), // 5. Expected Return Engine
    useRef(null), // 6. Reliability Engine
    useRef(null), // 7. Composite Engine
    useRef(null), // 8. Final Recommendation
    useRef(null), // 9. Explainable AI
  ];

  const loadInitialData = () => {
    setInitialLoading(true);
    setError(false);
    
    Promise.all([
      fetchStock(symbol),
      fetchCompanyProfile(symbol),
      fetchMyStocks(),
      fetchAnalysisHistory(symbol)
    ])
      .then(([stockRes, companyRes, myStocksRes, historyLogsRes]) => {
        setStock(stockRes.data);
        setCompany(companyRes.data);
        setHistoryLogs(historyLogsRes.data || []);
        
        const mySymbols = (myStocksRes.data || []).map(s => s.symbol.toUpperCase());
        setIsTracked(mySymbols.includes(symbol.toUpperCase()));
      })
      .catch((err) => {
        console.error('Failed to load stock detail assets', err);
        setError(true);
      })
      .finally(() => setInitialLoading(false));
  };

  const clientGetHistory = async (sym, period) => {
    try {
      const { default: client } = await import('../api/client');
      const res = await client.get(`/market/history/${encodeURIComponent(sym)}?period=${period}`);
      return res.data;
    } catch {
      return [];
    }
  };

  useEffect(() => {
    clientGetHistory(symbol, chartPeriod)
      .then((data) => setHistoryData(data || []))
      .catch(() => setHistoryData([]));
  }, [symbol, chartPeriod]);

  useEffect(() => {
    loadInitialData();
    // Reset analysis states when symbol changes
    setAnalysisCompleted(false);
    setAnalyzedStockData(null);
    setReportSections(Array(9).fill(false));
    setIsRevealing(false);
    setChartPeriod('1Y');
  }, [symbol]);

  const handleTrackToggle = async () => {
    try {
      if (isTracked) {
        await deleteFromMyStocks(symbol);
        setIsTracked(false);
      } else {
        await addToMyStocks(symbol);
        setIsTracked(true);
      }
    } catch (err) {
      console.error('Failed to toggle tracking status', err);
    }
  };

  const handleRunAnalysis = async () => {
    setIsAnalyzing(true);
    setIsRevealing(false);
    setReportSections(Array(9).fill(false));
    setAnalyzedStockData(null);
    setAnalysisCompleted(false);
    setGeneratedReportId(null);

    try {
      const [analyzeRes, historyRes] = await Promise.all([
        runAnalysis(symbol),
        fetchAnalysisHistory(symbol)
      ]);
      const wrapperData = analyzeRes.data;
      
      setAnalyzedStockData(wrapperData.result);
      setLastAnalysisId(wrapperData.analysis_id);
      setLastAnalysisTimestamp(wrapperData.analysis_timestamp);
      setHistoryLogs(historyRes.data || []);
      
      setIsAnalyzing(false);
      setIsRevealing(true);
      setAnalysisCompleted(true);

      // Sequentially activate sections every 800ms
      let currentSection = 0;
      setReportSections(prev => {
        const next = [...prev];
        next[0] = true;
        return next;
      });

      const interval = setInterval(() => {
        currentSection += 1;
        if (currentSection < 9) {
          setReportSections(prev => {
            const next = [...prev];
            next[currentSection] = true;
            return next;
          });
        } else {
          clearInterval(interval);
          setIsRevealing(false);
        }
      }, 800);

    } catch (err) {
      console.error('Analysis execution failed', err);
      setIsAnalyzing(false);
      setIsRevealing(false);
      const errorMsg = err.response?.data?.detail || 'Analysis execution failed. Please verify API is running.';
      alert(errorMsg);
    }
  };

  // Auto-scroll effect when sections activate
  useEffect(() => {
    if (!isRevealing) return;
    const activeIndex = reportSections.lastIndexOf(true);
    if (activeIndex >= 0 && sectionRefs[activeIndex]?.current) {
      setTimeout(() => {
        sectionRefs[activeIndex].current.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }, 100);
    }
  }, [reportSections, isRevealing]);

  if (initialLoading) return <LoadingSpinner />;
  if (error || !stock || !company) {
    return (
      <div className="fade-in">
        <button className="btn btn-back" onClick={() => navigate('/')}>
          ← Back to Workspace
        </button>
        <div className="card" style={{ textAlign: 'center', padding: '48px', marginTop: '16px' }}>
          <h2>Stock coverage not found</h2>
          <p style={{ color: 'var(--text-muted)', marginTop: '8px' }}>
            Symbol "{symbol}" is not registered in the database.
          </p>
        </div>
      </div>
    );
  }

  // Pre-analysis price data
  const isNotAnalyzed = stock.FinalRating === 'Not Analyzed';
  const reportData = analyzedStockData || (analysisCompleted ? stock : null);
  const currentFreshness = analysisCompleted 
    ? "Fresh" 
    : (historyLogs.length > 0 ? historyLogs[0].status : "Stale");

  // Status Badge Helper
  const getSectionStatusBadge = (idx) => {
    const isActive = reportSections[idx];
    const isNextActive = idx < 8 ? reportSections[idx + 1] : false;
    
    if (!isActive) return null;
    
    if (isNextActive) {
      return <span className="status-badge-locked">Locked</span>;
    } else if (idx === 8 && !isRevealing) {
      return <span className="status-badge-secured">Secured</span>;
    } else {
      return (
        <span className="status-badge-scanning">
          Scanning...
        </span>
      );
    }
  };

  // Neon Dot Helper
  const getNeonDotClass = (idx) => {
    const isActive = reportSections[idx];
    const isNextActive = idx < 8 ? reportSections[idx + 1] : false;
    if (!isActive) return 'neon-dot';
    return isNextActive ? 'neon-dot active' : 'neon-dot scanning';
  };

  return (
    <div className="fade-in stock-detail-container">
      
      {/* Top Navigation Row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <button className="btn btn-back" onClick={() => navigate('/search')}>
          ← Back to Search
        </button>
        
        <div style={{ display: 'flex', gap: '12px' }}>
          <button 
            className={`btn ${isTracked ? 'btn-secondary' : 'btn-primary'}`} 
            onClick={handleTrackToggle}
          >
            {isTracked ? '⭐ Tracked in Workspace' : '＋ Track in Workspace'}
          </button>
        </div>
      </div>

      {/* ── PRE-ANALYSIS STATE: COMPANY PROFILE & LIVE MARKET DATA ── */}
      <div className="two-col" style={{ marginBottom: '32px' }}>
        
        {/* Company Profile Card */}
        <div className="card" style={{ padding: '24px' }}>
          <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1 className="stock-title" style={{ margin: 0, fontSize: '32px', color: '#fff' }}>{company.company_name}</h1>
              <div style={{ display: 'flex', gap: '8px', marginTop: '4px', fontSize: '13px', color: 'var(--text-muted)' }}>
                <span>Ticker: <strong>{company.symbol}</strong></span>
                <span>•</span>
                <span>Sector: <strong>{company.sector}</strong></span>
                <span>•</span>
                <span>Industry: <strong>{company.industry}</strong></span>
              </div>
            </div>
            {company.logo_url && (
              <img 
                src={company.logo_url} 
                alt={`${company.company_name} Logo`} 
                style={{ width: '48px', height: '48px', borderRadius: '6px', objectFit: 'contain', background: '#fff', padding: '2px' }} 
                onError={(e) => e.target.style.display = 'none'}
              />
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px' }}>
            <div>
              <span className="text-muted text-xs">MARKET CAPITALIZATION</span>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fff', marginTop: '2px' }}>{company.market_cap}</div>
            </div>
            <div>
              <span className="text-muted text-xs">HEADQUARTERS</span>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fff', marginTop: '2px' }}>{company.headquarters}</div>
            </div>
            {company.employees && (
              <div>
                <span className="text-muted text-xs">EMPLOYEES</span>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fff', marginTop: '2px' }}>{company.employees}</div>
              </div>
            )}
            <div>
              <span className="text-muted text-xs">WEBSITE</span>
              <div style={{ marginTop: '2px' }}>
                <a href={company.website} target="_blank" rel="noopener noreferrer" style={{ color: '#6366f1', textDecoration: 'none', fontWeight: 600 }}>
                  {company.website.replace('https://', '').replace('www.', '')} ↗
                </a>
              </div>
            </div>
          </div>

          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
            <h4 style={{ color: '#fff', marginBottom: '6px' }}>Business Description</h4>
            <p style={{ fontSize: '14px', lineHeight: '1.6', color: 'var(--text-muted)' }}>{company.description}</p>
          </div>

          <div style={{ marginTop: '16px' }}>
            <h4 style={{ color: '#fff', marginBottom: '6px' }}>Business Segments</h4>
            <p style={{ fontSize: '14px', lineHeight: '1.6', color: 'var(--text-muted)' }}>{company.segments}</p>
          </div>

          <div style={{ marginTop: '16px' }}>
            <h4 style={{ color: '#fff', marginBottom: '6px' }}>Historical Background</h4>
            <p style={{ fontSize: '14px', lineHeight: '1.6', color: 'var(--text-muted)' }}>{company.history}</p>
          </div>
        </div>

        {/* Live Market Data & Historical Chart */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Live Market Card */}
          <div className="card" style={{ padding: '20px' }}>
            <h3 className="card-title" style={{ marginBottom: '16px' }}>📡 Live Market Data</h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
                <div className="text-muted text-xs">CURRENT PRICE</div>
                <div style={{ fontSize: '20px', fontWeight: 900, color: '#fff', marginTop: '4px' }}>
                  {stock.CurrentPrice !== null ? `₹${stock.CurrentPrice.toFixed(2)}` : '—'}
                </div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
                <div className="text-muted text-xs">DAILY CHANGE</div>
                <div style={{ 
                  fontSize: '20px', 
                  fontWeight: 900, 
                  color: stock.DailyChangePct > 0 ? '#10b981' : stock.DailyChangePct < 0 ? '#ef4444' : '#fff',
                  marginTop: '4px' 
                }}>
                  {stock.DailyChangePct !== null ? `${stock.DailyChangePct > 0 ? '+' : ''}${stock.DailyChangePct.toFixed(2)}%` : '—'}
                </div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
                <div className="text-muted text-xs">DAILY VOLUME</div>
                <div style={{ fontSize: '20px', fontWeight: 900, color: '#fff', marginTop: '4px' }}>
                  {stock.Volume !== null ? stock.Volume.toLocaleString('en-IN') : '—'}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px', fontSize: '11px', color: 'var(--text-muted)' }}>
              <span>Market Feed: <strong>Yahoo Finance</strong></span>
              <span>Market Data Updated: <strong>{stock.LastMarketUpdate || 'N/A'}</strong></span>
            </div>
          </div>

          {/* Historical Area Chart */}
          <div className="card" style={{ padding: '20px', flex: 1, minHeight: '320px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 className="card-title" style={{ margin: 0 }}>📈 Price History Chart</h3>
              
              {/* Dynamic Period Selectors */}
              <div className="filter-chips" style={{ display: 'flex', gap: '4px', margin: 0 }}>
                {['1M', '3M', '6M', '1Y'].map((p) => (
                  <button
                    key={p}
                    className={`filter-chip ${chartPeriod === p ? 'active' : ''}`}
                    onClick={() => setChartPeriod(p)}
                    style={{ padding: '4px 8px', fontSize: '11px', minWidth: '40px', height: '26px' }}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
            
            {historyData.length === 0 ? (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                No historical charting data available.
              </div>
            ) : (
              <div style={{ flex: 1, width: '100%', minHeight: '220px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={historyData}>
                    <defs>
                      <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="Date" stroke="rgba(255,255,255,0.3)" fontSize={10} tickLine={false} />
                    <YAxis stroke="rgba(255,255,255,0.3)" fontSize={10} domain={['auto', 'auto']} tickLine={false} />
                    <Tooltip 
                      contentStyle={{ background: '#111', border: '1px solid var(--border-color)', borderRadius: '6px', fontSize: '12px' }}
                      labelStyle={{ color: 'var(--text-muted)' }}
                    />
                    <Area type="monotone" dataKey="Close" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorClose)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── PRIMARY CTA: RUN PMS ANALYSIS BUTTON ── */}
      {!analysisCompleted && !isAnalyzing && (
        <div style={{ textAlign: 'center', padding: '32px 0', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)', marginBottom: '32px' }}>
          {isNotAnalyzed ? (
            <div style={{ maxWidth: '600px', margin: '0 auto' }}>
              <button 
                className="btn btn-primary" 
                disabled
                style={{ padding: '16px 48px', fontSize: '18px', fontWeight: 800, borderRadius: '8px', background: '#374151', color: '#9ca3af', border: 'none', cursor: 'not-allowed', boxShadow: 'none' }}
              >
                🔬 ANALYSIS UNAVAILABLE
              </button>
              <p className="text-muted text-xs" style={{ marginTop: '12px' }}>
                Full quantitative engine coverage is only available for pre-computed Nifty 50 stocks. Live market quote remains active.
              </p>
            </div>
          ) : (
            <div>
              <button 
                className="btn btn-primary" 
                onClick={handleRunAnalysis}
                style={{ padding: '16px 48px', fontSize: '18px', fontWeight: 800, borderRadius: '8px', boxShadow: '0 4px 20px rgba(99,102,241,0.4)' }}
              >
                🔬 RUN PMS ANALYSIS
              </button>
              <p className="text-muted text-xs" style={{ marginTop: '12px' }}>
                Runs Nifty 50 scoring models, random forest tabular ensemble, GRU sequence weights, and compiles XAI audit justifications.
              </p>
            </div>
          )}
        </div>
      )}

      {/* ── INITIALIZING STATE ── */}
      {isAnalyzing && (
        <div className="engine-initializing">
          <div className="engine-initializing-icon">🔬</div>
          <div className="engine-initializing-title">PMS Engine Initializing...</div>
          <p className="engine-initializing-sub">
            Connecting to security core... Fetching live quote feeds, running random forest tabular ensemble, deep learning GRU sequences, and generating explainable AI narratives.
          </p>
          <div className="engine-initializing-bar"></div>
        </div>
      )}

      {/* ── PROGRESSIVE RESEARCH REPORT ── */}
      {analysisCompleted && reportData && (
        <div className="fade-in progressive-report-wrap" style={{ marginTop: '32px' }}>
          
          {/* Section 1: Market Data */}
          {reportSections[0] && (
            <div ref={sectionRefs[0]} className={`report-section ${reportSections[0] ? 'active' : ''}`}>
              <div className="report-header">
                <div className="report-header-label">
                  <span className="report-header-seq">01</span>
                  <span className={getNeonDotClass(0)}></span>
                  <span>Market Data Engine</span>
                </div>
                {getSectionStatusBadge(0)}
              </div>
              <div className="report-body">
                <div className="report-market-grid">
                  <div className="report-market-cell">
                    <div className="report-market-cell-label">CURRENT PRICE</div>
                    <div className="report-market-cell-value">
                      ₹<ScoreCounter value={reportData.CurrentPrice} decimals={2} />
                    </div>
                  </div>
                  <div className="report-market-cell">
                    <div className="report-market-cell-label">DAILY CHANGE</div>
                    <div className="report-market-cell-value" style={{ color: reportData.DailyChangePct > 0 ? '#10b981' : reportData.DailyChangePct < 0 ? '#ef4444' : '#fff' }}>
                      {reportData.DailyChangePct > 0 ? '+' : ''}
                      <ScoreCounter value={reportData.DailyChangePct} decimals={2} suffix="%" />
                    </div>
                  </div>
                  <div className="report-market-cell">
                    <div className="report-market-cell-label">DAILY VOLUME</div>
                    <div className="report-market-cell-value">
                      <ScoreCounter value={reportData.Volume} decimals={0} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 2: Technical Engine */}
          {reportSections[1] && (
            <div ref={sectionRefs[1]} className={`report-section ${reportSections[1] ? 'active' : ''}`}>
              <div className="report-header">
                <div className="report-header-label">
                  <span className="report-header-seq">02</span>
                  <span className={getNeonDotClass(1)}></span>
                  <span>Technical Engine</span>
                </div>
                {getSectionStatusBadge(1)}
              </div>
              <div className="report-body">
                <div className="report-engine-row">
                  <div className="report-engine-score-block">
                    <div className="score-counter-label">Technical Score</div>
                    <div className={`score-counter ${reportData.TechnicalScore >= 0 ? 'positive' : 'negative'}`}>
                      <ScoreCounter value={reportData.TechnicalScore} decimals={2} />
                    </div>
                  </div>
                  <div className="report-engine-detail-block">
                    <div className="score-counter-reason">
                      {reportData.xai_explanation?.TechnicalScoreReason}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 3: ML Engine */}
          {reportSections[2] && (
            <div ref={sectionRefs[2]} className={`report-section ${reportSections[2] ? 'active' : ''}`}>
              <div className="report-header">
                <div className="report-header-label">
                  <span className="report-header-seq">03</span>
                  <span className={getNeonDotClass(2)}></span>
                  <span>ML Tabular Ensemble</span>
                </div>
                {getSectionStatusBadge(2)}
              </div>
              <div className="report-body">
                <div className="report-engine-row">
                  <div className="report-engine-score-block">
                    <div className="score-counter-label">ML Score</div>
                    <div className={`score-counter ${reportData.MLScore >= 0 ? 'positive' : 'negative'}`}>
                      <ScoreCounter value={reportData.MLScore} decimals={2} />
                    </div>
                  </div>
                  <div className="report-engine-detail-block">
                    <div className="score-counter-reason">
                      {reportData.xai_explanation?.MLScoreReason}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 4: GRU Engine */}
          {reportSections[3] && (
            <div ref={sectionRefs[3]} className={`report-section ${reportSections[3] ? 'active' : ''}`}>
              <div className="report-header">
                <div className="report-header-label">
                  <span className="report-header-seq">04</span>
                  <span className={getNeonDotClass(3)}></span>
                  <span>GRU Neural Network Sequence</span>
                </div>
                {getSectionStatusBadge(3)}
              </div>
              <div className="report-body">
                <div className="report-engine-row">
                  <div className="report-engine-score-block">
                    <div className="score-counter-label">GRU Score</div>
                    <div className={`score-counter ${reportData.GRUScore >= 0 ? 'positive' : 'negative'}`}>
                      <ScoreCounter value={reportData.GRUScore} decimals={2} />
                    </div>
                  </div>
                  <div className="report-engine-detail-block">
                    <div className="score-counter-reason">
                      {reportData.xai_explanation?.GRUScoreReason}
                    </div>
                  </div>
                </div>
                {reportData.GRU_LONG !== null && (
                  <div className="report-gru-probs">
                    <div className="report-gru-probs-label">GRU Direction Probabilities</div>
                    <div className="report-gru-bar">
                      <div className="report-gru-segment long" style={{ width: `${reportData.GRU_LONG}%` }}>
                        Long: {reportData.GRU_LONG.toFixed(1)}%
                      </div>
                      <div className="report-gru-segment hold" style={{ width: `${reportData.GRU_HOLD}%` }}>
                        Hold: {reportData.GRU_HOLD.toFixed(1)}%
                      </div>
                      <div className="report-gru-segment short" style={{ width: `${reportData.GRU_SHORT}%` }}>
                        Short: {reportData.GRU_SHORT.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Section 5: Expected Return Engine */}
          {reportSections[4] && (
            <div ref={sectionRefs[4]} className={`report-section ${reportSections[4] ? 'active' : ''}`}>
              <div className="report-header">
                <div className="report-header-label">
                  <span className="report-header-seq">05</span>
                  <span className={getNeonDotClass(4)}></span>
                  <span>Expected Return Model</span>
                </div>
                {getSectionStatusBadge(4)}
              </div>
              <div className="report-body">
                <div className="report-engine-row">
                  <div className="report-engine-score-block">
                    <div className="score-counter-label">Expected Return Score</div>
                    <div className={`score-counter ${reportData.ReturnScore >= 0 ? 'positive' : 'negative'}`}>
                      <ScoreCounter value={reportData.ReturnScore} decimals={2} />
                    </div>
                  </div>
                  <div className="report-engine-detail-block">
                    <div className="score-counter-reason">
                      {reportData.xai_explanation?.ReturnScoreReason}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 6: Reliability Engine */}
          {reportSections[5] && (
            <div ref={sectionRefs[5]} className={`report-section ${reportSections[5] ? 'active' : ''}`}>
              <div className="report-header">
                <div className="report-header-label">
                  <span className="report-header-seq">06</span>
                  <span className={getNeonDotClass(5)}></span>
                  <span>Reliability & Telemetry Integrity</span>
                </div>
                {getSectionStatusBadge(5)}
              </div>
              <div className="report-body">
                <div className="report-engine-row">
                  <div className="report-engine-score-block">
                    <div className="score-counter-label">Reliability Index</div>
                    <div className="score-counter neutral">
                      <ScoreCounter value={reportData.ReliabilityScore} decimals={2} suffix="%" />
                    </div>
                  </div>
                  <div className="report-engine-detail-block">
                    <div className="score-counter-reason">
                      The telemetry integrity model evaluates data stream noise, time latency, and indicator alignment. Scores above 80% indicate premium signal validity.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 7: Composite Engine */}
          {reportSections[6] && (
            <div ref={sectionRefs[6]} className={`report-section ${reportSections[6] ? 'active' : ''}`}>
              <div className="report-header">
                <div className="report-header-label">
                  <span className="report-header-seq">07</span>
                  <span className={getNeonDotClass(6)}></span>
                  <span>Composite Decision Engine</span>
                </div>
                {getSectionStatusBadge(6)}
              </div>
              <div className="report-body">
                <div className="report-composite-grid">
                  <div className="report-composite-cell">
                    <div className="report-composite-cell-label">COMPOSITE SCORE</div>
                    <div className="report-composite-cell-value">
                      <ScoreCounter value={reportData.CompositeScoreV2} decimals={2} />
                    </div>
                  </div>
                  <div className="report-composite-cell">
                    <div className="report-composite-cell-label">UNIVERSE RANK</div>
                    <div className="report-composite-cell-value">
                      #<ScoreCounter value={reportData.Rank} decimals={0} />
                    </div>
                  </div>
                  <div className="report-composite-cell">
                    <div className="report-composite-cell-label">PERCENTILE</div>
                    <div className="report-composite-cell-value">
                      <ScoreCounter value={reportData.Percentile} decimals={1} suffix="%" />
                    </div>
                  </div>
                  <div className="report-composite-cell">
                    <div className="report-composite-cell-label">UNIVERSE POSITION</div>
                    <div className="report-composite-cell-value" style={{ fontSize: '18px', paddingTop: '8px' }}>
                      {reportData.UniversePosition}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 8: Final Recommendation (CLIMAX CARD) */}
          {reportSections[7] && (
            <div ref={sectionRefs[7]} className={`report-section climax-card ${reportSections[7] ? 'active' : ''}`}>
              <div className="report-header">
                <div className="report-header-label">
                  <span className="report-header-seq">08</span>
                  <span className={getNeonDotClass(7)}></span>
                  <span>Final Investment Recommendation</span>
                </div>
                {getSectionStatusBadge(7)}
              </div>
              <div className="report-body">
                <div className="climax-inner">
                  <div className="climax-rating">
                    <RatingBadge rating={reportData.FinalRating} large />
                  </div>
                  
                  <div className="climax-metrics">
                    <div className="climax-metric">
                      <span className="climax-metric-label">Model Confidence</span>
                      <div className="climax-metric-value" style={{ color: confidenceColor(reportData.Confidence) }}>
                        <ScoreCounter value={reportData.Confidence} decimals={1} suffix="%" />
                      </div>
                      <div className="climax-confidence-bar" style={{ width: '80%' }}>
                        <div className="climax-confidence-track">
                          <div 
                            className="climax-confidence-fill" 
                            style={{ 
                              width: `${reportData.Confidence}%`, 
                              backgroundColor: confidenceColor(reportData.Confidence) 
                            }}
                          ></div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="climax-metric">
                      <span className="climax-metric-label">Conviction Level</span>
                      <div className="climax-metric-value" style={{ color: '#fff', fontSize: '18px', fontWeight: 800 }}>
                        {reportData.ConvictionLevel}
                      </div>
                    </div>
                    
                    <div className="climax-metric">
                      <span className="climax-metric-label">Portfolio Eligibility</span>
                      <div style={{ marginTop: '4px' }}>
                        {reportData.PortfolioEligible ? (
                          <span className="badge-eligible" style={{ fontSize: '12px', padding: '4px 12px' }}>ELIGIBLE</span>
                        ) : (
                          <span className="badge-not-eligible" style={{ fontSize: '12px', padding: '4px 12px' }}>NOT ELIGIBLE</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 9: Explainable AI Narrative */}
          {reportSections[8] && (
            <div ref={sectionRefs[8]} className={`report-section ${reportSections[8] ? 'active' : ''}`}>
              <div className="report-header">
                <div className="report-header-label">
                  <span className="report-header-seq">09</span>
                  <span className={getNeonDotClass(8)}></span>
                  <span>Explainable AI Model Justifications</span>
                </div>
                {getSectionStatusBadge(8)}
              </div>
              <div className="report-body">
                {reportData.xai_explanation && (
                  <div>
                    <div className="score-counter-reason" style={{ borderTop: 'none', paddingTop: 0, marginTop: 0, marginBottom: '24px' }}>
                      <strong>Consensus Integration Decision:</strong> {reportData.xai_explanation.FinalRatingReason}
                    </div>
                    
                    <div className="report-factors-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px', marginBottom: '24px' }}>
                      {/* Drivers Table */}
                      <div className="card" style={{ padding: '16px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                        <h4 style={{ color: '#fff', margin: '0 0 12px 0', fontSize: '15px' }}>Scoring Drivers (by Absolute Impact)</h4>
                        <div className="drivers-table-wrapper" style={{ maxHeight: '240px', overflowY: 'auto' }}>
                          <table className="drivers-table">
                            <thead>
                              <tr>
                                <th>Driver</th>
                                <th>Value</th>
                                <th>Impact</th>
                              </tr>
                            </thead>
                            <tbody>
                              {reportData.xai_explanation.RatingDrivers.map((driver, idx) => (
                                <tr key={idx}>
                                  <td>
                                    <div className="driver-name">{driver.name}</div>
                                    <div className="driver-desc" style={{ fontSize: '11px' }}>{driver.description}</div>
                                  </td>
                                  <td className="driver-val" style={{ fontWeight: 600 }}>{driver.value > 0 ? '+' : ''}{driver.value.toFixed(2)}</td>
                                  <td className="driver-impact" style={{ color: impactColor(driver.impact) }}>{impactLabel(driver.impact)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                      
                      {/* Positive & Risks */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        <div className="card factors-card positive-factors-card" style={{ padding: '16px', background: 'rgba(16,185,129,0.02)', border: '1px solid rgba(16,185,129,0.1)' }}>
                          <h5 style={{ color: '#10b981', margin: '0 0 8px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span>🟢</span> Top Positive Drivers
                          </h5>
                          <ul className="factors-list" style={{ margin: 0, paddingLeft: '16px' }}>
                            {reportData.top_positive_factors && reportData.top_positive_factors.map((f, i) => (
                              <li key={i} className="factor-item positive-factor" style={{ fontSize: '13px', marginBottom: '4px' }}>
                                <span className="factor-text">{f}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                        
                        <div className="card factors-card negative-factors-card" style={{ padding: '16px', background: 'rgba(239,44,44,0.02)', border: '1px solid rgba(239,44,44,0.1)' }}>
                          <h5 style={{ color: '#ef4444', margin: '0 0 8px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span>🔴</span> Top Risk / Drag Factors
                          </h5>
                          <ul className="factors-list" style={{ margin: 0, paddingLeft: '16px' }}>
                            {reportData.top_negative_factors && reportData.top_negative_factors.map((f, i) => (
                              <li key={i} className="factor-item negative-factor" style={{ fontSize: '13px', marginBottom: '4px' }}>
                                <span className="factor-text">{f}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                    
                    {/* Institutional Analyst Insight */}
                    <div className="report-insight-box">
                      <div className="report-insight-header">
                        <span>📋</span>
                        <span>PMS Engine Institutional Analyst Insight</span>
                      </div>
                      <p className="report-insight-text">{reportData.institutional_insight}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Report Generation Box */}
          {!isRevealing && reportSections[8] && (
            <>
              {!generatedReportId ? (
                <div className="card" style={{ padding: '24px', margin: '24px 0', textAlign: 'center', background: 'linear-gradient(135deg, rgba(16,185,129,0.05) 0%, rgba(5,150,105,0.05) 100%)', border: '1px solid rgba(16,185,129,0.2)' }}>
                  <h3 style={{ color: '#10b981', margin: '0 0 8px 0' }}>📄 Equity Research Report Available</h3>
                  <p className="text-muted" style={{ fontSize: '14px', marginBottom: '16px' }}>
                    Generate a publication-quality PDF or HTML report for {symbol} featuring complete XAI justifications and score card breakdowns.
                  </p>
                  <button
                    className="btn"
                    style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', color: '#fff', padding: '12px 36px', fontSize: '15px', fontWeight: 'bold', border: 'none', borderRadius: '6px', cursor: 'pointer', boxShadow: '0 4px 15px rgba(16,185,129,0.3)' }}
                    onClick={handleGenerateReport}
                    disabled={isGeneratingReport}
                  >
                    {isGeneratingReport ? '⏳ Generating Report...' : '📄 GENERATE RESEARCH REPORT'}
                  </button>
                </div>
              ) : (
                <div className="card" style={{ padding: '24px', margin: '24px 0', border: '1px solid var(--border-color)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
                    <h3 style={{ color: '#10b981', margin: 0 }}>📄 Equity Research Report Generated</h3>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <a
                        href={getReportDownloadUrl(generatedReportId, 'pdf')}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn"
                        style={{ background: '#0a1628', color: '#d4a843', border: '1px solid #d4a843', padding: '8px 16px', fontSize: '13px', borderRadius: '4px', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '6px' }}
                      >
                        📥 Download PDF
                      </a>
                      <a
                        href={getReportDownloadUrl(generatedReportId, 'html')}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn"
                        style={{ background: '#0a1628', color: '#d4a843', border: '1px solid #d4a843', padding: '8px 16px', fontSize: '13px', borderRadius: '4px', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '6px' }}
                      >
                        🌐 Download HTML
                      </a>
                    </div>
                  </div>
                  
                  {/* Inline Preview */}
                  <div className="reports-preview-frame-container" style={{ height: '600px', width: '100%', overflow: 'hidden', borderRadius: '6px', border: '1px solid var(--border-color)', background: '#fff' }}>
                    <iframe
                      src={getReportPreviewUrl(generatedReportId)}
                      style={{ width: '100%', height: '100%', border: 'none', background: '#fff' }}
                      title="Equity Research Report Preview"
                    />
                  </div>
                </div>
              )}

              {/* Re-run CTA Button */}
              <div className="report-rerun-cta" style={{ textAlign: 'center', marginTop: '16px' }}>
                <button 
                  className="btn btn-secondary" 
                  onClick={handleRunAnalysis}
                  style={{ padding: '12px 36px', borderRadius: '6px', fontSize: '14px', fontWeight: 'bold' }}
                >
                  🔬 RE-RUN PMS ANALYSIS
                </button>
              </div>
            </>
          )}

          {/* ── HISTORY LOGS CARD ── */}
          <div className="card" style={{ padding: '20px', marginTop: '24px', marginBottom: '32px' }}>
            <h3 className="card-title" style={{ marginBottom: '16px' }}>⏱️ Analysis History Logs ({symbol})</h3>
            {historyLogs.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>
                No past analysis runs saved in database cache.
              </div>
            ) : (
              <div className="table-container">
                <table className="data-table" style={{ width: '100%' }}>
                  <thead>
                    <tr>
                      <th>Run ID</th>
                      <th>Run Date</th>
                      <th>Rating</th>
                      <th>Confidence</th>
                      <th>Composite</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historyLogs.map((log, index) => (
                      <tr key={index}>
                        <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{log.analysis_id ? log.analysis_id.slice(0, 8) + '...' : 'BASELINE'}</td>
                        <td style={{ fontWeight: 600 }}>{log.analyzed_at}</td>
                        <td><RatingBadge rating={log.rating} /></td>
                        <td style={{ fontWeight: 700, color: confidenceColor(log.confidence) }}>{log.confidence.toFixed(1)}%</td>
                        <td style={{ fontWeight: 700 }}>{log.composite_score.toFixed(2)}</td>
                        <td>
                          <span className="badge-status" style={{ 
                            background: `${statusColor(log.status)}15`, 
                            color: statusColor(log.status),
                            border: `1px solid ${statusColor(log.status)}30`,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontWeight: 'bold',
                            fontSize: '10px'
                          }}>
                            {log.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>
      )}

    </div>
  );
}

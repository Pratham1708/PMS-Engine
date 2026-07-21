import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  fetchLatestSnapshotSummary,
  fetchSnapshotStatus,
  triggerSnapshotGeneration,
  triggerLiveAnalysis,
  fetchPipelineStatus,
} from '../api/stocks';
import QuantResearchLabModal from '../components/pipeline/QuantResearchLabModal';

const RATING_COLORS = {
  'STRONG BUY': '#10b981',
  'BUY':        '#3b82f6',
  'HOLD':       '#f59e0b',
  'SELL':       '#f97316',
  'STRONG SELL':'#ef4444',
};

const REGIME_CONFIG = {
  Bullish: { color: '#10b981', bg: 'rgba(16,185,129,0.12)', icon: '📈' },
  Bearish: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)',  icon: '📉' },
  Mixed:   { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', icon: '🔀' },
  Neutral: { color: '#6b7280', bg: 'rgba(107,114,128,0.1)', icon: '➡️' },
};

function PulseCard({ label, value, sub, accent }) {
  return (
    <div className="sd-pulse-card" style={{ '--accent': accent }}>
      <div className="sd-pulse-card-value">{value}</div>
      <div className="sd-pulse-card-label">{label}</div>
      {sub && <div className="sd-pulse-card-sub">{sub}</div>}
    </div>
  );
}

function RatingBar({ dist }) {
  if (!dist) return null;
  const total = (dist.strong_buy_count || 0) + (dist.buy_count || 0) +
    (dist.hold_count || 0) + (dist.sell_count || 0) + (dist.strong_sell_count || 0);
  const pct = (n) => total > 0 ? (n / total * 100) : 0;
  const segments = [
    { label: 'STRONG BUY', count: dist.strong_buy_count || 0, color: RATING_COLORS['STRONG BUY'] },
    { label: 'BUY',        count: dist.buy_count || 0,        color: RATING_COLORS['BUY'] },
    { label: 'HOLD',       count: dist.hold_count || 0,       color: RATING_COLORS['HOLD'] },
    { label: 'SELL',       count: dist.sell_count || 0,       color: RATING_COLORS['SELL'] },
    { label: 'STRONG SELL',count: dist.strong_sell_count || 0,color: RATING_COLORS['STRONG SELL'] },
  ];
  return (
    <div className="sd-rating-bar-wrap">
      <div className="sd-rating-bar">
        {segments.map(s => s.count > 0 && (
          <div key={s.label} title={`${s.label}: ${s.count}`}
            className="sd-rating-bar-seg"
            style={{ width: `${pct(s.count)}%`, background: s.color }}
          />
        ))}
      </div>
      <div className="sd-rating-bar-labels">
        {segments.map(s => (
          <div key={s.label} className="sd-rating-bar-label">
            <span className="sd-rating-dot" style={{ background: s.color }} />
            <span>{s.label}</span>
            <span className="sd-rating-count">{s.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function StockRow({ stock, onNavigate }) {
  const chg = parseFloat(stock.daily_chg_pct || 0);
  const isPos = chg > 0;
  return (
    <tr className="sd-stock-row" onClick={() => onNavigate(`/stock/${stock.symbol}`)}>
      <td className="sd-stock-sym">
        <div className="sd-stock-sym-badge">{stock.symbol?.replace('.NS', '')}</div>
      </td>
      <td>
        <span className="sd-rating-pill" style={{ background: RATING_COLORS[stock.final_rating] + '22', color: RATING_COLORS[stock.final_rating] }}>
          {stock.final_rating}
        </span>
      </td>
      <td className="sd-num">{stock.composite_score != null ? stock.composite_score.toFixed(1) : '—'}</td>
      <td className="sd-num">{stock.confidence != null ? `${stock.confidence.toFixed(0)}%` : '—'}</td>
      <td className={`sd-num ${isPos ? 'sd-pos' : chg < 0 ? 'sd-neg' : ''}`}>
        {chg !== 0 ? `${isPos ? '+' : ''}${chg.toFixed(2)}%` : '—'}
      </td>
    </tr>
  );
}

function ChangeCard({ change }) {
  const isUp = ['UPGRADE', 'NEW_BUY'].includes(change.change_type);
  const icons = { UPGRADE: '⬆️', DOWNGRADE: '⬇️', NEW_BUY: '🆕', NEW_SELL: '🔻', COMPOSITE_UP: '↑', COMPOSITE_DOWN: '↓', CONFIDENCE_UP: '↑', CONFIDENCE_DOWN: '↓' };
  return (
    <div className={`sd-change-card ${isUp ? 'sd-change-up' : 'sd-change-down'}`}>
      <span className="sd-change-icon">{icons[change.change_type] || '•'}</span>
      <span className="sd-change-sym">{change.symbol?.replace('.NS', '')}</span>
      <span className="sd-change-type">{change.change_type?.replace(/_/g, ' ')}</span>
      {change.prev_rating && (
        <span className="sd-change-ratings">
          <span style={{ color: RATING_COLORS[change.prev_rating] }}>{change.prev_rating}</span>
          {' → '}
          <span style={{ color: RATING_COLORS[change.new_rating] }}>{change.new_rating}</span>
        </span>
      )}
      {change.composite_diff != null && (
        <span className={`sd-change-diff ${change.composite_diff > 0 ? 'sd-pos' : 'sd-neg'}`}>
          {change.composite_diff > 0 ? '+' : ''}{change.composite_diff.toFixed(1)}
        </span>
      )}
    </div>
  );
}

function PipelineProgress({ pipeline, onOpenLab }) {
  if (!pipeline || pipeline.status === 'idle') return null;
  const pct = pipeline.pct_complete || 0;
  const isRunning = pipeline.status === 'running';
  return (
    <div className="sd-pipeline-progress" style={{ background: '#0f172a', border: '1px solid #3b82f6', borderRadius: '12px', padding: '16px', margin: '16px 0' }}>
      <div className="sd-pipeline-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="sd-pipeline-label" style={{ fontWeight: '800', color: '#38bdf8' }}>
          {isRunning ? '⚡ Quantitative Research Laboratory Active' : pipeline.status === 'completed' ? '✅ Pipeline Complete' : '❌ Pipeline Failed'}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span className="sd-pipeline-pct" style={{ fontWeight: '800', color: '#ffffff' }}>{pct.toFixed(0)}%</span>
          {onOpenLab && (
            <button
              onClick={onOpenLab}
              style={{ background: '#3b82f6', color: '#ffffff', border: 'none', padding: '6px 14px', borderRadius: '6px', fontWeight: '700', fontSize: '12px', cursor: 'pointer' }}
            >
              🔬 Open Interactive Research Lab
            </button>
          )}
        </div>
      </div>
      <div className="sd-pipeline-bar" style={{ height: '6px', background: '#1e293b', borderRadius: '3px', margin: '12px 0 8px 0', overflow: 'hidden' }}>
        <div className="sd-pipeline-fill" style={{ width: `${pct}%`, height: '100%', background: isRunning ? '#3b82f6' : pipeline.status === 'completed' ? '#10b981' : '#ef4444' }} />
      </div>
      {pipeline.current_stage && (
        <div className="sd-pipeline-stage" style={{ fontSize: '12px', color: '#94a3b8' }}>Stage: {pipeline.current_stage.replace(/_/g, ' ')}</div>
      )}
      <div className="sd-pipeline-counts" style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
        ✓ {pipeline.stocks_completed} ok · ✗ {pipeline.stocks_failed} failed · {pipeline.elapsed_sec?.toFixed(0)}s elapsed
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function SnapshotDashboard() {
  const [summary, setSummary] = useState(null);
  const [sysStatus, setSysStatus] = useState(null);
  const [pipeline, setPipeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [liveAnalysis, setLiveAnalysis] = useState(false);
  const [error, setError] = useState(null);
  const [isLabOpen, setIsLabOpen] = useState(false);
  const [replaySnapshotId, setReplaySnapshotId] = useState(null);
  const navigate = useNavigate();

  const loadData = useCallback(async () => {
    try {
      const [statusRes, pipelineRes] = await Promise.all([
        fetchSnapshotStatus(),
        fetchPipelineStatus(),
      ]);
      setSysStatus(statusRes.data);
      setPipeline(pipelineRes.data);

      if (statusRes.data?.latest_snapshot) {
        const summRes = await fetchLatestSnapshotSummary();
        setSummary(summRes.data);
      }
    } catch (err) {
      if (err.response?.status !== 404) {
        setError('Failed to load snapshot data');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Poll faster while pipeline is running
  useEffect(() => {
    if (pipeline?.status !== 'running') return;
    const fast = setInterval(async () => {
      try {
        const res = await fetchPipelineStatus();
        setPipeline(res.data);
        if (res.data.status !== 'running') {
          loadData();
          clearInterval(fast);
        }
      } catch {/* ignore */}
    }, 3000);
    return () => clearInterval(fast);
  }, [pipeline?.status, loadData]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      await triggerSnapshotGeneration();
      setTimeout(loadData, 1000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start pipeline');
    } finally {
      setTimeout(() => setGenerating(false), 2000);
    }
  };

  const handleLiveAnalysis = async () => {
    setLiveAnalysis(true);
    setError(null);
    try {
      await triggerLiveAnalysis();
      setTimeout(loadData, 1000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start live analysis');
    } finally {
      setTimeout(() => setLiveAnalysis(false), 2000);
    }
  };

  const isRunning = pipeline?.status === 'running' || sysStatus?.in_progress > 0;

  if (loading) {
    return (
      <div className="sd-loading">
        <div className="sd-loading-spin" />
        <div>Loading Daily Research Platform…</div>
      </div>
    );
  }

  const snap = summary?.meta;
  const breadth = summary?.breadth;
  const sectors = summary?.sectors || [];
  const topStocks = summary?.top_opportunities || [];
  const changes = summary?.changes_summary;
  const valSummary = summary?.validation_summary;

  // ── Empty State ────────────────────────────────────────────────────────────

  if (!snap) {
    return (
      <div className="sd-empty-state">
        <div className="sd-empty-icon">📊</div>
        <h1 className="sd-empty-title">PMS Engine Research Platform</h1>
        <p className="sd-empty-sub">
          No official snapshot has been generated yet.<br />
          Generate your first daily research snapshot to activate the platform.
        </p>
        <div className="sd-empty-actions">
          <button
            className={`sd-btn-primary ${isRunning || generating ? 'sd-btn-busy' : ''}`}
            onClick={handleGenerate}
            disabled={isRunning || generating}
          >
            {isRunning ? '⚡ Pipeline Running…' : generating ? '⚡ Starting…' : '⚡ Generate First Snapshot'}
          </button>
          <button
            className="sd-btn-secondary"
            onClick={() => navigate('/workspace')}
          >
            🏠 Go to Research Workspace
          </button>
        </div>
        {isRunning && <PipelineProgress pipeline={pipeline} onOpenLab={() => { setReplaySnapshotId(null); setIsLabOpen(true); }} />}
        {error && <div className="sd-error-msg">{error}</div>}
      </div>
    );
  }

  const regime = REGIME_CONFIG[breadth?.market_regime] || REGIME_CONFIG.Neutral;

  // ── Main Dashboard ─────────────────────────────────────────────────────────

  return (
    <div className="sd-dashboard">

      {/* ── Row 0: Actions ── */}
      <div className="sd-actions-row">
        <div className="sd-actions-left">
          <h1 className="sd-title">Daily Research Dashboard</h1>
          <span className="sd-subtitle">Official Snapshot · {snap.snapshot_date}</span>
        </div>
        <div className="sd-actions-right">
          <button
            className={`sd-btn-secondary ${liveAnalysis ? 'sd-btn-busy' : ''}`}
            onClick={handleLiveAnalysis}
            disabled={isRunning || liveAnalysis}
            title="Run on-demand analysis (does not replace official snapshot)"
          >
            🔬 Live Analysis
          </button>
          <button
            className={`sd-btn-primary ${generating || isRunning ? 'sd-btn-busy' : ''}`}
            onClick={handleGenerate}
            disabled={generating || isRunning}
          >
            {isRunning ? '⚡ Running…' : '⚡ Generate Snapshot'}
          </button>
        </div>
      </div>

      {error && <div className="sd-error-msg">{error}</div>}
      {isRunning && <PipelineProgress pipeline={pipeline} onOpenLab={() => { setReplaySnapshotId(null); setIsLabOpen(true); }} />}

      {/* ── Row 1: Market Pulse Cards ── */}
      <div className="sd-pulse-row">
        <PulseCard
          label="Market Date"
          value={snap.snapshot_date}
          sub={snap.published_at ? `Published ${snap.published_at.slice(11, 16)} IST` : 'Generating…'}
          accent="#3b82f6"
        />
        <PulseCard
          label="Stocks Processed"
          value={snap.stocks_processed || '—'}
          sub={snap.stocks_failed > 0 ? `${snap.stocks_failed} failed` : 'All OK'}
          accent="#10b981"
        />
        <div className="sd-pulse-card" style={{ '--accent': regime.color, background: regime.bg }}>
          <div className="sd-pulse-card-value">{regime.icon} {breadth?.market_regime || 'Neutral'}</div>
          <div className="sd-pulse-card-label">Market Regime</div>
          <div className="sd-pulse-card-sub">
            {breadth ? `A/D: ${breadth.advancing_stocks}/${breadth.declining_stocks}` : '—'}
          </div>
        </div>
        <PulseCard
          label="Avg Composite"
          value={breadth?.avg_composite != null ? breadth.avg_composite.toFixed(1) : '—'}
          sub="Universe Average"
          accent="#8b5cf6"
        />
        <PulseCard
          label="Avg Confidence"
          value={breadth?.avg_confidence != null ? `${breadth.avg_confidence.toFixed(0)}%` : '—'}
          sub="Signal Strength"
          accent="#f59e0b"
        />
        <PulseCard
          label="Data Quality"
          value={snap.validation_score != null ? `${snap.validation_score.toFixed(0)}/100` : '—'}
          sub={snap.validation_passed ? '✓ Validated' : '⚠ Warnings'}
          accent={snap.validation_passed ? '#10b981' : '#f59e0b'}
        />
      </div>

      {/* ── Row 2: Rating Distribution ── */}
      <div className="sd-section-card">
        <h2 className="sd-section-title">📊 Rating Distribution</h2>
        <RatingBar dist={breadth} />
      </div>

      {/* ── Row 3: Top Opportunities + Changes ── */}
      <div className="sd-split-row">
        {/* Top Stocks */}
        <div className="sd-section-card sd-split-left">
          <div className="sd-section-header">
            <h2 className="sd-section-title">⭐ Top Opportunities</h2>
            <button className="sd-link-btn" onClick={() => navigate('/search')}>View All →</button>
          </div>
          {topStocks.length > 0 ? (
            <table className="sd-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Rating</th>
                  <th>Composite</th>
                  <th>Confidence</th>
                  <th>Change</th>
                </tr>
              </thead>
              <tbody>
                {topStocks.slice(0, 8).map(s => (
                  <StockRow key={s.symbol} stock={s} onNavigate={navigate} />
                ))}
              </tbody>
            </table>
          ) : (
            <div className="sd-empty-cell">No strong buy/buy stocks in this snapshot</div>
          )}
        </div>

        {/* Recommendation Changes */}
        <div className="sd-section-card sd-split-right">
          <div className="sd-section-header">
            <h2 className="sd-section-title">🔄 Today's Changes</h2>
            <button className="sd-link-btn" onClick={() => navigate('/changes')}>View All →</button>
          </div>
          {changes ? (
            <div className="sd-changes-summary">
              <div className="sd-change-stat">
                <span className="sd-change-stat-val sd-pos">+{changes.new_buys || 0}</span>
                <span className="sd-change-stat-label">New Buys</span>
              </div>
              <div className="sd-change-stat">
                <span className="sd-change-stat-val sd-neg">{changes.new_sells || 0}</span>
                <span className="sd-change-stat-label">New Sells</span>
              </div>
              <div className="sd-change-stat">
                <span className="sd-change-stat-val sd-pos">↑{changes.upgrades || 0}</span>
                <span className="sd-change-stat-label">Upgrades</span>
              </div>
              <div className="sd-change-stat">
                <span className="sd-change-stat-val sd-neg">↓{changes.downgrades || 0}</span>
                <span className="sd-change-stat-label">Downgrades</span>
              </div>
              <div className="sd-change-stat">
                <span className="sd-change-stat-val">{changes.total || 0}</span>
                <span className="sd-change-stat-label">Total Changes</span>
              </div>
            </div>
          ) : (
            <div className="sd-empty-cell">No previous snapshot to compare against</div>
          )}
        </div>
      </div>

      {/* ── Row 4: Sector Rankings ── */}
      <div className="sd-section-card">
        <div className="sd-section-header">
          <h2 className="sd-section-title">🏢 Sector Rankings</h2>
          <button className="sd-link-btn" onClick={() => navigate('/sectors')}>View All →</button>
        </div>
        {sectors.length > 0 ? (
          <table className="sd-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Sector</th>
                <th>Stocks</th>
                <th>Avg Composite</th>
                <th>Bullish %</th>
                <th>Top Stock</th>
              </tr>
            </thead>
            <tbody>
              {sectors.map((s, i) => (
                <tr key={s.sector}>
                  <td className="sd-num">{i + 1}</td>
                  <td><strong>{s.sector}</strong></td>
                  <td className="sd-num">{s.stock_count}</td>
                  <td className="sd-num">{s.avg_composite != null ? s.avg_composite.toFixed(1) : '—'}</td>
                  <td>
                    <div className="sd-sector-bar">
                      <div className="sd-sector-fill" style={{ width: `${s.bullish_pct || 0}%` }} />
                      <span>{s.bullish_pct != null ? `${s.bullish_pct.toFixed(0)}%` : '—'}</span>
                    </div>
                  </td>
                  <td className="sd-stock-sym-small">{s.top_stock?.replace('.NS', '') || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="sd-empty-cell">Sector data not available</div>
        )}
      </div>

      {/* ── Row 5: Market Breadth ── */}
      {breadth && (
        <div className="sd-section-card">
          <div className="sd-section-header">
            <h2 className="sd-section-title">📈 Market Breadth</h2>
            <button className="sd-link-btn" onClick={() => navigate('/breadth')}>View All →</button>
          </div>
          <div className="sd-breadth-grid">
            <div className="sd-breadth-item">
              <div className="sd-breadth-label">Above EMA 20</div>
              <div className="sd-breadth-bar-wrap">
                <div className="sd-breadth-bar-bg">
                  <div className="sd-breadth-bar-fill sd-breadth-green" style={{ width: `${breadth.pct_above_ema20 || 0}%` }} />
                </div>
                <span className="sd-breadth-pct">{breadth.pct_above_ema20 != null ? `${breadth.pct_above_ema20.toFixed(0)}%` : '—'}</span>
              </div>
            </div>
            <div className="sd-breadth-item">
              <div className="sd-breadth-label">Above EMA 50</div>
              <div className="sd-breadth-bar-wrap">
                <div className="sd-breadth-bar-bg">
                  <div className="sd-breadth-bar-fill sd-breadth-blue" style={{ width: `${breadth.pct_above_ema50 || 0}%` }} />
                </div>
                <span className="sd-breadth-pct">{breadth.pct_above_ema50 != null ? `${breadth.pct_above_ema50.toFixed(0)}%` : '—'}</span>
              </div>
            </div>
            <div className="sd-breadth-item">
              <div className="sd-breadth-label">Above EMA 200</div>
              <div className="sd-breadth-bar-wrap">
                <div className="sd-breadth-bar-bg">
                  <div className="sd-breadth-bar-fill sd-breadth-purple" style={{ width: `${breadth.pct_above_ema200 || 0}%` }} />
                </div>
                <span className="sd-breadth-pct">{breadth.pct_above_ema200 != null ? `${breadth.pct_above_ema200.toFixed(0)}%` : '—'}</span>
              </div>
            </div>
            <div className="sd-breadth-stat">
              <span className="sd-breadth-stat-val sd-pos">{breadth.advancing_stocks}</span>
              <span className="sd-breadth-stat-label">Advancing</span>
            </div>
            <div className="sd-breadth-stat">
              <span className="sd-breadth-stat-val sd-neg">{breadth.declining_stocks}</span>
              <span className="sd-breadth-stat-label">Declining</span>
            </div>
            <div className="sd-breadth-stat">
              <span className="sd-breadth-stat-val">{breadth.advance_decline_ratio?.toFixed(2) || '—'}</span>
              <span className="sd-breadth-stat-label">A/D Ratio</span>
            </div>
          </div>
        </div>
      )}

      {/* ── Row 6: Validation + Pipeline Status ── */}
      {(valSummary || summary?.pipeline_summary) && (
        <div className="sd-split-row">
          {valSummary && (
            <div className="sd-section-card sd-split-left">
              <h2 className="sd-section-title">✅ Validation Status</h2>
              <div className="sd-val-grid">
                <div className="sd-val-item sd-val-pass">
                  <span className="sd-val-count">{valSummary.pass}</span>
                  <span className="sd-val-label">Passed</span>
                </div>
                <div className="sd-val-item sd-val-warn">
                  <span className="sd-val-count">{valSummary.warning}</span>
                  <span className="sd-val-label">Warnings</span>
                </div>
                <div className="sd-val-item sd-val-fail">
                  <span className="sd-val-count">{valSummary.fail}</span>
                  <span className="sd-val-label">Failed</span>
                </div>
              </div>
              {valSummary.score != null && (
                <div className="sd-quality-score">
                  Quality Score: <strong>{valSummary.score.toFixed(0)}/100</strong>
                </div>
              )}
              <button className="sd-link-btn" onClick={() => navigate('/data-quality')}>
                View Data Quality Report →
              </button>
            </div>
          )}
          {summary?.pipeline_summary && (
            <div className="sd-section-card sd-split-right">
              <h2 className="sd-section-title">⚙️ Pipeline Summary</h2>
              <div className="sd-pipeline-stats">
                <div>Total Stages: <strong>{summary.pipeline_summary.total_stages}</strong></div>
                <div>Completed: <strong className="sd-pos">{summary.pipeline_summary.completed}</strong></div>
                <div>With Warnings: <strong className="sd-warn">{summary.pipeline_summary.with_warnings}</strong></div>
                <div>Failed: <strong className="sd-neg">{summary.pipeline_summary.failed}</strong></div>
                {summary.pipeline_summary.duration_sec && (
                  <div>Duration: <strong>{summary.pipeline_summary.duration_sec.toFixed(0)}s</strong></div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      <QuantResearchLabModal
        isOpen={isLabOpen}
        onClose={() => {
          setIsLabOpen(false);
          setReplaySnapshotId(null);
        }}
        replaySnapshotId={replaySnapshotId}
      />
    </div>
  );
}

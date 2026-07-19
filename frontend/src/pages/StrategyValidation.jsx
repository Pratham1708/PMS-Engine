/**
 * StrategyValidation.jsx — Strategy Health Score Dashboard
 * Phase 14C: 11-category validation with correlation heatmap, bias tags,
 * warnings/errors/recommendations, and backtest launch CTA.
 */

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import {
  RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer,
  PieChart, Pie, Cell, Tooltip, Legend,
} from "recharts";
import { validateStrategy } from "../api/backtestApi";
import "./StrategyValidation.css";

// ── Score colour ramp ─────────────────────────────────────────────────────────
const scoreColor = (pct) => {
  if (pct >= 80) return "#10b981";
  if (pct >= 60) return "#f59e0b";
  if (pct >= 40) return "#f97316";
  return "#ef4444";
};

const statusIcon = (status) => {
  if (status === "pass") return "✓";
  if (status === "warn") return "⚠";
  return "✗";
};
const statusClass = (status) => {
  if (status === "pass") return "check-pass";
  if (status === "warn") return "check-warn";
  return "check-fail";
};

// ── Pearson r heatmap colour ──────────────────────────────────────────────────
const corrColor = (r) => {
  const abs = Math.abs(r);
  if (abs >= 0.85) return r >= 0 ? "#ef4444" : "#3b82f6";
  if (abs >= 0.6)  return r >= 0 ? "#f97316" : "#60a5fa";
  if (abs >= 0.3)  return r >= 0 ? "#fbbf24" : "#93c5fd";
  return "#1e293b";
};

// ── Bias tag badge component ──────────────────────────────────────────────────
const BiasTag = ({ tag }) => {
  let color = "#10b981", icon = "✓";
  if (tag.includes("survivorship")) { color = "#f59e0b"; icon = "⚠"; }
  if (tag.includes("high")) { color = "#ef4444"; icon = "✗"; }
  if (tag.includes("medium")) { color = "#f97316"; icon = "⚠"; }
  return (
    <span className="bias-tag" style={{ borderColor: color, color }}>
      {icon} {tag}
    </span>
  );
};

// ── Category card ─────────────────────────────────────────────────────────────
const CategoryCard = ({ cat, index }) => {
  const [expanded, setExpanded] = useState(false);
  const pct = (cat.score / cat.max_score) * 100;
  const color = scoreColor(pct);

  return (
    <div className={`cat-card cat-${cat.status}`} onClick={() => setExpanded(!expanded)}>
      <div className="cat-header">
        <div className="cat-title">
          <span className="cat-status-dot" style={{ background: color }} />
          <span className="cat-name">{cat.category}</span>
        </div>
        <div className="cat-score-wrap">
          <div className="cat-score-bar">
            <div className="cat-score-fill" style={{ width: `${pct}%`, background: color }} />
          </div>
          <span className="cat-score-label" style={{ color }}>
            {cat.score.toFixed(1)} / {cat.max_score}
          </span>
        </div>
        <span className="cat-chevron">{expanded ? "▲" : "▼"}</span>
      </div>
      {expanded && (
        <div className="cat-checks">
          {(cat.checks || []).map((c, i) => (
            <div key={i} className={`check-row ${statusClass(c.status)}`}>
              <span className="check-icon">{statusIcon(c.status)}</span>
              <span className="check-name">{c.name}</span>
              {c.detail && <span className="check-detail">{c.detail}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Correlation heatmap ───────────────────────────────────────────────────────
const CorrelationHeatmap = ({ matrix }) => {
  if (!matrix || matrix.length === 0) return (
    <div className="heatmap-empty">Insufficient feature data for correlation analysis.</div>
  );

  const features = [...new Set(matrix.flatMap((p) => [p.feature_a, p.feature_b]))];
  const n = features.length;
  const get = (a, b) => {
    if (a === b) return { pearson_r: 1.0 };
    const pair = matrix.find((p) =>
      (p.feature_a === a && p.feature_b === b) ||
      (p.feature_a === b && p.feature_b === a)
    );
    return pair || { pearson_r: 0 };
  };

  return (
    <div className="heatmap-container" style={{ overflowX: "auto" }}>
      <div className="heatmap-grid" style={{ gridTemplateColumns: `80px repeat(${n}, 56px)` }}>
        {/* Header row */}
        <div />
        {features.map((f) => (
          <div key={f} className="heatmap-label heatmap-col-label" title={f}>
            {f.slice(0, 6)}
          </div>
        ))}
        {/* Data rows */}
        {features.map((rowF) => (
          <React.Fragment key={rowF}>
            <div className="heatmap-label heatmap-row-label" title={rowF}>
              {rowF.slice(0, 8)}
            </div>
            {features.map((colF) => {
              const cell = get(rowF, colF);
              const r = cell.pearson_r;
              const bg = corrColor(r);
              return (
                <div
                  key={colF}
                  className="heatmap-cell"
                  style={{ background: bg }}
                  title={`${rowF} × ${colF}: r=${r.toFixed(3)}`}
                >
                  <span className="heatmap-r">{r.toFixed(2)}</span>
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>
      <div className="heatmap-legend">
        <span style={{ color: "#3b82f6" }}>■</span> Strong neg. correlation &nbsp;
        <span style={{ color: "#1e293b" }}>■</span> Low correlation &nbsp;
        <span style={{ color: "#ef4444" }}>■</span> Strong pos. correlation
      </div>
    </div>
  );
};

// ── Main component ────────────────────────────────────────────────────────────
const WEIGHT_COLORS = [
  "#6366f1","#8b5cf6","#a78bfa","#c4b5fd","#7c3aed","#4f46e5","#818cf8",
  "#34d399","#10b981","#059669","#f59e0b","#f97316","#ef4444",
];

export default function StrategyValidation() {
  const { strategyId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("categories");
  const [showBacktestModal, setShowBacktestModal] = useState(false);

  // The strategy definition may be passed via navigation state (from Studio wizard)
  const stateDefinition = location.state?.definition;
  const strategyName = location.state?.strategyName || "";

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        strategy_id: strategyId,
        strategy_name: strategyName,
      };
      if (stateDefinition) payload.definition = stateDefinition;
      const { data } = await validateStrategy(payload);
      setReport(data);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, [strategyId, stateDefinition, strategyName]);

  useEffect(() => { load(); }, [load]);

  if (loading) return (
    <div className="sv-page sv-loading">
      <div className="sv-spinner" />
      <p>Running 11-category validation analysis…</p>
    </div>
  );

  if (error) return (
    <div className="sv-page sv-error">
      <div className="sv-error-icon">⚠</div>
      <h2>Validation Error</h2>
      <p>{error}</p>
      <button className="sv-btn-primary" onClick={load}>Retry</button>
    </div>
  );

  if (!report) return null;

  const { validation_score, passed, categories, correlation_matrix,
    bias_tags, warnings, errors: validationErrors, recommendations } = report;
  const pct = validation_score;
  const color = scoreColor(pct);

  // Pie chart data for weight distribution
  const definition = stateDefinition || {};
  const features = definition.features || [];
  const weights = definition.weights || {};
  const weightPieData = features.map((f) => ({
    name: f, value: weights[f] || 0,
  })).filter((d) => d.value > 0);

  return (
    <div className="sv-page">
      {/* Header */}
      <div className="sv-header">
        <div className="sv-header-left">
          <button className="sv-back-btn" onClick={() => navigate(-1)}>← Back to Studio</button>
          <div>
            <h1 className="sv-title">Strategy Validation</h1>
            <p className="sv-subtitle">{report.strategy_name || strategyId}</p>
          </div>
        </div>
        <div className="sv-header-right">
          <button className="sv-btn-secondary" onClick={load}>↻ Re-run</button>
          <button
            className="sv-btn-primary"
            disabled={validationErrors && validationErrors.length > 0}
            onClick={() => setShowBacktestModal(true)}
            title={validationErrors?.length > 0 ? "Fix validation errors before backtesting" : ""}
          >
            ▶ Run Backtest
          </button>
        </div>
      </div>

      {/* Hero — Overall Score */}
      <div className="sv-hero">
        <div className="sv-gauge-wrap">
          <ResponsiveContainer width={220} height={220}>
            <RadialBarChart
              cx="50%" cy="50%"
              innerRadius="70%" outerRadius="90%"
              barSize={18}
              data={[{ value: pct, fill: color }]}
              startAngle={225} endAngle={-45}
            >
              <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
              <RadialBar background dataKey="value" cornerRadius={10} />
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="sv-gauge-label" style={{ color }}>
            <span className="sv-gauge-score">{pct.toFixed(0)}</span>
            <span className="sv-gauge-max">/100</span>
          </div>
          <div className={`sv-pass-badge ${passed ? "sv-badge-pass" : "sv-badge-fail"}`}>
            {passed ? "✓ Validated" : "✗ Not Validated"}
          </div>
        </div>

        <div className="sv-hero-right">
          <div className="sv-bias-tags">
            {(bias_tags || []).map((tag) => <BiasTag key={tag} tag={tag} />)}
          </div>
          <div className="sv-cat-summary">
            {(categories || []).map((cat) => (
              <div key={cat.category} className="sv-cat-mini">
                <span className="sv-cat-mini-name">{cat.category}</span>
                <div className="sv-cat-mini-bar">
                  <div
                    className="sv-cat-mini-fill"
                    style={{
                      width: `${(cat.score / cat.max_score) * 100}%`,
                      background: scoreColor((cat.score / cat.max_score) * 100),
                    }}
                  />
                </div>
                <span className="sv-cat-mini-pts" style={{ color: scoreColor((cat.score / cat.max_score) * 100) }}>
                  {cat.score.toFixed(0)}/{cat.max_score}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="sv-tabs">
        {["categories", "heatmap", "weights", "diagnostics"].map((tab) => (
          <button
            key={tab}
            className={`sv-tab ${activeTab === tab ? "sv-tab-active" : ""}`}
            onClick={() => setActiveTab(tab)}
          >
            {{ categories: "Category Breakdown", heatmap: "Correlation Matrix",
               weights: "Weight Distribution", diagnostics: "Diagnostics" }[tab]}
          </button>
        ))}
      </div>

      <div className="sv-tab-content">
        {/* CATEGORIES */}
        {activeTab === "categories" && (
          <div className="sv-cat-grid">
            {(categories || []).map((cat, i) => (
              <CategoryCard key={cat.category} cat={cat} index={i} />
            ))}
          </div>
        )}

        {/* HEATMAP */}
        {activeTab === "heatmap" && (
          <div className="sv-heatmap-section">
            <h3 className="sv-section-title">Feature Correlation Matrix (Pearson r)</h3>
            <p className="sv-section-desc">
              Red = high positive correlation (redundant features) · Blue = high negative · Dark = independent
            </p>
            <CorrelationHeatmap matrix={correlation_matrix} />
          </div>
        )}

        {/* WEIGHTS */}
        {activeTab === "weights" && (
          <div className="sv-weights-section">
            <h3 className="sv-section-title">Weight Distribution</h3>
            {weightPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={320}>
                <PieChart>
                  <Pie
                    data={weightPieData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%" cy="50%"
                    outerRadius={120}
                    label={({ name, value }) => `${name}: ${value}%`}
                  >
                    {weightPieData.map((_, i) => (
                      <Cell key={i} fill={WEIGHT_COLORS[i % WEIGHT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => `${v}%`} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="sv-empty-state">No features selected. Return to Strategy Studio to select features.</p>
            )}
          </div>
        )}

        {/* DIAGNOSTICS */}
        {activeTab === "diagnostics" && (
          <div className="sv-diag-section">
            {validationErrors?.length > 0 && (
              <div className="sv-diag-group sv-diag-errors">
                <h3 className="sv-diag-title">🚫 Blocking Errors</h3>
                <p className="sv-diag-subtitle">Must be resolved before backtest execution.</p>
                {validationErrors.map((e, i) => (
                  <div key={i} className="sv-diag-item sv-item-error">{e}</div>
                ))}
              </div>
            )}
            {warnings?.length > 0 && (
              <div className="sv-diag-group sv-diag-warnings">
                <h3 className="sv-diag-title">⚠ Warnings</h3>
                <p className="sv-diag-subtitle">Non-blocking — backtest will proceed but results may be affected.</p>
                {warnings.map((w, i) => (
                  <div key={i} className="sv-diag-item sv-item-warn">{w}</div>
                ))}
              </div>
            )}
            {recommendations?.length > 0 && (
              <div className="sv-diag-group sv-diag-recs">
                <h3 className="sv-diag-title">💡 Recommendations</h3>
                {recommendations.map((r, i) => (
                  <div key={i} className="sv-diag-item sv-item-rec">{r}</div>
                ))}
              </div>
            )}
            {!validationErrors?.length && !warnings?.length && !recommendations?.length && (
              <div className="sv-empty-state">
                <span style={{ fontSize: "3rem" }}>✓</span>
                <p>No issues detected. Strategy is ready for backtesting.</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Backtest Launch Modal */}
      {showBacktestModal && (
        <BacktestLaunchModal
          strategyId={strategyId}
          strategyName={report.strategy_name}
          onClose={() => setShowBacktestModal(false)}
          onLaunch={(runId) => navigate(`/backtest/${runId}`)}
        />
      )}
    </div>
  );
}

// ── Backtest Launch Modal ──────────────────────────────────────────────────────
import { runBacktest } from "../api/backtestApi";

function BacktestLaunchModal({ strategyId, strategyName, onClose, onLaunch }) {
  const [params, setParams] = useState({
    start_date: "2024-01-01",
    end_date: new Date().toISOString().slice(0, 10),
    benchmark: "NIFTY50",
    rebalance_freq: "Monthly",
    weighting_scheme: "Equal",
    initial_capital: 1000000,
    max_holdings: 15,
    transaction_cost: 0.001,
    slippage: 0.001,
  });
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);

  const launch = async () => {
    setRunning(true);
    setError(null);
    try {
      const { data } = await runBacktest({ ...params, strategy_id: strategyId });
      onLaunch(data.run_id);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    } finally {
      setRunning(false);
    }
  };

  const update = (key, val) => setParams((p) => ({ ...p, [key]: val }));

  return (
    <div className="sv-modal-overlay" onClick={(e) => e.target.classList.contains("sv-modal-overlay") && onClose()}>
      <div className="sv-modal">
        <div className="sv-modal-header">
          <h2>Launch Backtest — {strategyName}</h2>
          <button className="sv-modal-close" onClick={onClose}>×</button>
        </div>
        <div className="sv-modal-body">
          <div className="sv-form-grid">
            <label>Start Date<input type="date" value={params.start_date} onChange={(e) => update("start_date", e.target.value)} /></label>
            <label>End Date<input type="date" value={params.end_date} onChange={(e) => update("end_date", e.target.value)} /></label>
            <label>Benchmark
              <select value={params.benchmark} onChange={(e) => update("benchmark", e.target.value)}>
                <option value="NIFTY50">NIFTY 50</option>
                <option value="NIFTY500">NIFTY 500</option>
              </select>
            </label>
            <label>Rebalance Frequency
              <select value={params.rebalance_freq} onChange={(e) => update("rebalance_freq", e.target.value)}>
                <option value="Daily">Daily</option>
                <option value="Weekly">Weekly</option>
                <option value="Monthly">Monthly</option>
                <option value="Quarterly">Quarterly</option>
              </select>
            </label>
            <label>Weighting Scheme
              <select value={params.weighting_scheme} onChange={(e) => update("weighting_scheme", e.target.value)}>
                <option value="Equal">Equal Weight</option>
                <option value="ScoreWeighted">Score Weighted</option>
                <option value="RiskParity">Risk Parity</option>
                <option value="VolAdjusted">Volatility Adjusted</option>
              </select>
            </label>
            <label>Max Holdings
              <input type="number" min={2} max={50} value={params.max_holdings} onChange={(e) => update("max_holdings", +e.target.value)} />
            </label>
            <label>Initial Capital (₹)
              <input type="number" min={10000} step={100000} value={params.initial_capital} onChange={(e) => update("initial_capital", +e.target.value)} />
            </label>
            <label>Transaction Cost
              <input type="number" min={0} max={0.05} step={0.001} value={params.transaction_cost} onChange={(e) => update("transaction_cost", +e.target.value)} />
            </label>
          </div>
          {error && <div className="sv-modal-error">{error}</div>}
        </div>
        <div className="sv-modal-footer">
          <button className="sv-btn-secondary" onClick={onClose} disabled={running}>Cancel</button>
          <button className="sv-btn-primary" onClick={launch} disabled={running}>
            {running ? "Running simulation…" : "▶ Run Backtest"}
          </button>
        </div>
      </div>
    </div>
  );
}

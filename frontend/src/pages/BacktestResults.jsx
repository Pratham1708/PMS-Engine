/**
 * BacktestResults.jsx — Institutional Backtest Results Dashboard
 * Phase 14C: Triple-series equity curve, metrics cards, benchmark comparison,
 * trade log with attribution drawer, rolling stats, portfolio timeline.
 */

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, CartesianGrid, BarChart, Bar, ReferenceLine,
  AreaChart, Area,
} from "recharts";
import { getBacktestResult } from "../api/backtestApi";
import "./BacktestResults.css";

// ── Utilities ─────────────────────────────────────────────────────────────────
const fmt = (v, decimals = 2) =>
  v == null ? "—" : typeof v === "number" ? v.toFixed(decimals) : v;
const fmtPct = (v) => v == null ? "—" : `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
const fmtNum = (v, dec = 2) => v == null ? "—" : Number(v).toLocaleString("en-IN", { maximumFractionDigits: dec });
const deltaClass = (v, higherBetter = true) => {
  if (v == null) return "";
  const pos = v > 0;
  return (higherBetter ? pos : !pos) ? "delta-pos" : "delta-neg";
};

// ── Custom Tooltip ────────────────────────────────────────────────────────────
const EquityTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bt-tooltip">
      <div className="bt-tooltip-date">{label}</div>
      {payload.map((p) => (
        <div key={p.name} className="bt-tooltip-row" style={{ color: p.color }}>
          <span>{p.name}</span>
          <span>₹{fmtNum(p.value, 0)}</span>
        </div>
      ))}
    </div>
  );
};

// ── Metric Cards ──────────────────────────────────────────────────────────────
const MetricCard = ({ label, value, pmsValue, benchValue, unit = "%", higherBetter = true }) => {
  const diffPms = (typeof value === "number" && typeof pmsValue === "number")
    ? value - pmsValue : null;
  const diffBench = (typeof value === "number" && typeof benchValue === "number")
    ? value - benchValue : null;
  return (
    <div className="bt-metric-card">
      <div className="bt-metric-label">{label}</div>
      <div className="bt-metric-value">
        {fmt(value, 2)}{unit}
      </div>
      <div className="bt-metric-compare">
        {diffPms != null && (
          <span className={`bt-metric-delta ${deltaClass(diffPms, higherBetter)}`}>
            {diffPms >= 0 ? "+" : ""}{fmt(diffPms, 2)}{unit} vs PMS
          </span>
        )}
        {diffBench != null && (
          <span className={`bt-metric-delta ${deltaClass(diffBench, higherBetter)}`}>
            {diffBench >= 0 ? "+" : ""}{fmt(diffBench, 2)}{unit} vs {"\u24B7"}
          </span>
        )}
      </div>
    </div>
  );
};

// ── Trade Attribution Drawer ──────────────────────────────────────────────────
const TradeDrawer = ({ trade, onClose }) => {
  if (!trade) return null;
  const attr = trade.attribution || {};
  const isWin = trade.return_pct > 0;

  return (
    <div className="bt-drawer-overlay" onClick={(e) => e.target.classList.contains("bt-drawer-overlay") && onClose()}>
      <div className="bt-drawer">
        <div className="bt-drawer-header">
          <div>
            <h3>{trade.company_name || trade.symbol}</h3>
            <span className="bt-drawer-sym">{trade.symbol} · {trade.sector}</span>
          </div>
          <button className="bt-drawer-close" onClick={onClose}>×</button>
        </div>

        <div className="bt-drawer-summary">
          <div className={`bt-drawer-return ${isWin ? "bt-win" : "bt-loss"}`}>
            {fmtPct(trade.return_pct)}
          </div>
          <div className="bt-drawer-meta-grid">
            <div><span>Entry</span><strong>{trade.entry_date}</strong></div>
            <div><span>Exit</span><strong>{trade.exit_date}</strong></div>
            <div><span>Held</span><strong>{trade.holding_days}d</strong></div>
            <div><span>Entry Score</span><strong>{fmt(trade.entry_score)}</strong></div>
            <div><span>Exit Score</span><strong>{fmt(trade.exit_score)}</strong></div>
            <div><span>Entry Rating</span><strong>{trade.entry_rating}</strong></div>
          </div>
        </div>

        {attr.why_entered && (
          <div className="bt-attr-section">
            <div className="bt-attr-title">Why Entered</div>
            <p className="bt-attr-text">{attr.why_entered}</p>
          </div>
        )}
        {attr.why_exited && (
          <div className="bt-attr-section">
            <div className="bt-attr-title">Why Exited</div>
            <p className="bt-attr-text">{attr.why_exited}</p>
          </div>
        )}

        {attr.top_contributors?.length > 0 && (
          <div className="bt-attr-section">
            <div className="bt-attr-title">Top Contributing Features (Entry)</div>
            {attr.top_contributors.map((c, i) => (
              <div key={i} className="bt-contrib-row">
                <span className="bt-contrib-label">{c.label || c.feature_id}</span>
                <div className="bt-contrib-bar">
                  <div
                    className={`bt-contrib-fill ${c.contribution >= 0 ? "bt-contrib-pos" : "bt-contrib-neg"}`}
                    style={{ width: `${Math.min(Math.abs(c.contribution) * 400, 100)}%` }}
                  />
                </div>
                <span className={`bt-contrib-val ${c.contribution >= 0 ? "bt-win" : "bt-loss"}`}>
                  {c.contribution >= 0 ? "+" : ""}{fmt(c.contribution, 3)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ── Benchmark Comparison Table ────────────────────────────────────────────────
const ComparisonTable = ({ rows }) => {
  if (!rows?.length) return null;
  return (
    <div className="bt-table-wrap">
      <table className="bt-cmp-table">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Custom Strategy</th>
            <th>PMS Default</th>
            <th>Benchmark</th>
            <th>vs PMS</th>
            <th>vs Benchmark</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              <td className="bt-cmp-label">{row.metric_label}</td>
              <td className="bt-cmp-strategy">{fmt(row.strategy_value, 2)}</td>
              <td>{fmt(row.pms_default_value, 2)}</td>
              <td>{fmt(row.benchmark_value, 2)}</td>
              <td className={deltaClass(row.strategy_vs_default, row.higher_is_better)}>
                {row.strategy_vs_default >= 0 ? "+" : ""}{fmt(row.strategy_vs_default, 2)}
              </td>
              <td className={deltaClass(row.strategy_vs_benchmark, row.higher_is_better)}>
                {row.strategy_vs_benchmark >= 0 ? "+" : ""}{fmt(row.strategy_vs_benchmark, 2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ── Execution Log ─────────────────────────────────────────────────────────────
const ExecutionLog = ({ entries }) => (
  <div className="bt-execlog">
    {(entries || []).map((e, i) => (
      <div key={i} className={`bt-execlog-row bt-execlog-${e.integrity_status}`}>
        <div className="bt-execlog-date">{e.snapshot_date}</div>
        <div className={`bt-execlog-status`}>
          {e.integrity_status === "verified" ? "✓" : e.integrity_status === "warned" ? "⚠" : "✗"}
          {" "}{e.integrity_status}
        </div>
        <div className="bt-execlog-meta">
          <span>{e.stocks_scored} scored</span>
          <span>{e.buy_signals} buys ({e.buy_pct?.toFixed(0)}%)</span>
          <span>{e.trades_executed} trades</span>
          <span>₹{fmtNum(e.portfolio_value, 0)}</span>
        </div>
        {e.notes && <div className="bt-execlog-notes">{e.notes}</div>}
      </div>
    ))}
  </div>
);

// ── Versioning panel ──────────────────────────────────────────────────────────
const VersioningPanel = ({ v }) => {
  if (!v) return null;
  return (
    <div className="bt-version-panel">
      <div className="bt-version-title">Report Versioning</div>
      <div className="bt-version-grid">
        {Object.entries({
          "Backtest Version": v.backtest_version,
          "Engine Version": v.engine_version,
          "Strategy Version": v.strategy_version,
          "Snapshot Range": v.snapshot_version_range,
          "Feature Registry": v.feature_registry_version,
          "Model Version": v.model_version,
          "Generated": v.generated_at?.slice(0, 16),
        }).map(([k, val]) => (
          <div key={k} className="bt-version-row">
            <span className="bt-version-key">{k}</span>
            <span className="bt-version-val">{val || "—"}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// ── Main Component ────────────────────────────────────────────────────────────
const TABS = [
  { id: "overview", label: "Overview" },
  { id: "equity", label: "Equity Curve" },
  { id: "metrics", label: "Risk Metrics" },
  { id: "trades", label: "Trade Log" },
  { id: "comparison", label: "Comparison Table" },
  { id: "portfolio", label: "Portfolio Timeline" },
  { id: "execution", label: "Execution Log" },
];

export default function BacktestResults() {
  const { runId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [selectedTrade, setSelectedTrade] = useState(null);
  const [tradeSort, setTradeSort] = useState({ key: "return_pct", asc: false });
  const [tradeFilter, setTradeFilter] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data: d } = await getBacktestResult(runId);
      setData(d);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => { load(); }, [load]);

  if (loading) return (
    <div className="bt-page bt-loading">
      <div className="bt-spinner" />
      <p>Loading backtest results…</p>
    </div>
  );
  if (error) return (
    <div className="bt-page bt-error">
      <div style={{ fontSize: "2.5rem" }}>⚠</div>
      <h2>Error loading results</h2>
      <p>{error}</p>
      <button className="bt-btn-primary" onClick={load}>Retry</button>
    </div>
  );
  if (!data) return null;

  const cm = data.custom_metrics || {};
  const pm = data.pms_default_metrics || {};
  const bm = data.benchmark_metrics || {};
  const summary = data.summary || {};
  const versioning = data.versioning || {};

  // Summary cards config
  const summaryCards = [
    { label: "Total Return", value: summary.total_return_pct, pmsValue: summary.pms_total_return_pct, benchValue: summary.benchmark_total_return_pct },
    { label: "CAGR", value: summary.cagr_pct, pmsValue: summary.pms_cagr_pct, benchValue: summary.benchmark_cagr_pct },
    { label: "Sharpe Ratio", value: summary.sharpe_ratio, pmsValue: summary.pms_sharpe_ratio, benchValue: summary.benchmark_sharpe_ratio, unit: "×" },
    { label: "Sortino Ratio", value: summary.sortino_ratio, unit: "×" },
    { label: "Max Drawdown", value: summary.max_drawdown_pct, pmsValue: summary.pms_max_drawdown_pct, benchValue: summary.benchmark_max_drawdown_pct, higherBetter: false },
    { label: "Win Rate", value: summary.win_rate_pct },
    { label: "Profit Factor", value: summary.profit_factor, unit: "×" },
    { label: "Alpha", value: summary.alpha_pct },
    { label: "Beta", value: summary.beta, unit: "×", higherBetter: false },
  ];

  // Trade log filtering/sorting
  const filteredTrades = (data.trade_log || [])
    .filter((t) => !tradeFilter || t.symbol.toLowerCase().includes(tradeFilter.toLowerCase()) ||
      t.company_name?.toLowerCase().includes(tradeFilter.toLowerCase()))
    .sort((a, b) => {
      const av = a[tradeSort.key], bv = b[tradeSort.key];
      return tradeSort.asc ? av - bv : bv - av;
    });

  const sortTrade = (key) => {
    setTradeSort((s) => ({ key, asc: s.key === key ? !s.asc : false }));
  };

  return (
    <div className="bt-page">
      {/* Header */}
      <div className="bt-header">
        <div className="bt-header-left">
          <button className="bt-back-btn" onClick={() => navigate(-1)}>← Back</button>
          <div>
            <h1 className="bt-title">Backtest Results</h1>
            <p className="bt-subtitle">
              {data.strategy_name} · {data.start_date} → {data.end_date} · {data.rebalance_freq} · {data.benchmark}
            </p>
          </div>
        </div>
        <div className="bt-header-badges">
          <span className="bt-badge bt-badge-blue">{data.weighting_scheme}</span>
          <span className="bt-badge bt-badge-purple">{data.snapshots_used} snapshots</span>
          <span className={`bt-badge ${data.status === "completed" ? "bt-badge-green" : "bt-badge-red"}`}>
            {data.status}
          </span>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="bt-summary-grid">
        {summaryCards.map((c, i) => (
          <MetricCard key={i} {...c} />
        ))}
      </div>

      {/* Tabs */}
      <div className="bt-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`bt-tab ${activeTab === tab.id ? "bt-tab-active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="bt-tab-content">
        {/* OVERVIEW */}
        {activeTab === "overview" && (
          <div className="bt-overview">
            <div className="bt-equity-preview">
              <h3 className="bt-section-title">Equity Curve — Strategy vs PMS Default vs Benchmark</h3>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={data.equity_curve || []} margin={{ left: 20, right: 20, top: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#475569" }} tickFormatter={(d) => d?.slice(5)} />
                  <YAxis tick={{ fontSize: 11, fill: "#475569" }} tickFormatter={(v) => `₹${(v/100000).toFixed(1)}L`} />
                  <Tooltip content={<EquityTooltip />} />
                  <Legend />
                  <Line type="monotone" dataKey="custom" name="Custom Strategy" stroke="#6366f1" strokeWidth={2.5} dot={false} />
                  <Line type="monotone" dataKey="pms_default" name="PMS Default" stroke="#10b981" strokeWidth={1.5} dot={false} strokeDasharray="6 3" />
                  <Line type="monotone" dataKey="benchmark" name={data.benchmark} stroke="#475569" strokeWidth={1.5} dot={false} strokeDasharray="3 3" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="bt-overview-bottom">
              <div className="bt-wl-section">
                <h3 className="bt-section-title">Win / Loss Distribution</h3>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={data.win_loss_histogram || []} margin={{ bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="bucket" tick={{ fontSize: 9, fill: "#475569" }} />
                    <YAxis tick={{ fontSize: 10, fill: "#475569" }} />
                    <Tooltip />
                    <Bar dataKey="count" name="Trades"
                      fill="#6366f1"
                      shape={(props) => {
                        const { x, y, width, height, payload } = props;
                        const color = payload.low >= 0 ? "#10b981" : "#ef4444";
                        return <rect x={x} y={y} width={width} height={height} fill={color} rx={3} />;
                      }}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="bt-quick-metrics">
                <h3 className="bt-section-title">Quick Stats</h3>
                <div className="bt-qm-grid">
                  {[
                    { label: "Total Trades", value: cm.trades?.total_trades, unit: "" },
                    { label: "Avg Holding", value: cm.trades?.avg_holding_days, unit: "d" },
                    { label: "Avg Win", value: cm.trades?.avg_win_pct, unit: "%" },
                    { label: "Avg Loss", value: cm.trades?.avg_loss_pct, unit: "%" },
                    { label: "Expectancy", value: cm.trades?.expectancy_pct, unit: "%" },
                    { label: "Avg Turnover", value: cm.portfolio?.avg_turnover_pct, unit: "%" },
                    { label: "Information Ratio", value: cm.risk?.information_ratio, unit: "×" },
                    { label: "Calmar Ratio", value: cm.risk?.calmar_ratio, unit: "×" },
                  ].map((s, i) => (
                    <div key={i} className="bt-qm-row">
                      <span>{s.label}</span>
                      <strong className={s.value != null && s.value < 0 ? "bt-neg" : "bt-pos"}>
                        {fmt(s.value, 2)}{s.unit}
                      </strong>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <VersioningPanel v={versioning} />
          </div>
        )}

        {/* EQUITY CURVE */}
        {activeTab === "equity" && (
          <div>
            <h3 className="bt-section-title">Full Equity Curve</h3>
            <ResponsiveContainer width="100%" height={440}>
              <AreaChart data={data.equity_curve || []} margin={{ left: 20, right: 20, top: 10, bottom: 10 }}>
                <defs>
                  <linearGradient id="gCustom" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gPms" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#475569" }} tickFormatter={(d) => d?.slice(0, 7)} />
                <YAxis tick={{ fontSize: 10, fill: "#475569" }} tickFormatter={(v) => `₹${(v/100000).toFixed(0)}L`} />
                <Tooltip content={<EquityTooltip />} />
                <Legend />
                <Area type="monotone" dataKey="custom" name="Custom Strategy" stroke="#6366f1" fill="url(#gCustom)" strokeWidth={2.5} dot={false} />
                <Area type="monotone" dataKey="pms_default" name="PMS Default" stroke="#10b981" fill="url(#gPms)" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="benchmark" name="Benchmark" stroke="#475569" strokeWidth={1.5} dot={false} strokeDasharray="4 4" />
              </AreaChart>
            </ResponsiveContainer>

            <h3 className="bt-section-title" style={{ marginTop: 28 }}>Drawdown Curve</h3>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart
                data={(cm.drawdown?.drawdown_curve || []).map((d, i) => ({
                  ...d,
                  pms_dd: pm.drawdown?.drawdown_curve?.[i]?.drawdown_pct ?? 0,
                }))}
                margin={{ left: 20, right: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" tick={{ fontSize: 9, fill: "#475569" }} tickFormatter={(d) => d?.slice(0, 7)} />
                <YAxis tick={{ fontSize: 9, fill: "#475569" }} tickFormatter={(v) => `${v.toFixed(0)}%`} />
                <Tooltip formatter={(v) => `${v.toFixed(2)}%`} />
                <ReferenceLine y={0} stroke="#334155" />
                <Area type="monotone" dataKey="drawdown_pct" name="Custom DD" stroke="#ef4444" fill="rgba(239,68,68,0.15)" dot={false} />
                <Area type="monotone" dataKey="pms_dd" name="PMS DD" stroke="#f97316" fill="rgba(249,115,22,0.08)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* RISK METRICS */}
        {activeTab === "metrics" && (
          <div>
            <h3 className="bt-section-title">Risk & Return Metrics — All Three Series</h3>
            <div className="bt-metrics-triple">
              {[
                { label: "Custom Strategy", m: cm, color: "#6366f1" },
                { label: "PMS Default", m: pm, color: "#10b981" },
                { label: data.benchmark, m: bm, color: "#475569" },
              ].map(({ label, m, color }) => (
                <div key={label} className="bt-metrics-col" style={{ borderTopColor: color }}>
                  <div className="bt-metrics-col-label" style={{ color }}>{label}</div>
                  {[
                    ["CAGR", m.returns?.cagr_pct, "%"],
                    ["Total Return", m.returns?.total_return_pct, "%"],
                    ["Volatility", m.risk?.annualized_volatility_pct, "%"],
                    ["Sharpe", m.risk?.sharpe_ratio, "×"],
                    ["Sortino", m.risk?.sortino_ratio, "×"],
                    ["Calmar", m.risk?.calmar_ratio, "×"],
                    ["Beta", m.risk?.beta, "×"],
                    ["Alpha", m.risk?.alpha_pct, "%"],
                    ["Info Ratio", m.risk?.information_ratio, "×"],
                    ["Max Drawdown", m.drawdown?.max_drawdown_pct, "%"],
                    ["Max Recovery", m.drawdown?.max_recovery_days, "d"],
                    ["Win Rate", m.trades?.win_rate_pct, "%"],
                    ["Profit Factor", m.trades?.profit_factor, "×"],
                    ["Expectancy", m.trades?.expectancy_pct, "%"],
                  ].map(([name, val, unit]) => (
                    <div key={name} className="bt-metrics-row">
                      <span>{name}</span>
                      <strong className={val != null && val < 0 ? "bt-neg" : ""}>{fmt(val, 2)}{unit}</strong>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TRADES */}
        {activeTab === "trades" && (
          <div>
            <div className="bt-trade-toolbar">
              <input
                className="bt-trade-search"
                placeholder="Search symbol or company…"
                value={tradeFilter}
                onChange={(e) => setTradeFilter(e.target.value)}
              />
              <span className="bt-trade-count">{filteredTrades.length} trades</span>
            </div>
            <div className="bt-table-wrap">
              <table className="bt-trade-table">
                <thead>
                  <tr>
                    {[
                      ["symbol", "Symbol"],
                      ["entry_date", "Entry"],
                      ["exit_date", "Exit"],
                      ["holding_days", "Days"],
                      ["entry_score", "Entry Score"],
                      ["return_pct", "Return %"],
                    ].map(([key, label]) => (
                      <th
                        key={key}
                        className={`bt-sort-col ${tradeSort.key === key ? "bt-sort-active" : ""}`}
                        onClick={() => sortTrade(key)}
                      >
                        {label} {tradeSort.key === key ? (tradeSort.asc ? "▲" : "▼") : ""}
                      </th>
                    ))}
                    <th>Entry Rating</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTrades.map((t, i) => (
                    <tr key={i} className="bt-trade-row" onClick={() => setSelectedTrade(t)}>
                      <td>
                        <div className="bt-trade-sym">{t.symbol}</div>
                        <div className="bt-trade-co">{t.company_name}</div>
                      </td>
                      <td>{t.entry_date}</td>
                      <td>{t.exit_date}</td>
                      <td>{t.holding_days}d</td>
                      <td>{fmt(t.entry_score)}</td>
                      <td className={t.return_pct >= 0 ? "bt-win" : "bt-loss"}>
                        {fmtPct(t.return_pct)}
                      </td>
                      <td>
                        <span className={`bt-rating-badge bt-rating-${t.entry_rating?.replace(" ", "-").toLowerCase()}`}>
                          {t.entry_rating}
                        </span>
                      </td>
                      <td><button className="bt-attr-btn">Details →</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* COMPARISON */}
        {activeTab === "comparison" && (
          <div>
            <h3 className="bt-section-title">Benchmark Comparison Table</h3>
            <p style={{ color: "#64748b", fontSize: "0.86rem", marginBottom: "16px" }}>
              Custom Strategy vs PMS Default vs {data.benchmark}.
              Green = outperforming; Red = underperforming.
            </p>
            <ComparisonTable rows={data.benchmark_comparison_table} />
          </div>
        )}

        {/* PORTFOLIO TIMELINE */}
        {activeTab === "portfolio" && (
          <div>
            <h3 className="bt-section-title">Portfolio Timeline</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart
                data={(data.portfolio_timeline || []).slice(-24)}
                margin={{ left: 20, right: 20, top: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" tick={{ fontSize: 9, fill: "#475569" }} tickFormatter={(d) => d?.slice(5)} />
                <YAxis tick={{ fontSize: 9, fill: "#475569" }} />
                <Tooltip />
                <Bar dataKey="num_positions" name="# Holdings" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>

            <div className="bt-portfolio-cards">
              {(data.portfolio_timeline || []).slice(-6).reverse().map((e, i) => (
                <div key={i} className="bt-port-card">
                  <div className="bt-port-date">{e.date}</div>
                  <div className="bt-port-val">₹{fmtNum(e.portfolio_value, 0)}</div>
                  <div className="bt-port-meta">
                    <span>{e.num_positions} positions</span>
                    <span>Cash: {e.cash_pct?.toFixed(1)}%</span>
                    <span>Turnover: {e.turnover_pct?.toFixed(1)}%</span>
                  </div>
                  {e.top_holdings?.slice(0, 3).map((h, j) => (
                    <div key={j} className="bt-port-holding">
                      <span>{h.symbol}</span>
                      <span className="bt-port-w">{(h.weight * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* EXECUTION LOG */}
        {activeTab === "execution" && (
          <div>
            <h3 className="bt-section-title">Snapshot Execution Log</h3>
            <p style={{ color: "#64748b", fontSize: "0.86rem", marginBottom: 12 }}>
              Every snapshot used in the simulation. Integrity checks shown per period.
            </p>
            <ExecutionLog entries={data.execution_log} />
          </div>
        )}
      </div>

      {/* Trade Attribution Drawer */}
      {selectedTrade && (
        <TradeDrawer trade={selectedTrade} onClose={() => setSelectedTrade(null)} />
      )}
    </div>
  );
}

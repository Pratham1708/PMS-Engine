/**
 * BacktestHistory.jsx — Institutional Backtest Run Archive
 * Phase 14C: View all historical simulation runs, statuses, metrics summary,
 * and link to detailed reports.
 */

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { listBacktestHistory, deleteBacktestRun } from "../api/backtestApi";
import "./BacktestHistory.css";

const fmt = (v) => v == null ? "—" : typeof v === "number" ? v.toFixed(2) : v;

export default function BacktestHistory() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await listBacktestHistory();
      setRuns(data || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e, runId) => {
    e.stopPropagation();
    if (window.confirm("Permanently delete this backtest run and its reports?")) {
      try {
        await deleteBacktestRun(runId);
        setRuns((prev) => prev.filter((r) => r.run_id !== runId));
      } catch (err) {
        alert("Failed to delete run: " + err.message);
      }
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return (
    <div className="bth-page bth-loading">
      <div className="bth-spinner" />
      <p>Loading backtest runs history…</p>
    </div>
  );

  return (
    <div className="bth-page">
      <div className="bth-header">
        <div>
          <h1 className="bth-title">🧪 Backtest Engine</h1>
          <p className="bth-subtitle">Archive of quantitative strategy simulation reports</p>
        </div>
        <button className="bth-btn-primary" onClick={() => navigate("/studio")}>
          🎨 Design New Strategy
        </button>
      </div>

      {error && <div className="bth-error">Error: {error}</div>}

      {runs.length === 0 ? (
        <div className="bth-empty">
          <div className="bth-empty-icon">🧪</div>
          <h3>No Backtest Runs Found</h3>
          <p>Go to the Strategy Studio, select a strategy, and click "Validate" then "Run Backtest".</p>
          <button className="bth-btn-primary" onClick={() => navigate("/studio")}>
            Go to Strategy Studio
          </button>
        </div>
      ) : (
        <div className="bth-list-wrap table-scroll-container">
          <table className="bth-table">
            <thead>
              <tr>
                <th>Strategy Name</th>
                <th>Rebalance</th>
                <th>Benchmark</th>
                <th>Date Range</th>
                <th>Total Return</th>
                <th>CAGR</th>
                <th>Sharpe</th>
                <th>Max DD</th>
                <th>Status</th>
                <th>Executed At</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => {
                const s = r.summary || {};
                return (
                  <tr key={r.run_id} className="bth-row" onClick={() => navigate(`/backtest/${r.run_id}`)}>
                    <td>
                      <div className="bth-strat-name">{r.strategy_name}</div>
                      <div className="bth-run-id">{r.run_id.slice(0, 8)}…</div>
                    </td>
                    <td>{r.rebalance_freq}</td>
                    <td>{r.benchmark}</td>
                    <td className="bth-date-range">
                      {r.start_date} → {r.end_date}
                    </td>
                    <td className={`bth-metric ${s.total_return_pct >= 0 ? "bth-pos" : "bth-neg"}`}>
                      {s.total_return_pct != null ? `${s.total_return_pct >= 0 ? "+" : ""}${s.total_return_pct.toFixed(1)}%` : "—"}
                    </td>
                    <td className={`bth-metric ${s.cagr_pct >= 0 ? "bth-pos" : "bth-neg"}`}>
                      {s.cagr_pct != null ? `${s.cagr_pct.toFixed(1)}%` : "—"}
                    </td>
                    <td className="bth-metric font-mono">
                      {s.sharpe_ratio != null ? `${s.sharpe_ratio.toFixed(2)}×` : "—"}
                    </td>
                    <td className="bth-metric bth-neg">
                      {s.max_drawdown_pct != null ? `${s.max_drawdown_pct.toFixed(1)}%` : "—"}
                    </td>
                    <td>
                      <span className={`bth-status bth-status-${r.status.toLowerCase()}`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="bth-time">{r.created_at?.slice(0, 16).replace("T", " ")}</td>
                    <td>
                      <button className="bth-delete-btn" onClick={(e) => handleDelete(e, r.run_id)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

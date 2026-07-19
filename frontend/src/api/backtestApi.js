/**
 * backtestApi.js — Axios wrappers for Phase 14C Backtest & Validation endpoints.
 */

import axios from "axios";

const BASE = "/api/backtest";

/** Launch a backtest run. Returns full BacktestDetailResponse. */
export const runBacktest = (params) => axios.post(`${BASE}/run`, params);

/** Get full backtest result by run_id. */
export const getBacktestResult = (runId) => axios.get(`${BASE}/${runId}`);

/** List backtest history. Optional strategyId filter. */
export const listBacktestHistory = (strategyId) =>
  axios.get(`${BASE}/history`, { params: strategyId ? { strategy_id: strategyId } : {} });

/** Delete a backtest run. */
export const deleteBacktestRun = (runId) => axios.delete(`${BASE}/${runId}`);

/** Run strategy validation only (no simulation). */
export const validateStrategy = (payload) => axios.post(`${BASE}/validate`, payload);

/** Download report URL (for opening in new tab or FileResponse). */
export const getReportUrl = (runId, format = "json") =>
  `${BASE}/${runId}/report?format=${format}`;

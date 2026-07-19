import client from "./client";

const BASE = "/backtest";

/** Launch a backtest run. Returns full BacktestDetailResponse. */
export const runBacktest = (params) => client.post(`${BASE}/run`, params);

/** Get full backtest result by run_id. */
export const getBacktestResult = (runId) => client.get(`${BASE}/${runId}`);

/** List backtest history. Optional strategyId filter. */
export const listBacktestHistory = (strategyId) =>
  client.get(`${BASE}/history`, { params: strategyId ? { strategy_id: strategyId } : {} });

/** Delete a backtest run. */
export const deleteBacktestRun = (runId) => client.delete(`${BASE}/${runId}`);

/** Run strategy validation only (no simulation). */
export const validateStrategy = (payload) => client.post(`${BASE}/validate`, payload);

/** Download report URL (for opening in new tab or FileResponse). */
export const getReportUrl = (runId, format = "json") =>
  `${client.defaults.baseURL || "/api"}${BASE}/${runId}/report?format=${format}`;


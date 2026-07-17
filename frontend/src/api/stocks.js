import client from './client';

// Core Stock Data Endpoints
export const fetchStocks = (params = {}) => client.get('/stocks', { params });
export const fetchStock = (symbol) => client.get(`/stock/${encodeURIComponent(symbol)}`);
export const fetchDashboard = () => client.get('/dashboard');
export const fetchPortfolio = (capital) => client.get('/portfolio', { params: { capital } });
export const fetchTopBuys = (limit = 10) => client.get('/top-buys', { params: { limit } });
export const fetchTopSells = (limit = 10) => client.get('/top-sells', { params: { limit } });
export const fetchRatingsDistribution = () => client.get('/ratings-distribution');
export const fetchScannerSummary = () => client.get('/scanner-summary');
export const refreshScanner = () => client.post('/refresh');

// Personalized Research Workspace & Stock Interest Endpoints
export const fetchMyStocks = () => client.get('/mystocks');
export const addToMyStocks = (symbol) => client.post('/mystocks', { symbol });
export const deleteFromMyStocks = (symbol) => client.delete(`/mystocks/${encodeURIComponent(symbol)}`);
export const fetchRecentAnalysis = () => client.get('/recent-analysis');
export const fetchAnalysisHistory = (symbol) => client.get(`/analysis-history/${encodeURIComponent(symbol)}`);
export const fetchCompanyProfile = (symbol) => client.get(`/company/${encodeURIComponent(symbol)}`);
export const fetchResearchWorkspace = () => client.get('/research-workspace');
export const runAnalysis = (symbol) => client.post(`/analyze/${encodeURIComponent(symbol)}`);

// ── Phase 13 Daily Snapshot Publishing Platform ──────────────────────────────

// Pipeline Control
export const triggerSnapshotGeneration = () => client.post('/snapshot/generate');
export const triggerLiveAnalysis = () => client.post('/snapshot/live-analysis');
export const fetchPipelineStatus = () => client.get('/snapshot/pipeline/status');
export const fetchPipelineTimeline = (snapshotId) => client.get(`/snapshot/pipeline/${encodeURIComponent(snapshotId)}`);

// System Status
export const fetchSnapshotStatus = () => client.get('/snapshot/status');

// Latest Snapshot
export const fetchLatestSnapshot = () => client.get('/snapshot/latest');
export const fetchLatestSnapshotSummary = () => client.get('/snapshot/latest/summary');
export const fetchLatestStocks = () => client.get('/snapshot/latest/stocks');
export const fetchLatestStock = (symbol) => client.get(`/snapshot/latest/stock/${encodeURIComponent(symbol)}`);
export const fetchLatestBreadth = () => client.get('/snapshot/latest/breadth');
export const fetchLatestSectors = () => client.get('/snapshot/latest/sectors');
export const fetchLatestWatchlists = () => client.get('/snapshot/latest/watchlists');
export const fetchLatestWatchlist = (name) => client.get(`/snapshot/latest/watchlist/${encodeURIComponent(name)}`);
export const fetchLatestChanges = (changeType, significantOnly) => {
  const params = {};
  if (changeType) params.change_type = changeType;
  if (significantOnly) params.significant_only = true;
  return client.get('/snapshot/latest/changes', { params });
};
export const fetchLatestValidation = () => client.get('/snapshot/latest/validation');
export const fetchLatestPipeline = () => client.get('/snapshot/latest/pipeline');
export const fetchLatestReports = () => client.get('/snapshot/latest/reports');
export const fetchLatestDataQuality = () => client.get('/snapshot/latest/data-quality');

// Historical Archive
export const fetchSnapshotDates = (limit = 365) => client.get('/snapshot/dates', { params: { limit } });
export const fetchSnapshotByDate = (date) => client.get(`/snapshot/${date}`);
export const fetchSnapshotStocksByDate = (date) => client.get(`/snapshot/${date}/stocks`);
export const fetchSnapshotBreadthByDate = (date) => client.get(`/snapshot/${date}/breadth`);
export const fetchSnapshotSectorsByDate = (date) => client.get(`/snapshot/${date}/sectors`);
export const fetchSnapshotChangesByDate = (date) => client.get(`/snapshot/${date}/changes`);
export const fetchSnapshotValidationByDate = (date) => client.get(`/snapshot/${date}/validation`);
export const fetchSnapshotPipelineByDate = (date) => client.get(`/snapshot/${date}/pipeline`);
export const fetchSnapshotReportsByDate = (date) => client.get(`/snapshot/${date}/reports`);

// Comparison
export const fetchCompareSnapshots = (date1, date2) =>
  client.get('/snapshot/compare', { params: { date1, date2 } });
export const fetchCompareStock = (symbol, limit = 90) =>
  client.get('/snapshot/compare/stock', { params: { symbol, limit } });

// Explainability Engine
export const fetchExplainScore = (scoreType, symbol, strategyId = null) => {
  const params = {};
  if (symbol) params.symbol = symbol;
  if (strategyId) params.strategy_id = strategyId;
  return client.get(`/explain/${scoreType}`, { params });
};

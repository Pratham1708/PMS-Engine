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

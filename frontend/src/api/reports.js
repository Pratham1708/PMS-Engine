import client from './client';

export const generateStockReport = (symbol) =>
  client.get(`/reports/stock/${encodeURIComponent(symbol)}`);

export const generateWorkspaceReport = () =>
  client.get('/reports/workspace');

export const generateMarketReport = () =>
  client.get('/reports/market');

export const listReports = () =>
  client.get('/reports/list');

export const getReportPreviewUrl = (reportId) =>
  `${client.defaults.baseURL}/reports/preview/${encodeURIComponent(reportId)}`;

export const getReportDownloadUrl = (reportId, format = 'pdf') =>
  `${client.defaults.baseURL}/reports/download/${encodeURIComponent(reportId)}?format=${format}`;

// Direct Export URLs
export const getDirectStockReportUrl = (symbol, format = 'pdf') =>
  `${client.defaults.baseURL}/reports/stock/${encodeURIComponent(symbol)}/${format}`;

export const getDirectWorkspaceReportUrl = (format = 'pdf') =>
  `${client.defaults.baseURL}/reports/workspace/${format}`;

export const getDirectMarketReportUrl = (format = 'pdf') =>
  `${client.defaults.baseURL}/reports/market/${format}`;

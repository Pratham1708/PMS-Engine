import client from './client';

export const fetchStrategies = () => client.get('/strategies');
export const fetchStrategy = (id) => client.get(`/strategies/${id}`);
export const createStrategy = (data) => client.post('/strategies', data);
export const updateStrategy = (id, data) => client.put(`/strategies/${id}`, data);
export const deleteStrategy = (id) => client.delete(`/strategies/${id}`);
export const duplicateStrategy = (id, newName = null) => {
  const params = {};
  if (newName) params.new_name = newName;
  return client.post(`/strategies/${id}/duplicate`, null, { params });
};

export const fetchFeaturesRegistry = () => client.get('/strategies/features/registry');
export const validateStrategy = (definition) => client.post('/strategies/validate', definition);
export const previewStrategyExplain = (definition, symbol, snapshotId = null) => {
  const params = {};
  if (snapshotId) params.snapshot_id = snapshotId;
  params.symbol = symbol;
  return client.post('/strategies/preview', definition, { params });
};
export const executeStrategyScoring = (definition, snapshotId = null) => {
  const params = {};
  if (snapshotId) params.snapshot_id = snapshotId;
  return client.post('/strategies/execute', definition, { params });
};

/**
 * Test a strategy against a single stock.
 * Returns: { symbol, strategy_score, recommendation, confidence, rank, total_stocks, feature_breakdown, ... }
 */
export const testStockStrategy = (strategy, symbol, snapshotId = null) =>
  client.post('/strategies/test-stock', { strategy, symbol, snapshot_id: snapshotId });

/**
 * Fetch available historical snapshot IDs and dates for the Historical tab.
 */
export const fetchSnapshotsList = (limit = 10) =>
  client.get('/strategies/snapshots/list', { params: { limit } });

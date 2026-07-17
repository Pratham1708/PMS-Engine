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

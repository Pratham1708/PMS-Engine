import client from './client';

// Indicators
export const getIndicators = () => client.get('/lab/indicators');
export const runIndicatorBacktest = (data) => client.post('/lab/indicator/run', data);
export const getExperimentStatus = (id) => client.get(`/lab/indicator/status/${id}`);
export const getIndicatorResult = (id) => client.get(`/lab/indicator/result/${id}`);
export const runIndicatorOptimize = (data) => client.post('/lab/indicator/optimize', data);
export const getOptimizeResult = (id) => client.get(`/lab/indicator/optimize/result/${id}`);
export const compareIndicators = (ids) => client.get(`/lab/indicator/compare?ids=${encodeURIComponent(ids)}`);

// Engine validation
export const validateEngine = (data) => client.post('/lab/engine/validate', data || {});
export const getEngineResult = (id) => client.get(`/lab/engine/result/${id}`);
export const getScoreDistribution = (scoreCol) => client.get(`/lab/engine/score-distribution?score_column=${encodeURIComponent(scoreCol)}`);

// Models
export const listModels = () => client.get('/lab/models/list');
export const compareModels = (data) => client.post('/lab/models/compare', data || {});
export const getModelResult = (id) => client.get(`/lab/models/result/${id}`);
export const getModelCalibration = (model) => client.get(`/lab/models/calibration/${model}`);
export const getModelStability = (model) => client.get(`/lab/models/stability/${model}`);
export const getFeatureImportance = () => client.get('/lab/models/feature-importance');
export const getModelRegimePerf = (model) => client.get(`/lab/models/regime-performance/${model}`);

// Features
export const getFeatureImportancePermutation = () => client.get('/lab/features/importance');
export const getFeatureCorrelation = () => client.get('/lab/features/correlation');
export const getFeatureMI = () => client.get('/lab/features/mutual-information');
export const getFeatureVIF = () => client.get('/lab/features/vif');
export const getFeatureShap = () => client.get('/lab/features/shap-proxy');
export const getFeatureDrift = () => client.get('/lab/features/drift');
export const getFeatureRedundancy = () => client.get('/lab/features/redundancy');
export const getFeatureStability = () => client.get('/lab/features/stability');
export const getFullFeatureAnalysis = () => client.get('/lab/features/full-analysis');

// Composite
export const getCompositeAnalysis = () => client.get('/lab/composite/current-analysis');
export const optimizeWeights = (data) => client.post('/lab/composite/optimize-weights', data);
export const getWeightOptResult = (id) => client.get(`/lab/composite/optimize-result/${id}`);
export const getRegimeWeights = () => client.get('/lab/composite/regime-weights');
export const getWeightSnapshots = (expId) => client.get(`/lab/composite/snapshots?exp_id=${encodeURIComponent(expId)}`);

// Validation (Recommendation Audit)
export const populateAuditQueue = () => client.post('/lab/validation/populate', {});
export const processValidations = (data) => client.post('/lab/validation/process', data || {});
export const getValidationDashboard = () => client.get('/lab/validation/dashboard');
export const getSymbolValidation = (sym) => client.get(`/lab/validation/symbol/${encodeURIComponent(sym)}`);
export const getValidationTrend = () => client.get('/lab/validation/trend');

// Portfolio
export const getPortfolioStrategies = () => client.get('/lab/portfolio/strategies');
export const runPortfolioBacktest = (data) => client.post('/lab/portfolio/backtest', data);
export const getPortfolioResult = (id) => client.get(`/lab/portfolio/result/${id}`);
export const comparePortfolioStrategies = (ids) => client.get(`/lab/portfolio/compare?ids=${encodeURIComponent(ids)}`);

// Market (regimes, sector)
export const detectRegimes = (data) => client.post('/lab/regime/detect', data);
export const getRegimeResult = (id) => client.get(`/lab/regime/result/${id}`);
export const getSectorAnalysis = () => client.get('/lab/sector/analysis');
export const runSectorReturns = (data) => client.post('/lab/sector/returns', data);
export const getSectorResult = (id) => client.get(`/lab/sector/result/${id}`);
export const runBenchmarkCompare = (data) => client.post('/lab/benchmark/compare', data);
export const getBenchmarkResult = (id) => client.get(`/lab/benchmark/result/${id}`);

// Experiments
export const listExperiments = (params) => client.get('/lab/experiments', { params });
export const getExperimentDetail = (id) => client.get(`/lab/experiments/${id}`);
export const deleteExperiment = (id) => client.delete(`/lab/experiments/${id}`);
export const exportExperimentUrl = (id) => `${client.defaults.baseURL}/lab/experiments/${encodeURIComponent(id)}/export`;
export const getExperimentsSummary = () => client.get('/lab/experiments/summary');

// Reports
export const generateLabReport = (data) => client.post('/lab/reports/generate', data);
export const listLabReports = () => client.get('/lab/reports');
export const getLabReportHtmlUrl = (id) => `${client.defaults.baseURL}/lab/reports/${encodeURIComponent(id)}/html`;
export const getLabReportPdfUrl = (id) => `${client.defaults.baseURL}/lab/reports/${encodeURIComponent(id)}/pdf`;
export const getLabReportPreviewUrl = (id) => `${client.defaults.baseURL}/lab/reports/${encodeURIComponent(id)}/preview`;

// Quant Lab Extensions Endpoints
export const runCrossIndicator = (data) => client.post('/lab/cross-indicator/run', data);
export const runEnsemble = (data) => client.post('/lab/ensemble/run', data);
export const runHyperopt = (data) => client.post('/lab/hyperopt/run', data);
export const runMonteCarlo = (data) => client.post('/lab/monte-carlo/run', data);
export const runStressTest = (data) => client.post('/lab/stress-test/run', data);
export const runPositionSizing = (data) => client.post('/lab/position-sizing/run', data);
export const runPortfolioConstruction = (data) => client.post('/lab/portfolio-construction/run', data);
export const getCorrelationLab = (sym, per) => client.get(`/lab/correlation/run?symbol=${encodeURIComponent(sym)}&period=${encodeURIComponent(per)}`);
export const getMarketBreadth = (per) => client.get(`/lab/breadth/run?period=${encodeURIComponent(per)}`);
export const getLiquidityResearch = (sym) => client.get(`/lab/liquidity/run?symbol=${encodeURIComponent(sym)}`);
export const getDriftMonitor = () => client.get('/lab/drift/run');
export const getDriftAlerts = () => client.get('/lab/drift/alerts');

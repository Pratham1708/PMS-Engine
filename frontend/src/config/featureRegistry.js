// Feature Registry — Central metadata for platform capabilities across Landing, Feature Cards, Workspace & Knowledge Center
export const FEATURE_REGISTRY = [
  {
    id: 'snapshot-engine',
    title: 'Snapshot Engine',
    tagline: 'Immutable Daily Market Snapshots',
    description: 'Generates point-in-time quantitative snapshots with historical audit trail and zero lookahead bias.',
    icon: 'Camera',
    category: 'Pipeline',
    route: '/archive'
  },
  {
    id: 'quant-studio',
    title: 'Quant Strategy Studio',
    tagline: 'Custom Factor & Strategy Builder',
    description: 'Construct multi-factor quantitative strategies with weight controls, risk bounds, and validation checks.',
    icon: 'Sliders',
    category: 'Strategies',
    route: '/studio'
  },
  {
    id: 'backtesting-engine',
    title: 'Historical Backtester',
    tagline: 'Institutional Performance Simulation',
    description: 'Simulate historical strategy returns, Sharpe ratios, max drawdown, and turnover across 365+ snapshot dates.',
    icon: 'History',
    category: 'Strategies',
    route: '/backtest/history'
  },
  {
    id: 'pipeline-visualizer',
    title: 'Pipeline Visualizer',
    tagline: 'Real-Time Quantitative Data Flow',
    description: 'Monitor data ingestion, feature generation, ML inference, and score aggregation stage-by-stage.',
    icon: 'Zap',
    category: 'Pipeline',
    route: '/'
  },
  {
    id: 'machine-learning',
    title: 'Ensemble ML Engine',
    tagline: 'LightGBM, XGBoost & Neural Scoring',
    description: 'Predict directional price probability using 70+ quantitative features and multi-model ensemble consensus.',
    icon: 'Cpu',
    category: 'Labs',
    route: '/lab/models'
  },
  {
    id: 'explainable-ai',
    title: 'Explainable AI (XAI)',
    tagline: 'Score Breakdown & Attribution',
    description: 'Audit exact score contributors, indicator weights, and confidence bands for every recommendation.',
    icon: 'Eye',
    category: 'Research',
    route: '/search'
  },
  {
    id: 'risk-analytics',
    title: 'Risk & Stress Engine',
    tagline: 'Monte Carlo & Crisis Stress Tests',
    description: 'Evaluate portfolio tail risk, drawdown probabilities, and sector concentration limits.',
    icon: 'Shield',
    category: 'Risk',
    route: '/lab/monte-carlo'
  },
  {
    id: 'portfolio-construction',
    title: 'Portfolio Constructor',
    tagline: 'Mean-Variance & Kelly Sizing',
    description: 'Optimal asset allocation using Kelly Criterion, Black-Litterman, and risk parity models.',
    icon: 'Briefcase',
    category: 'Portfolio',
    route: '/lab/construction'
  },
  {
    id: 'research-laboratory',
    title: 'Quant Research Labs',
    tagline: '24 Specialized Quantitative Sandbox Labs',
    description: 'Deep dive into feature engineering, regime detection, correlation matrices, and drift monitoring.',
    icon: 'FlaskConical',
    category: 'Labs',
    route: '/lab'
  }
];

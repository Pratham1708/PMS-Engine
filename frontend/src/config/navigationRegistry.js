// Configuration-driven Navigation Registry for Sticky Horizontal Header & Mega Dropdowns
export const NAVIGATION_REGISTRY = [
  {
    key: 'markets',
    label: 'Markets',
    children: [
      { label: 'Market Overview', route: '/market', icon: 'BarChart2', desc: 'Indices, top gainers, market regime' },
      { label: 'Sector Performance', route: '/sectors', icon: 'PieChart', desc: 'Sector wise snapshot breakdown' },
      { label: 'Market Breadth', route: '/breadth', icon: 'Activity', desc: 'Advance/decline & momentum indicators' },
      { label: 'Ratings Distribution', route: '/ratings', icon: 'Award', desc: 'Strong Buy to Strong Sell split' },
      { label: 'Watchlists', route: '/watchlists', icon: 'Star', desc: 'Smart watchlists & custom filters' }
    ]
  },
  {
    key: 'research',
    label: 'Research',
    children: [
      { label: 'Dashboard', route: '/dashboard', icon: 'LayoutDashboard', desc: 'Signals cache & top opportunities' },
      { label: 'Stock Search', route: '/search', icon: 'Search', desc: 'Search 50+ covered universe stocks' },
      { label: 'Research Workspace', route: '/workspace', icon: 'Compass', desc: 'Central research launchpad' },
      { label: 'Historical Archive', route: '/archive', icon: 'Archive', desc: '365+ point-in-time snapshot vault' },
      { label: 'Portfolio Allocation', route: '/portfolio', icon: 'Briefcase', desc: 'Capital allocation & recommendations' }
    ]
  },
  {
    key: 'strategies',
    label: 'Strategies',
    children: [
      { label: 'Quant Strategy Studio', route: '/studio', icon: 'Sliders', desc: 'Custom factor & weight strategy builder' },
      { label: 'Strategy Validation', route: '/strategy/validation', icon: 'CheckCircle', desc: 'Audit strategy factor bounds & weights' },
      { label: 'Backtest History', route: '/backtest/history', icon: 'History', desc: 'Historical strategy backtest performance' }
    ]
  },
  {
    key: 'analytics',
    label: 'Analytics',
    children: [
      { label: 'Research Reports', route: '/reports', icon: 'FileText', desc: 'Executive & detailed research reports' },
      { label: 'Daily Changes', route: '/changes', icon: 'TrendingUp', desc: 'Rating upgrades, downgrades & drifts' }
    ]
  },
  {
    key: 'pipeline',
    label: 'Pipeline',
    children: [
      { label: 'Snapshot Dashboard', route: '/', icon: 'Zap', desc: 'Live execution visualizer & status' },
      { label: 'Snapshot Diagnostics', route: '/snapshot-diagnostics', icon: 'Cpu', desc: 'System status & admin controls' },
      { label: 'Data Quality & Integrity', route: '/data-quality', icon: 'ShieldCheck', desc: 'Data freshness & validation checks' }
    ]
  },
  {
    key: 'labs',
    label: 'Labs',
    isGrouped: true,
    groups: [
      {
        category: 'Market Intelligence',
        items: [
          { label: 'Indicator Lab', route: '/lab/indicators' },
          { label: 'Sector Analysis Lab', route: '/lab/sector' },
          { label: 'Market Regime Lab', route: '/lab/regime' },
          { label: 'Market Breadth Lab', route: '/lab/breadth' },
          { label: 'Liquidity Audit Lab', route: '/lab/liquidity' }
        ]
      },
      {
        category: 'Feature Engineering',
        items: [
          { label: 'Feature Selection Lab', route: '/lab/features' },
          { label: 'Cross-Indicator Lab', route: '/lab/cross-indicator' }
        ]
      },
      {
        category: 'Machine Learning',
        items: [
          { label: 'Model Research Lab', route: '/lab/models' },
          { label: 'Ensemble Strategy Lab', route: '/lab/ensemble', isLocked: true, remark: 'Coming Soon' },
          { label: 'Hyperparameter Lab', route: '/lab/hyperopt' }
        ]
      },
      {
        category: 'Risk & Stress Testing',
        items: [
          { label: 'Monte Carlo Sandbox', route: '/lab/monte-carlo' },
          { label: 'Crisis Stress Tester', route: '/lab/stress' },
          { label: 'Position Sizing Lab', route: '/lab/sizing' },
          { label: 'Score Drift Monitor', route: '/lab/drift' }
        ]
      },
      {
        category: 'Portfolio Research',
        items: [
          { label: 'Portfolio Strategies', route: '/lab/portfolio', isLocked: true, remark: 'Coming Soon' },
          { label: 'Portfolio Construction', route: '/lab/construction' },
          { label: 'Correlation Research', route: '/lab/correlation' },
          { label: 'Benchmark Comparison', route: '/lab/benchmark', isLocked: true, remark: 'Coming Soon' }
        ]
      },
      {
        category: 'Validation & Audit',
        items: [
          { label: 'Engine Score Validation', route: '/lab/engine' },
          { label: 'Composite Weights Lab', route: '/lab/composite' },
          { label: 'Recommendation Audit', route: '/lab/validation' }
        ]
      },
      {
        category: 'Experiment Registry',
        items: [
          { label: 'Experiment History', route: '/lab/experiments' },
          { label: 'Lab Reports Compiler', route: '/lab/reports' }
        ]
      }
    ]
  },
  {
    key: 'resources',
    label: 'Resources',
    children: [
      { label: 'Knowledge Center', route: '/docs', icon: 'BookOpen', desc: 'User guides, API docs & quant concepts' },
      { label: 'Technology Stack', route: '/landing#technology', icon: 'Layers', desc: 'React, FastAPI, PostgreSQL, TF architecture' }
    ]
  }
];

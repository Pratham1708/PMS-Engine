// Widget Registry — Enables customizable dashboard widget grids
export const WIDGET_REGISTRY = [
  {
    id: 'market-regime',
    title: 'Market Regime & Volatility',
    component: 'MarketRegimeWidget',
    defaultSize: 'small',
    category: 'Market'
  },
  {
    id: 'snapshot-status',
    title: "Today's Snapshot Status",
    component: 'SnapshotStatusWidget',
    defaultSize: 'small',
    category: 'Pipeline'
  },
  {
    id: 'top-opportunities',
    title: 'Top Quantitative Opportunities',
    component: 'TopOpportunitiesWidget',
    defaultSize: 'large',
    category: 'Research'
  },
  {
    id: 'portfolio-summary',
    title: 'Portfolio Capital Allocation',
    component: 'PortfolioSummaryWidget',
    defaultSize: 'medium',
    category: 'Portfolio'
  },
  {
    id: 'recent-activity',
    title: 'Recent Activity & Backtests',
    component: 'RecentActivityWidget',
    defaultSize: 'medium',
    category: 'History'
  },
  {
    id: 'system-health',
    title: 'System Health & Data Integrity',
    component: 'SystemHealthWidget',
    defaultSize: 'small',
    category: 'Pipeline'
  }
];

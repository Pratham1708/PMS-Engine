import { ROUTE_REGISTRY } from './routeRegistry';
import { FEATURE_REGISTRY } from './featureRegistry';

// Build initial static searchable index entries from ROUTE_REGISTRY and FEATURE_REGISTRY
export const buildStaticSearchIndex = () => {
  const index = [];

  // Add Pages
  Object.values(ROUTE_REGISTRY).forEach((route) => {
    index.push({
      id: `page-${route.path}`,
      title: route.name,
      subtitle: `Navigation • ${route.category || route.pillar || 'Workspace'}`,
      type: 'page',
      category: 'Pages',
      route: route.path,
      icon: 'Layout'
    });
  });

  // Add Features
  FEATURE_REGISTRY.forEach((feat) => {
    index.push({
      id: `feat-${feat.id}`,
      title: feat.title,
      subtitle: `${feat.tagline} • ${feat.category}`,
      type: 'feature',
      category: 'Features',
      route: feat.route,
      icon: feat.icon
    });
  });

  // Add Sample Popular Indian Universe Stocks for Instant Search Offline Fallback
  const defaultStocks = [
    { symbol: 'RELIANCE', name: 'Reliance Industries Ltd.', sector: 'Energy' },
    { symbol: 'TCS', name: 'Tata Consultancy Services', sector: 'Technology' },
    { symbol: 'HDFCBANK', name: 'HDFC Bank Ltd.', sector: 'Financial Services' },
    { symbol: 'INFY', name: 'Infosys Ltd.', sector: 'Technology' },
    { symbol: 'ICICIBANK', name: 'ICICI Bank Ltd.', sector: 'Financial Services' },
    { symbol: 'HINDUNILVR', name: 'Hindustan Unilever Ltd.', sector: 'Consumer Goods' },
    { symbol: 'ITC', name: 'ITC Ltd.', sector: 'Consumer Goods' },
    { symbol: 'SBIN', name: 'State Bank of India', sector: 'Financial Services' },
    { symbol: 'BHARTIARTL', name: 'Bharti Airtel Ltd.', sector: 'Telecom' },
    { symbol: 'LTI', name: 'LTIMindtree Ltd.', sector: 'Technology' },
    { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank', sector: 'Financial Services' },
    { symbol: 'LT', name: 'Larsen & Toubro Ltd.', sector: 'Construction' },
    { symbol: 'AXISBANK', name: 'Axis Bank Ltd.', sector: 'Financial Services' },
    { symbol: 'ASIANPAINT', name: 'Asian Paints Ltd.', sector: 'Consumer Durables' },
    { symbol: 'MARUTI', name: 'Maruti Suzuki India Ltd.', sector: 'Automobile' }
  ];

  defaultStocks.forEach((stk) => {
    index.push({
      id: `stock-${stk.symbol}`,
      title: stk.symbol,
      subtitle: `${stk.name} • ${stk.sector}`,
      type: 'stock',
      category: 'Stocks',
      route: `/stock/${stk.symbol}`,
      icon: 'TrendingUp'
    });
  });

  return index;
};

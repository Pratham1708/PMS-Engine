import { useLocation, Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { ROUTE_REGISTRY } from '../../config/routeRegistry';

export default function ContextualBreadcrumbs() {
  const location = useLocation();
  const currentPath = location.pathname;

  // Find matching route entry
  let matchedEntry = Object.values(ROUTE_REGISTRY).find((r) => r.path === currentPath);
  if (!matchedEntry && currentPath.startsWith('/stock/')) {
    const symbol = currentPath.split('/stock/')[1];
    matchedEntry = { name: `Stock ${symbol}`, category: 'Research' };
  }

  const category = matchedEntry?.category || matchedEntry?.pillar || 'Workspace';
  const pageName = matchedEntry?.name || 'Dashboard';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        fontSize: '0.8rem',
        color: 'var(--color-text-secondary)',
        padding: '12px 24px 0 24px'
      }}
    >
      <Link to="/workspace" style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--color-text-muted)' }}>
        <Home size={13} />
        <span>Workspace</span>
      </Link>
      <ChevronRight size={12} style={{ color: 'var(--color-text-muted)' }} />
      <span style={{ color: 'var(--color-text-muted)' }}>{category}</span>
      <ChevronRight size={12} style={{ color: 'var(--color-text-muted)' }} />
      <span style={{ fontWeight: '600', color: 'var(--color-text-primary)' }}>{pageName}</span>
    </div>
  );
}

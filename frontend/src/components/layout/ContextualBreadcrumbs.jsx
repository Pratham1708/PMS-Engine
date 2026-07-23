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
        padding: '8px 0 0 0',
        maxWidth: '100%',
        overflowX: 'auto',
        whiteSpace: 'nowrap',
        WebkitOverflowScrolling: 'touch'
      }}
    >
      <Link to="/workspace" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--color-text-muted)', whiteSpace: 'nowrap', flexShrink: 0 }}>
        <Home size={13} />
        <span>Workspace</span>
      </Link>
      <ChevronRight size={12} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />
      <span style={{ color: 'var(--color-text-muted)', whiteSpace: 'nowrap', flexShrink: 0 }}>{category}</span>
      <ChevronRight size={12} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />
      <span style={{ fontWeight: '600', color: 'var(--color-text-primary)', whiteSpace: 'nowrap', flexShrink: 0 }}>{pageName}</span>
    </div>
  );
}

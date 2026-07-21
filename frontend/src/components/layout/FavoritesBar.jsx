import { Link } from 'react-router-dom';
import { Star, Plus } from 'lucide-react';
import * as Icons from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

export default function FavoritesBar() {
  const { pinnedFavorites } = useWorkspace();

  return (
    <div
      style={{
        height: '32px',
        background: 'rgba(15, 23, 42, 0.4)',
        borderBottom: '1px solid var(--color-border-subtle)',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        fontSize: '0.75rem'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--color-text-muted)', fontWeight: '600', marginRight: '8px' }}>
        <Star size={12} style={{ color: '#fbbf24' }} />
        <span>Favorites:</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', overflowX: 'auto' }}>
        {pinnedFavorites.map((fav, idx) => {
          const IconComp = fav.icon && Icons[fav.icon] ? Icons[fav.icon] : Icons.Bookmark;
          return (
            <Link
              key={idx}
              to={fav.route}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '2px 8px',
                borderRadius: '4px',
                background: 'rgba(255, 255, 255, 0.05)',
                color: 'var(--color-text-secondary)',
                textDecoration: 'none',
                transition: 'all 0.15s ease'
              }}
            >
              <IconComp size={11} style={{ color: 'var(--color-accent-primary)' }} />
              <span>{fav.label}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, X, ChevronRight, Layout, TrendingUp, Sliders, Zap } from 'lucide-react';
import { useCommandPalette } from '../../context/CommandPaletteContext';
import { buildStaticSearchIndex } from '../../config/globalSearchIndex';

export default function CommandPalette() {
  const { isOpen, closeCommandPalette } = useCommandPalette();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const navigate = useNavigate();

  const searchIndex = useMemo(() => buildStaticSearchIndex(), []);

  const filteredResults = useMemo(() => {
    if (!query.trim()) return searchIndex.slice(0, 8);
    const q = query.toLowerCase();
    return searchIndex.filter(
      (item) => item.title.toLowerCase().includes(q) || item.subtitle.toLowerCase().includes(q)
    ).slice(0, 12);
  }, [query, searchIndex]);

  if (!isOpen) return null;

  const handleSelect = (item) => {
    closeCommandPalette();
    navigate(item.route);
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'rgba(9, 13, 22, 0.75)',
        backdropFilter: 'blur(12px)',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: '10vh'
      }}
      onClick={closeCommandPalette}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '640px',
          background: 'var(--color-bg-surface)',
          border: '1px solid var(--color-border-glow)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Header Input */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '16px 20px',
            borderBottom: '1px solid var(--color-border-subtle)'
          }}
        >
          <Search size={20} style={{ color: 'var(--color-accent-primary)' }} />
          <input
            type="text"
            placeholder="Type a stock, page, strategy, lab, or command..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
            style={{
              flex: 1,
              background: 'none',
              border: 'none',
              outline: 'none',
              color: 'var(--color-text-primary)',
              fontSize: '1rem',
              fontFamily: 'var(--font-family-sans)'
            }}
          />
          <button
            onClick={closeCommandPalette}
            style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Results List */}
        <div style={{ maxHeight: '380px', overflowY: 'auto', padding: '8px' }}>
          {filteredResults.length === 0 ? (
            <div style={{ padding: '32px', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
              No matches found for "{query}". Try searching for RELIANCE, Strategy, or Model Lab.
            </div>
          ) : (
            filteredResults.map((item, idx) => (
              <div
                key={item.id}
                onClick={() => handleSelect(item)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)',
                  cursor: 'pointer',
                  background: idx === selectedIndex ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                  transition: 'all 0.15s ease'
                }}
              >
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: 'var(--radius-xs)',
                    background: 'rgba(255, 255, 255, 0.05)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--color-accent-primary)'
                  }}
                >
                  {item.type === 'stock' ? <TrendingUp size={16} /> : <Layout size={16} />}
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-primary)' }}>
                    {item.title}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{item.subtitle}</div>
                </div>

                <ChevronRight size={14} style={{ color: 'var(--color-text-muted)' }} />
              </div>
            ))
          )}
        </div>

        {/* Footer shortcuts helper */}
        <div
          style={{
            padding: '10px 20px',
            background: 'rgba(15, 23, 42, 0.4)',
            borderTop: '1px solid var(--color-border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.72rem',
            color: 'var(--color-text-muted)'
          }}
        >
          <span>Use <strong>↑↓</strong> to navigate, <strong>Enter</strong> to select</span>
          <span><strong>ESC</strong> to close</span>
        </div>
      </div>
    </div>
  );
}

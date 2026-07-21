import { createContext, useContext, useState, useEffect } from 'react';

const WorkspaceContext = createContext();

const DEFAULT_FAVORITES = [
  { label: 'Quant Studio', route: '/studio', icon: 'Sliders' },
  { label: 'Backtests', route: '/backtest/history', icon: 'History' },
  { label: 'Pipeline', route: '/', icon: 'Zap' },
  { label: 'Stock Search', route: '/search', icon: 'Search' }
];

export function WorkspaceProvider({ children }) {
  const [pinnedFavorites, setPinnedFavorites] = useState(() => {
    const saved = localStorage.getItem('pms_favorites');
    return saved ? JSON.parse(saved) : DEFAULT_FAVORITES;
  });

  const [recentItems, setRecentItems] = useState(() => {
    const saved = localStorage.getItem('pms_recents');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    localStorage.setItem('pms_favorites', JSON.stringify(pinnedFavorites));
  }, [pinnedFavorites]);

  useEffect(() => {
    localStorage.setItem('pms_recents', JSON.stringify(recentItems));
  }, [recentItems]);

  const toggleFavorite = (item) => {
    setPinnedFavorites((prev) => {
      const exists = prev.some((fav) => fav.route === item.route);
      if (exists) {
        return prev.filter((fav) => fav.route !== item.route);
      } else {
        return [...prev, item];
      }
    });
  };

  const addRecentItem = (item) => {
    setRecentItems((prev) => {
      const filtered = prev.filter((r) => r.route !== item.route);
      return [{ ...item, timestamp: new Date().toISOString() }, ...filtered].slice(0, 10);
    });
  };

  return (
    <WorkspaceContext.Provider
      value={{
        pinnedFavorites,
        toggleFavorite,
        recentItems,
        addRecentItem
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export const useWorkspace = () => useContext(WorkspaceContext);

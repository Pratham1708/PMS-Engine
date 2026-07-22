import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const MEMORY_KEY = 'pms_nav_memory_v2';

export function useNavigationMemory() {
  const location = useLocation();

  const [memory, setMemory] = useState(() => {
    try {
      const saved = localStorage.getItem(MEMORY_KEY);
      return saved ? JSON.parse(saved) : { lastPath: '/', expandedDrawer: {}, activeBottomTab: '/workspace' };
    } catch {
      return { lastPath: '/', expandedDrawer: {}, activeBottomTab: '/workspace' };
    }
  });

  // Track active page route & save state
  useEffect(() => {
    setMemory((prev) => {
      const updated = {
        ...prev,
        lastPath: location.pathname,
        activeBottomTab: getMatchingBottomTab(location.pathname)
      };
      try {
        localStorage.setItem(MEMORY_KEY, JSON.stringify(updated));
      } catch (e) {
        console.error('Failed to save nav memory', e);
      }
      return updated;
    });
  }, [location.pathname]);

  const toggleDrawerSection = (sectionKey) => {
    setMemory((prev) => {
      const expanded = { ...prev.expandedDrawer, [sectionKey]: !prev.expandedDrawer[sectionKey] };
      const updated = { ...prev, expandedDrawer: expanded };
      try {
        localStorage.setItem(MEMORY_KEY, JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
  };

  return {
    lastPath: memory.lastPath,
    activeBottomTab: memory.activeBottomTab,
    expandedDrawer: memory.expandedDrawer || {},
    toggleDrawerSection
  };
}

function getMatchingBottomTab(path) {
  if (path.startsWith('/market') || path.startsWith('/sectors') || path.startsWith('/breadth')) return '/market';
  if (path.startsWith('/reports') || path.startsWith('/docs') || path.startsWith('/lab')) return '/lab';
  if (path.startsWith('/studio') || path.startsWith('/strategy') || path.startsWith('/backtest')) return '/studio';
  if (path.startsWith('/workspace') || path === '/') return '/workspace';
  if (path.startsWith('/login') || path.startsWith('/profile')) return '/profile';
  return '/workspace';
}

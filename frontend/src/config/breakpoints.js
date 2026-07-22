import { useState, useEffect } from 'react';

// Centralized Responsive Breakpoints Definition (px)
export const BREAKPOINTS = {
  XS: 480,   // Small Phones (0 - 479px)
  SM: 768,   // Standard/Large Phones (480 - 767px)
  MD: 1024,  // Tablet Portrait / Small Tablet (768 - 1023px)
  LG: 1440,  // Tablet Landscape / Small Laptop (1024 - 1439px)
  XL: 1920,  // Standard Laptop / Desktop (1440 - 1919px)
  XXL: Infinity // Large Desktop (1920px+)
};

/**
 * Custom hook to subscribe to window resize and compute current device profile
 */
export function useBreakpoint() {
  const [windowWidth, setWindowWidth] = useState(
    typeof window !== 'undefined' ? window.innerWidth : 1200
  );
  const [windowHeight, setWindowHeight] = useState(
    typeof window !== 'undefined' ? window.innerHeight : 800
  );

  useEffect(() => {
    if (typeof window === 'undefined') return;

    function handleResize() {
      setWindowWidth(window.innerWidth);
      setWindowHeight(window.innerHeight);
    }

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const isXs = windowWidth < BREAKPOINTS.XS;
  const isSm = windowWidth >= BREAKPOINTS.XS && windowWidth < BREAKPOINTS.SM;
  const isMd = windowWidth >= BREAKPOINTS.SM && windowWidth < BREAKPOINTS.MD;
  const isLg = windowWidth >= BREAKPOINTS.MD && windowWidth < BREAKPOINTS.LG;
  const isXl = windowWidth >= BREAKPOINTS.LG && windowWidth < BREAKPOINTS.XL;
  const isXxl = windowWidth >= BREAKPOINTS.XL;

  const isMobile = windowWidth < BREAKPOINTS.SM; // < 768px
  const isTablet = windowWidth >= BREAKPOINTS.SM && windowWidth < BREAKPOINTS.LG; // 768px - 1023px
  const isDesktop = windowWidth >= BREAKPOINTS.MD; // 1024px+
  const isLandscape = windowWidth > windowHeight && isMobile;

  return {
    windowWidth,
    windowHeight,
    isXs,
    isSm,
    isMd,
    isLg,
    isXl,
    isXxl,
    isMobile,
    isTablet,
    isDesktop,
    isLandscape
  };
}

/**
 * Hook to monitor mobile soft-keyboard visibility via Visual Viewport API
 */
export function useKeyboardVisible() {
  const [isKeyboardVisible, setIsKeyboardVisible] = useState(false);
  const [keyboardHeight, setKeyboardHeight] = useState(0);

  useEffect(() => {
    if (typeof window === 'undefined' || !window.visualViewport) return;

    function handleViewportChange() {
      const vv = window.visualViewport;
      const heightDiff = window.innerHeight - vv.height;
      if (heightDiff > 150) {
        setIsKeyboardVisible(true);
        setKeyboardHeight(heightDiff);
      } else {
        setIsKeyboardVisible(false);
        setKeyboardHeight(0);
      }
    }

    window.visualViewport.addEventListener('resize', handleViewportChange);
    window.visualViewport.addEventListener('scroll', handleViewportChange);

    return () => {
      window.visualViewport.removeEventListener('resize', handleViewportChange);
      window.visualViewport.removeEventListener('scroll', handleViewportChange);
    };
  }, []);

  return { isKeyboardVisible, keyboardHeight };
}

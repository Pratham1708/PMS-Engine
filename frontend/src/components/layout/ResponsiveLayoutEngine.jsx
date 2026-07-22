import React from 'react';
import { useBreakpoint } from '../../config/breakpoints';

/**
 * Responsive Layout Provider — High Priority Central Engine
 * Render desktop, tablet, or mobile variants or adapt via breakpoint properties.
 */
export function ResponsiveLayout({ desktop, tablet, mobile, children }) {
  const { isMobile, isTablet, isDesktop } = useBreakpoint();

  if (isMobile && mobile) return <>{mobile}</>;
  if (isTablet && tablet) return <>{tablet}</>;
  if (isDesktop && desktop) return <>{desktop}</>;

  return <>{children}</>;
}

/**
 * Enterprise Responsive Grid System
 */
export function ResponsiveGrid({
  children,
  cols = { desktop: 4, tablet: 2, mobile: 1 },
  gap = 'var(--spacing-md)',
  minWidth = '280px',
  className = '',
  style = {}
}) {
  const { isMobile, isTablet } = useBreakpoint();

  const currentCols = isMobile
    ? cols.mobile ?? 1
    : isTablet
    ? cols.tablet ?? 2
    : cols.desktop ?? 4;

  return (
    <div
      className={`responsive-grid ${className}`}
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${currentCols}, minmax(min(100%, ${minWidth}), 1fr))`,
        gap: gap,
        width: '100%',
        boxSizing: 'border-box',
        ...style
      }}
    >
      {children}
    </div>
  );
}

/**
 * Enterprise Responsive Stack Container
 */
export function ResponsiveStack({
  children,
  direction = { desktop: 'row', mobile: 'column' },
  align = 'stretch',
  justify = 'flex-start',
  gap = 'var(--spacing-md)',
  className = '',
  style = {}
}) {
  const { isMobile } = useBreakpoint();

  const currentDirection = isMobile
    ? direction.mobile ?? 'column'
    : direction.desktop ?? 'row';

  return (
    <div
      className={`responsive-stack ${className}`}
      style={{
        display: 'flex',
        flexDirection: currentDirection,
        alignItems: align,
        justifyContent: justify,
        gap: gap,
        width: '100%',
        boxSizing: 'border-box',
        ...style
      }}
    >
      {children}
    </div>
  );
}

export default ResponsiveLayout;

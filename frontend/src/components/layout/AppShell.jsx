import { useState } from 'react';
import LiveHeaderTicker from './LiveHeaderTicker';
import HorizontalNavbar from './HorizontalNavbar';
import FavoritesBar from './FavoritesBar';
import ContextualBreadcrumbs from './ContextualBreadcrumbs';
import ContextQuickActions from './ContextQuickActions';
import InstitutionalDock from './InstitutionalDock';
import CategorizedNotifications from '../workspace/CategorizedNotifications';
import MobileDrawer from './MobileDrawer';
import BottomNavBar from './BottomNavBar';

export default function AppShell({ children, pageTitle }) {
  const [showNotifications, setShowNotifications] = useState(false);
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);

  return (
    <div
      className="page-scroll-container"
      style={{
        minHeight: '100vh',
        background: 'var(--color-bg-base)',
        color: 'var(--color-text-primary)',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      {/* 1. Bloomberg Live Header Ticker (Desktop / Tablet) */}
      <div className="hide-tablet-down">
        <LiveHeaderTicker onToggleNotifications={() => setShowNotifications((prev) => !prev)} />
      </div>

      {/* 2. Sticky Horizontal Navbar / Mobile Top App Bar */}
      <HorizontalNavbar
        onOpenDrawer={() => setIsMobileDrawerOpen(true)}
        onToggleNotifications={() => setShowNotifications((prev) => !prev)}
      />

      {/* 3. Workspace Favorites Bar (Desktop Only) */}
      <div className="hide-tablet-down">
        <FavoritesBar />
      </div>

      {/* 4. Contextual Header (Breadcrumbs + Context Quick Actions) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 var(--page-padding-x)',
          marginTop: '8px',
          flexWrap: 'wrap',
          gap: '8px'
        }}
      >
        <ContextualBreadcrumbs />
        <div className="hide-mobile">
          <ContextQuickActions />
        </div>
      </div>

      {/* 5. Main Content Canvas */}
      <main
        style={{
          flex: 1,
          padding: 'var(--page-padding-y) var(--page-padding-x)',
          paddingBottom: 'calc(var(--bottom-nav-height) + var(--safe-area-bottom) + 32px)',
          maxWidth: '100%',
          boxSizing: 'border-box'
        }}
      >
        {children}
      </main>

      {/* 6. Institutional Bottom Dock (Desktop / Tablet) */}
      <InstitutionalDock />

      {/* 7. Mobile Persistent Bottom Navigation Bar (< 768px) */}
      <BottomNavBar />

      {/* 8. Slide-out Mobile Navigation Drawer */}
      <MobileDrawer
        isOpen={isMobileDrawerOpen}
        onClose={() => setIsMobileDrawerOpen(false)}
      />

      {/* 9. Categorized Notification Drawer Overlay */}
      {showNotifications && (
        <CategorizedNotifications onClose={() => setShowNotifications(false)} />
      )}
    </div>
  );
}

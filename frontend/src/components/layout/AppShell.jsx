import { useState } from 'react';
import LiveHeaderTicker from './LiveHeaderTicker';
import HorizontalNavbar from './HorizontalNavbar';
import FavoritesBar from './FavoritesBar';
import ContextualBreadcrumbs from './ContextualBreadcrumbs';
import ContextQuickActions from './ContextQuickActions';
import InstitutionalDock from './InstitutionalDock';
import CategorizedNotifications from '../workspace/CategorizedNotifications';

export default function AppShell({ children, pageTitle }) {
  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'var(--color-bg-base)',
        color: 'var(--color-text-primary)',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      {/* 1. Bloomberg Live Header Ticker */}
      <LiveHeaderTicker onToggleNotifications={() => setShowNotifications((prev) => !prev)} />

      {/* 2. Sticky Horizontal Navbar */}
      <HorizontalNavbar />

      {/* 3. Workspace Favorites Bar */}
      <FavoritesBar />

      {/* 4. Contextual Header (Breadcrumbs + Context Quick Actions) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          marginTop: '8px'
        }}
      >
        <ContextualBreadcrumbs />
        <ContextQuickActions />
      </div>

      {/* 5. Main Content Canvas */}
      <main
        style={{
          flex: 1,
          padding: '16px 24px 60px 24px',
          maxWidth: '100%',
          boxSizing: 'border-box'
        }}
      >
        {children}
      </main>

      {/* 6. Institutional Bottom Dock */}
      <InstitutionalDock />

      {/* 7. Categorized Notification Drawer Overlay */}
      {showNotifications && (
        <CategorizedNotifications onClose={() => setShowNotifications(false)} />
      )}
    </div>
  );
}

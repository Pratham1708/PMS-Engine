import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { path: '/', label: 'Daily Snapshot', icon: '⚡' },
  { path: '/workspace', label: 'Research Workspace', icon: '🏠' },
  { path: '/watchlists', label: 'Smart Watchlists', icon: '📋' },
  { path: '/changes', label: 'What\'s Changed', icon: '🔄' },
  { path: '/sectors', label: 'Sector Snapshot', icon: '🏢' },
  { path: '/breadth', label: 'Market Breadth', icon: '📈' },
  { path: '/archive', label: 'Archive & Compare', icon: '📚' },
  { path: '/data-quality', label: 'Data Quality', icon: '🛡️' },
  { path: '/search', label: 'Stock Search', icon: '🔍' },
  { path: '/reports', label: 'Research Reports', icon: '📄' },
  { path: '/lab', label: 'Quant Laboratory', icon: '🔬' },
];


export default function Sidebar({ isCollapsed, toggleSidebar, closeMobileSidebar }) {
  const location = useLocation();

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">P</div>
        <div className="sidebar-brand-info">
          <div className="sidebar-brand-text">PMS Engine</div>
          <div className="sidebar-brand-sub">Institutional Analytics</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`sidebar-link ${location.pathname === item.path ? 'active' : ''}`}
            onClick={closeMobileSidebar}
          >
            <span className="sidebar-link-icon">{item.icon}</span>
            <span className="sidebar-link-text">{item.label}</span>
          </Link>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button className="sidebar-collapse-btn" onClick={toggleSidebar} title={isCollapsed ? "Expand Menu" : "Collapse Menu"}>
          <span className="sidebar-collapse-icon">{isCollapsed ? '❯' : '❮'}</span>
          <span className="sidebar-collapse-text">Collapse Menu</span>
        </button>
      </div>
    </aside>
  );
}

import { useState } from 'react';
import { refreshScanner } from '../../api/stocks';

export default function Header({ title, onToggleMobileSidebar }) {
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState('');

  const handleRefresh = async () => {
    setRefreshing(true);
    setMessage('');
    try {
      const res = await refreshScanner();
      setMessage(`✓ Refreshed — ${res.data.stocks_loaded} stocks loaded`);
      setTimeout(() => setMessage(''), 3000);
    } catch {
      setMessage('✗ Refresh failed');
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <header className="header">
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <button className="mobile-toggle-btn" onClick={onToggleMobileSidebar} title="Toggle Menu">
          ☰
        </button>
        <h1 className="header-title">{title}</h1>
      </div>
      <div className="header-actions">
        {message && (
          <span style={{ fontSize: '13px', color: message.startsWith('✓') ? '#10b981' : '#ef4444' }}>
            {message}
          </span>
        )}
        <button
          className="btn btn-refresh"
          onClick={handleRefresh}
          disabled={refreshing}
        >
          {refreshing ? '⟳ Refreshing...' : '⟳ Refresh Scanner'}
        </button>
      </div>
    </header>
  );
}

/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect, useCallback } from 'react';
import { fetchStocks } from '../api/stocks';
import {
  generateStockReport,
  generateWorkspaceReport,
  generateMarketReport,
  listReports,
  getReportPreviewUrl,
  getReportDownloadUrl,
  getDirectStockReportUrl,
  getDirectWorkspaceReportUrl,
  getDirectMarketReportUrl,
} from '../api/reports';
import LoadingSpinner from '../components/common/LoadingSpinner';

const REPORT_TYPES = {
  stock: {
    icon: '📈',
    title: 'Stock Research Report',
    description: 'Deep-dive analysis on a single stock with XAI explanations, scoring breakdown, and institutional recommendation.',
    gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
  },
  workspace: {
    icon: '💼',
    title: 'Research Workspace Report',
    description: 'Personal workspace analysis compiling tracked stocks, coverage ratios, active scoring metrics, and deep research summaries.',
    gradient: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
  },
  market: {
    icon: '🌐',
    title: 'Market Overview Report',
    description: 'Complete Nifty 50 universe analysis with rating distributions, top/bottom decile stocks, and market breadth.',
    gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
  },
};

function formatDate(ts) {
  if (!ts) return '—';
  try {
    const d = new Date(ts);
    return d.toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return ts;
  }
}

function typeLabel(type) {
  switch (type) {
    case 'stock': return '📈 Stock';
    case 'workspace': return '💼 Workspace';
    case 'market': return '🌐 Market';
    default: return type;
  }
}

export default function Reports() {
  const [stocks, setStocks] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState({ stock: false, workspace: false, market: false });
  const [previewId, setPreviewId] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [initialLoading, setInitialLoading] = useState(true);

  const refreshReportList = useCallback(async () => {
    try {
      const res = await listReports();
      setReports(res.data || []);
    } catch {
      // Silently ignore
    }
  }, []);

  // Load stock list and report history
  useEffect(() => {
    Promise.all([
      fetchStocks().then((res) => {
        const list = res.data || [];
        setStocks(list);
        if (list.length > 0) setSelectedSymbol(list[0].Symbol);
      }),
      refreshReportList(),
    ]).finally(() => setInitialLoading(false));
  }, [refreshReportList]);

  const showSuccess = (msg) => {
    setSuccess(msg);
    setTimeout(() => setSuccess(null), 4000);
  };

  const handleGenerate = async (type) => {
    setError(null);
    setLoading((prev) => ({ ...prev, [type]: true }));

    try {
      let res;
      if (type === 'stock') {
        if (!selectedSymbol) { setError('Please select a stock symbol.'); return; }
        res = await generateStockReport(selectedSymbol);
      } else if (type === 'workspace') {
        res = await generateWorkspaceReport();
      } else {
        res = await generateMarketReport();
      }

      const meta = res.data;
      showSuccess(`${REPORT_TYPES[type].title} generated successfully!`);
      setPreviewId(meta.report_id);
      await refreshReportList();
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to generate ${type} report.`);
    } finally {
      setLoading((prev) => ({ ...prev, [type]: false }));
    }
  };

  if (initialLoading) return <LoadingSpinner />;

  return (
    <div className="fade-in">
      {/* Header Section */}
      <div className="reports-hero">
        <div className="reports-hero-content">
          <h1 className="reports-hero-title">📄 Research Reports</h1>
          <p className="reports-hero-subtitle">
            Generate institutional-grade research reports with AI-powered explanations, scoring breakdowns, and actionable recommendations.
          </p>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="reports-alert reports-alert-error">
          <span className="reports-alert-icon">⚠️</span>
          <span>{error}</span>
          <button className="reports-alert-close" onClick={() => setError(null)}>×</button>
        </div>
      )}
      {success && (
        <div className="reports-alert reports-alert-success">
          <span className="reports-alert-icon">✅</span>
          <span>{success}</span>
        </div>
      )}

      {/* Report Generation Cards */}
      <div className="reports-generator-grid">
        {/* Stock Report Card */}
        <div className="reports-gen-card">
          <div className="reports-gen-card-header" style={{ background: REPORT_TYPES.stock.gradient }}>
            <span className="reports-gen-icon">{REPORT_TYPES.stock.icon}</span>
            <h3 className="reports-gen-title">{REPORT_TYPES.stock.title}</h3>
          </div>
          <div className="reports-gen-card-body">
            <p className="reports-gen-desc">{REPORT_TYPES.stock.description}</p>
            <div className="reports-gen-input-group">
              <label className="reports-gen-label">Select Stock Symbol</label>
              <select
                className="reports-gen-select"
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
              >
                {stocks.map((s) => (
                  <option key={s.Symbol} value={s.Symbol}>{s.Symbol} — {s.FinalRating}</option>
                ))}
              </select>
            </div>
            
            <button
              className="reports-gen-btn"
              style={{ background: REPORT_TYPES.stock.gradient }}
              disabled={loading.stock}
              onClick={() => handleGenerate('stock')}
            >
              {loading.stock ? (
                <><span className="reports-spinner" /> Generating...</>
              ) : (
                <>📄 Generate Stock Report</>
              )}
            </button>

            {/* Direct export buttons */}
            <div className="reports-direct-export">
              <span className="reports-direct-label">Direct Export:</span>
              <div className="reports-direct-links">
                <a
                  href={getDirectStockReportUrl(selectedSymbol, 'pdf')}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="reports-direct-link reports-direct-pdf"
                >
                  📥 PDF
                </a>
                <a
                  href={getDirectStockReportUrl(selectedSymbol, 'html')}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="reports-direct-link reports-direct-html"
                >
                  🌐 HTML
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Workspace Report Card */}
        <div className="reports-gen-card">
          <div className="reports-gen-card-header" style={{ background: REPORT_TYPES.workspace.gradient }}>
            <span className="reports-gen-icon">{REPORT_TYPES.workspace.icon}</span>
            <h3 className="reports-gen-title">{REPORT_TYPES.workspace.title}</h3>
          </div>
          <div className="reports-gen-card-body">
            <p className="reports-gen-desc">{REPORT_TYPES.workspace.description}</p>
            <div className="reports-gen-input-group">
              <label className="reports-gen-label">Report Scope</label>
              <div className="reports-gen-scope-badge" style={{ backgroundColor: '#eef2ff', color: '#4f46e5' }}>
                Tracked Stocks &amp; Research History
              </div>
            </div>
            
            <button
              className="reports-gen-btn"
              style={{ background: REPORT_TYPES.workspace.gradient }}
              disabled={loading.workspace}
              onClick={() => handleGenerate('workspace')}
            >
              {loading.workspace ? (
                <><span className="reports-spinner" /> Generating...</>
              ) : (
                <>📄 Generate Workspace Report</>
              )}
            </button>

            {/* Direct export buttons */}
            <div className="reports-direct-export">
              <span className="reports-direct-label">Direct Export:</span>
              <div className="reports-direct-links">
                <a
                  href={getDirectWorkspaceReportUrl('pdf')}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="reports-direct-link reports-direct-pdf"
                >
                  📥 PDF
                </a>
                <a
                  href={getDirectWorkspaceReportUrl('html')}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="reports-direct-link reports-direct-html"
                >
                  🌐 HTML
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Market Report Card */}
        <div className="reports-gen-card">
          <div className="reports-gen-card-header" style={{ background: REPORT_TYPES.market.gradient }}>
            <span className="reports-gen-icon">{REPORT_TYPES.market.icon}</span>
            <h3 className="reports-gen-title">{REPORT_TYPES.market.title}</h3>
          </div>
          <div className="reports-gen-card-body">
            <p className="reports-gen-desc">{REPORT_TYPES.market.description}</p>
            <div className="reports-gen-input-group">
              <label className="reports-gen-label">Report Scope</label>
              <div className="reports-gen-scope-badge">
                Nifty 50 — Full Universe Analysis
              </div>
            </div>
            
            <button
              className="reports-gen-btn"
              style={{ background: REPORT_TYPES.market.gradient }}
              disabled={loading.market}
              onClick={() => handleGenerate('market')}
            >
              {loading.market ? (
                <><span className="reports-spinner" /> Generating...</>
              ) : (
                <>📄 Generate Market Report</>
              )}
            </button>

            {/* Direct export buttons */}
            <div className="reports-direct-export">
              <span className="reports-direct-label">Direct Export:</span>
              <div className="reports-direct-links">
                <a
                  href={getDirectMarketReportUrl('pdf')}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="reports-direct-link reports-direct-pdf"
                >
                  📥 PDF
                </a>
                <a
                  href={getDirectMarketReportUrl('html')}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="reports-direct-link reports-direct-html"
                >
                  🌐 HTML
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Report Preview */}
      {previewId && (
        <div className="page-section" style={{ marginTop: '30px' }}>
          <div className="section-header">
            <h2 className="section-title">Report Preview</h2>
            <div className="reports-preview-actions">
              <a
                href={getReportDownloadUrl(previewId, 'pdf')}
                target="_blank"
                rel="noopener noreferrer"
                className="reports-download-btn reports-download-pdf"
              >
                📥 Download PDF
              </a>
              <a
                href={getReportDownloadUrl(previewId, 'html')}
                target="_blank"
                rel="noopener noreferrer"
                className="reports-download-btn reports-download-html"
              >
                🌐 Download HTML
              </a>
              <button
                className="reports-download-btn reports-close-preview"
                onClick={() => setPreviewId(null)}
              >
                ✕ Close
              </button>
            </div>
          </div>
          <div className="reports-preview-frame-container">
            <iframe
              src={getReportPreviewUrl(previewId)}
              className="reports-preview-iframe"
              title="Report Preview"
            />
          </div>
        </div>
      )}

      {/* Report History */}
      <div className="page-section">
        <div className="section-header">
          <h2 className="section-title">📋 Report History</h2>
          <button className="btn-refresh" onClick={refreshReportList}>🔄 Refresh</button>
        </div>
        <div className="card">
          {reports.length === 0 ? (
            <div className="reports-empty-state">
              <div className="reports-empty-icon">📭</div>
              <p className="reports-empty-text">No reports generated yet.</p>
              <p className="reports-empty-sub">Use the cards above to generate your first institutional research report.</p>
            </div>
          ) : (
            <div className="reports-history-table-wrap">
              <table className="reports-history-table">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Report ID</th>
                    <th>Stock Symbol</th>
                    <th>Generated</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((r) => (
                    <tr key={r.report_id} className={previewId === r.report_id ? 'active-preview-row' : ''}>
                      <td><span className="reports-type-chip">{typeLabel(r.type)}</span></td>
                      <td className="reports-id-cell">{r.report_id}</td>
                      <td style={{ fontWeight: 'bold' }}>{r.symbol || '—'}</td>
                      <td>{formatDate(r.generated_at)}</td>
                      <td>
                        <div className="reports-action-btns">
                          <button
                            className="reports-action-btn reports-action-preview"
                            onClick={() => setPreviewId(r.report_id)}
                            title="Preview"
                          >👁️</button>
                          <a
                            className="reports-action-btn reports-action-pdf"
                            href={getReportDownloadUrl(r.report_id, 'pdf')}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="Download PDF"
                          >📥</a>
                          <a
                            className="reports-action-btn reports-action-html"
                            href={getReportDownloadUrl(r.report_id, 'html')}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="Download HTML"
                          >🌐</a>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

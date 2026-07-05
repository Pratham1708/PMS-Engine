import React, { useEffect, useState } from 'react';
import { listLabReports, generateLabReport, listExperiments, getLabReportPreviewUrl, getLabReportHtmlUrl, getLabReportPdfUrl } from '../../api/labApi';

const REPORT_TYPES = [
  { value: 'indicator', label: 'Indicator Backtest & Optimize' },
  { value: 'model', label: 'Model Research Lab' },
  { value: 'portfolio', label: 'Portfolio Performance & Rebalancing' },
  { value: 'validation', label: 'Recommendation Validation Audit' },
  { value: 'engine', label: 'Engine score Validation' }
];

export default function LabReports() {
  const [reports, setReports] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Selection states
  const [selectedType, setSelectedType] = useState('indicator');
  const [selectedExpId, setSelectedExpId] = useState('');
  
  // Generation state
  const [generating, setGenerating] = useState(false);
  const [genMessage, setGenMessage] = useState('');
  
  // Preview state
  const [previewReportId, setPreviewReportId] = useState(null);

  const fetchReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listLabReports();
      setReports(res.data || []);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch list of generated lab reports.');
    } finally {
      setLoading(false);
    }
  };

  const fetchExperimentsForType = async (type) => {
    try {
      let moduleFilter = '';
      if (type === 'indicator') moduleFilter = 'indicator_backtest,indicator_optimize';
      else if (type === 'model') moduleFilter = 'model_compare';
      else if (type === 'portfolio') moduleFilter = 'portfolio_backtest';
      else if (type === 'engine') moduleFilter = 'pms_score_validation';
      
      if (!moduleFilter) {
        setExperiments([]);
        setSelectedExpId('');
        return;
      }

      // Check if we have multiple comma modules, call separately or list all
      const modules = moduleFilter.split(',');
      let allExps = [];
      for (const mod of modules) {
        const res = await listExperiments({ module: mod });
        allExps = [...allExps, ...(res.data || [])];
      }
      
      const completed = allExps.filter((e) => e.status === 'complete');
      setExperiments(completed);
      if (completed.length > 0) {
        setSelectedExpId(completed[0].experiment_id);
      } else {
        setSelectedExpId('');
      }
    } catch (err) {
      console.error('Failed to load experiments for report type:', err);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  useEffect(() => {
    fetchExperimentsForType(selectedType);
  }, [selectedType]);

  const handleGenerate = async () => {
    setError(null);
    setGenMessage('');
    
    if (selectedType !== 'validation' && !selectedExpId) {
      alert('This report type requires selecting a completed experiment.');
      return;
    }

    setGenerating(true);
    try {
      const payload = {
        report_type: selectedType,
        experiment_id: selectedType === 'validation' ? undefined : selectedExpId
      };
      const res = await generateLabReport(payload);
      setGenMessage(res.data?.message || 'Report compilation started in background...');
      
      // Reload reports list after a short timeout to let file writing complete
      setTimeout(() => {
        setGenerating(false);
        fetchReports();
      }, 3000);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to start report generation.');
      setGenerating(false);
    }
  };

  const togglePreview = (reportId) => {
    if (previewReportId === reportId) {
      setPreviewReportId(null);
    } else {
      setPreviewReportId(reportId);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '800' }}>📋 Jinja2 & PDF Research Report Compiler</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Compile print-ready, high-fidelity quantitative analysis summaries in HTML and PDF formats.
        </p>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px', marginBottom: '20px' }}>
          ⚠️ {error}
        </div>
      )}

      {genMessage && (
        <div style={{ padding: '12px 16px', background: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '6px', marginBottom: '20px' }}>
          ℹ️ {genMessage}
        </div>
      )}

      {/* Generator Tool */}
      <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)', marginBottom: '28px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '16px' }}>Generate Research Summary</h3>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '20px',
          alignItems: 'end'
        }}>
          <div style={{ flex: 1, minWidth: '220px' }}>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Report Type</label>
            <select
              className="input"
              style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
            >
              {REPORT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          {selectedType !== 'validation' && (
            <div style={{ flex: 1.5, minWidth: '280px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Target Experiment Run</label>
              {experiments.length === 0 ? (
                <select
                  className="input"
                  style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: 'var(--text-muted)' }}
                  disabled
                >
                  <option>No completed {selectedType} experiments found.</option>
                </select>
              ) : (
                <select
                  className="input"
                  style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: '6px', color: '#fff' }}
                  value={selectedExpId}
                  onChange={(e) => setSelectedExpId(e.target.value)}
                >
                  {experiments.map((e) => (
                    <option key={e.experiment_id} value={e.experiment_id}>
                      {e.name} ({e.started_at})
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}

          <button
            onClick={handleGenerate}
            className="btn-primary"
            style={{ padding: '10px 20px', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
            disabled={generating || (selectedType !== 'validation' && !selectedExpId)}
          >
            {generating ? 'Compiling Report...' : '🛠 Compile Research PDF'}
          </button>
        </div>
      </div>

      {/* Reports Listing */}
      <div className="card" style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-lg)' }}>
        <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Completed Reports Registry</h3>
        
        {loading && reports.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '30px' }}>
            <div className="spinner" style={{ margin: '0 auto 8px auto', border: '3px solid rgba(255,255,255,0.1)', borderTop: '3px solid var(--accent-primary)', borderRadius: '50%', width: '24px', height: '24px', animation: 'spin 1s linear infinite' }}></div>
          </div>
        ) : reports.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', textAlign: 'center', padding: '20px' }}>
            No research reports compiled yet. Select a template type above to run the compiler.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table" style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th>Report ID</th>
                    <th>Report Classification</th>
                    <th>Associated Experiment</th>
                    <th>Compiled At</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((rep) => (
                    <React.Fragment key={rep.report_id}>
                      <tr>
                        <td style={{ fontFamily: 'monospace', fontSize: '11px', color: 'var(--text-muted)' }}>
                          {rep.report_id.slice(0, 8)}...
                        </td>
                        <td>
                          <strong>{rep.report_type.toUpperCase()} REPORT</strong>
                        </td>
                        <td style={{ fontFamily: 'monospace', fontSize: '11px', color: 'var(--text-secondary)' }}>
                          {rep.experiment_id ? rep.experiment_id.slice(0, 8) : 'Global / Validation'}
                        </td>
                        <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                          {rep.generated_at}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <div style={{ display: 'inline-flex', gap: '6px' }}>
                            <button
                              onClick={() => togglePreview(rep.report_id)}
                              className="btn-secondary"
                              style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '4px' }}
                            >
                              {previewReportId === rep.report_id ? 'Close' : 'Preview'}
                            </button>
                            <a
                              href={getLabReportHtmlUrl(rep.report_id)}
                              className="btn-secondary"
                              style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '4px', textDecoration: 'none', display: 'inline-block' }}
                              download
                            >
                              HTML
                            </a>
                            {rep.pdf_path && (
                              <a
                                href={getLabReportPdfUrl(rep.report_id)}
                                className="btn-secondary"
                                style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '4px', textDecoration: 'none', display: 'inline-block' }}
                                download
                              >
                                PDF
                              </a>
                            )}
                          </div>
                        </td>
                      </tr>
                      {previewReportId === rep.report_id && (
                        <tr>
                          <td colSpan={5} style={{ padding: '20px', borderTop: '1px solid var(--border-primary)', borderBottom: '1px solid var(--border-primary)', background: '#0a0f1d' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                              <h4 style={{ fontSize: '13px', fontWeight: '700', color: 'var(--accent-primary)' }}>HTML Report Preview</h4>
                              <button onClick={() => setPreviewReportId(null)} className="btn-secondary" style={{ padding: '2px 8px', fontSize: '10px' }}>
                                Close Preview
                              </button>
                            </div>
                            <div style={{ width: '100%', height: '600px', border: '1px solid var(--border-primary)', borderRadius: '8px', overflow: 'hidden', background: '#fff' }}>
                              <iframe
                                src={getLabReportPreviewUrl(rep.report_id)}
                                style={{ width: '100%', height: '100%', border: 'none' }}
                                title="Report Preview"
                              />
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

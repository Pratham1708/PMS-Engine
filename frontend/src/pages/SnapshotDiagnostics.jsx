import { useState, useEffect } from 'react';
import axios from 'axios';
import './SnapshotDiagnostics.css';
import LoadingSpinner from '../components/common/LoadingSpinner';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export default function SnapshotDiagnostics() {
  const [snapshots, setSnapshots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [targetDate, setTargetDate] = useState('');
  const [generating, setGenerating] = useState(false);
  const [actionMessage, setActionMessage] = useState(null);
  const [selectedSnapshot, setSelectedSnapshot] = useState(null);
  const [validationResults, setValidationResults] = useState([]);
  const [validatingId, setValidatingId] = useState(null);

  const loadSnapshots = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${BASE_URL}/snapshot/diagnostics/list`);
      setSnapshots(res.data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('Failed to load snapshot diagnostics. Make sure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSnapshots();
  }, []);

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!targetDate) return;
    try {
      setGenerating(true);
      setActionMessage({ type: 'info', text: `Triggering snapshot generation for ${targetDate}...` });
      const res = await axios.post(`${BASE_URL}/snapshot/generate?date=${targetDate}`);
      setActionMessage({ type: 'success', text: res.data.message || `Pipeline started for ${targetDate}.` });
      
      // Auto reload list after 5 seconds to show progress
      setTimeout(loadSnapshots, 5000);
    } catch (err) {
      console.error(err);
      setActionMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to start snapshot pipeline.' });
    } finally {
      setGenerating(false);
    }
  };

  const handleValidate = async (snapshotId) => {
    // Find the snapshot object from list to potentially select it
    const targetSnap = snapshots.find(s => s.snapshot_id === snapshotId);
    try {
      setValidatingId(snapshotId);
      setActionMessage({ type: 'info', text: 'Running snapshot integrity checks...' });
      const res = await axios.post(`${BASE_URL}/snapshot/${snapshotId}/validate`);
      setActionMessage({ 
        type: 'success', 
        text: `Validation complete. Status: ${res.data.status}, Score: ${res.data.score}%` 
      });
      // Show results in the validation panel — auto-select the row if not already selected
      const checks = res.data.checks || [];
      setValidationResults(checks);
      if (targetSnap) setSelectedSnapshot(targetSnap);
      loadSnapshots();
    } catch (err) {
      console.error(err);
      setActionMessage({ type: 'error', text: err.response?.data?.detail || 'Validation execution failed.' });
    } finally {
      setValidatingId(null);
    }
  };

  const handleDelete = async (snapshotId, date) => {
    if (!window.confirm(`Are you absolutely sure you want to delete the snapshot for ${date}? This will delete all record entries cascade-wide.`)) {
      return;
    }
    try {
      setActionMessage({ type: 'info', text: `Deleting snapshot for ${date}...` });
      const res = await axios.delete(`${BASE_URL}/snapshot/${snapshotId}`);
      setActionMessage({ type: 'success', text: res.data?.message || `Snapshot ${date} deleted successfully.` });
      if (selectedSnapshot?.snapshot_id === snapshotId) {
        setSelectedSnapshot(null);
        setValidationResults([]);
      }
      loadSnapshots();
    } catch (err) {
      console.error(err);
      setActionMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to delete snapshot.' });
    }
  };

  const inspectValidation = async (snap) => {
    setSelectedSnapshot(snap);
    setValidationResults([]);
    try {
      // GET /snapshot/{date}/validation returns a bare list of ValidationResult objects
      const res = await axios.get(`${BASE_URL}/snapshot/${snap.snapshot_date}/validation`);
      // res.data is a list directly, not a dict with a validation_checks key
      setValidationResults(Array.isArray(res.data) ? res.data : (res.data.validation_checks || []));
    } catch (err) {
      console.error(err);
      // If validation not run/found, validationResults remains empty
    }
  };

  if (loading && snapshots.length === 0) return <LoadingSpinner />;

  return (
    <div className="diagnostics-page">
      <div className="diagnostics-header">
        <h1 className="diagnostics-title">🔧 Snapshot Diagnostics & Administration</h1>
        <p className="diagnostics-subtitle">
          Manage snapshot lifecycles, monitor indicators/scores population integrity, and trigger custom-date historical generation.
        </p>
      </div>

      {actionMessage && (
        <div className={`action-alert alert-${actionMessage.type}`}>
          {actionMessage.text}
          <button className="alert-close" onClick={() => setActionMessage(null)}>×</button>
        </div>
      )}

      {/* Control Panel */}
      <div className="control-panel-grid">
        <div className="control-card trigger-generator-card">
          <h3>📅 Trigger Historical Snapshot Generation</h3>
          <p className="card-desc">
            Manually trigger the Daily Ingestion and Scoring Pipeline for a specific trading day. The system will load OHLCV prices, compute technical indicators, ML models, and PMS default scores.
          </p>
          <form className="generate-form" onSubmit={handleGenerate}>
            <div className="input-group">
              <label>Target Date</label>
              <input 
                type="date" 
                value={targetDate} 
                onChange={(e) => setTargetDate(e.target.value)} 
                required 
              />
            </div>
            <button className="btn btn-primary" type="submit" disabled={generating}>
              {generating ? 'Starting Pipeline...' : '🚀 Trigger Generation'}
            </button>
          </form>
        </div>

        <div className="control-card stats-summary-card">
          <h3>📊 Pipeline Overview</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-val">{snapshots.length}</span>
              <span className="stat-lbl">Total Snapshots</span>
            </div>
            <div className="stat-item">
              <span className="stat-val text-green">
                {snapshots.filter(s => s.status?.startsWith('completed') || s.status === 'published').length}
              </span>
              <span className="stat-lbl">Completed</span>
            </div>
            <div className="stat-item">
              <span className="stat-val text-yellow">
                {snapshots.filter(s => s.status === 'draft' || s.status === 'generating').length}
              </span>
              <span className="stat-lbl">Draft / Generating</span>
            </div>
            <div className="stat-item">
              <span className="stat-val text-red">
                {snapshots.filter(s => s.status === 'failed').length}
              </span>
              <span className="stat-lbl">Failed</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Left Snapshots Table, Right Validation Inspector */}
      <div className="diagnostics-layout-grid">
        <div className="snapshots-list-col">
          <div className="table-card">
            <div className="table-header">
              <h3>📦 Database Snapshots Registry</h3>
              <button className="btn btn-secondary btn-sm" onClick={loadSnapshots}>🔄 Refresh Registry</button>
            </div>
            <div className="table-wrapper">
              <table className="diagnostics-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Records (S / I / Sc)</th>
                    <th>Validation</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {snapshots.map((snap) => {
                    const isSelected = selectedSnapshot?.snapshot_id === snap.snapshot_id;
                    const statusClass = `status-${snap.status || 'unknown'}`;
                    
                    return (
                      <tr 
                        key={snap.snapshot_id} 
                        className={isSelected ? 'selected-row' : ''}
                        onClick={() => inspectValidation(snap)}
                      >
                        <td>
                          <div className="date-cell">
                            <strong>{snap.snapshot_date}</strong>
                            <span className="sub-id">{snap.snapshot_id?.substring(0, 8)}...</span>
                          </div>
                        </td>
                        <td>
                          <span className={`status-pill ${statusClass}`}>
                            {snap.status?.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td>
                          <div className="counts-cell">
                            <span className="count-pill badge-stock" title="Stocks Count">{snap.stocks_count}</span>
                            <span className="count-pill badge-ind" title="Indicators Count">{snap.indicators_count}</span>
                            <span className="count-pill badge-score" title="Scores Count">{snap.scores_count}</span>
                          </div>
                        </td>
                        <td>
                          <div className="validation-cell">
                            {snap.validation_passed ? (
                              <span className="val-score score-pass">
                                Pass ({snap.validation_score}%)
                              </span>
                            ) : (
                              <span className="val-score score-fail">
                                Fail ({snap.validation_score || 0}%)
                              </span>
                            )}
                          </div>
                        </td>
                        <td>
                          <div className="actions-cell" onClick={(e) => e.stopPropagation()}>
                            <button 
                              className="btn btn-action" 
                              onClick={() => handleValidate(snap.snapshot_id)}
                              disabled={validatingId === snap.snapshot_id}
                              title="Re-run validation checks"
                            >
                              {validatingId === snap.snapshot_id ? '...' : '🛡️'}
                            </button>
                            <button 
                              className="btn btn-action btn-danger" 
                              onClick={() => handleDelete(snap.snapshot_id, snap.snapshot_date)}
                              title="Delete snapshot & cascading records"
                            >
                              🗑️
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Validation Inspector Column */}
        <div className="validation-inspector-col">
          <div className="inspector-card">
            <h3>🔬 Integrity Validation Details</h3>
            {!selectedSnapshot ? (
              <div className="inspector-empty">
                Select a snapshot date from the table to inspect pre-publish validation rules and diagnostic values.
              </div>
            ) : (
              <div className="inspector-content">
                <div className="inspector-header-details">
                  <h4>Snapshot Date: {selectedSnapshot.snapshot_date}</h4>
                  <div className="inspector-score-summary">
                    Validation Score: <strong>{selectedSnapshot.validation_score || 0}%</strong>
                  </div>
                </div>

                {selectedSnapshot.failure_reason && selectedSnapshot.failure_reason !== 'None' && (
                  <div className="failure-reason-box">
                    <strong>Failure Details:</strong>
                    <p>{selectedSnapshot.failure_reason}</p>
                  </div>
                )}

                <div className="checks-list">
                  {validationResults.length === 0 ? (
                    <div className="loading-checks">
                      No validation rule details loaded. Try running integrity validation first.
                    </div>
                  ) : (
                    <table className="inspector-checks-table">
                      <thead>
                        <tr>
                          <th>Rule Check</th>
                          <th>Status</th>
                          <th>Detail</th>
                        </tr>
                      </thead>
                      <tbody>
                        {validationResults.map((check) => {
                          const statusClass = `chk-${check.status}`;
                          return (
                            <tr key={check.check_name}>
                              <td>
                                <strong>{check.check_name?.replace(/_/g, ' ').toUpperCase()}</strong>
                              </td>
                              <td>
                                <span className={`check-pill ${statusClass}`}>{check.status}</span>
                              </td>
                              <td className="detail-txt">{check.detail || '—'}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

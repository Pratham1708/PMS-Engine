import { useState, useEffect } from 'react';
import { fetchSnapshotStatus, triggerSnapshotGeneration } from '../../api/stocks';
import QuantResearchLabModal from '../pipeline/QuantResearchLabModal';

const FRESHNESS_CONFIG = {
  fresh:   { label: 'Fresh',   color: '#10b981', bg: 'rgba(16,185,129,0.12)', dot: '#10b981' },
  recent:  { label: 'Recent',  color: '#3b82f6', bg: 'rgba(59,130,246,0.12)', dot: '#3b82f6' },
  aging:   { label: 'Aging',   color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', dot: '#f59e0b' },
  stale:   { label: 'Stale',   color: '#ef4444', bg: 'rgba(239,68,68,0.12)',  dot: '#ef4444' },
  no_data: { label: 'No Data', color: '#6b7280', bg: 'rgba(107,114,128,0.12)',dot: '#9ca3af' },
};

export default function SnapshotBanner() {
  const [status, setStatus] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [isLabOpen, setIsLabOpen] = useState(false);

  const loadStatus = async () => {
    try {
      const res = await fetchSnapshotStatus();
      setStatus(res.data);
    } catch {
      // Silently fail — banner is non-critical
    }
  };

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleGenerate = async () => {
    if (generating) return;
    setGenerating(true);
    setError(null);
    try {
      await triggerSnapshotGeneration();
      setIsLabOpen(true);
      setTimeout(loadStatus, 3000);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to start pipeline';
      setError(msg);
    } finally {
      setTimeout(() => setGenerating(false), 2000);
    }
  };

  if (!status) return null;

  const fresh = FRESHNESS_CONFIG[status.data_freshness] || FRESHNESS_CONFIG.no_data;
  const snap = status.latest_snapshot;
  const isRunning = status.in_progress > 0;

  return (
    <>
      <div className="snapshot-banner">
        {/* Left: badge */}
        <div className="snapshot-banner-left">
          {isRunning ? (
            <div
              className="snapshot-badge snapshot-badge--running"
              onClick={() => setIsLabOpen(true)}
              style={{ cursor: 'pointer' }}
              title="Click to view live Quantitative Research Laboratory"
            >
              <span className="snapshot-badge-dot snapshot-badge-dot--pulse" />
              ⚡ Pipeline Active (View Lab)
            </div>
          ) : snap ? (
            <div className="snapshot-badge snapshot-badge--official">
              <span className="snapshot-badge-dot" />
              Official Snapshot
            </div>
          ) : (
            <div className="snapshot-badge snapshot-badge--none">
              <span className="snapshot-badge-dot snapshot-badge-dot--grey" />
              No Snapshot
            </div>
          )}
        </div>

        {/* Center: snapshot info */}
        <div className="snapshot-banner-center">
          {snap ? (
            <>
              <span className="snapshot-banner-date">
                📅 {snap.snapshot_date}
              </span>
              <span className="snapshot-banner-sep">·</span>
              <span className="snapshot-banner-stocks">
                {snap.stocks_processed} stocks
              </span>
              {snap.pipeline_duration_sec && (
                <>
                  <span className="snapshot-banner-sep">·</span>
                  <span className="snapshot-banner-dur">
                    {snap.pipeline_duration_sec.toFixed(0)}s pipeline
                  </span>
                </>
              )}
              <span className="snapshot-banner-sep">·</span>
              <span
                className="snapshot-banner-freshness"
                style={{ color: fresh.color, background: fresh.bg }}
              >
                <span
                  className="snapshot-banner-fresh-dot"
                  style={{ background: fresh.dot }}
                />
                {fresh.label}
              </span>
            </>
          ) : (
            <span className="snapshot-banner-empty">
              No snapshot generated yet — click Generate to publish today's research
            </span>
          )}
          {error && <span className="snapshot-banner-error">{error}</span>}
        </div>

        {/* Right: action buttons */}
        <div className="snapshot-banner-right" style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setIsLabOpen(true)}
            style={{
              background: 'rgba(56, 189, 248, 0.15)',
              color: '#38bdf8',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              borderRadius: '6px',
              padding: '6px 12px',
              fontWeight: '700',
              fontSize: '12px',
              cursor: 'pointer',
            }}
          >
            🔬 Research Lab
          </button>

          <button
            className={`snapshot-banner-btn ${generating || isRunning ? 'snapshot-banner-btn--busy' : ''}`}
            onClick={handleGenerate}
            disabled={generating || isRunning}
            title="Generate Official Daily Snapshot"
          >
            {isRunning ? (
              <><span className="btn-spinner" />Running…</>
            ) : generating ? (
              <><span className="btn-spinner" />Starting…</>
            ) : (
              <>⚡ Generate Snapshot</>
            )}
          </button>
        </div>
      </div>

      <QuantResearchLabModal
        isOpen={isLabOpen}
        onClose={() => setIsLabOpen(false)}
      />
    </>
  );
}

import React, { useState } from 'react';
import { usePipelineExecutionContext } from '../../hooks/usePipelineExecutionContext';
import LabStageNodes from './LabStageNodes';
import StockQueuePanel from './StockQueuePanel';
import MiniOHLCChart from './MiniOHLCChart';
import FeatureAndMLPipeline from './FeatureAndMLPipeline';
import CompositeScoreAnimator from './CompositeScoreAnimator';
import SnapshotVaultIntegrity from './SnapshotVaultIntegrity';
import PipelineTimelineScrubber from './PipelineTimelineScrubber';
import ExecutionLogTerminal from './ExecutionLogTerminal';
import StockDetailDrawer from './StockDetailDrawer';

export default function QuantResearchLabModal({ isOpen, onClose, replaySnapshotId = null }) {
  const ctx = usePipelineExecutionContext();
  const [selectedStock, setSelectedStock] = useState(null);

  // If a replay snapshotId is passed, auto-start replay on mount/change
  React.useEffect(() => {
    if (isOpen && replaySnapshotId && ctx.mode !== 'replay') {
      ctx.startReplay(replaySnapshotId);
    }
  }, [isOpen, replaySnapshotId]);

  if (!isOpen) return null;

  const activeStockData = ctx.activeStock ? ctx.stockPayloads[ctx.activeStock] : null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(2, 6, 23, 0.96)',
        backdropFilter: 'blur(12px)',
        zIndex: 9999,
        padding: 'clamp(12px, 3vw, 24px)',
        overflowY: 'auto',
        color: '#f8fafc',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #1e293b', paddingBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: '#38bdf8', color: '#0f172a', padding: '6px 12px', borderRadius: '8px', fontWeight: '800', fontSize: '14px', flexShrink: 0 }}>
            QRL
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '800', color: '#f8fafc', letterSpacing: '-0.02em' }}>
              Quantitative Research Laboratory
            </h2>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>
              Institutional AI-Powered Pipeline Visualizer · {ctx.mode === 'replay' ? `Replay Mode (${ctx.snapshotId})` : 'Live Stream'}
            </span>
          </div>
        </div>

        {/* Right Header Stats & Close */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>PIPELINE PROGRESS</div>
            <div style={{ fontSize: '16px', fontWeight: '800', color: '#38bdf8' }}>{ctx.pctComplete.toFixed(0)}%</div>
          </div>

          {ctx.mode === 'replay' && (
            <button
              onClick={ctx.switchToLive}
              style={{ background: '#1e293b', color: '#38bdf8', border: '1px solid #334155', borderRadius: '6px', padding: '6px 12px', fontSize: '12px', cursor: 'pointer', fontWeight: '600' }}
            >
              ⚡ Switch to Live Stream
            </button>
          )}

          <button
            onClick={onClose}
            style={{ background: '#ef4444', color: '#ffffff', border: 'none', borderRadius: '8px', padding: '8px 16px', fontWeight: '700', fontSize: '13px', cursor: 'pointer' }}
          >
            Close Laboratory
          </button>
        </div>
      </div>

      {/* Stage Node Graph */}
      <LabStageNodes currentStage={ctx.currentStage} completedStages={ctx.completedStages} />

      {/* Main Grid */}
      <div className="qrl-main-grid">
        {/* Left: Stock Queue Panel */}
        <StockQueuePanel
          activeStock={ctx.activeStock}
          completedStocks={ctx.completedStocks}
          onSelectStock={(sym) => setSelectedStock(sym)}
        />

        {/* Right: Main Laboratory Panels */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <MiniOHLCChart symbol={ctx.activeStock} ohlcv={activeStockData?.ohlcv} />
          <FeatureAndMLPipeline indicators={activeStockData?.indicators} />
          <CompositeScoreAnimator scoreData={activeStockData} />
          <SnapshotVaultIntegrity completedStocksCount={ctx.completedStocks.length} />
        </div>
      </div>

      {/* Execution Terminal Log */}
      <ExecutionLogTerminal logs={ctx.logs} />

      {/* Bottom Interactive Timeline Scrubber */}
      <PipelineTimelineScrubber
        timelineEvents={ctx.timelineEvents}
        mode={ctx.mode}
        isPlayingReplay={ctx.isPlayingReplay}
        replayIndex={ctx.replayIndex}
        totalReplayEvents={ctx.replayEvents.length}
        replaySpeed={ctx.replaySpeed}
        onTogglePlayPause={ctx.toggleReplayPlayPause}
        onStepChange={ctx.setReplayStep}
        onSpeedChange={ctx.setReplaySpeed}
      />

      {/* Stock Detail Side Drawer */}
      {selectedStock && (
        <StockDetailDrawer
          symbol={selectedStock}
          stockPayload={ctx.stockPayloads[selectedStock]}
          onClose={() => setSelectedStock(null)}
        />
      )}
    </div>
  );
}

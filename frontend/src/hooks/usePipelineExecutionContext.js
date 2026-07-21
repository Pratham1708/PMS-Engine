import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { fetchPipelineStatus } from '../api/stocks';

export const LAB_STAGES = [
  { id: '01_load_security_master', name: 'Market Data Observatory', code: 'MDO' },
  { id: '02_download_ohlcv', name: 'OHLCV Ingestion Engine', code: 'OIE' },
  { id: '06_generate_indicators', name: 'Technical Analysis Engine', code: 'TAE' },
  { id: '07_generate_features', name: 'Feature Engineering Lab', code: 'FEL' },
  { id: '08_run_ml_models', name: 'Machine Learning Laboratory', code: 'MLL' },
  { id: '10_generate_risk_scores', name: 'Risk Analytics Lab', code: 'RAL' },
  { id: '13_generate_confidence_scores', name: 'Reliability Diagnostics', code: 'RDL' },
  { id: '14_generate_composite_scores', name: 'Composite Scoring Engine', code: 'CSE' },
  { id: '15_generate_recommendations', name: 'Recommendation Engine', code: 'RCE' },
  { id: '22_publish_snapshot', name: 'Snapshot Vault & Database', code: 'SVD' },
];

export function usePipelineExecutionContext() {
  const [mode, setMode] = useState('live'); // 'live' | 'replay'
  const [status, setStatus] = useState('idle'); // 'idle' | 'running' | 'completed' | 'failed'
  const [snapshotId, setSnapshotId] = useState(null);
  const [currentStage, setCurrentStage] = useState('01_load_security_master');
  const [completedStages, setCompletedStages] = useState(new Set());
  const [pctComplete, setPctComplete] = useState(0);
  const [elapsedSec, setElapsedSec] = useState(0);
  const [activeStock, setActiveStock] = useState(null);
  const [completedStocks, setCompletedStocks] = useState([]);
  const [queuedStocks, setQueuedStocks] = useState([]);
  const [stockPayloads, setStockPayloads] = useState({});
  const [dbInserts, setDbInserts] = useState({ master: 0, stock: 0, indicator: 0, score: 0 });
  const [logs, setLogs] = useState([]);
  const [timelineEvents, setTimelineEvents] = useState([]);

  // Replay state
  const [replayEvents, setReplayEvents] = useState([]);
  const [replayIndex, setReplayIndex] = useState(0);
  const [isPlayingReplay, setIsPlayingReplay] = useState(false);
  const [replaySpeed, setReplaySpeed] = useState(1);

  const wsRef = useRef(null);
  const timerRef = useRef(null);
  const pollingRef = useRef(null);
  const isWsConnectedRef = useRef(false);

  // Process a single event envelope
  const processEvent = useCallback((evt) => {
    if (!evt) return;
    const { event_type, stage_name, stock_symbol, payload, timestamp } = evt;
    const logTime = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();

    if (event_type === 'pipeline_started') {
      setStatus('running');
      setSnapshotId(payload?.snapshot_id || evt.snapshot_id);
      setPctComplete(0);
      setCompletedStages(new Set());
      setCompletedStocks([]);
      setStockPayloads({});
      setLogs((prev) => [...prev, { time: logTime, text: `Pipeline started: ${payload?.snapshot_id || ''}`, type: 'info' }]);
      setTimelineEvents((prev) => [...prev, { time: logTime, label: 'Pipeline Started' }]);
    } else if (event_type === 'stage_started') {
      setCurrentStage(stage_name || payload?.stage);
      if (payload?.pct_complete) setPctComplete(payload.pct_complete);
      setLogs((prev) => [...prev, { time: logTime, text: `Started stage: ${stage_name || payload?.stage}`, type: 'stage' }]);
    } else if (event_type === 'stage_completed') {
      const stg = stage_name || payload?.stage;
      setCompletedStages((prev) => new Set([...prev, stg]));
      setLogs((prev) => [...prev, { time: logTime, text: `Completed stage: ${stg} (${payload?.duration_sec || 0}s)`, type: 'success' }]);
      setTimelineEvents((prev) => [...prev, { time: logTime, label: `Stage: ${stg}` }]);
    } else if (event_type === 'stage_progress') {
      const sym = stock_symbol || payload?.stock;
      if (sym) {
        setActiveStock(sym);
        setCompletedStocks((prev) => (prev.includes(sym) ? prev : [...prev, sym]));
        if (payload?.ohlcv || payload?.payload || payload?.indicators) {
          setStockPayloads((prev) => ({
            ...prev,
            [sym]: {
              ...(prev[sym] || {}),
              ohlcv: payload.ohlcv || prev[sym]?.ohlcv,
              indicators: payload.indicators || payload.payload || prev[sym]?.indicators,
            },
          }));
        }
      }
      if (payload?.log) {
        setLogs((prev) => [...prev, { time: logTime, text: payload.log, type: 'progress' }]);
      }
    } else if (event_type === 'pipeline_completed') {
      setStatus('completed');
      setPctComplete(100);
      setActiveStock(null);
      setLogs((prev) => [...prev, { time: logTime, text: 'Pipeline completed successfully!', type: 'success' }]);
      setTimelineEvents((prev) => [...prev, { time: logTime, label: 'Pipeline Published' }]);
    } else if (event_type === 'initial_state') {
      if (payload?.monitor) {
        const mon = payload.monitor;
        setStatus(mon.status || 'idle');
        if (mon.current_stage) setCurrentStage(mon.current_stage);
        if (mon.pct_complete) setPctComplete(mon.pct_complete);
        if (mon.elapsed_sec) setElapsedSec(mon.elapsed_sec);
      }
    }
  }, []);

  // Robust WebSocket Connection & Polling Fallback
  useEffect(() => {
    if (mode !== 'live') return;

    let apiHost = 'localhost:8000';
    const envUrl = import.meta.env.VITE_API_URL;
    if (envUrl) {
      try {
        const parsed = new URL(envUrl);
        apiHost = parsed.host;
      } catch (e) {}
    } else if (window.location.hostname) {
      apiHost = `${window.location.hostname}:8000`;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${apiHost}/api/ws/pipeline`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        isWsConnectedRef.current = true;
        setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), text: `Connected to live stream at ${wsUrl}`, type: 'info' }]);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          processEvent(data);
        } catch (err) {
          console.error('[WebSocket] Parse error:', err);
        }
      };

      ws.onerror = () => {
        isWsConnectedRef.current = false;
        setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), text: 'WebSocket connection error (switched to polling fallback)', type: 'error' }]);
      };

      ws.onclose = () => {
        isWsConnectedRef.current = false;
      };

      return () => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      };
    } catch (e) {
      console.error('[WebSocket] Init error:', e);
    }
  }, [mode, processEvent]);

  // Polling Fallback (if WebSocket is disconnected or in cold start)
  useEffect(() => {
    if (mode !== 'live') return;

    const pollStatus = async () => {
      try {
        const res = await fetchPipelineStatus();
        if (res?.data) {
          const data = res.data;
          setStatus(data.status || 'idle');
          if (data.current_stage) setCurrentStage(data.current_stage);
          if (data.pct_complete !== undefined) setPctComplete(data.pct_complete);
          if (data.elapsed_sec !== undefined) setElapsedSec(data.elapsed_sec);
          if (data.stage_log && data.stage_log.length > 0) {
            const completed = new Set(data.stage_log.map((s) => s.stage));
            setCompletedStages(completed);
          }
        }
      } catch (err) {
        // Silently ignore polling errors
      }
    };

    pollStatus();
    pollingRef.current = setInterval(pollStatus, 1500);

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [mode]);

  // Replay playback loop
  useEffect(() => {
    if (mode !== 'replay' || !isPlayingReplay || replayEvents.length === 0) return;

    const intervalMs = Math.max(100, Math.round(1000 / replaySpeed));

    timerRef.current = setInterval(() => {
      setReplayIndex((prevIndex) => {
        if (prevIndex >= replayEvents.length - 1) {
          setIsPlayingReplay(false);
          clearInterval(timerRef.current);
          return prevIndex;
        }
        const nextIdx = prevIndex + 1;
        const evt = replayEvents[nextIdx];
        if (evt) {
          processEvent(evt.payload || evt);
        }
        return nextIdx;
      });
    }, intervalMs);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [mode, isPlayingReplay, replayEvents, replaySpeed, processEvent]);

  // Start Replay mode for a snapshot
  const startReplay = async (targetSnapshotId) => {
    try {
      setMode('replay');
      setIsPlayingReplay(false);
      setReplayIndex(0);
      setSnapshotId(targetSnapshotId);
      setStatus('running');
      setCompletedStages(new Set());
      setCompletedStocks([]);
      setStockPayloads({});
      setLogs([{ time: new Date().toLocaleTimeString(), text: `Loading replay events for ${targetSnapshotId}...`, type: 'info' }]);

      const res = await axios.get(`/api/snapshot/pipeline/${targetSnapshotId}/events`);
      const events = res.data?.events || [];

      if (events.length === 0) {
        setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), text: `No stored replay events found for ${targetSnapshotId}`, type: 'error' }]);
        setStatus('idle');
        return;
      }

      setReplayEvents(events);
      setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), text: `Loaded ${events.length} replay events. Click Play to start.`, type: 'success' }]);
      setIsPlayingReplay(true);
    } catch (err) {
      console.error('[Replay] Failed to load replay events:', err);
      setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), text: `Failed to load replay events: ${err.message}`, type: 'error' }]);
    }
  };

  const toggleReplayPlayPause = () => {
    setIsPlayingReplay((prev) => !prev);
  };

  const setReplayStep = (index) => {
    if (index < 0 || index >= replayEvents.length) return;
    setReplayIndex(index);
    const evt = replayEvents[index];
    if (evt) {
      processEvent(evt.payload || evt);
    }
  };

  const switchToLive = () => {
    setMode('live');
    setIsPlayingReplay(false);
    setReplayEvents([]);
  };

  return {
    mode,
    status,
    snapshotId,
    currentStage,
    completedStages,
    pctComplete,
    elapsedSec,
    activeStock,
    completedStocks,
    queuedStocks,
    stockPayloads,
    dbInserts,
    logs,
    timelineEvents,

    // Replay controls
    replayEvents,
    replayIndex,
    isPlayingReplay,
    replaySpeed,
    setReplaySpeed,
    startReplay,
    toggleReplayPlayPause,
    setReplayStep,
    switchToLive,
  };
}

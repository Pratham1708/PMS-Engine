# Frontend Architectural Context & Component Structure — PMS Engine

This document provides a comprehensive, detailed overview of the frontend codebase of the PMS Engine. Use this reference when planning new features, refactoring existing views, or integrating additional analytics.

---

## 1. Core Technology Stack & Architecture

- **Framework**: React 19 (`react`, `react-dom`) + Vite (`vite` v8)
- **Routing**: React Router DOM v7 (`react-router-dom`)
- **Styling System**: CSS Tokenized Design System (`src/index.css`) with institutional dark theme tokens, HSL color palettes, glassmorphic containers, and micro-animations.
- **Financial Charting**: TradingView Lightweight Charts (`lightweight-charts` v5.2) + Recharts (`recharts` v3.8)
- **HTTP & Event Streaming**:
  - Axios client (`src/api/client.js`) configured with `VITE_API_URL` fallback (`http://localhost:8000/api`).
  - WebSockets (`/api/ws/pipeline`) with automatic HTTP polling fallback for real-time Quantitative Research Laboratory streaming.

---

## 2. Directory Structure

```
frontend/src/
├── api/                             # API Integration Services
├── components/                      # Reusable UI Components
│   ├── common/                      # Reusable UI Molecules & Modals
│   ├── layout/                      # Page Shell & Navigation
│   ├── charts/                      # Financial & Interactive Charts
│   └── pipeline/                    # Quantitative Research Laboratory Visualizer
├── hooks/                           # Custom React Hooks & State Controllers
├── pages/                           # Main Application Pages & Dashboards
│   └── QuantLab/                    # Specialized Quantitative Research Sub-Labs (24 Labs)
├── App.jsx                          # Root Router & Shell Setup
├── index.css                        # Tokenized CSS Design System
└── main.jsx                         # React Entrypoint
```

---

## 3. Detailed Component Breakdown

### 3.1 API Services Layer (`src/api/`)

| File | Purpose & Responsibilities |
|---|---|
| `client.js` | Base Axios client instance with `baseURL` resolution (`import.meta.env.VITE_API_URL` or `http://localhost:8000/api`) and 90s timeout. |
| `stocks.js` | Core API functions for stock search, ratings, portfolios, daily snapshots, pipeline controls (`triggerSnapshotGeneration`, `fetchPipelineStatus`), and watchlists. |
| `labApi.js` | API client for Quant Research Laboratory endpoints (indicators, features, models, composite calibration, validation). |
| `strategyApi.js` | Quantitative Strategy Studio API calls (CRUD for custom strategy rules, signal definitions, parameters). |
| `backtestApi.js` | Backtesting Engine APIs (simulation runs, equity curves, trade logs, performance metrics). |
| `reports.js` | Executive & Institutional PDF report generation endpoints. |

---

### 3.2 Custom Hooks (`src/hooks/`)

| File | Description |
|---|---|
| `usePipelineExecutionContext.js` | Central state controller for live WebSocket event streaming (`/api/ws/pipeline`), sequence ordering, stock queue management, and historical Replay Mode (Play, Pause, Step, 1x/2x/5x/10x speeds). Features automatic HTTP polling fallback. |

---

### 3.3 Reusable Components (`src/components/`)

#### Common UI Elements (`src/components/common/`)
- **`SnapshotBanner.jsx`**: Global banner displayed across pages indicating official snapshot status, data freshness (`Fresh`, `Recent`, `Aging`, `Stale`), and quick trigger for `QuantResearchLabModal`.
- **`ExplainModal.jsx`**: XAI (Explainable AI) modal showing mathematical driver contributions, feature weights, rating rule breakdowns, and mathematical formulas for a stock.
- **`ExplainActions.jsx`**: Actionable recommendations and rating driver badges.
- **`RatingBadge.jsx`**: Color-coded badges for `STRONG BUY`, `BUY`, `HOLD`, `SELL`, `STRONG SELL`.
- **`ConfidenceBar.jsx`**: Institutional confidence level indicator bar.
- **`ScoreBar.jsx`**: Normalized 0–100 score visualizer bar.
- **`StatCard.jsx`**: Summary KPI metric card.
- **`LoadingSpinner.jsx`**: Loading spinner component.

#### Layout Components (`src/components/layout/`)
- **`Header.jsx`**: Top header bar with quick search, market regime status, system health indicators, and navigation shortcuts.
- **`Sidebar.jsx`**: Primary sidebar navigation linking to Snapshot Dashboard, Quant Lab, Strategy Studio, Screener, Backtests, and Reports.

#### Financial Charting Components (`src/components/charts/`)
- **`FinancialChart.jsx`**: TradingView Lightweight Charts candlestick component with EMA/SMA overlays, Volume sub-chart, RSI/MACD panels, and custom tooltips.
- **`SankeyFlow.jsx`**: Custom capital flow & score allocation visualizer diagram.
- **`ChartIndicators.jsx`**: Technical indicator toggle panel (EMA, SMA, Bollinger Bands, VWAP, Supertrend).
- **`ChartToolbar.jsx`**: Timeframe selectors (1D, 1W, 1M, 3M, 1Y, 5Y) and chart style toggles (Candlestick, Line, Area).
- **`ChartLegend.jsx`**: Interactive overlay legend displaying exact values under crosshair.
- **`ChartUtils.js` & `ChartTheme.js`**: Data converters, date formatters, and institutional dark theme color tokens.

#### Quantitative Research Laboratory Visualizer (`src/components/pipeline/`)
- **`QuantResearchLabModal.jsx`**: Master fullscreen modal container with header stats, mode toggle (Live vs Replay), and grid layout.
- **`LabStageNodes.jsx`**: 10-stage node workflow diagram (Market Data → Indicators → ML → Risk → Reliability → Composite → Recommendations → Snapshot Vault) with active glows and SVG particle flows.
- **`StockQueuePanel.jsx`**: Active stock processing status, completed stock chips, and queued stock lists.
- **`MiniOHLCChart.jsx`**: Live market quote preview (Open, High, Low, Close, Volume) and daily percentage change.
- **`FeatureAndMLPipeline.jsx`**: Visualizes Feature Engineering (OHLCV → Technicals → Feature Vectors) and ML Model outputs (Random Forest, XGBoost, LightGBM, GRU Sequence Encoding).
- **`CompositeScoreAnimator.jsx`**: Step-by-step additive score contribution animation (+Trend, +Momentum, +Volume, +ML, +Risk, +Reliability = Composite Score).
- **`SnapshotVaultIntegrity.jsx`**: DB insert row counters (`snapshot_master`, `snapshot_stock`, `snapshot_indicator`, `snapshot_score`) and 100% integrity validation badges.
- **`ExecutionLogTerminal.jsx`**: Real-time terminal log viewer with timestamp formatting and auto-scroll.
- **`PipelineTimelineScrubber.jsx`**: Interactive timeline scrubber with timestamped stage checkpoints & step controls.
- **`StockDetailDrawer.jsx`**: Interactive side drawer opening when any processed stock is clicked.

---

### 3.4 Main Pages & Dashboards (`src/pages/`)

#### Snapshot Publishing & Diagnostics
- **`SnapshotDashboard.jsx`**: Master control center for daily official snapshot generation, market pulse cards, top rating changes, and pipeline visualizer triggers.
- **`HistoricalSnapshots.jsx`**: Archive explorer for past daily snapshots with Replay Pipeline triggers.
- **`WhatsChanged.jsx`**: Snapshot comparison tool detailing rating upgrades, downgrades, and composite score deltas between dates.
- **`SnapshotDiagnostics.jsx`**: System diagnostics, data validation check results, and manual trigger controls.
- **`DataQuality.jsx`**: Pre-publish data quality and integrity report view.

#### Core Analytics & Research Workspace
- **`Dashboard.jsx`**: High-level portfolio summary, top opportunities, and rating distribution.
- **`MarketOverview.jsx`**: NIFTY 50 market pulse, sector performance heatmaps, and breadth metrics.
- **`StockDetail.jsx`**: In-depth single stock workspace with financial charts, indicator tables, ML scores, XAI drivers, and financial metrics.
- **`StockSearch.jsx`**: Fast search and universe navigation interface.
- **`ResearchWorkspace.jsx`**: Personalized stock watchlists and custom research tracking.
- **`Screener.jsx`**: Multi-factor stock screener filtering by ratings, composite scores, technicals, and sector.
- **`Ratings.jsx`**: Institutional rating distribution breakdown and sector heatmaps.
- **`SectorSnapshot.jsx`**: Sector aggregations, bull/bear ratios, and sector leaders.
- **`MarketBreadth.jsx`**: Advance/Decline ratios, 52-week highs/lows, and regime classifications.
- **`Portfolio.jsx`**: Capital allocation tool and portfolio optimization view.
- **`Reports.jsx`**: Institutional PDF report generator and archive.
- **`Watchlists.jsx`**: 16 smart automated watchlists (High Conviction, Momentum Leaders, Breakout Candidates, Quality, etc.).
- **`SystemOverview.jsx`**: Architectural documentation view of the PMS Engine.

#### Quantitative Strategy Studio & Backtesting
- **`QuantStrategyStudio.jsx`**: Strategy builder interface for defining custom entry/exit rules, composite weightings, and risk limits.
- **`StrategyValidation.jsx`**: Multi-phase strategy validation testing hub.
- **`BacktestResults.jsx`**: Detailed backtest results visualizer with equity curves, drawdown charts, trade logs, and Sharpe/Sortino metrics.
- **`BacktestHistory.jsx`**: Historical backtest execution run library.

#### Quant Research Laboratory Suite (`src/pages/QuantLab/`)
Contains 24 specialized quantitative research sandboxes:
- **`QuantLabHome.jsx`**: Research promotion workflow stepper.
- **`IndicatorLab.jsx`**: Custom indicator parameter tuning sandbox.
- **`FeatureLab.jsx`**: Feature engineering & Z-score normalization lab.
- **`ModelLab.jsx`**: ML model benchmarking & probability calibration.
- **`EnsembleLab.jsx`**: Model weight blending and ensemble sandbox.
- **`CompositeValidationLab.jsx`**: Composite scoring calibration & validation.
- **`PortfolioConstructionLab.jsx` & `PortfolioStrategies.jsx`**: Allocation and rebalancing strategies.
- **`Risk Analytics Labs`**: `MonteCarloLab`, `StressTestLab`, `PositionSizingLab`, `LiquidityLab`.
- **`Validation & Drift Labs`**: `EngineValidationLab`, `DriftMonitorLab`, `RegimeLab`, `CorrelatonLab`, `CrossIndicatorLab`, `HyperoptLab`.

---

## 4. Routing Architecture (`src/App.jsx`)

The routing shell uses React Router v7 and wraps pages in standard layout navigation:

```jsx
<Router>
  <SnapshotBanner />
  <div className="app-shell">
    <Sidebar />
    <main className="app-content">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/snapshot" element={<SnapshotDashboard />} />
        <Route path="/snapshot/archive" element={<HistoricalSnapshots />} />
        <Route path="/snapshot/compare" element={<WhatsChanged />} />
        <Route path="/snapshot/diagnostics" element={<SnapshotDiagnostics />} />
        <Route path="/stock/:symbol" element={<StockDetail />} />
        <Route path="/quant-lab" element={<QuantLabHome />} />
        <Route path="/strategy-studio" element={<QuantStrategyStudio />} />
        <Route path="/backtest/results/:runId" element={<BacktestResults />} />
        {/* Additional routes for Screener, Ratings, Sectors, Reports, etc. */}
      </Routes>
    </main>
  </div>
</Router>
```

---

## 5. Summary Guidelines for Future Frontend Enhancements

When adding new components or features:
1. **Maintain Design Aesthetics**: Reuse tokens from `src/index.css` (dark background `#020617`, card containers `#0f172a`, borders `#1e293b`, accent cyan `#38bdf8`, emerald `#10b981`, and amber `#f59e0b`).
2. **Reuse API Client**: Use `src/api/client.js` or specialized API modules (`stocks.js`, `labApi.js`) rather than raw `fetch()` calls.
3. **Data Flow**: Connect real-time or snapshot data directly to state/hooks without synthetic placeholders.
4. **Modularity**: Place reusable widgets in `src/components/common/` and domain-specific visualizers in specialized component subfolders (`charts/`, `pipeline/`).

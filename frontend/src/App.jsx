import { useState } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import ResearchWorkspace from './pages/ResearchWorkspace';
import Dashboard from './pages/Dashboard';
import StockSearch from './pages/StockSearch';
import StockDetail from './pages/StockDetail';
import MarketOverview from './pages/MarketOverview';
import Reports from './pages/Reports';
import QuantStrategyStudio from './pages/QuantStrategyStudio';
import StrategyValidation from './pages/StrategyValidation';
import BacktestResults from './pages/BacktestResults';
import BacktestHistory from './pages/BacktestHistory';

// Quant Lab Page Imports
import QuantLabHome from './pages/QuantLab/QuantLabHome';
import IndicatorLab from './pages/QuantLab/IndicatorLab';
import EngineValidationLab from './pages/QuantLab/EngineValidationLab';
import ModelLab from './pages/QuantLab/ModelLab';
import FeatureLab from './pages/QuantLab/FeatureLab';
import CompositeValidationLab from './pages/QuantLab/CompositeValidationLab';
import RecommendationValidation from './pages/QuantLab/RecommendationValidation';
import PortfolioStrategies from './pages/QuantLab/PortfolioStrategies';
import SectorLab from './pages/QuantLab/SectorLab';
import RegimeLab from './pages/QuantLab/RegimeLab';
import BenchmarkComparison from './pages/QuantLab/BenchmarkComparison';
import ExperimentHistory from './pages/QuantLab/ExperimentHistory';
import LabReports from './pages/QuantLab/LabReports';

import CrossIndicatorLab from './pages/QuantLab/CrossIndicatorLab';
import EnsembleLab from './pages/QuantLab/EnsembleLab';
import HyperoptLab from './pages/QuantLab/HyperoptLab';
import MonteCarloLab from './pages/QuantLab/MonteCarloLab';
import StressTestLab from './pages/QuantLab/StressTestLab';
import PositionSizingLab from './pages/QuantLab/PositionSizingLab';
import PortfolioConstructionLab from './pages/QuantLab/PortfolioConstructionLab';
import CorrelationLab from './pages/QuantLab/CorrelationLab';
import MarketBreadthLab from './pages/QuantLab/MarketBreadthLab';
import LiquidityLab from './pages/QuantLab/LiquidityLab';
import DriftMonitorLab from './pages/QuantLab/DriftMonitorLab';

// Snapshot Publishing Platform Components
import SnapshotBanner from './components/common/SnapshotBanner';
import SnapshotDashboard from './pages/SnapshotDashboard';
import Watchlists from './pages/Watchlists';
import WhatsChanged from './pages/WhatsChanged';
import SectorSnapshot from './pages/SectorSnapshot';
import MarketBreadth from './pages/MarketBreadth';
import HistoricalSnapshots from './pages/HistoricalSnapshots';
import DataQuality from './pages/DataQuality';
import SnapshotDiagnostics from './pages/SnapshotDiagnostics';



const PAGE_TITLES = {
  '/': 'Daily Research Snapshot Terminal',
  '/workspace': 'Institutional Research Workspace',
  '/watchlists': 'Smart Watchlists',
  '/changes': 'Daily Recommendation Changes',
  '/sectors': 'Sector Averages Snapshot',
  '/breadth': 'Market Breadth Indicators',
  '/archive': 'Historical Snapshot Archive',
  '/data-quality': 'Data Quality & Diagnostics',
  '/snapshot-diagnostics': 'Snapshot Diagnostics & Administration',
  '/dashboard': 'Dashboard Signals Cache',
  '/search': 'Stock Search',
  '/market': 'Market Overview',
  '/reports': 'Research Reports',
  '/studio': 'Quant Strategy Studio',
  '/lab': 'Quant Research Laboratory',

  '/lab/indicators': 'Indicator Lab',
  '/lab/engine': 'Engine Score Validation',
  '/lab/models': 'Model Research Lab',
  '/lab/features': 'Feature Selection Lab',
  '/lab/composite': 'Composite Weights Validation',
  '/lab/validation': 'Recommendation Audit Lab',
  '/lab/portfolio': 'Portfolio Strategies Backtester',
  '/lab/sector': 'Sector Analysis Lab',
  '/lab/regime': 'Market Regime Detection',
  '/lab/benchmark': 'Benchmark Comparison Lab',
  '/lab/experiments': 'Experiment History Registry',
  '/lab/reports': 'Quant Lab Reports Compiler',
  '/lab/cross-indicator': 'Cross-Indicator Lab',
  '/lab/ensemble': 'Ensemble Strategy Lab',
  '/lab/hyperopt': 'Parameter Hyperopt Lab',
  '/lab/monte-carlo': 'Monte Carlo Sandbox',
  '/lab/stress': 'Crisis Stress Tester',
  '/lab/sizing': 'Position Sizing Lab',
  '/lab/construction': 'Portfolio Construction Lab',
  '/lab/correlation': 'Correlation Research Lab',
  '/lab/breadth': 'Market Breadth Indices',
  '/lab/liquidity': 'Liquidity Audit Lab',
  '/lab/drift': 'Score Drift Monitor',
};

function AppContent() {
  const location = useLocation();

  // State for collapsible sidebar
  const [isCollapsed, setIsCollapsed] = useState(() => {
    return localStorage.getItem('sidebar-collapsed') === 'true';
  });

  // State for mobile drawer
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const toggleSidebar = () => {
    setIsCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem('sidebar-collapsed', String(next));
      return next;
    });
  };

  const toggleMobileSidebar = () => {
    setIsMobileOpen((prev) => !prev);
  };

  const closeMobileSidebar = () => {
    setIsMobileOpen(false);
  };

  // Match stock detail routes
  const isStockDetail = location.pathname.startsWith('/stock/');
  const title = isStockDetail
    ? 'Stock detail'
    : PAGE_TITLES[location.pathname] || 'PMS Engine';

  return (
    <div className={`app-layout ${isCollapsed ? 'sidebar-collapsed' : ''} ${isMobileOpen ? 'mobile-sidebar-open' : ''}`}>
      <Sidebar 
        isCollapsed={isCollapsed} 
        toggleSidebar={toggleSidebar} 
        closeMobileSidebar={closeMobileSidebar} 
      />
      {isMobileOpen && (
        <div className="sidebar-backdrop" onClick={closeMobileSidebar} />
      )}
      <div 
        className="app-body" 
        style={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column', 
          minWidth: 0, 
          maxWidth: '100%',
          boxSizing: 'border-box'
        }}
      >
        <Header title={title} onToggleMobileSidebar={toggleMobileSidebar} />
        <SnapshotBanner />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<SnapshotDashboard />} />
            <Route path="/workspace" element={<ResearchWorkspace />} />
            <Route path="/watchlists" element={<Watchlists />} />
            <Route path="/changes" element={<WhatsChanged />} />
            <Route path="/sectors" element={<SectorSnapshot />} />
            <Route path="/breadth" element={<MarketBreadth />} />
            <Route path="/archive" element={<HistoricalSnapshots />} />
            <Route path="/data-quality" element={<DataQuality />} />
            <Route path="/snapshot-diagnostics" element={<SnapshotDiagnostics />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/search" element={<StockSearch />} />
            <Route path="/stock/:symbol" element={<StockDetail />} />
            <Route path="/market" element={<MarketOverview />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/studio" element={<QuantStrategyStudio />} />
            <Route path="/strategy/:strategyId/validate" element={<StrategyValidation />} />
            <Route path="/backtest/:runId" element={<BacktestResults />} />
            <Route path="/backtest/history" element={<BacktestHistory />} />

            
            {/* Quant Lab Routes */}
            <Route path="/lab" element={<QuantLabHome />} />
            <Route path="/lab/indicators" element={<IndicatorLab />} />
            <Route path="/lab/engine" element={<EngineValidationLab />} />
            <Route path="/lab/models" element={<ModelLab />} />
            <Route path="/lab/features" element={<FeatureLab />} />
            <Route path="/lab/composite" element={<CompositeValidationLab />} />
            <Route path="/lab/validation" element={<RecommendationValidation />} />
            <Route path="/lab/portfolio" element={<PortfolioStrategies />} />
            <Route path="/lab/sector" element={<SectorLab />} />
            <Route path="/lab/regime" element={<RegimeLab />} />
            <Route path="/lab/benchmark" element={<BenchmarkComparison />} />
            <Route path="/lab/experiments" element={<ExperimentHistory />} />
            <Route path="/lab/reports" element={<LabReports />} />

            {/* New Extensions Routes */}
            <Route path="/lab/cross-indicator" element={<CrossIndicatorLab />} />
            <Route path="/lab/ensemble" element={<EnsembleLab />} />
            <Route path="/lab/hyperopt" element={<HyperoptLab />} />
            <Route path="/lab/monte-carlo" element={<MonteCarloLab />} />
            <Route path="/lab/stress" element={<StressTestLab />} />
            <Route path="/lab/sizing" element={<PositionSizingLab />} />
            <Route path="/lab/construction" element={<PortfolioConstructionLab />} />
            <Route path="/lab/correlation" element={<CorrelationLab />} />
            <Route path="/lab/breadth" element={<MarketBreadthLab />} />
            <Route path="/lab/liquidity" element={<LiquidityLab />} />
            <Route path="/lab/drift" element={<DriftMonitorLab />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

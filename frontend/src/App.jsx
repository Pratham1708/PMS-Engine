import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { WorkspaceProvider } from './context/WorkspaceContext';
import { CommandPaletteProvider } from './context/CommandPaletteContext';

// Navigation & Layout Components
import AppShell from './components/layout/AppShell';
import CommandPalette from './components/workspace/CommandPalette';

// Pages - Marketing & Auth
import LandingPage from './pages/Landing/LandingPage';
import LoginPage from './pages/Authentication/LoginPage';

// Pages - Workspace
import WorkspaceHub from './pages/Workspace/WorkspaceHub';
import WorkspaceDashboard from './pages/Workspace/WorkspaceDashboard';
import KnowledgeCenter from './pages/Knowledge/KnowledgeCenter';

// Existing Pages
import Dashboard from './pages/Dashboard';
import StockSearch from './pages/StockSearch';
import StockDetail from './pages/StockDetail';
import MarketOverview from './pages/MarketOverview';
import Reports from './pages/Reports';
import QuantStrategyStudio from './pages/QuantStrategyStudio';
import StrategyValidation from './pages/StrategyValidation';
import BacktestResults from './pages/BacktestResults';
import BacktestHistory from './pages/BacktestHistory';
import Watchlists from './pages/Watchlists';
import WhatsChanged from './pages/WhatsChanged';
import SectorSnapshot from './pages/SectorSnapshot';
import MarketBreadth from './pages/MarketBreadth';
import HistoricalSnapshots from './pages/HistoricalSnapshots';
import DataQuality from './pages/DataQuality';
import SnapshotDiagnostics from './pages/SnapshotDiagnostics';
import SnapshotDashboard from './pages/SnapshotDashboard';

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

function WorkspaceRoute({ children, title }) {
  return <AppShell pageTitle={title}>{children}</AppShell>;
}

function AppContent() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  return (
    <>
      <CommandPalette />
      <Routes>
        {/* Public Marketing & Auth Routes */}
        <Route path="/landing" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />

        {/* Root Route: If authenticated go to Workspace, else Landing */}
        <Route path="/" element={isAuthenticated ? <WorkspaceRoute title="Daily Research Snapshot Terminal"><SnapshotDashboard /></WorkspaceRoute> : <LandingPage />} />

        {/* Core Workspace Hub & Dashboard */}
        <Route path="/workspace" element={<WorkspaceHub />} />
        <Route path="/dashboard" element={<WorkspaceDashboard />} />
        <Route path="/docs" element={<KnowledgeCenter />} />

        {/* Workspace AppShell Routes */}
        <Route path="/watchlists" element={<WorkspaceRoute title="Smart Watchlists"><Watchlists /></WorkspaceRoute>} />
        <Route path="/changes" element={<WorkspaceRoute title="Daily Recommendation Changes"><WhatsChanged /></WorkspaceRoute>} />
        <Route path="/sectors" element={<WorkspaceRoute title="Sector Averages Snapshot"><SectorSnapshot /></WorkspaceRoute>} />
        <Route path="/breadth" element={<WorkspaceRoute title="Market Breadth Indicators"><MarketBreadth /></WorkspaceRoute>} />
        <Route path="/archive" element={<WorkspaceRoute title="Historical Snapshot Archive"><HistoricalSnapshots /></WorkspaceRoute>} />
        <Route path="/data-quality" element={<WorkspaceRoute title="Data Quality & Diagnostics"><DataQuality /></WorkspaceRoute>} />
        <Route path="/snapshot-diagnostics" element={<WorkspaceRoute title="Snapshot Diagnostics"><SnapshotDiagnostics /></WorkspaceRoute>} />
        <Route path="/search" element={<WorkspaceRoute title="Stock Search"><StockSearch /></WorkspaceRoute>} />
        <Route path="/stock/:symbol" element={<WorkspaceRoute title="Stock Detail"><StockDetail /></WorkspaceRoute>} />
        <Route path="/market" element={<WorkspaceRoute title="Market Overview"><MarketOverview /></WorkspaceRoute>} />
        <Route path="/reports" element={<WorkspaceRoute title="Research Reports"><Reports /></WorkspaceRoute>} />
        <Route path="/studio" element={<WorkspaceRoute title="Quant Strategy Studio"><QuantStrategyStudio /></WorkspaceRoute>} />
        <Route path="/strategy/:strategyId/validate" element={<WorkspaceRoute title="Strategy Validation"><StrategyValidation /></WorkspaceRoute>} />
        <Route path="/backtest/:runId" element={<WorkspaceRoute title="Backtest Results"><BacktestResults /></WorkspaceRoute>} />
        <Route path="/backtest/history" element={<WorkspaceRoute title="Backtest History"><BacktestHistory /></WorkspaceRoute>} />

        {/* Quant Lab Routes */}
        <Route path="/lab" element={<WorkspaceRoute title="Quant Research Laboratory"><QuantLabHome /></WorkspaceRoute>} />
        <Route path="/lab/indicators" element={<WorkspaceRoute title="Indicator Lab"><IndicatorLab /></WorkspaceRoute>} />
        <Route path="/lab/engine" element={<WorkspaceRoute title="Engine Score Validation"><EngineValidationLab /></WorkspaceRoute>} />
        <Route path="/lab/models" element={<WorkspaceRoute title="Model Research Lab"><ModelLab /></WorkspaceRoute>} />
        <Route path="/lab/features" element={<WorkspaceRoute title="Feature Selection Lab"><FeatureLab /></WorkspaceRoute>} />
        <Route path="/lab/composite" element={<WorkspaceRoute title="Composite Weights Validation"><CompositeValidationLab /></WorkspaceRoute>} />
        <Route path="/lab/validation" element={<WorkspaceRoute title="Recommendation Audit Lab"><RecommendationValidation /></WorkspaceRoute>} />
        <Route path="/lab/portfolio" element={<WorkspaceRoute title="Portfolio Strategies Backtester"><PortfolioStrategies /></WorkspaceRoute>} />
        <Route path="/lab/sector" element={<WorkspaceRoute title="Sector Analysis Lab"><SectorLab /></WorkspaceRoute>} />
        <Route path="/lab/regime" element={<WorkspaceRoute title="Market Regime Detection"><RegimeLab /></WorkspaceRoute>} />
        <Route path="/lab/benchmark" element={<WorkspaceRoute title="Benchmark Comparison Lab"><BenchmarkComparison /></WorkspaceRoute>} />
        <Route path="/lab/experiments" element={<WorkspaceRoute title="Experiment History Registry"><ExperimentHistory /></WorkspaceRoute>} />
        <Route path="/lab/reports" element={<WorkspaceRoute title="Quant Lab Reports Compiler"><LabReports /></WorkspaceRoute>} />
        <Route path="/lab/cross-indicator" element={<WorkspaceRoute title="Cross-Indicator Lab"><CrossIndicatorLab /></WorkspaceRoute>} />
        <Route path="/lab/ensemble" element={<WorkspaceRoute title="Ensemble Strategy Lab"><EnsembleLab /></WorkspaceRoute>} />
        <Route path="/lab/hyperopt" element={<WorkspaceRoute title="Parameter Hyperopt Lab"><HyperoptLab /></WorkspaceRoute>} />
        <Route path="/lab/monte-carlo" element={<WorkspaceRoute title="Monte Carlo Sandbox"><MonteCarloLab /></WorkspaceRoute>} />
        <Route path="/lab/stress" element={<WorkspaceRoute title="Crisis Stress Tester"><StressTestLab /></WorkspaceRoute>} />
        <Route path="/lab/sizing" element={<WorkspaceRoute title="Position Sizing Lab"><PositionSizingLab /></WorkspaceRoute>} />
        <Route path="/lab/construction" element={<WorkspaceRoute title="Portfolio Construction Lab"><PortfolioConstructionLab /></WorkspaceRoute>} />
        <Route path="/lab/correlation" element={<WorkspaceRoute title="Correlation Research Lab"><CorrelationLab /></WorkspaceRoute>} />
        <Route path="/lab/breadth" element={<WorkspaceRoute title="Market Breadth Indices"><MarketBreadthLab /></WorkspaceRoute>} />
        <Route path="/lab/liquidity" element={<WorkspaceRoute title="Liquidity Audit Lab"><LiquidityLab /></WorkspaceRoute>} />
        <Route path="/lab/drift" element={<WorkspaceRoute title="Score Drift Monitor"><DriftMonitorLab /></WorkspaceRoute>} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <WorkspaceProvider>
          <CommandPaletteProvider>
            <BrowserRouter>
              <AppContent />
            </BrowserRouter>
          </CommandPaletteProvider>
        </WorkspaceProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}

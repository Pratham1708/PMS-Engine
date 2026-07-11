"""
Pydantic response schemas for PMS Engine API.
All API responses are strictly typed via these models.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class StockSummary(BaseModel):
    """Compact stock representation for lists and dashboard."""
    Symbol: str
    FinalRating: str
    Confidence: float
    CompositeScoreV2: float
    Sector: str = "\u2014"
    CurrentPrice: Optional[float] = None
    DailyChangePct: Optional[float] = None
    Volume: Optional[int] = None


class RatingDriver(BaseModel):
    name: str
    value: float
    contribution: str
    impact: str
    description: str


class XaiExplanation(BaseModel):
    TechnicalScoreReason: str
    MLScoreReason: str
    GRUScoreReason: str
    ReturnScoreReason: str
    FinalRatingReason: str
    RatingDrivers: List[RatingDriver]


class StockDetail(BaseModel):
    """Full stock detail with all scoring dimensions and XAI data."""
    Symbol: str
    FinalRating: str
    Confidence: float
    CompositeScoreV2: float
    TechnicalScore: float
    MLScore: float
    GRUScore: float
    ReliabilityScore: float
    RiskScore: Optional[float] = None
    MomentumScore: Optional[float] = None
    TrendScore: Optional[float] = None
    Sector: str = "\u2014"
    CompanyName: Optional[str] = None
    Industry: Optional[str] = None
    Website: Optional[str] = None
    GRU_HOLD: Optional[float] = None
    GRU_LONG: Optional[float] = None
    GRU_SHORT: Optional[float] = None
    ReturnScore: Optional[float] = None
    Rank: int = 0
    Percentile: float = 0.0
    UniversePosition: str = "\u2014"
    PortfolioEligible: bool = False
    ConvictionLevel: str = "Medium Conviction"
    
    # Live market fields
    CurrentPrice: Optional[float] = None
    Open: Optional[float] = None
    High: Optional[float] = None
    Low: Optional[float] = None
    Volume: Optional[int] = None
    PreviousClose: Optional[float] = None
    DailyChangePct: Optional[float] = None
    DailyChangeAmount: Optional[float] = None
    LastMarketUpdate: Optional[str] = None
    LastScannerRun: Optional[str] = None
    
    # Explainable AI Fields
    xai_explanation: Optional[XaiExplanation] = None
    top_positive_factors: Optional[List[str]] = None
    top_negative_factors: Optional[List[str]] = None
    institutional_insight: Optional[str] = None


class Contribution(BaseModel):
    name: str
    value: Optional[float] = None
    weight: Optional[float] = None
    contribution: Optional[float] = None
    direction: str  # "positive" | "negative" | "neutral"
    description: str


class ValidationMetric(BaseModel):
    metric: str
    value: str
    description: str


class ResearchReference(BaseModel):
    paper: str
    author: str
    year: int
    link: Optional[str] = None
    description: str


class ScoreInterpretation(BaseModel):
    range: str
    meaning: str
    action: str


class ExplainScoreResponse(BaseModel):
    score_type: str
    symbol: Optional[str] = None
    current_value: Optional[float] = None
    purpose: str
    formula: str
    factors: List[str]
    validation: List[ValidationMetric]
    interpretation: List[ScoreInterpretation]
    limitations: List[str]
    references: List[ResearchReference]
    current_values: Optional[dict] = None
    current_contributions: List[Contribution] = []
    dynamic_explanation: str
    why_not: str
    historical_context: Optional[List[dict]] = None
    llm_summary: Optional[str] = None


class DashboardData(BaseModel):
    """Aggregated dashboard metrics."""
    total_stocks: int
    strong_buy_count: int
    buy_count: int
    hold_count: int
    sell_count: int
    strong_sell_count: int
    avg_confidence: float
    avg_composite: float
    top_buys: List[StockSummary]
    top_sells: List[StockSummary]


class PortfolioStock(BaseModel):
    """Single stock in a portfolio allocation."""
    Symbol: str
    FinalRating: str
    Confidence: float
    CompositeScoreV2: float
    Weight: float
    Amount: float
    Sector: str = "\u2014"


class PortfolioResponse(BaseModel):
    """Complete portfolio allocation response."""
    capital: float
    total_stocks: int
    stocks: List[PortfolioStock]
    avg_confidence: float
    avg_composite: float


class RatingDistribution(BaseModel):
    """Count of stocks per rating level."""
    strong_buy: int = 0
    buy: int = 0
    hold: int = 0
    sell: int = 0
    strong_sell: int = 0


class ScannerSummary(BaseModel):
    """Universe-wide summary statistics."""
    total_stocks: int
    avg_confidence: float
    avg_composite: float
    max_composite: float
    min_composite: float
    avg_technical: float
    avg_ml: float
    avg_gru: float
    avg_reliability: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    stocks_loaded: int


class RefreshResponse(BaseModel):
    """Scanner refresh response."""
    message: str
    stocks_loaded: int


class UserStockAdd(BaseModel):
    """Request model for adding a symbol to My Stocks."""
    symbol: str


class UserStockResponse(BaseModel):
    """Response model for a user stock of interest."""
    symbol: str
    added_at: str
    sector: str = "—"
    current_price: Optional[float] = None
    daily_change_pct: Optional[float] = None
    last_rating: str = "Not Analyzed"
    last_confidence: Optional[float] = None
    last_composite: Optional[float] = None
    analyzed_at: Optional[str] = None
    last_status: Optional[str] = "Stale"


class RecentAnalysisResponse(BaseModel):
    """Response model for recently analyzed stocks list."""
    symbol: str
    rating: str
    confidence: float
    composite_score: float
    analyzed_at: str
    status: str = "Stale"
    sector: str = "—"
    current_price: Optional[float] = None


class AnalysisHistoryEntry(BaseModel):
    """Response model for a single past analysis run."""
    analysis_id: str
    rating: str
    confidence: float
    composite_score: float
    analyzed_at: str
    status: str = "Stale"


class CompanyProfile(BaseModel):
    """Response model for detailed company profile info."""
    company_name: str
    symbol: str
    sector: str
    industry: str
    market_cap: str
    employees: Optional[str] = None
    headquarters: str
    website: str
    description: str
    segments: str
    history: str
    logo_url: Optional[str] = None


class WorkspaceStats(BaseModel):
    """Universe statistics for the workspace."""
    total_universe: int
    my_stocks_count: int
    analyzed_universe_count: int


class WorkspaceResponse(BaseModel):
    """Combined dashboard response for the Research Workspace."""
    my_stocks: List[UserStockResponse]
    recent_analysis: List[RecentAnalysisResponse]
    saved_reports: List[dict]
    universe_stats: WorkspaceStats


class AnalyzeResponse(BaseModel):
    """Response wrapper for a complete stock analysis execution."""
    analysis_id: str
    symbol: str
    status: str
    analysis_timestamp: str
    result: StockDetail


# ── Phase 13 Snapshot Schemas ─────────────────────────────────────────────────

class SnapshotMeta(BaseModel):
    """Master snapshot registry record."""
    snapshot_id: str
    snapshot_date: str
    market_date: str
    generated_at: str
    is_official: bool
    status: str
    stocks_processed: int
    stocks_failed: int
    universe_version: Optional[str] = None
    engine_version: Optional[str] = None
    indicator_version: Optional[str] = None
    scoring_version: Optional[str] = None
    ml_model_version: Optional[str] = None
    feature_version: Optional[str] = None
    software_build: Optional[str] = None
    pipeline_started_at: Optional[str] = None
    pipeline_ended_at: Optional[str] = None
    pipeline_duration_sec: Optional[float] = None
    validation_passed: bool = False
    validation_score: Optional[float] = None
    published_at: Optional[str] = None
    notes: Optional[str] = None


class SnapshotStockRecord(BaseModel):
    """Per-stock record from a snapshot (OHLCV + scores + rating)."""
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    # OHLCV
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    prev_close: Optional[float] = None
    daily_chg_pct: Optional[float] = None
    daily_chg_amt: Optional[float] = None
    week52_high: Optional[float] = None
    week52_low: Optional[float] = None
    # Scores
    technical_score: Optional[float] = None
    ml_score: Optional[float] = None
    gru_score: Optional[float] = None
    risk_score: Optional[float] = None
    momentum_score: Optional[float] = None
    trend_score: Optional[float] = None
    confidence: Optional[float] = None
    composite_score: Optional[float] = None
    reliability_score: Optional[float] = None
    # Recommendation
    final_rating: Optional[str] = None
    portfolio_eligible: bool = False
    conviction_level: Optional[str] = None
    rank: Optional[int] = None
    percentile: Optional[float] = None
    universe_position: Optional[str] = None
    # Data quality
    data_source: str = "yfinance"
    download_status: str = "success"
    data_warnings: Optional[str] = None


class SnapshotIndicatorRecord(BaseModel):
    """Key computed indicators for a stock in a snapshot."""
    symbol: str
    rsi_14: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    atr_14: Optional[float] = None
    stoch_k: Optional[float] = None
    adx_14: Optional[float] = None
    obv: Optional[float] = None
    vwap: Optional[float] = None
    above_ema20: bool = False
    above_ema50: bool = False
    above_ema200: bool = False
    near_52w_high: bool = False
    near_52w_low: bool = False


class SnapshotScoreRecord(BaseModel):
    """Detailed score breakdown with XAI drivers for a stock in a snapshot."""
    symbol: str
    trend_component: Optional[float] = None
    momentum_component: Optional[float] = None
    volatility_component: Optional[float] = None
    volume_component: Optional[float] = None
    lgbm_signal: Optional[float] = None
    rf_signal: Optional[float] = None
    xgb_signal: Optional[float] = None
    gru_hold: Optional[float] = None
    gru_long: Optional[float] = None
    gru_short: Optional[float] = None
    return_score: Optional[float] = None
    primary_driver: Optional[str] = None
    secondary_driver: Optional[str] = None
    w_technical: float = 0.40
    w_ml: float = 0.35
    w_gru: float = 0.15
    w_reliability: float = 0.10


class SectorSnapshotRecord(BaseModel):
    """Sector-level aggregated stats from a snapshot."""
    sector: str
    stock_count: int
    avg_composite: Optional[float] = None
    avg_confidence: Optional[float] = None
    avg_technical: Optional[float] = None
    avg_momentum: Optional[float] = None
    avg_trend: Optional[float] = None
    avg_risk: Optional[float] = None
    strong_buy_count: int = 0
    buy_count: int = 0
    hold_count: int = 0
    sell_count: int = 0
    strong_sell_count: int = 0
    bullish_pct: Optional[float] = None
    bearish_pct: Optional[float] = None
    sector_rank: Optional[int] = None
    top_stock: Optional[str] = None
    weakest_stock: Optional[str] = None
    avg_daily_chg_pct: Optional[float] = None


class MarketBreadthResponse(BaseModel):
    """Universe-wide market breadth metrics from a snapshot."""
    total_stocks: int = 0
    advancing_stocks: int = 0
    declining_stocks: int = 0
    unchanged_stocks: int = 0
    advance_decline_ratio: Optional[float] = None
    advance_volume: int = 0
    decline_volume: int = 0
    stocks_above_ema20: int = 0
    stocks_above_ema50: int = 0
    stocks_above_ema200: int = 0
    pct_above_ema20: Optional[float] = None
    pct_above_ema50: Optional[float] = None
    pct_above_ema200: Optional[float] = None
    week52_high_count: int = 0
    week52_low_count: int = 0
    avg_composite: Optional[float] = None
    avg_confidence: Optional[float] = None
    avg_rsi: Optional[float] = None
    avg_momentum: Optional[float] = None
    avg_daily_chg_pct: Optional[float] = None
    bullish_pct: Optional[float] = None
    bearish_pct: Optional[float] = None
    market_regime: str = "Neutral"
    strong_buy_count: int = 0
    buy_count: int = 0
    hold_count: int = 0
    sell_count: int = 0
    strong_sell_count: int = 0
    # Future placeholders
    india_vix: Optional[float] = None
    pcr: Optional[float] = None
    fii_activity: Optional[float] = None
    dii_activity: Optional[float] = None


class WatchlistEntry(BaseModel):
    """Single stock entry in a watchlist."""
    symbol: str
    rank_in_list: int
    score_used: Optional[float] = None
    reason: Optional[str] = None


class WatchlistResponse(BaseModel):
    """Named watchlist with its member stocks."""
    watchlist_name: str
    display_name: str
    description: str
    stocks: List[WatchlistEntry] = []


class RecommendationChange(BaseModel):
    """Recommendation diff between consecutive snapshots."""
    symbol: str
    change_type: str
    prev_rating: Optional[str] = None
    new_rating: Optional[str] = None
    composite_diff: Optional[float] = None
    confidence_diff: Optional[float] = None
    technical_diff: Optional[float] = None
    ml_diff: Optional[float] = None
    momentum_diff: Optional[float] = None
    trend_diff: Optional[float] = None
    risk_diff: Optional[float] = None
    primary_driver: Optional[str] = None
    secondary_driver: Optional[str] = None
    is_significant: bool = False
    prev_snapshot_id: Optional[str] = None


class ValidationResult(BaseModel):
    """Single validation check result."""
    check_name: str
    status: str  # 'pass' | 'fail' | 'warning'
    detail: Optional[str] = None
    affected_count: int = 0
    threshold: Optional[float] = None
    actual_value: Optional[float] = None


class PipelineStageResult(BaseModel):
    """Pipeline stage execution record."""
    stage_name: str
    stage_status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_sec: Optional[float] = None
    stocks_success: int = 0
    stocks_failed: int = 0
    warnings_count: int = 0
    errors_count: int = 0
    log_summary: Optional[str] = None


class PipelineStatusResponse(BaseModel):
    """Real-time pipeline monitor state."""
    snapshot_id: Optional[str] = None
    current_stage: Optional[str] = None
    total_stages: int = 23
    completed_stages: int = 0
    pct_complete: float = 0.0
    stocks_total: int = 0
    stocks_completed: int = 0
    stocks_failed: int = 0
    elapsed_sec: float = 0.0
    est_remaining_sec: Optional[float] = None
    status: str = "idle"
    warnings: List[str] = []
    errors: List[str] = []
    started_at: Optional[str] = None
    stage_log: List[dict] = []


class SnapshotSummary(BaseModel):
    """Top-level daily dashboard aggregate."""
    meta: SnapshotMeta
    breadth: Optional[MarketBreadthResponse] = None
    sectors: List[SectorSnapshotRecord] = []
    top_opportunities: List[SnapshotStockRecord] = []
    changes_summary: Optional[dict] = None
    validation_summary: Optional[dict] = None
    pipeline_summary: Optional[dict] = None


class DataQualityResponse(BaseModel):
    """Data quality dashboard for a snapshot."""
    snapshot_id: str
    snapshot_date: str
    health_score: float  # 0-100
    coverage_pct: float
    universe_size: int
    downloaded_count: int
    failed_count: int
    cached_count: int
    live_count: int
    mock_count: int
    freshness_hours: Optional[float] = None
    validation_checks: List[ValidationResult] = []
    validation_pass_count: int = 0
    validation_warn_count: int = 0
    validation_fail_count: int = 0
    failed_symbols: List[str] = []
    status: str  # 'healthy' | 'degraded' | 'critical'


class SnapshotStatusResponse(BaseModel):
    """System-level snapshot status."""
    latest_snapshot: Optional[SnapshotMeta] = None
    total_snapshots: int = 0
    in_progress: int = 0
    data_freshness: str = "no_data"  # 'fresh'|'recent'|'aging'|'stale'|'no_data'
    pipeline_available: bool = True


class CompareSnapshotResponse(BaseModel):
    """Side-by-side comparison of two snapshots."""
    date1: str
    date2: str
    snapshot1: Optional[SnapshotMeta] = None
    snapshot2: Optional[SnapshotMeta] = None
    breadth1: Optional[MarketBreadthResponse] = None
    breadth2: Optional[MarketBreadthResponse] = None
    sectors1: List[SectorSnapshotRecord] = []
    sectors2: List[SectorSnapshotRecord] = []
    stock_changes: List[RecommendationChange] = []
    regime_change: Optional[str] = None
    composite_delta: Optional[float] = None
    confidence_delta: Optional[float] = None

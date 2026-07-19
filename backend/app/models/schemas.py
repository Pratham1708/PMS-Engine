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


class NormalizationExplain(BaseModel):
    method: str
    range: str
    logic: str


class FeatureMetadata(BaseModel):
    data_source: str
    plain_formula: str
    latex_formula: str
    normalization: NormalizationExplain
    reference: ResearchReference


class RuntimeFeatureContribution(BaseModel):
    feature_key: str
    current_value: str
    weight: float
    contribution: float
    effect: str  # "positive" | "negative" | "neutral"
    confidence: str  # "High" | "Medium" | "Low"


class FeatureAttribution(BaseModel):
    feature_key: str
    name: str
    current_value: str
    normalized_value: float
    weight: float
    contribution: float
    effect: str
    explanation: str
    confidence: str
    metadata: FeatureMetadata


class CategoryContribution(BaseModel):
    category: str
    features: List[FeatureAttribution]
    subtotal: float


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
    explanation_type: str = "global_importance"  # "global_importance" | "local_shap" | "integrated_gradients" | "permutation_importance"
    feature_attributions: Optional[List[CategoryContribution]] = None



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
    pipeline_run_id: Optional[str] = None
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


from typing import Any, Dict, List

class ScoreChange(BaseModel):
    prev: Optional[float] = None
    curr: Optional[float] = None
    delta: Optional[float] = None
    pct_change: Optional[float] = None
    category: str

class DriverDetail(BaseModel):
    feature: str
    prev_value: Any
    curr_value: Any
    change: str
    effect: str

class StockDeltaRecord(BaseModel):
    symbol: str
    company_name: str
    sector: str
    transition_type: str
    prev_rating: Optional[str] = None
    new_rating: Optional[str] = None
    score_changes: Dict[str, ScoreChange]
    rank_movement: Optional[int] = None
    sector_movement: Optional[int] = None
    drivers: List[DriverDetail] = []

class ComparisonMetadata(BaseModel):
    date1: str
    date2: str
    snapshot_id_1: str
    snapshot_id_2: str
    strategy_id: str = "pms_default"
    generated_at: str
    comparison_version: str
    version_warnings: List[str] = []

class PortfolioComparisonSummary(BaseModel):
    upgrades: int
    downgrades: int
    unchanged: int
    avg_composite_change: float
    avg_technical_change: float
    avg_expected_return_change: float
    strongest_improving: List[StockDeltaRecord] = []
    largest_deteriorating: List[StockDeltaRecord] = []

class RecommendationComparisonSummary(BaseModel):
    upgrade_list: List[StockDeltaRecord] = []
    downgrade_list: List[StockDeltaRecord] = []
    matrix: Dict[str, Dict[str, int]] = {}

class SectorDeltaRecord(BaseModel):
    sector: str
    stock_count: int
    avg_composite_change: float
    avg_technical_change: float
    avg_momentum_change: float
    avg_risk_change: float
    upgrades: int
    downgrades: int
    sector_rank_diff: int

class SectorComparisonSummary(BaseModel):
    best_sector: Optional[str] = None
    worst_sector: Optional[str] = None
    most_upgrades: Optional[str] = None
    largest_momentum_gain: Optional[str] = None
    largest_risk_reduction: Optional[str] = None
    sector_deltas: List[SectorDeltaRecord] = []

class WaterfallPoint(BaseModel):
    name: str
    value: float
    display: str

class HistogramBucket(BaseModel):
    bucket: str
    count: int

class SectorHeatmapPoint(BaseModel):
    sector: str
    avg_composite_change: float
    avg_technical_change: float
    upgrades: int
    downgrades: int
    stock_count: int

class ComparisonVisualizations(BaseModel):
    waterfall: List[WaterfallPoint] = []
    histogram: List[HistogramBucket] = []
    sector_heatmap: List[SectorHeatmapPoint] = []

class CompareSnapshotResponse(BaseModel):
    """Side-by-side comparison of two snapshots."""
    comparison_metadata: ComparisonMetadata
    portfolio_summary: PortfolioComparisonSummary
    sector_summary: SectorComparisonSummary
    recommendation_summary: RecommendationComparisonSummary
    stock_deltas: List[StockDeltaRecord] = []
    visualizations: ComparisonVisualizations


# ── Quant Strategy Studio Schemas ───────────────────────────────────────────

from typing import Dict, Any

class FeatureSelectionModel(BaseModel):
    feature_id: str
    feature_group: str
    enabled: bool = True

class WeightAllocationModel(BaseModel):
    feature_id: str
    weight: float
    normalization_method: Optional[str] = "Default"
    contribution_method: Optional[str] = "Additive"

class ScoringConfigModel(BaseModel):
    scoring_method: str = "Weighted Average"
    aggregation_method: str = "Additive"
    threshold_buy: float = 35.0
    threshold_hold: float = -15.0
    threshold_sell: float = -15.0
    normalization: str = "Default"
    recommendation_method: str = "Standard"

class StrategyDefinitionModel(BaseModel):
    features: List[FeatureSelectionModel] = []
    weights: List[WeightAllocationModel] = []
    scoring_config: ScoringConfigModel = Field(default_factory=ScoringConfigModel)
    risk_profile: Optional[str] = "Medium"
    filters: Optional[Dict[str, Any]] = None

class StrategyVersionModel(BaseModel):
    version: str
    timestamp: str
    change_summary: Optional[str] = None
    created_by: Optional[str] = None

class StrategyCreateRequest(BaseModel):
    strategy_name: str
    description: Optional[str] = None
    strategy_type: str = "Stock"  # Stock, Portfolio, ETF, Sector, Options, Screening, Allocation
    strategy_prompt: Optional[str] = None  # text/AI prompt
    strategy_definition: StrategyDefinitionModel
    visibility: str = "Private"  # Private, Public, Shared

class StrategyUpdateRequest(BaseModel):
    strategy_name: Optional[str] = None
    description: Optional[str] = None
    strategy_type: Optional[str] = None
    strategy_prompt: Optional[str] = None
    strategy_definition: Optional[StrategyDefinitionModel] = None
    visibility: Optional[str] = None
    status: Optional[str] = None  # Draft, Published, Archived
    change_summary: Optional[str] = "Updated strategy configuration"

class StrategyResponse(BaseModel):
    strategy_id: str
    owner_id: Optional[str] = None
    strategy_name: str
    description: Optional[str] = None
    strategy_type: str
    strategy_prompt: Optional[str] = None
    strategy_definition: StrategyDefinitionModel
    visibility: str
    version: str
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    versions: List[StrategyVersionModel] = []

class HealthScoreBreakdown(BaseModel):
    diversification: int
    weight_balance: int
    feature_independence: int
    normalization: int
    risk_coverage: int
    overall: int

class StrategyValidationResponse(BaseModel):
    valid: bool
    health_score: int
    health_breakdown: HealthScoreBreakdown
    errors: List[str]
    warnings: List[str]
    complexity: str  # Low, Medium, High
    estimated_behavior: str  # Conservative, Moderate, Aggressive

class CompareMetricRecord(BaseModel):
    symbol: str
    company_name: str
    sector: str
    current_price: Optional[float] = None
    daily_change_pct: Optional[float] = None
    # PMS Default values
    default_score: float
    default_rating: str
    default_rank: int
    # Custom strategy values
    custom_score: float
    custom_rating: str
    custom_rank: int
    # Differences
    score_diff: float
    rank_diff: int
    rating_diff: str
    expected_return_diff: float

class StrategyExecuteResponse(BaseModel):
    strategy_id: str
    strategy_name: str
    snapshot_id: str
    status: str
    total_stocks: int
    stocks: List[CompareMetricRecord] = []


# ── Phase 14C: Backtest & Validation Schemas ─────────────────────────────────

class BacktestRunRequest(BaseModel):
    strategy_id: str
    start_date: str                              # YYYY-MM-DD
    end_date: str                                # YYYY-MM-DD
    benchmark: str = "NIFTY50"                  # NIFTY50 | NIFTY500
    rebalance_freq: str = "Monthly"              # Daily | Weekly | Monthly | Quarterly
    weighting_scheme: str = "Equal"             # Equal | ScoreWeighted | RiskParity | VolAdjusted
    initial_capital: float = 1_000_000.0
    max_holdings: int = 15
    position_size: float = 10.0                 # max % per position
    transaction_cost: float = 0.001
    slippage: float = 0.001


class ReportVersioning(BaseModel):
    model_config = {"protected_namespaces": ()}
    backtest_version: str = "14C.1"
    engine_version: str
    strategy_version: str
    snapshot_version_range: str                 # e.g. "v1.0.0–v1.2.0"
    feature_registry_version: str = "1.0.0"
    model_version: str
    generated_at: str


class CorrelationPair(BaseModel):
    feature_a: str
    feature_b: str
    pearson_r: float


class ValidationCategoryResult(BaseModel):
    category: str
    score: float
    max_score: float
    status: str                                 # pass | warn | fail
    checks: List[Dict[str, Any]] = []
    detail: str = ""


class ValidationReportResponse(BaseModel):
    report_id: str
    strategy_id: str
    strategy_name: str
    validation_score: float
    passed: bool
    categories: List[ValidationCategoryResult] = []
    correlation_matrix: List[CorrelationPair] = []
    bias_tags: List[str] = []
    warnings: List[str] = []
    errors: List[str] = []
    recommendations: List[str] = []
    generated_at: str


class ExecutionLogEntry(BaseModel):
    snapshot_date: str
    snapshot_id: str
    integrity_status: str                       # verified | excluded | warned
    integrity_checks: Dict[str, bool] = {}
    stocks_scored: int = 0
    signals_generated: int = 0
    buy_signals: int = 0
    sell_signals: int = 0
    buy_pct: float = 0.0
    trades_executed: int = 0
    portfolio_value: float = 0.0
    turnover_pct: float = 0.0
    notes: str = ""


class TradeAttribution(BaseModel):
    why_entered: str = ""
    why_exited: str = ""
    top_contributors: List[Dict[str, Any]] = []   # [{feature_id, label, contribution}]
    top_detractors: List[Dict[str, Any]] = []
    entry_eqif_available: bool = False
    exit_eqif_available: bool = False


class TradeRecord(BaseModel):
    trade_id: str
    symbol: str
    company_name: str = ""
    sector: str = ""
    entry_date: str
    exit_date: str
    holding_days: int
    entry_price: float
    exit_price: float
    entry_score: float
    exit_score: float
    entry_rating: str
    exit_rating: str
    return_pct: float
    position_weight: float = 0.0
    entry_snapshot_id: str
    exit_snapshot_id: str
    attribution: Optional[TradeAttribution] = None


class ReturnMetrics(BaseModel):
    total_return_pct: float = 0.0
    cagr_pct: float = 0.0
    annualized_return_pct: float = 0.0
    monthly_returns: List[Dict[str, Any]] = []    # [{year, month, return_pct}]
    quarterly_returns: List[Dict[str, Any]] = []
    yearly_returns: List[Dict[str, Any]] = []


class RiskMetrics(BaseModel):
    annualized_volatility_pct: float = 0.0
    beta: float = 0.0
    alpha_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    information_ratio: float = 0.0
    treynor_ratio: float = 0.0


class DrawdownMetrics(BaseModel):
    max_drawdown_pct: float = 0.0
    avg_drawdown_pct: float = 0.0
    max_recovery_days: int = 0
    total_underwater_days: int = 0
    drawdown_curve: List[Dict[str, Any]] = []    # [{date, drawdown_pct}]


class TradeMetrics(BaseModel):
    total_trades: int = 0
    win_rate_pct: float = 0.0
    loss_rate_pct: float = 0.0
    avg_win_pct: float = 0.0
    avg_loss_pct: float = 0.0
    profit_factor: float = 0.0
    expectancy_pct: float = 0.0
    avg_holding_days: float = 0.0


class PortfolioMetrics(BaseModel):
    avg_portfolio_score: float = 0.0
    avg_turnover_pct: float = 0.0
    avg_cash_utilization_pct: float = 0.0
    sector_allocation: Dict[str, float] = {}
    avg_position_concentration_pct: float = 0.0
    top5_weight_pct: float = 0.0
    feature_utilization_pct: float = 0.0


class BenchmarkRelativeMetrics(BaseModel):
    excess_return_pct: float = 0.0
    tracking_error_pct: float = 0.0
    relative_max_drawdown_pct: float = 0.0
    relative_sharpe: float = 0.0
    relative_cagr_pct: float = 0.0


class RollingMetrics(BaseModel):
    rolling_cagr: List[Dict[str, Any]] = []        # [{date, d30, d90, d252}]
    rolling_volatility: List[Dict[str, Any]] = []
    rolling_sharpe: List[Dict[str, Any]] = []
    rolling_sortino: List[Dict[str, Any]] = []
    rolling_win_rate: List[Dict[str, Any]] = []
    rolling_drawdown: List[Dict[str, Any]] = []
    rolling_alpha: List[Dict[str, Any]] = []


class PerformanceMetrics(BaseModel):
    returns: ReturnMetrics = ReturnMetrics()
    risk: RiskMetrics = RiskMetrics()
    drawdown: DrawdownMetrics = DrawdownMetrics()
    trades: TradeMetrics = TradeMetrics()
    portfolio: PortfolioMetrics = PortfolioMetrics()
    benchmark_relative: BenchmarkRelativeMetrics = BenchmarkRelativeMetrics()
    rolling: RollingMetrics = RollingMetrics()


class PortfolioTimelineEntry(BaseModel):
    date: str
    snapshot_id: str
    portfolio_value: float
    cash: float
    cash_pct: float
    sector_allocation: Dict[str, float] = {}
    top_holdings: List[Dict[str, Any]] = []      # [{symbol, weight, score, rating}]
    avg_score: float = 0.0
    num_positions: int = 0
    period_return_pct: float = 0.0
    turnover_pct: float = 0.0


class BenchmarkComparisonRow(BaseModel):
    metric: str
    metric_label: str
    strategy_value: float
    pms_default_value: float
    benchmark_value: float
    strategy_vs_default: float
    strategy_vs_benchmark: float
    higher_is_better: bool = True


class BacktestSummaryCards(BaseModel):
    """Lightweight summary returned immediately; full metrics in BacktestDetailResponse."""
    total_return_pct: float = 0.0
    cagr_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate_pct: float = 0.0
    profit_factor: float = 0.0
    alpha_pct: float = 0.0
    beta: float = 0.0
    # Parallel values for the other 2 series
    pms_total_return_pct: float = 0.0
    pms_cagr_pct: float = 0.0
    pms_sharpe_ratio: float = 0.0
    pms_max_drawdown_pct: float = 0.0
    benchmark_total_return_pct: float = 0.0
    benchmark_cagr_pct: float = 0.0
    benchmark_sharpe_ratio: float = 0.0
    benchmark_max_drawdown_pct: float = 0.0


class BacktestRunResponse(BaseModel):
    run_id: str
    strategy_id: str
    strategy_name: str
    status: str
    summary: Optional[BacktestSummaryCards] = None
    created_at: str
    execution_time_sec: Optional[float] = None
    error_msg: Optional[str] = None
    versioning: Optional[ReportVersioning] = None


class BacktestDetailResponse(BaseModel):
    run_id: str
    strategy_id: str
    strategy_name: str
    status: str
    # Simulation parameters
    start_date: str
    end_date: str
    benchmark: str
    rebalance_freq: str
    weighting_scheme: str
    initial_capital: float
    snapshots_used: int = 0
    # Triple series metrics
    custom_metrics: PerformanceMetrics = PerformanceMetrics()
    pms_default_metrics: PerformanceMetrics = PerformanceMetrics()
    benchmark_metrics: PerformanceMetrics = PerformanceMetrics()
    # Chart series
    equity_curve: List[Dict[str, Any]] = []          # [{date, custom, pms_default, benchmark}]
    sector_allocation_timeline: List[Dict[str, Any]] = []
    win_loss_histogram: List[Dict[str, Any]] = []     # [{bucket, count}]
    # Tables
    summary: BacktestSummaryCards = BacktestSummaryCards()
    trade_log: List[TradeRecord] = []
    portfolio_timeline: List[PortfolioTimelineEntry] = []
    benchmark_comparison_table: List[BenchmarkComparisonRow] = []
    # Execution
    execution_log: List[ExecutionLogEntry] = []
    versioning: Optional[ReportVersioning] = None
    validation_report: Optional[ValidationReportResponse] = None
    created_at: str = ""
    execution_time_sec: float = 0.0

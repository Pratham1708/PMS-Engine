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
    Sector: str = "\u2014"
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


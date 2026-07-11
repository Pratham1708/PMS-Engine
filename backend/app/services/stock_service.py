"""
Stock Service — Core business logic for stock data queries.
All data is sourced from the SQLite snapshot database when available, falling back to cached CSV.
"""

from typing import List, Optional, Any, Dict
import pandas as pd

from app.data.loader import data_loader
from app.models.schemas import (
    StockDetail,
    StockSummary,
    DashboardData,
    RatingDistribution,
    ScannerSummary,
    XaiExplanation,
)
from app.services import xai_service, db


def _get_snapshot_df(snapshot_id: str) -> pd.DataFrame:
    """Load all stock records for a snapshot from SQLite."""
    conn = db.get_db_connection()
    try:
        query = """
        SELECT
            ss.symbol AS Symbol,
            ss.final_rating AS FinalRating,
            ss.confidence AS Confidence,
            ss.composite_score AS CompositeScoreV2,
            ss.technical_score AS TechnicalScore,
            ss.ml_score AS MLScore,
            ss.gru_score AS GRUScore,
            ss.reliability_score AS ReliabilityScore,
            ss.risk_score AS RiskScore,
            ss.momentum_score AS MomentumScore,
            ss.trend_score AS TrendScore,
            ss.sector AS Sector,
            ss.open AS Open,
            ss.high AS High,
            ss.low AS Low,
            ss.close AS CurrentPrice,
            ss.volume AS Volume,
            ss.prev_close AS PreviousClose,
            ss.daily_chg_pct AS DailyChangePct,
            ss.daily_chg_amt AS DailyChangeAmount,
            ss.rank AS Rank,
            ss.percentile AS Percentile,
            ss.universe_position AS UniversePosition,
            ss.portfolio_eligible AS PortfolioEligible,
            ss.conviction_level AS ConvictionLevel,
            sc.gru_hold AS GRU_HOLD,
            sc.gru_long AS GRU_LONG,
            sc.gru_short AS GRU_SHORT,
            sc.return_score AS ReturnScore,
            sc.trend_component,
            sc.momentum_component,
            sc.volatility_component,
            sc.volume_component,
            sc.primary_driver,
            sc.secondary_driver
        FROM snapshot_stock ss
        LEFT JOIN snapshot_score sc ON sc.snapshot_id = ss.snapshot_id AND sc.symbol = ss.symbol
        WHERE ss.snapshot_id = ?
        """
        return pd.read_sql_query(query, conn, params=(snapshot_id,))
    finally:
        conn.close()


def _get_active_df() -> pd.DataFrame:
    """Return latest snapshot DataFrame or fall back to DataLoader."""
    try:
        latest = db.get_latest_snapshot()
        if latest:
            return _get_snapshot_df(latest["snapshot_id"])
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Error loading snapshot DataFrame: {e}")
    return data_loader.get_df()


def _df_to_stock_detail(row: pd.Series) -> StockDetail:
    """Convert a DataFrame row to StockDetail model including dynamic XAI fields."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"[ENGINE DEBUG] Loaded {row.get('Symbol')}: TechnicalScore={row.get('TechnicalScore')}, "
        f"MLScore={row.get('MLScore')}, GRUScore={row.get('GRUScore')}, "
        f"ReliabilityScore={row.get('ReliabilityScore')}, CompositeScoreV2={row.get('CompositeScoreV2')}"
    )

    rank_val = row.get("Rank")
    rank = int(rank_val) if pd.notna(rank_val) else 0

    pct_val = row.get("Percentile")
    percentile = float(pct_val) if pd.notna(pct_val) else 0.0

    universe_pos = row.get("UniversePosition", "—")
    if pd.isna(universe_pos):
        universe_pos = "—"

    portfolio_eligible = bool(row.get("PortfolioEligible", False)) if pd.notna(row.get("PortfolioEligible")) else False
    conviction_level = row.get("ConvictionLevel", "Medium Conviction")
    if pd.isna(conviction_level):
        conviction_level = "Medium Conviction"


    # Safe float handling for merged nullable fields
    confidence_val = float(row["Confidence"]) if pd.notna(row.get("Confidence")) else 50.0
    comp_val = float(row["CompositeScoreV2"]) if pd.notna(row.get("CompositeScoreV2")) else 50.0
    tech_val = float(row["TechnicalScore"]) if pd.notna(row.get("TechnicalScore")) else 50.0
    ml_val = float(row["MLScore"]) if pd.notna(row.get("MLScore")) else 50.0
    gru_val = float(row["GRUScore"]) if pd.notna(row.get("GRUScore")) else 50.0
    reliability_val = float(row["ReliabilityScore"]) if pd.notna(row.get("ReliabilityScore")) else 50.0

    gru_hold = float(row["GRU_HOLD"]) if pd.notna(row.get("GRU_HOLD")) else None
    gru_long = float(row["GRU_LONG"]) if pd.notna(row.get("GRU_LONG")) else None
    gru_short = float(row["GRU_SHORT"]) if pd.notna(row.get("GRU_SHORT")) else None
    return_score = float(row["ReturnScore"]) if pd.notna(row.get("ReturnScore")) else None

    # Retrieve or dynamically compute Trend, Momentum, and Risk scores
    risk_val = float(row["RiskScore"]) if pd.notna(row.get("RiskScore")) else (100.0 - confidence_val)
    momentum_val = float(row["MomentumScore"]) if pd.notna(row.get("MomentumScore")) else (tech_val * 0.8 + ml_val * 0.2)
    trend_val = float(row["TrendScore"]) if pd.notna(row.get("TrendScore")) else (gru_val * 0.6 + tech_val * 0.4)

    # Generate explanations
    tech_reason = xai_service.generate_technical_reason(tech_val)
    ml_reason = xai_service.generate_ml_reason(ml_val)
    gru_reason = xai_service.generate_gru_reason(gru_val, gru_long, gru_short, gru_hold)
    ret_reason = xai_service.generate_return_reason(return_score)
    rating_reason = xai_service.generate_rating_reason(
        row["Symbol"], row["FinalRating"], comp_val, rank, percentile, universe_pos
    )
    drivers = xai_service.generate_rating_drivers(row)

    xai = XaiExplanation(
        TechnicalScoreReason=tech_reason,
        MLScoreReason=ml_reason,
        GRUScoreReason=gru_reason,
        ReturnScoreReason=ret_reason,
        FinalRatingReason=rating_reason,
        RatingDrivers=drivers
    )

    pos_factors = xai_service.generate_positive_factors(row)
    neg_factors = xai_service.generate_negative_factors(row)
    insight = xai_service.generate_institutional_insight(row, rank, percentile)

    return StockDetail(
        Symbol=row["Symbol"],
        FinalRating=row["FinalRating"],
        Confidence=round(confidence_val, 2),
        CompositeScoreV2=round(comp_val, 2),
        TechnicalScore=round(tech_val, 2),
        MLScore=round(ml_val, 2),
        GRUScore=round(gru_val, 2),
        ReliabilityScore=round(reliability_val, 2),
        RiskScore=round(risk_val, 2),
        MomentumScore=round(momentum_val, 2),
        TrendScore=round(trend_val, 2),
        Sector=str(row["Sector"]) if pd.notna(row.get("Sector")) else "—",
        CompanyName=row.get("CompanyName") if pd.notna(row.get("CompanyName")) else None,
        Industry=row.get("Industry") if pd.notna(row.get("Industry")) else None,
        Website=row.get("Website") if pd.notna(row.get("Website")) else None,
        GRU_HOLD=gru_hold,
        GRU_LONG=gru_long,
        GRU_SHORT=gru_short,
        ReturnScore=return_score,
        Rank=rank,
        Percentile=percentile,
        UniversePosition=universe_pos,
        PortfolioEligible=portfolio_eligible,
        ConvictionLevel=conviction_level,
        xai_explanation=xai,
        top_positive_factors=pos_factors,
        top_negative_factors=neg_factors,
        institutional_insight=insight,
        # Live market fields
        CurrentPrice=float(row["CurrentPrice"]) if pd.notna(row.get("CurrentPrice")) else None,
        Open=float(row["Open"]) if pd.notna(row.get("Open")) else None,
        High=float(row["High"]) if pd.notna(row.get("High")) else None,
        Low=float(row["Low"]) if pd.notna(row.get("Low")) else None,
        Volume=int(row["Volume"]) if pd.notna(row.get("Volume")) else None,
        PreviousClose=float(row["PreviousClose"]) if pd.notna(row.get("PreviousClose")) else None,
        DailyChangePct=float(row["DailyChangePct"]) if pd.notna(row.get("DailyChangePct")) else None,
        DailyChangeAmount=float(row["DailyChangeAmount"]) if pd.notna(row.get("DailyChangeAmount")) else None,
        LastMarketUpdate=data_loader.last_market_update,
        LastScannerRun=data_loader.last_scanner_run
    )



def _df_to_stock_summary(row: pd.Series) -> StockSummary:
    """Convert a DataFrame row to StockSummary model."""
    return StockSummary(
        Symbol=row["Symbol"],
        FinalRating=row["FinalRating"],
        Confidence=round(row["Confidence"], 2),
        CompositeScoreV2=round(row["CompositeScoreV2"], 2),
        Sector=row.get("Sector", "—"),
        # Live market fields
        CurrentPrice=float(row["CurrentPrice"]) if pd.notna(row.get("CurrentPrice")) else None,
        DailyChangePct=float(row["DailyChangePct"]) if pd.notna(row.get("DailyChangePct")) else None,
        Volume=int(row["Volume"]) if pd.notna(row.get("Volume")) else None
    )


def get_all_stocks(
    sort_by: str = "CompositeScoreV2",
    order: str = "desc",
    rating: Optional[str] = None,
    search: Optional[str] = None,
) -> List[StockDetail]:
    """
    Return all stocks with optional sorting, filtering, and search.


    Args:
        sort_by: Column name to sort by.
        order: 'asc' or 'desc'.
        rating: Filter by FinalRating value.
        search: Search substring in Symbol (case-insensitive).
    """
    df = _get_active_df()

    if df.empty:
        return []

    # Filter by rating
    if rating:
        df = df[df["FinalRating"] == rating]

    # Search by symbol
    if search:
        df = df[df["Symbol"].str.contains(search.upper(), case=False, na=False)]

    # Sort
    ascending = order.lower() == "asc"
    if sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=ascending)

    return [_df_to_stock_detail(row) for _, row in df.iterrows()]


def get_stock(symbol: str) -> Optional[StockDetail]:
    """Return a single stock by symbol, or None if not found.

    Resolution order:
    1. Latest snapshot (SQLite) — preferred; reflects most recent scanner run.
    2. CSV data_loader fallback — used when the snapshot exists but does not
       contain this symbol (e.g. snapshot is partial / still being built).
    """
    import logging
    _log = logging.getLogger(__name__)

    df = _get_active_df()
    match = df[df["Symbol"] == symbol]
    if match.empty:
        match = df[df["Symbol"].str.upper() == symbol.upper()]

    if match.empty:
        # Cascade: the snapshot may be partial — try the full CSV universe
        csv_df = data_loader.get_df()
        match = csv_df[csv_df["Symbol"] == symbol]
        if match.empty:
            match = csv_df[csv_df["Symbol"].str.upper() == symbol.upper()]
        if not match.empty:
            _log.info(
                f"[StockService] '{symbol}' not in latest snapshot; "
                "serving from CSV data_loader fallback."
            )
        else:
            return None

    return _df_to_stock_detail(match.iloc[0])


def get_top_buys(limit: int = 10) -> List[StockSummary]:
    """Return top BUY and STRONG BUY stocks sorted by CompositeScoreV2 desc."""
    df = _get_active_df()
    buys = df[df["FinalRating"].isin(["STRONG BUY", "BUY"])]
    buys = buys.sort_values("CompositeScoreV2", ascending=False).head(limit)
    return [_df_to_stock_summary(row) for _, row in buys.iterrows()]


def get_top_sells(limit: int = 10) -> List[StockSummary]:
    """Return top SELL and STRONG SELL stocks sorted by CompositeScoreV2 asc."""
    df = _get_active_df()
    sells = df[df["FinalRating"].isin(["SELL", "STRONG SELL"])]
    sells = sells.sort_values("CompositeScoreV2", ascending=True).head(limit)
    return [_df_to_stock_summary(row) for _, row in sells.iterrows()]


def get_dashboard() -> DashboardData:
    """Build aggregated dashboard data."""
    df = _get_active_df()

    rating_counts = df["FinalRating"].value_counts()

    return DashboardData(
        total_stocks=len(df),
        strong_buy_count=int(rating_counts.get("STRONG BUY", 0)),
        buy_count=int(rating_counts.get("BUY", 0)),
        hold_count=int(rating_counts.get("HOLD", 0)),
        sell_count=int(rating_counts.get("SELL", 0)),
        strong_sell_count=int(rating_counts.get("STRONG SELL", 0)),
        avg_confidence=round(df["Confidence"].mean(), 2),
        avg_composite=round(df["CompositeScoreV2"].mean(), 2),
        top_buys=get_top_buys(5),
        top_sells=get_top_sells(5),
    )


def get_ratings_distribution() -> RatingDistribution:
    """Return count of stocks per rating level."""
    df = _get_active_df()
    counts = df["FinalRating"].value_counts()

    return RatingDistribution(
        strong_buy=int(counts.get("STRONG BUY", 0)),
        buy=int(counts.get("BUY", 0)),
        hold=int(counts.get("HOLD", 0)),
        sell=int(counts.get("SELL", 0)),
        strong_sell=int(counts.get("STRONG SELL", 0)),
    )


def get_scanner_summary() -> ScannerSummary:
    """Return universe-wide summary statistics."""
    df = _get_active_df()

    return ScannerSummary(
        total_stocks=len(df),
        avg_confidence=round(df["Confidence"].mean(), 2),
        avg_composite=round(df["CompositeScoreV2"].mean(), 2),
        max_composite=round(df["CompositeScoreV2"].max(), 2),
        min_composite=round(df["CompositeScoreV2"].min(), 2),
        avg_technical=round(df["TechnicalScore"].mean(), 2),
        avg_ml=round(df["MLScore"].mean(), 2),
        avg_gru=round(df["GRUScore"].mean(), 2),
        avg_reliability=round(df["ReliabilityScore"].mean(), 2),
    )


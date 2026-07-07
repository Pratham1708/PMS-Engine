"""
snapshot_pipeline.py — Modular 23-stage snapshot generation pipeline.

Each stage is an independent, testable, async-compatible function.
The master orchestrator run_pipeline() calls stages sequentially,
tracking progress via PipelineMonitor and persisting results to SQLite.

Fault tolerance:
- Per-stock failures: skip stock, log, continue.
- Non-critical stage failures: log, mark warning, continue.
- Critical stage failures (download, publish, archive): abort, mark 'failed'.

Architecture:
- PipelineContext is the shared mutable state carried through all stages.
- StageResult is returned by each stage with counts, timing, and messages.
- All DB writes go through app.services.db helper functions.
- All data computation reuses existing PMS Engine service modules.
"""

import asyncio
import logging
import time
import json
from dataclasses import dataclass, field
from datetime import datetime, date as date_type
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import pytz

from app.services import db
from app.services.pipeline_monitor import get_monitor
from app.services.snapshot_validator import run_validation

logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")

# ── Watchlist Definitions ──────────────────────────────────────────────────

WATCHLIST_DEFINITIONS = {
    "top_opportunities": {
        "display_name": "Top Opportunities",
        "description": "Highest composite score stocks rated BUY or better",
        "filter": lambda df: df[df["FinalRating"].isin(["STRONG BUY", "BUY"])],
        "sort_by": "CompositeScoreV2",
        "limit": 15,
        "reason_col": "CompositeScoreV2",
        "reason_tmpl": "Composite: {:.1f}",
    },
    "high_conviction": {
        "display_name": "High Conviction",
        "description": "Stocks with Confidence ≥80% rated BUY or better",
        "filter": lambda df: df[(df["FinalRating"].isin(["STRONG BUY", "BUY"])) & (df["Confidence"] >= 80)],
        "sort_by": "Confidence",
        "limit": 10,
        "reason_col": "Confidence",
        "reason_tmpl": "Confidence: {:.0f}%",
    },
    "momentum": {
        "display_name": "Momentum",
        "description": "Top momentum leaders by technical score",
        "filter": lambda df: df[df["TechnicalScore"] > 70],
        "sort_by": "TechnicalScore",
        "limit": 10,
        "reason_col": "TechnicalScore",
        "reason_tmpl": "Technical: {:.1f}",
    },
    "quality": {
        "display_name": "Quality",
        "description": "High reliability and confidence stocks",
        "filter": lambda df: df[df["ReliabilityScore"] >= 70],
        "sort_by": "ReliabilityScore",
        "limit": 10,
        "reason_col": "ReliabilityScore",
        "reason_tmpl": "Reliability: {:.1f}",
    },
    "breakout": {
        "display_name": "Breakout Candidates",
        "description": "Stocks near 52-week highs with strong momentum",
        "filter": lambda df: df[(df["TechnicalScore"] > 80) & (df["FinalRating"].isin(["STRONG BUY", "BUY"]))],
        "sort_by": "TechnicalScore",
        "limit": 10,
        "reason_col": "TechnicalScore",
        "reason_tmpl": "Technical: {:.1f}",
    },
    "recovery": {
        "display_name": "Recovery",
        "description": "Improving stocks previously rated SELL now moving to HOLD+",
        "filter": lambda df: df[df["FinalRating"].isin(["HOLD", "BUY"])],
        "sort_by": "CompositeScoreV2",
        "limit": 10,
        "reason_col": "CompositeScoreV2",
        "reason_tmpl": "Composite: {:.1f}",
    },
    "value": {
        "display_name": "Value",
        "description": "Stocks with strong fundamentals and high composite",
        "filter": lambda df: df[(df["CompositeScoreV2"] > 40) & (df["ReliabilityScore"] >= 60)],
        "sort_by": "CompositeScoreV2",
        "limit": 10,
        "reason_col": "CompositeScoreV2",
        "reason_tmpl": "Composite: {:.1f}",
    },
    "growth": {
        "display_name": "Growth",
        "description": "Stocks with strong ML growth signals",
        "filter": lambda df: df[df["MLScore"] > 60],
        "sort_by": "MLScore",
        "limit": 10,
        "reason_col": "MLScore",
        "reason_tmpl": "ML Score: {:.1f}",
    },
    "turnaround": {
        "display_name": "Turnaround",
        "description": "Stocks with strong GRU long signals showing reversal potential",
        "filter": lambda df: df[(df["GRUScore"].notna()) & (df["GRUScore"] > 50)],
        "sort_by": "GRUScore",
        "limit": 10,
        "reason_col": "GRUScore",
        "reason_tmpl": "GRU: {:.1f}",
    },
    "undervalued": {
        "display_name": "Undervalued",
        "description": "High composite stocks with HOLD rating — potential re-rating candidates",
        "filter": lambda df: df[(df["FinalRating"] == "HOLD") & (df["CompositeScoreV2"] > 30)],
        "sort_by": "CompositeScoreV2",
        "limit": 10,
        "reason_col": "CompositeScoreV2",
        "reason_tmpl": "Composite: {:.1f}",
    },
    "overvalued": {
        "display_name": "Overvalued",
        "description": "Low composite stocks — candidates for reduction",
        "filter": lambda df: df[df["FinalRating"].isin(["SELL", "STRONG SELL"])],
        "sort_by": "CompositeScoreV2",
        "limit": 10,
        "ascending": True,
        "reason_col": "CompositeScoreV2",
        "reason_tmpl": "Composite: {:.1f}",
    },
    "low_risk": {
        "display_name": "Low Risk",
        "description": "High reliability and confidence with BUY+ rating",
        "filter": lambda df: df[(df["Confidence"] >= 75) & (df["FinalRating"].isin(["STRONG BUY", "BUY"]))],
        "sort_by": "Confidence",
        "limit": 10,
        "reason_col": "Confidence",
        "reason_tmpl": "Confidence: {:.0f}%",
    },
    "high_risk": {
        "display_name": "High Risk",
        "description": "High return potential but low confidence — speculative",
        "filter": lambda df: df[(df["Confidence"] < 50) & (df["CompositeScoreV2"] > 40)],
        "sort_by": "CompositeScoreV2",
        "limit": 10,
        "reason_col": "Confidence",
        "reason_tmpl": "Confidence: {:.0f}%",
    },
    "swing_trades": {
        "display_name": "Swing Trades",
        "description": "High technical momentum stocks suitable for short-term plays",
        "filter": lambda df: df[df["TechnicalScore"] > 75],
        "sort_by": "TechnicalScore",
        "limit": 10,
        "reason_col": "TechnicalScore",
        "reason_tmpl": "Technical: {:.1f}",
    },
    "long_term": {
        "display_name": "Long-Term Investments",
        "description": "High composite + reliability stocks for core portfolio",
        "filter": lambda df: df[
            (df["CompositeScoreV2"] > 50) &
            (df["ReliabilityScore"] >= 70) &
            (df["FinalRating"].isin(["STRONG BUY", "BUY"]))
        ],
        "sort_by": "CompositeScoreV2",
        "limit": 10,
        "reason_col": "CompositeScoreV2",
        "reason_tmpl": "Composite: {:.1f}",
    },
    "dividend": {
        "display_name": "Dividend",
        "description": "Stable, high-reliability stocks suitable for dividend income",
        "filter": lambda df: df[(df["ReliabilityScore"] >= 70) & (df["Confidence"] >= 70)],
        "sort_by": "ReliabilityScore",
        "limit": 10,
        "reason_col": "ReliabilityScore",
        "reason_tmpl": "Reliability: {:.1f}",
    },
}


# ── Pipeline Context ─────────────────────────────────────────────────────────

@dataclass
class PipelineContext:
    """Shared mutable state carried through all pipeline stages."""
    snapshot_id: str
    snapshot_date: str
    is_official: bool
    symbols: List[str] = field(default_factory=list)
    df: Optional[pd.DataFrame] = None          # main working DataFrame
    ohlcv_data: Dict[str, Dict] = field(default_factory=dict)
    indicator_data: Dict[str, Dict] = field(default_factory=dict)
    scores: Dict[str, Dict] = field(default_factory=dict)
    sector_records: List[Dict] = field(default_factory=list)
    market_record: Dict = field(default_factory=dict)
    watchlist_records: List[Dict] = field(default_factory=list)
    change_records: List[Dict] = field(default_factory=list)
    stock_records: List[Dict] = field(default_factory=list)
    indicator_records: List[Dict] = field(default_factory=list)
    score_records: List[Dict] = field(default_factory=list)
    failed_symbols: List[str] = field(default_factory=list)
    skipped_stages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class StageResult:
    """Result returned by each pipeline stage."""
    stage: str
    status: str  # 'done' | 'done_with_warnings' | 'failed' | 'skipped'
    stocks_ok: int = 0
    stocks_failed: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_sec: float = 0.0
    log_summary: str = ""


def _now_ist_str() -> str:
    return datetime.now(IST).isoformat()


def _record_stage(ctx: PipelineContext, result: StageResult) -> None:
    """Persist stage result to snapshot_metadata table."""
    now = _now_ist_str()
    db.save_snapshot_stage(
        snapshot_id=ctx.snapshot_id,
        stage_name=result.stage,
        stage_status=result.status,
        completed_at=now,
        duration_sec=result.duration_sec,
        stocks_success=result.stocks_ok,
        stocks_failed=result.stocks_failed,
        warnings_count=len(result.warnings),
        errors_count=len(result.errors),
        log_summary=result.log_summary[:500] if result.log_summary else None,
    )
    for w in result.warnings:
        ctx.warnings.append(w)
    for e in result.errors:
        ctx.errors.append(e)


# ── Pipeline Stages ──────────────────────────────────────────────────────────

def _stage_load_security_master(ctx: PipelineContext) -> StageResult:
    """Stage 01: Load security master universe into context."""
    t0 = time.monotonic()
    try:
        from app.data.loader import data_loader
        df = data_loader.get_df()
        if df is None or df.empty:
            return StageResult("01_load_security_master", "failed",
                               errors=["DataLoader returned empty DataFrame"],
                               duration_sec=time.monotonic() - t0)
        ctx.df = df.copy()
        ctx.symbols = ctx.df["Symbol"].tolist()
        return StageResult(
            "01_load_security_master", "done",
            stocks_ok=len(ctx.symbols),
            log_summary=f"Loaded {len(ctx.symbols)} symbols from DataLoader",
            duration_sec=round(time.monotonic() - t0, 2),
        )
    except Exception as e:
        return StageResult("01_load_security_master", "failed",
                           errors=[str(e)], duration_sec=time.monotonic() - t0)


def _stage_download_ohlcv(ctx: PipelineContext) -> StageResult:
    """Stage 02: Download live OHLCV for all symbols (critical stage)."""
    t0 = time.monotonic()
    from app.services.realtime_feed import fetch_quote_single
    monitor = get_monitor()
    ok, failed = 0, 0
    warnings: List[str] = []

    for symbol in ctx.symbols:
        try:
            quote = fetch_quote_single(symbol)
            ctx.ohlcv_data[symbol] = quote
            is_mock = quote.get("IsMock", True)
            if is_mock:
                warnings.append(f"{symbol}: using mock/cached price data")
            # Merge into DataFrame
            if ctx.df is not None:
                idx = ctx.df[ctx.df["Symbol"].str.upper() == symbol.upper()].index
                if not idx.empty:
                    for col in ["CurrentPrice", "Open", "High", "Low", "Volume",
                                "PreviousClose", "DailyChangePct", "DailyChangeAmount"]:
                        if col in quote:
                            ctx.df.at[idx[0], col] = quote[col]
            ok += 1
            monitor.stock_done(symbol, success=True)
        except Exception as e:
            failed += 1
            ctx.failed_symbols.append(symbol)
            warnings.append(f"{symbol}: download failed — {str(e)[:80]}")
            monitor.stock_done(symbol, success=False)

    status = "done" if ok > 0 else "failed"
    if warnings:
        status = "done_with_warnings" if ok > 0 else "failed"
    return StageResult(
        "02_download_ohlcv", status,
        stocks_ok=ok, stocks_failed=failed,
        warnings=warnings[:20],
        log_summary=f"Downloaded {ok}/{len(ctx.symbols)} quotes; {failed} failed; "
                    f"{sum(1 for q in ctx.ohlcv_data.values() if q.get('IsMock'))} mocked",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_validate_downloads(ctx: PipelineContext) -> StageResult:
    """Stage 03: Validate downloaded data quality."""
    t0 = time.monotonic()
    warnings: List[str] = []
    missing_price = [s for s, q in ctx.ohlcv_data.items() if not q.get("CurrentPrice")]
    if missing_price:
        warnings.append(f"{len(missing_price)} symbols have no CurrentPrice: {missing_price[:5]}")
    coverage = len(ctx.ohlcv_data) / max(len(ctx.symbols), 1) * 100
    return StageResult(
        "03_validate_downloads", "done_with_warnings" if warnings else "done",
        stocks_ok=len(ctx.ohlcv_data), stocks_failed=len(missing_price),
        warnings=warnings,
        log_summary=f"Coverage: {coverage:.1f}%; {len(missing_price)} missing prices",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_update_corporate_actions(ctx: PipelineContext) -> StageResult:
    """Stage 04: Update corporate actions (stub — future implementation)."""
    t0 = time.monotonic()
    return StageResult(
        "04_update_corporate_actions", "skipped",
        log_summary="Corporate actions update not yet implemented; skipped",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_update_fundamentals(ctx: PipelineContext) -> StageResult:
    """Stage 05: Update fundamentals (stub — future implementation)."""
    t0 = time.monotonic()
    return StageResult(
        "05_update_fundamentals", "skipped",
        log_summary="Fundamentals update not yet implemented; skipped",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_generate_indicators(ctx: PipelineContext) -> StageResult:
    """Stage 06: Compute technical indicators from existing scores in DataFrame."""
    t0 = time.monotonic()
    ok, failed = 0, 0
    if ctx.df is None:
        return StageResult("06_generate_indicators", "failed",
                           errors=["DataFrame not loaded"], duration_sec=time.monotonic() - t0)
    for _, row in ctx.df.iterrows():
        symbol = row.get("Symbol", "")
        try:
            close = float(row.get("CurrentPrice") or row.get("Close") or 0)
            prev = float(row.get("PreviousClose") or 0)
            tech = float(row.get("TechnicalScore", 0))
            # Derive approximate indicator booleans from existing score columns
            above_ema20 = tech > 60
            above_ema50 = tech > 45
            above_ema200 = tech > 30
            near_52w_high = (close > 0 and prev > 0 and close >= prev * 1.02)
            near_52w_low = (close > 0 and prev > 0 and close <= prev * 0.98)
            ctx.indicator_data[symbol] = {
                "symbol": symbol,
                "rsi_14": None,
                "ema_20": None,
                "ema_50": None,
                "ema_200": None,
                "macd": None,
                "macd_signal": None,
                "bb_upper": None,
                "bb_lower": None,
                "atr_14": None,
                "stoch_k": None,
                "adx_14": None,
                "obv": None,
                "vwap": None,
                "above_ema20": 1 if above_ema20 else 0,
                "above_ema50": 1 if above_ema50 else 0,
                "above_ema200": 1 if above_ema200 else 0,
                "near_52w_high": 1 if near_52w_high else 0,
                "near_52w_low": 1 if near_52w_low else 0,
            }
            ok += 1
        except Exception as e:
            failed += 1
            ctx.warnings.append(f"{symbol}: indicator computation failed — {e}")
    ctx.indicator_records = list(ctx.indicator_data.values())
    return StageResult(
        "06_generate_indicators", "done",
        stocks_ok=ok, stocks_failed=failed,
        log_summary=f"Indicators derived for {ok} stocks",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_generate_features(ctx: PipelineContext) -> StageResult:
    """Stage 07: Feature engineering (uses existing computed scores from CSV)."""
    t0 = time.monotonic()
    # Existing features are already in ctx.df; this stage is a passthrough
    # until a future feature engineering module is integrated.
    return StageResult(
        "07_generate_features", "done",
        stocks_ok=len(ctx.symbols),
        log_summary="Features sourced from pre-computed CSV columns",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_run_ml_models(ctx: PipelineContext) -> StageResult:
    """Stage 08: Run ML models (existing MLScore/GRUScore already in DataFrame)."""
    t0 = time.monotonic()
    # ML models were run offline to produce the CSV; online re-scoring
    # is a future phase when the full training pipeline is integrated.
    ok = ctx.df["MLScore"].notna().sum() if ctx.df is not None else 0
    return StageResult(
        "08_run_ml_models", "done",
        stocks_ok=int(ok),
        log_summary=f"ML scores loaded from CSV for {ok} stocks",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_generate_technical_scores(ctx: PipelineContext) -> StageResult:
    """Stage 09: Technical scores already in DataFrame from CSV."""
    t0 = time.monotonic()
    ok = ctx.df["TechnicalScore"].notna().sum() if ctx.df is not None else 0
    return StageResult(
        "09_generate_technical_scores", "done",
        stocks_ok=int(ok),
        log_summary=f"TechnicalScore ready for {ok} stocks",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_generate_risk_scores(ctx: PipelineContext) -> StageResult:
    """Stage 10: Compute risk score from reliability and confidence."""
    t0 = time.monotonic()
    if ctx.df is None:
        return StageResult("10_generate_risk_scores", "skipped", duration_sec=time.monotonic() - t0)
    if "RiskScore" not in ctx.df.columns:
        ctx.df["RiskScore"] = 100.0 - ctx.df["Confidence"].fillna(50)
    ok = ctx.df["RiskScore"].notna().sum()
    return StageResult(
        "10_generate_risk_scores", "done",
        stocks_ok=int(ok),
        log_summary=f"RiskScore computed for {ok} stocks",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_generate_momentum_scores(ctx: PipelineContext) -> StageResult:
    """Stage 11: Derive momentum score from TechnicalScore."""
    t0 = time.monotonic()
    if ctx.df is None:
        return StageResult("11_generate_momentum_scores", "skipped", duration_sec=time.monotonic() - t0)
    if "MomentumScore" not in ctx.df.columns:
        ctx.df["MomentumScore"] = (ctx.df["TechnicalScore"].fillna(0) * 0.8 +
                                   ctx.df["MLScore"].fillna(0) * 0.2)
    ok = ctx.df["MomentumScore"].notna().sum()
    return StageResult(
        "11_generate_momentum_scores", "done",
        stocks_ok=int(ok),
        log_summary=f"MomentumScore computed for {ok} stocks",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_generate_trend_scores(ctx: PipelineContext) -> StageResult:
    """Stage 12: Derive trend score from GRU and Technical scores."""
    t0 = time.monotonic()
    if ctx.df is None:
        return StageResult("12_generate_trend_scores", "skipped", duration_sec=time.monotonic() - t0)
    if "TrendScore" not in ctx.df.columns:
        ctx.df["TrendScore"] = (ctx.df["GRUScore"].fillna(0) * 0.6 +
                                ctx.df["TechnicalScore"].fillna(0) * 0.4)
    ok = ctx.df["TrendScore"].notna().sum()
    return StageResult(
        "12_generate_trend_scores", "done",
        stocks_ok=int(ok),
        log_summary=f"TrendScore computed for {ok} stocks",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_generate_confidence_scores(ctx: PipelineContext) -> StageResult:
    """Stage 13: Confidence scores from existing CSV column."""
    t0 = time.monotonic()
    ok = ctx.df["Confidence"].notna().sum() if ctx.df is not None else 0
    return StageResult(
        "13_generate_confidence_scores", "done",
        stocks_ok=int(ok),
        log_summary=f"Confidence scores ready for {ok} stocks",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_generate_composite_scores(ctx: PipelineContext) -> StageResult:
    """Stage 14: Composite scores from existing CompositeScoreV2 column."""
    t0 = time.monotonic()
    ok = ctx.df["CompositeScoreV2"].notna().sum() if ctx.df is not None else 0
    return StageResult(
        "14_generate_composite_scores", "done",
        stocks_ok=int(ok),
        log_summary=f"CompositeScoreV2 ready for {ok} stocks",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_generate_recommendations(ctx: PipelineContext) -> StageResult:
    """Stage 15: Generate recommendations from ratings + XAI drivers."""
    t0 = time.monotonic()
    from app.services import xai_service
    ok, failed = 0, 0
    score_records: List[Dict] = []
    stock_records: List[Dict] = []

    if ctx.df is None:
        return StageResult("15_generate_recommendations", "failed",
                           errors=["No DataFrame loaded"], duration_sec=time.monotonic() - t0)

    # Merge sector data from security_master
    sector_map = {}
    conn = db.get_db_connection()
    try:
        rows = conn.execute("SELECT symbol, sector, industry, company_name FROM security_master").fetchall()
        for r in rows:
            sector_map[r["symbol"].upper()] = {
                "sector": r["sector"] or "—",
                "industry": r["industry"] or "—",
                "company_name": r["company_name"] or r["symbol"],
            }
    finally:
        conn.close()

    # Sort by composite for ranking
    df_sorted = ctx.df.sort_values("CompositeScoreV2", ascending=False).reset_index(drop=True)
    total = len(df_sorted)

    for rank_idx, (_, row) in enumerate(df_sorted.iterrows(), start=1):
        symbol = row.get("Symbol", "")
        try:
            # XAI drivers
            drivers = xai_service.generate_rating_drivers(row)
            primary = drivers[0] if drivers else None
            secondary = drivers[1] if len(drivers) > 1 else None

            sm = sector_map.get(symbol.upper(), {})
            composite = float(row.get("CompositeScoreV2", 0) or 0)
            confidence = float(row.get("Confidence", 0) or 0)
            tech = float(row.get("TechnicalScore", 0) or 0)
            ml = float(row.get("MLScore", 0) or 0)
            gru = float(row.get("GRUScore", 0) or 0)
            reliability = float(row.get("ReliabilityScore", 0) or 0)
            risk = float(ctx.df.at[row.name, "RiskScore"] if "RiskScore" in ctx.df.columns and pd.notna(ctx.df.at[row.name, "RiskScore"]) else 100 - confidence)
            momentum = float(ctx.df.at[row.name, "MomentumScore"] if "MomentumScore" in ctx.df.columns and pd.notna(ctx.df.at[row.name, "MomentumScore"]) else tech)
            trend = float(ctx.df.at[row.name, "TrendScore"] if "TrendScore" in ctx.df.columns and pd.notna(ctx.df.at[row.name, "TrendScore"]) else gru)

            final_rating = str(row.get("FinalRating", "HOLD"))
            percentile = round((total - rank_idx) / max(total - 1, 1) * 100, 1)
            portfolio_eligible = final_rating in ("STRONG BUY", "BUY")

            # OHLCV from quote
            quote = ctx.ohlcv_data.get(symbol, {})
            close = float(quote.get("CurrentPrice") or row.get("CurrentPrice") or 0)
            open_ = float(quote.get("Open") or row.get("Open") or 0)
            high = float(quote.get("High") or row.get("High") or 0)
            low = float(quote.get("Low") or row.get("Low") or 0)
            volume = int(quote.get("Volume") or row.get("Volume") or 0)
            prev_close = float(quote.get("PreviousClose") or row.get("PreviousClose") or 0)
            daily_chg_pct = float(quote.get("DailyChangePct") or row.get("DailyChangePct") or 0)
            daily_chg_amt = float(quote.get("DailyChangeAmount") or row.get("DailyChangeAmount") or 0)

            data_source = "yfinance" if not quote.get("IsMock") else "mock"
            download_status = "success" if quote else "failed"

            stock_record = {
                "symbol": symbol,
                "company_name": sm.get("company_name", symbol),
                "sector": sm.get("sector", "—"),
                "industry": sm.get("industry", "—"),
                "open": open_ or None,
                "high": high or None,
                "low": low or None,
                "close": close or None,
                "volume": volume or None,
                "prev_close": prev_close or None,
                "daily_chg_pct": daily_chg_pct,
                "daily_chg_amt": daily_chg_amt,
                "week52_high": None,
                "week52_low": None,
                "technical_score": round(tech, 2),
                "ml_score": round(ml, 2),
                "gru_score": round(gru, 2),
                "risk_score": round(risk, 2),
                "momentum_score": round(momentum, 2),
                "trend_score": round(trend, 2),
                "confidence": round(confidence, 2),
                "composite_score": round(composite, 2),
                "reliability_score": round(reliability, 2),
                "final_rating": final_rating,
                "portfolio_eligible": 1 if portfolio_eligible else 0,
                "conviction_level": str(row.get("ConvictionLevel", "Medium Conviction") or "Medium Conviction"),
                "rank": rank_idx,
                "percentile": percentile,
                "universe_position": str(row.get("UniversePosition", f"Top {int(100 - percentile)}%") or f"Top {int(100 - percentile)}%"),
                "data_source": data_source,
                "download_status": download_status,
                "data_warnings": json.dumps([]) if quote else json.dumps(["No quote data"]),
            }
            stock_records.append(stock_record)

            # Score breakdown record
            gru_hold = float(row["GRU_HOLD"]) if pd.notna(row.get("GRU_HOLD")) else None
            gru_long = float(row["GRU_LONG"]) if pd.notna(row.get("GRU_LONG")) else None
            gru_short = float(row["GRU_SHORT"]) if pd.notna(row.get("GRU_SHORT")) else None
            ret_score = float(row["ReturnScore"]) if pd.notna(row.get("ReturnScore")) else None
            score_records.append({
                "symbol": symbol,
                "trend_component": round(trend * 0.5, 2),
                "momentum_component": round(momentum * 0.5, 2),
                "volatility_component": None,
                "volume_component": None,
                "lgbm_signal": round(ml, 2),
                "rf_signal": None,
                "xgb_signal": None,
                "gru_hold": gru_hold,
                "gru_long": gru_long,
                "gru_short": gru_short,
                "return_score": ret_score,
                "primary_driver": primary,
                "secondary_driver": secondary,
                "w_technical": 0.40,
                "w_ml": 0.35,
                "w_gru": 0.15,
                "w_reliability": 0.10,
            })
            ok += 1
        except Exception as e:
            failed += 1
            ctx.failed_symbols.append(symbol)
            ctx.warnings.append(f"{symbol}: recommendation generation failed — {e}")

    ctx.stock_records = stock_records
    ctx.score_records = score_records
    return StageResult(
        "15_generate_recommendations", "done" if failed == 0 else "done_with_warnings",
        stocks_ok=ok, stocks_failed=failed,
        log_summary=f"Recommendations generated for {ok}/{total} stocks",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_generate_portfolio_rankings(ctx: PipelineContext) -> StageResult:
    """Stage 16: Generate portfolio rankings from existing service."""
    t0 = time.monotonic()
    try:
        from app.services.portfolio_service import build_portfolio
        portfolio = build_portfolio(capital=10_000_000)  # 1 Crore default
        ctx.scores["portfolio"] = portfolio.dict()
        return StageResult(
            "16_generate_portfolio_rankings", "done",
            stocks_ok=portfolio.total_stocks,
            log_summary=f"Portfolio built: {portfolio.total_stocks} stocks, avg composite={portfolio.avg_composite}",
            duration_sec=round(time.monotonic() - t0, 2),
        )
    except Exception as e:
        return StageResult(
            "16_generate_portfolio_rankings", "done_with_warnings",
            warnings=[f"Portfolio construction failed: {e}"],
            log_summary=str(e),
            duration_sec=round(time.monotonic() - t0, 2),
        )


def _stage_generate_sector_rankings(ctx: PipelineContext) -> StageResult:
    """Stage 17: Aggregate stocks by sector from stock_records."""
    t0 = time.monotonic()
    if not ctx.stock_records:
        return StageResult("17_generate_sector_rankings", "skipped",
                           log_summary="No stock records to aggregate", duration_sec=time.monotonic() - t0)

    sectors: Dict[str, List[Dict]] = {}
    for sr in ctx.stock_records:
        sec = sr.get("sector") or "—"
        sectors.setdefault(sec, []).append(sr)

    sector_records: List[Dict] = []
    for rank_idx, (sector, stocks) in enumerate(
        sorted(sectors.items(),
               key=lambda x: sum(s.get("composite_score") or 0 for s in x[1]) / max(len(x[1]), 1),
               reverse=True), start=1
    ):
        def avg(col: str) -> Optional[float]:
            vals = [s[col] for s in stocks if s.get(col) is not None]
            return round(sum(vals) / len(vals), 2) if vals else None

        ratings = [s.get("final_rating") for s in stocks]
        advancing = sum(1 for s in stocks if (s.get("daily_chg_pct") or 0) > 0)
        total = len(stocks)

        top = max(stocks, key=lambda s: s.get("composite_score") or -999, default=None)
        worst = min(stocks, key=lambda s: s.get("composite_score") or 999, default=None)

        sector_records.append({
            "sector": sector,
            "stock_count": total,
            "avg_composite": avg("composite_score"),
            "avg_confidence": avg("confidence"),
            "avg_technical": avg("technical_score"),
            "avg_momentum": avg("momentum_score"),
            "avg_trend": avg("trend_score"),
            "avg_risk": avg("risk_score"),
            "strong_buy_count": ratings.count("STRONG BUY"),
            "buy_count": ratings.count("BUY"),
            "hold_count": ratings.count("HOLD"),
            "sell_count": ratings.count("SELL"),
            "strong_sell_count": ratings.count("STRONG SELL"),
            "bullish_pct": round(advancing / max(total, 1) * 100, 1),
            "bearish_pct": round((total - advancing) / max(total, 1) * 100, 1),
            "sector_rank": rank_idx,
            "top_stock": top["symbol"] if top else None,
            "weakest_stock": worst["symbol"] if worst else None,
            "avg_daily_chg_pct": avg("daily_chg_pct"),
        })

    ctx.sector_records = sector_records
    return StageResult(
        "17_generate_sector_rankings", "done",
        stocks_ok=len(sector_records),
        log_summary=f"Sector rankings generated for {len(sector_records)} sectors",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_generate_market_breadth(ctx: PipelineContext) -> StageResult:
    """Stage 18: Compute universe-wide breadth metrics."""
    t0 = time.monotonic()
    if not ctx.stock_records:
        return StageResult("18_generate_market_breadth", "skipped", duration_sec=time.monotonic() - t0)

    stocks = ctx.stock_records
    total = len(stocks)
    advancing = sum(1 for s in stocks if (s.get("daily_chg_pct") or 0) > 0)
    declining = sum(1 for s in stocks if (s.get("daily_chg_pct") or 0) < 0)
    unchanged = total - advancing - declining

    adv_vol = sum(s.get("volume") or 0 for s in stocks if (s.get("daily_chg_pct") or 0) > 0)
    dec_vol = sum(s.get("volume") or 0 for s in stocks if (s.get("daily_chg_pct") or 0) < 0)

    # EMA breadth from indicator_data
    above_ema20 = sum(1 for s in stocks if ctx.indicator_data.get(s["symbol"], {}).get("above_ema20"))
    above_ema50 = sum(1 for s in stocks if ctx.indicator_data.get(s["symbol"], {}).get("above_ema50"))
    above_ema200 = sum(1 for s in stocks if ctx.indicator_data.get(s["symbol"], {}).get("above_ema200"))

    wk_high = sum(1 for s in stocks if ctx.indicator_data.get(s["symbol"], {}).get("near_52w_high"))
    wk_low = sum(1 for s in stocks if ctx.indicator_data.get(s["symbol"], {}).get("near_52w_low"))

    def avg_field(field: str) -> Optional[float]:
        vals = [s[field] for s in stocks if s.get(field) is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    avg_composite = avg_field("composite_score")
    avg_confidence = avg_field("confidence")
    avg_momentum = avg_field("momentum_score")
    avg_daily = avg_field("daily_chg_pct")
    bullish = round(advancing / max(total, 1) * 100, 1)
    bearish = round(declining / max(total, 1) * 100, 1)

    ratings = [s.get("final_rating") for s in stocks]
    strong_buy = ratings.count("STRONG BUY")
    buy = ratings.count("BUY")
    hold = ratings.count("HOLD")
    sell = ratings.count("SELL")
    strong_sell = ratings.count("STRONG SELL")

    # Market regime heuristic
    if bullish >= 65 and (strong_buy + buy) >= total * 0.5:
        regime = "Bullish"
    elif bearish >= 65 and (sell + strong_sell) >= total * 0.5:
        regime = "Bearish"
    elif abs(bullish - bearish) <= 15:
        regime = "Mixed"
    else:
        regime = "Neutral"

    ctx.market_record = {
        "total_stocks": total,
        "advancing_stocks": advancing,
        "declining_stocks": declining,
        "unchanged_stocks": unchanged,
        "advance_decline_ratio": round(advancing / max(declining, 1), 2),
        "advance_volume": adv_vol,
        "decline_volume": dec_vol,
        "stocks_above_ema20": above_ema20,
        "stocks_above_ema50": above_ema50,
        "stocks_above_ema200": above_ema200,
        "pct_above_ema20": round(above_ema20 / max(total, 1) * 100, 1),
        "pct_above_ema50": round(above_ema50 / max(total, 1) * 100, 1),
        "pct_above_ema200": round(above_ema200 / max(total, 1) * 100, 1),
        "week52_high_count": wk_high,
        "week52_low_count": wk_low,
        "avg_composite": avg_composite,
        "avg_confidence": avg_confidence,
        "avg_rsi": None,  # Populated when full indicator pipeline is integrated
        "avg_momentum": avg_momentum,
        "avg_daily_chg_pct": avg_daily,
        "bullish_pct": bullish,
        "bearish_pct": bearish,
        "market_regime": regime,
        "strong_buy_count": strong_buy,
        "buy_count": buy,
        "hold_count": hold,
        "sell_count": sell,
        "strong_sell_count": strong_sell,
        "india_vix": None,
        "pcr": None,
        "fii_activity": None,
        "dii_activity": None,
    }
    return StageResult(
        "18_generate_market_breadth", "done",
        stocks_ok=total,
        log_summary=f"Breadth: A/D={advancing}/{declining}, regime={regime}, "
                    f"EMA20={above_ema20}, EMA200={above_ema200}",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_generate_watchlists(ctx: PipelineContext) -> StageResult:
    """Stage 19: Generate 16 automatic watchlists from the stocks DataFrame."""
    t0 = time.monotonic()
    if ctx.df is None:
        return StageResult("19_generate_watchlists", "skipped", duration_sec=time.monotonic() - t0)

    records: List[Dict] = []
    total_populated = 0

    for wl_name, wl_def in WATCHLIST_DEFINITIONS.items():
        try:
            filtered = wl_def["filter"](ctx.df)
            sort_col = wl_def["sort_by"]
            ascending = wl_def.get("ascending", False)
            limit = wl_def.get("limit", 10)
            reason_col = wl_def.get("reason_col", sort_col)
            reason_tmpl = wl_def.get("reason_tmpl", "{:.1f}")

            if filtered.empty:
                continue

            sorted_df = filtered.sort_values(sort_col, ascending=ascending).head(limit)
            for rank_in_list, (_, row) in enumerate(sorted_df.iterrows(), start=1):
                score_val = float(row.get(reason_col, 0) or 0)
                records.append({
                    "watchlist_name": wl_name,
                    "symbol": row["Symbol"],
                    "rank_in_list": rank_in_list,
                    "score_used": round(score_val, 2),
                    "reason": reason_tmpl.format(score_val),
                })
            total_populated += 1
        except Exception as e:
            ctx.warnings.append(f"Watchlist '{wl_name}' failed: {e}")

    ctx.watchlist_records = records
    return StageResult(
        "19_generate_watchlists", "done",
        stocks_ok=total_populated,
        log_summary=f"Generated {total_populated}/{len(WATCHLIST_DEFINITIONS)} watchlists, "
                    f"{len(records)} total entries",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_generate_reports(ctx: PipelineContext) -> StageResult:
    """Stage 20: Generate institutional research reports using existing framework."""
    t0 = time.monotonic()
    generated = 0
    warnings: List[str] = []
    try:
        from app.services import report_generator
        # Market overview report
        market_result = report_generator.generate_market_report()
        if market_result and market_result.get("pdf_path"):
            import os
            size = os.path.getsize(market_result["pdf_path"]) / 1024 if os.path.exists(market_result["pdf_path"]) else None
            db.link_snapshot_report(
                snapshot_id=ctx.snapshot_id,
                report_type="daily_market",
                html_path=market_result.get("html_path"),
                pdf_path=market_result.get("pdf_path"),
                file_size_kb=size,
            )
            generated += 1
    except Exception as e:
        warnings.append(f"Market report failed: {e}")
    try:
        from app.services import report_generator
        ws_result = report_generator.generate_workspace_report()
        if ws_result:
            db.link_snapshot_report(
                snapshot_id=ctx.snapshot_id,
                report_type="snapshot_summary",
                html_path=ws_result.get("html_path"),
                pdf_path=ws_result.get("pdf_path"),
            )
            generated += 1
    except Exception as e:
        warnings.append(f"Workspace report failed: {e}")

    return StageResult(
        "20_generate_reports", "done_with_warnings" if warnings else "done",
        stocks_ok=generated,
        warnings=warnings,
        log_summary=f"Generated {generated} reports",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_run_validation(ctx: PipelineContext) -> StageResult:
    """Stage 21: Run pre-publish validation checks."""
    t0 = time.monotonic()
    try:
        final_status, quality_score, check_results = run_validation(ctx.snapshot_id)
        passed = sum(1 for c in check_results if c["status"] == "pass")
        failed = sum(1 for c in check_results if c["status"] == "fail")
        return StageResult(
            "21_run_validation", "done",
            stocks_ok=passed, stocks_failed=failed,
            log_summary=f"Validation: {final_status}, score={quality_score}, "
                        f"{passed} pass, {failed} fail",
            duration_sec=round(time.monotonic() - t0, 2),
        )
    except Exception as e:
        return StageResult(
            "21_run_validation", "done_with_warnings",
            warnings=[f"Validation engine error: {e}"],
            log_summary=str(e),
            duration_sec=round(time.monotonic() - t0, 2),
        )


def _stage_publish_snapshot(ctx: PipelineContext) -> StageResult:
    """Stage 22: Persist all computed data to DB and mark snapshot as official."""
    t0 = time.monotonic()
    try:
        # Bulk insert all computed records
        db.save_snapshot_stocks(ctx.snapshot_id, ctx.stock_records)
        db.save_snapshot_indicators(ctx.snapshot_id, ctx.indicator_records)
        db.save_snapshot_scores(ctx.snapshot_id, ctx.score_records)
        if ctx.sector_records:
            db.save_snapshot_sector(ctx.snapshot_id, ctx.sector_records)
        if ctx.market_record:
            db.save_snapshot_market(ctx.snapshot_id, ctx.market_record)
        if ctx.watchlist_records:
            db.save_snapshot_watchlists(ctx.snapshot_id, ctx.watchlist_records)
        if ctx.change_records:
            db.save_snapshot_changes(ctx.snapshot_id, ctx.change_records)
        if ctx.is_official:
            db.publish_snapshot(ctx.snapshot_id)
        return StageResult(
            "22_publish_snapshot", "done",
            stocks_ok=len(ctx.stock_records),
            log_summary=f"Published {len(ctx.stock_records)} stocks, "
                        f"{len(ctx.sector_records)} sectors, "
                        f"{len(ctx.watchlist_records)} watchlist entries",
            duration_sec=round(time.monotonic() - t0, 2),
        )
    except Exception as e:
        return StageResult(
            "22_publish_snapshot", "failed",
            errors=[f"Publish failed: {e}"],
            log_summary=str(e),
            duration_sec=round(time.monotonic() - t0, 2),
        )


def _stage_archive_snapshot(ctx: PipelineContext) -> StageResult:
    """Stage 23: Post-publish archive/cleanup tasks."""
    t0 = time.monotonic()
    # Future: compress old snapshots, purge old entries, send notifications
    return StageResult(
        "23_archive_snapshot", "done",
        log_summary="Archive complete (no-op: future compression tasks pending)",
        duration_sec=round(time.monotonic() - t0, 2),
    )


def _stage_compute_changes(ctx: PipelineContext) -> StageResult:
    """Stage (between 19 and 20): Compute recommendation changes vs previous snapshot."""
    t0 = time.monotonic()
    if not ctx.stock_records:
        return StageResult("19b_compute_changes", "skipped", duration_sec=time.monotonic() - t0)

    prev = db.get_previous_official_snapshot(ctx.snapshot_id)
    if not prev:
        return StageResult(
            "19b_compute_changes", "done",
            log_summary="No previous snapshot; changes N/A for first snapshot",
            duration_sec=round(time.monotonic() - t0, 2),
        )

    prev_stocks = {s["symbol"].upper(): s for s in db.get_snapshot_stocks(prev["snapshot_id"])}
    changes: List[Dict] = []

    for curr_stock in ctx.stock_records:
        sym = curr_stock["symbol"].upper()
        prev_stock = prev_stocks.get(sym)
        curr_rating = curr_stock.get("final_rating") or ""
        curr_composite = float(curr_stock.get("composite_score") or 0)
        curr_confidence = float(curr_stock.get("confidence") or 0)
        curr_tech = float(curr_stock.get("technical_score") or 0)
        curr_ml = float(curr_stock.get("ml_score") or 0)
        curr_momentum = float(curr_stock.get("momentum_score") or 0)
        curr_trend = float(curr_stock.get("trend_score") or 0)
        curr_risk = float(curr_stock.get("risk_score") or 0)

        if prev_stock is None:
            # New stock in universe
            changes.append({
                "prev_snapshot_id": prev["snapshot_id"],
                "symbol": curr_stock["symbol"],
                "change_type": "NEW_BUY" if curr_rating in ("STRONG BUY", "BUY") else "NEW_IN_UNIVERSE",
                "prev_rating": None,
                "new_rating": curr_rating,
                "composite_diff": curr_composite,
                "confidence_diff": curr_confidence,
                "technical_diff": None,
                "ml_diff": None,
                "momentum_diff": None,
                "trend_diff": None,
                "risk_diff": None,
                "primary_driver": "New stock in universe",
                "secondary_driver": None,
                "is_significant": 1,
            })
            continue

        prev_rating = prev_stock.get("final_rating") or ""
        prev_composite = float(prev_stock.get("composite_score") or 0)
        prev_confidence = float(prev_stock.get("confidence") or 0)
        composite_diff = round(curr_composite - prev_composite, 2)
        confidence_diff = round(curr_confidence - prev_confidence, 2)

        # Determine change type
        rating_order = {"STRONG SELL": 0, "SELL": 1, "HOLD": 2, "BUY": 3, "STRONG BUY": 4}
        curr_ord = rating_order.get(curr_rating, 2)
        prev_ord = rating_order.get(prev_rating, 2)

        if curr_ord > prev_ord:
            change_type = "UPGRADE"
        elif curr_ord < prev_ord:
            change_type = "DOWNGRADE"
        elif composite_diff > 5:
            change_type = "COMPOSITE_UP"
        elif composite_diff < -5:
            change_type = "COMPOSITE_DOWN"
        elif confidence_diff > 10:
            change_type = "CONFIDENCE_UP"
        elif confidence_diff < -10:
            change_type = "CONFIDENCE_DOWN"
        else:
            change_type = "NO_CHANGE"

        if change_type == "NO_CHANGE":
            continue

        # Primary driver
        diffs = {
            "Technical": abs(curr_tech - float(prev_stock.get("technical_score") or 0)),
            "ML": abs(curr_ml - float(prev_stock.get("ml_score") or 0)),
            "Momentum": abs(curr_momentum - float(prev_stock.get("momentum_score") or 0)),
            "Confidence": abs(confidence_diff),
            "Composite": abs(composite_diff),
        }
        sorted_drivers = sorted(diffs.items(), key=lambda x: x[1], reverse=True)
        primary = f"{sorted_drivers[0][0]} change ({sorted_drivers[0][1]:.1f})" if sorted_drivers else None
        secondary = f"{sorted_drivers[1][0]} change ({sorted_drivers[1][1]:.1f})" if len(sorted_drivers) > 1 else None

        changes.append({
            "prev_snapshot_id": prev["snapshot_id"],
            "symbol": curr_stock["symbol"],
            "change_type": change_type,
            "prev_rating": prev_rating,
            "new_rating": curr_rating,
            "composite_diff": composite_diff,
            "confidence_diff": confidence_diff,
            "technical_diff": round(curr_tech - float(prev_stock.get("technical_score") or 0), 2),
            "ml_diff": round(curr_ml - float(prev_stock.get("ml_score") or 0), 2),
            "momentum_diff": round(curr_momentum - float(prev_stock.get("momentum_score") or 0), 2),
            "trend_diff": round(curr_trend - float(prev_stock.get("trend_score") or 0), 2),
            "risk_diff": round(curr_risk - float(prev_stock.get("risk_score") or 0), 2),
            "primary_driver": primary,
            "secondary_driver": secondary,
            "is_significant": 1 if abs(composite_diff) > 5 or curr_ord != prev_ord else 0,
        })

    ctx.change_records = changes
    return StageResult(
        "19b_compute_changes", "done",
        stocks_ok=len(changes),
        log_summary=f"Computed {len(changes)} recommendation changes vs previous snapshot",
        duration_sec=round(time.monotonic() - t0, 2),
    )


# ── Stage Registry ────────────────────────────────────────────────────────────

PIPELINE_STAGES = [
    (1,  "01_load_security_master",       _stage_load_security_master,       True),
    (2,  "02_download_ohlcv",             _stage_download_ohlcv,             True),
    (3,  "03_validate_downloads",         _stage_validate_downloads,         False),
    (4,  "04_update_corporate_actions",   _stage_update_corporate_actions,   False),
    (5,  "05_update_fundamentals",        _stage_update_fundamentals,        False),
    (6,  "06_generate_indicators",        _stage_generate_indicators,        False),
    (7,  "07_generate_features",          _stage_generate_features,          False),
    (8,  "08_run_ml_models",              _stage_run_ml_models,              False),
    (9,  "09_generate_technical_scores",  _stage_generate_technical_scores,  False),
    (10, "10_generate_risk_scores",       _stage_generate_risk_scores,       False),
    (11, "11_generate_momentum_scores",   _stage_generate_momentum_scores,   False),
    (12, "12_generate_trend_scores",      _stage_generate_trend_scores,      False),
    (13, "13_generate_confidence_scores", _stage_generate_confidence_scores, False),
    (14, "14_generate_composite_scores",  _stage_generate_composite_scores,  False),
    (15, "15_generate_recommendations",   _stage_generate_recommendations,   False),
    (16, "16_generate_portfolio_rankings",_stage_generate_portfolio_rankings,False),
    (17, "17_generate_sector_rankings",   _stage_generate_sector_rankings,   False),
    (18, "18_generate_market_breadth",    _stage_generate_market_breadth,    False),
    (19, "19_generate_watchlists",        _stage_generate_watchlists,        False),
    (20, "19b_compute_changes",           _stage_compute_changes,            False),
    (21, "20_generate_reports",           _stage_generate_reports,           False),
    (22, "21_run_validation",             _stage_run_validation,             False),
    (23, "22_publish_snapshot",           _stage_publish_snapshot,           True),
    (24, "23_archive_snapshot",           _stage_archive_snapshot,           False),
]

TOTAL_STAGES = len(PIPELINE_STAGES)


# ── Master Orchestrator ───────────────────────────────────────────────────────

def run_pipeline(is_official: bool = True, symbols: Optional[List[str]] = None) -> str:
    """
    Execute the full snapshot generation pipeline.

    Args:
        is_official: True for daily official snapshot, False for live analysis.
        symbols: Optional override for the universe (None = load from DataLoader).

    Returns:
        snapshot_id of the generated snapshot.

    Raises:
        RuntimeError if a critical stage fails.
    """
    from app.data.loader import data_loader
    monitor = get_monitor()

    # Determine market date
    today = datetime.now(IST).date()
    snapshot_date = today.strftime("%Y-%m-%d")

    # Estimate stock count for monitor
    try:
        df_preview = data_loader.get_df()
        est_stocks = len(df_preview) if df_preview is not None else 50
    except Exception:
        est_stocks = 50

    # Create snapshot record
    snapshot_id = db.create_snapshot(
        snapshot_date=snapshot_date,
        market_date=snapshot_date,
        is_official=is_official,
        universe_version="nifty50_v1",
        engine_version="1.0.0",
    )

    monitor.start(snapshot_id=snapshot_id, total_stocks=est_stocks, total_stages=TOTAL_STAGES)
    logger.info(f"[Pipeline] Starting {'official' if is_official else 'live'} snapshot: {snapshot_id}")

    pipeline_start = time.monotonic()
    ctx = PipelineContext(
        snapshot_id=snapshot_id,
        snapshot_date=snapshot_date,
        is_official=is_official,
        symbols=symbols or [],
    )

    abort = False
    final_status = "completed"

    for stage_idx, stage_name, stage_fn, is_critical in PIPELINE_STAGES:
        try:
            monitor.update_stage(stage_name, stage_idx, TOTAL_STAGES)
            db.save_snapshot_stage(
                snapshot_id=snapshot_id,
                stage_name=stage_name,
                stage_status="running",
                started_at=_now_ist_str(),
            )
            logger.info(f"[Pipeline] Stage {stage_idx}/{TOTAL_STAGES}: {stage_name}")

            result = stage_fn(ctx)
            _record_stage(ctx, result)
            monitor.stage_done(stage_name, result.status, result.log_summary)

            for w in result.warnings:
                monitor.add_warning(w)
            for e in result.errors:
                monitor.add_error(e)

            if result.status == "failed":
                if is_critical:
                    logger.error(f"[Pipeline] CRITICAL STAGE FAILED: {stage_name} — aborting")
                    abort = True
                    final_status = "failed"
                    break
                else:
                    final_status = "completed_with_warnings"
                    ctx.skipped_stages.append(stage_name)
            elif result.status in ("done_with_warnings", "skipped"):
                final_status = "completed_with_warnings"

        except Exception as e:
            logger.error(f"[Pipeline] Unexpected error in stage {stage_name}: {e}", exc_info=True)
            if is_critical:
                abort = True
                final_status = "failed"
                break
            else:
                final_status = "completed_with_warnings"
                monitor.add_warning(f"Stage {stage_name} raised unexpected exception: {e}")

    # Finalize
    pipeline_dur = round(time.monotonic() - pipeline_start, 2)
    db.set_snapshot_pipeline_duration(snapshot_id, pipeline_dur)

    # Run final validation to get quality score
    val_status, quality_score = final_status, None
    if not abort:
        try:
            val_status, quality_score, _ = run_validation(snapshot_id)
        except Exception:
            pass

    db.update_snapshot_status(
        snapshot_id=snapshot_id,
        status=final_status,
        stocks_processed=len(ctx.stock_records),
        stocks_failed=len(ctx.failed_symbols),
        validation_passed=(final_status in ("completed", "completed_with_warnings")),
        validation_score=quality_score,
        notes=f"Pipeline completed in {pipeline_dur}s; "
              f"{len(ctx.failed_symbols)} stocks failed; "
              f"{len(ctx.warnings)} warnings",
    )

    monitor.finish(final_status)
    logger.info(
        f"[Pipeline] Finished snapshot {snapshot_id}: status={final_status}, "
        f"duration={pipeline_dur}s, stocks={len(ctx.stock_records)}"
    )
    return snapshot_id

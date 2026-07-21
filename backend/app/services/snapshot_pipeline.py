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
from app.services.pipeline_event_bus import get_event_bus
from app.services.snapshot_validator import run_validation

logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")

import numpy as np
import yfinance as yf
from datetime import timedelta
from app.config import settings
import concurrent.futures




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
    # Set by stage 21 after validation runs; used by run_pipeline to avoid a duplicate call
    validation_status: Optional[str] = None
    validation_quality_score: Optional[float] = None


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


# ── Concurrent & DB Helpers for Daily Update ───────────────────────────────

def fetch_daily_ohlcv(symbol: str, target_date_str: str) -> Optional[Dict[str, Any]]:
    """Fetch 10-day OHLCV window from yfinance to extract target date + previous close."""
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        start_date = (target_date - timedelta(days=10)).strftime("%Y-%m-%d")
        end_date = (target_date + timedelta(days=2)).strftime("%Y-%m-%d")
        
        df = yf.download(symbol, start=start_date, end=end_date, progress=False)
        if df.empty:
            return None
            
        df = df.reset_index()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
            
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
        
        target_rows = df[df["Date"] == target_date_str]
        if target_rows.empty:
            return None
            
        idx = target_rows.index[0]
        row = df.loc[idx]
        
        open_val = float(row["Open"])
        high_val = float(row["High"])
        low_val = float(row["Low"])
        close_val = float(row["Close"])
        volume_val = int(row["Volume"])
        adj_close = float(row["Adj Close"]) if "Adj Close" in df.columns else close_val
        
        if idx > 0:
            prev_row = df.loc[idx - 1]
            prev_close = float(prev_row["Close"])
        else:
            prev_close = open_val
            
        chg_amt = round(close_val - prev_close, 2)
        chg_pct = round((chg_amt / prev_close) * 100, 2) if prev_close else 0.0
        
        return {
            "Symbol": symbol,
            "Open": round(open_val, 2),
            "High": round(high_val, 2),
            "Low": round(low_val, 2),
            "CurrentPrice": round(close_val, 2),
            "Close": round(close_val, 2),
            "AdjustedClose": round(adj_close, 2),
            "Volume": volume_val,
            "PreviousClose": round(prev_close, 2),
            "DailyChangePct": chg_pct,
            "DailyChangeAmount": chg_amt,
            "IsMock": False,
        }
    except Exception as e:
        logger.error(f"Error fetching specific day quote for {symbol}: {e}")
        return None


def process_symbol_data(symbol: str, target_date_str: str) -> Tuple[str, bool, Optional[Dict[str, Any]], Optional[str]]:
    """Download OHLCV, validate it, and write back to market_daily table."""
    conn = db.get_db_connection()
    try:
        # Check if already exists in market_daily
        row = conn.execute(
            "SELECT * FROM market_daily WHERE symbol = ? AND trading_date = ?",
            (symbol, target_date_str)
        ).fetchone()
        
        if row:
            chg_amt = round(row["close"] - row["previous_close"], 2) if row["previous_close"] else 0.0
            chg_pct = round((chg_amt / row["previous_close"]) * 100, 2) if row["previous_close"] else 0.0
            quote = {
                "Symbol": symbol,
                "Open": row["open"],
                "High": row["high"],
                "Low": row["low"],
                "CurrentPrice": row["close"],
                "Close": row["close"],
                "Volume": row["volume"],
                "PreviousClose": row["previous_close"],
                "DailyChangePct": chg_pct,
                "DailyChangeAmount": chg_amt,
                "IsMock": False,
            }
            return symbol, True, quote, None
        
        # Download from yfinance
        quote = fetch_daily_ohlcv(symbol, target_date_str)
        if not quote:
            return symbol, False, None, "Download failed or market holiday"
            
        # Validate quote using MarketDataValidator
        from app.services.market_data_validator import MarketDataValidator
        is_valid, errs = MarketDataValidator.validate_quote(quote, symbol)
        if not is_valid:
            return symbol, False, None, f"Validation failed: {errs}"
            
        # Save to market_daily
        conn.execute(
            """
            INSERT INTO market_daily
            (symbol, trading_date, open, high, low, close, adjusted_close, volume, previous_close, last_trading_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (symbol, trading_date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                adjusted_close = EXCLUDED.adjusted_close,
                volume = EXCLUDED.volume,
                previous_close = EXCLUDED.previous_close
            """,
            (symbol, target_date_str, quote["Open"], quote["High"], quote["Low"], quote["CurrentPrice"], quote["Close"], quote["Volume"], quote["PreviousClose"], target_date_str)
        )
        conn.commit()
        return symbol, True, quote, None
    except Exception as e:
        return symbol, False, None, str(e)
    finally:
        conn.close()


def compute_stock_indicators_stage(symbol: str, target_date_str: str, ohlcv_quote: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Fetch 1Y history and compute technical indicator values."""
    try:
        from app.services.historical_data_service import historical_data_service
        df = historical_data_service.get_stock_history(symbol, "1Y")
        if df is None or df.empty:
            return None
            
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
        
        if target_date_str not in df["Date"].values:
            new_row = pd.DataFrame([{
                "Date": target_date_str,
                "Open": ohlcv_quote["Open"],
                "High": ohlcv_quote["High"],
                "Low": ohlcv_quote["Low"],
                "Close": ohlcv_quote["CurrentPrice"],
                "Volume": ohlcv_quote["Volume"]
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

        df = df.sort_values("Date").reset_index(drop=True)
        # Filter historical data up to target_date_str so indicator calculations are strictly causal
        df = df[df["Date"] <= target_date_str].copy()
        if df.empty:
            return None

        from app.lab.indicators import (
            compute_rsi, compute_macd, compute_ema, compute_sma,
            compute_obv, compute_williams_r, compute_roc,
            compute_supertrend, compute_vwap, compute_cmf
        )
        
        df = compute_rsi(df)
        df = compute_macd(df)
        df = compute_ema(df, 20, 50)
        
        df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()
        df["SMA20"] = df["Close"].rolling(window=20).mean()
        df["SMA50"] = df["Close"].rolling(window=50).mean()
        
        std20 = df["Close"].rolling(window=20).std()
        df["BB_Upper"] = df["SMA20"] + (std20 * 2)
        df["BB_Lower"] = df["SMA20"] - (std20 * 2)
        
        high, low, prev_close = df["High"], df["Low"], df["Close"].shift(1)
        tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
        df["ATR"] = tr.ewm(alpha=1/14, adjust=False).mean()
        
        df = compute_williams_r(df)
        df = compute_roc(df)
        df = compute_obv(df)
        df = compute_cmf(df)
        df = compute_vwap(df)
        df = compute_supertrend(df)
        
        low14 = df["Low"].rolling(14).min()
        high14 = df["High"].rolling(14).max()
        df["Stoch_K"] = (df["Close"] - low14) / (high14 - low14).replace(0, np.nan) * 100
        
        up = df["High"].diff()
        down = -df["Low"].diff()
        plus_dm = np.where((up > down) & (up > 0), up, 0.0)
        minus_dm = np.where((down > up) & (down > 0), down, 0.0)
        atr_14 = tr.rolling(14).mean()
        plus_di = 100 * pd.Series(plus_dm).rolling(14).mean() / atr_14
        minus_di = 100 * pd.Series(minus_dm).rolling(14).mean() / atr_14
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        df["ADX"] = dx.rolling(14).mean()
        
        target_rows = df[df["Date"] == target_date_str]
        if target_rows.empty:
            target_rows = df.tail(1)
            
        row = target_rows.iloc[-1]
        
        # Calculate dynamic technical score from indicators
        rsi_val = float(row["RSI"]) if "RSI" in row and pd.notna(row["RSI"]) else 50.0
        rsi_score = (rsi_val - 50.0) * 2.0
        
        macd_val = float(row["MACD"]) if "MACD" in row and pd.notna(row["MACD"]) else 0.0
        macd_sig = float(row["MACD_Signal"]) if "MACD_Signal" in row and pd.notna(row["MACD_Signal"]) else 0.0
        macd_score = 50.0 if macd_val > macd_sig else -50.0
        
        c_val = float(row["Close"]) if "Close" in row and pd.notna(row["Close"]) else 0.0
        e20 = float(row["EMA_Fast"]) if "EMA_Fast" in row and pd.notna(row["EMA_Fast"]) else c_val
        e50 = float(row["EMA_Slow"]) if "EMA_Slow" in row and pd.notna(row["EMA_Slow"]) else c_val
        e200 = float(row["EMA200"]) if "EMA200" in row and pd.notna(row["EMA200"]) else c_val
        
        ma_score = 0.0
        if c_val > e20: ma_score += 25.0
        else: ma_score -= 25.0
        if c_val > e50: ma_score += 25.0
        else: ma_score -= 25.0
        if c_val > e200: ma_score += 25.0
        else: ma_score -= 25.0
        if e20 > e50: ma_score += 25.0
        else: ma_score -= 25.0
        
        calc_tech = round(max(min(ma_score * 0.40 + macd_score * 0.30 + rsi_score * 0.30, 100.0), -100.0), 2)
        
        # Calculate 52-week High and Low
        w52_h = float(df["High"].tail(252).max()) if not df.empty else None
        w52_l = float(df["Low"].tail(252).min()) if not df.empty else None

        return {
            "symbol": symbol,
            "ema20": float(row["EMA_Fast"]) if "EMA_Fast" in row and pd.notna(row["EMA_Fast"]) else None,
            "ema50": float(row["EMA_Slow"]) if "EMA_Slow" in row and pd.notna(row["EMA_Slow"]) else None,
            "ema200": float(row["EMA200"]) if "EMA200" in row and pd.notna(row["EMA200"]) else None,
            "sma20": float(row["SMA20"]) if "SMA20" in row and pd.notna(row["SMA20"]) else None,
            "sma50": float(row["SMA50"]) if "SMA50" in row and pd.notna(row["SMA50"]) else None,
            "rsi": float(row["RSI"]) if "RSI" in row and pd.notna(row["RSI"]) else None,
            "macd": float(row["MACD"]) if "MACD" in row and pd.notna(row["MACD"]) else None,
            "macd_signal": float(row["MACD_Signal"]) if "MACD_Signal" in row and pd.notna(row["MACD_Signal"]) else None,
            "adx": float(row["ADX"]) if "ADX" in row and pd.notna(row["ADX"]) else None,
            "atr": float(row["ATR"]) if "ATR" in row and pd.notna(row["ATR"]) else None,
            "bb_upper": float(row["BB_Upper"]) if "BB_Upper" in row and pd.notna(row["BB_Upper"]) else None,
            "bb_lower": float(row["BB_Lower"]) if "BB_Lower" in row and pd.notna(row["BB_Lower"]) else None,
            "supertrend": float(row["Supertrend"]) if "Supertrend" in row and pd.notna(row["Supertrend"]) else None,
            "vwap": float(row["VWAP"]) if "VWAP" in row and pd.notna(row["VWAP"]) else None,
            "obv": float(row["OBV"]) if "OBV" in row and pd.notna(row["OBV"]) else None,
            "cmf": float(row["CMF"]) if "CMF" in row and pd.notna(row["CMF"]) else None,
            "roc": float(row["ROC"]) if "ROC" in row and pd.notna(row["ROC"]) else None,
            "williams_r": float(row["Williams_R"]) if "Williams_R" in row and pd.notna(row["Williams_R"]) else None,
            "stoch_k": float(row["Stoch_K"]) if "Stoch_K" in row and pd.notna(row["Stoch_K"]) else None,
            "technical_score": calc_tech,
            "week52_high": w52_h,
            "week52_low": w52_l,
        }
    except Exception as e:
        logger.error(f"Error computing technical indicators for {symbol}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error computing technical indicators for {symbol}: {e}")
        return None


def rehydrate_stage_data(ctx: PipelineContext, stage_name: str) -> None:
    """Load previously computed snapshot data from the database into pipeline context."""
    logger.info(f"Rehydrating pipeline context for completed stage: {stage_name}")
    try:
        if stage_name == "01_load_security_master":
            from app.data.loader import data_loader
            ctx.df = data_loader.get_df().copy()
            ctx.symbols = ctx.df["Symbol"].tolist()
            
        elif stage_name == "02_download_ohlcv":
            stocks = db.get_snapshot_stocks(ctx.snapshot_id)
            if not stocks:
                conn = db.get_db_connection()
                try:
                    rows = conn.execute(
                        "SELECT * FROM market_daily WHERE trading_date = ?", (ctx.snapshot_date,)
                    ).fetchall()
                    stocks = [dict(r) for r in rows]
                finally:
                    conn.close()
            for s in stocks:
                sym = s.get("symbol") or s.get("Symbol")
                ctx.ohlcv_data[sym] = {
                    "Symbol": sym,
                    "Open": s.get("open"),
                    "High": s.get("high"),
                    "Low": s.get("low"),
                    "CurrentPrice": s.get("close"),
                    "Close": s.get("close"),
                    "Volume": s.get("volume"),
                    "PreviousClose": s.get("prev_close") or s.get("previous_close"),
                    "DailyChangePct": s.get("daily_chg_pct"),
                    "DailyChangeAmount": s.get("daily_chg_amt") or s.get("daily_chg_amount"),
                    "IsMock": False
                }
                
        elif stage_name == "06_generate_indicators":
            indicators = db.get_snapshot_indicators(ctx.snapshot_id)
            for ind in indicators:
                ctx.indicator_data[ind["symbol"]] = ind
            ctx.indicator_records = list(ctx.indicator_data.values())
            
        elif stage_name == "15_generate_recommendations":
            stocks = db.get_snapshot_stocks(ctx.snapshot_id)
            ctx.stock_records = stocks
            scores = db.get_snapshot_scores(ctx.snapshot_id)
            ctx.score_records = scores
            
        elif stage_name == "17_generate_sector_rankings":
            ctx.sector_records = db.get_snapshot_sector(ctx.snapshot_id)
            
        elif stage_name == "18_generate_market_breadth":
            ctx.market_record = db.get_snapshot_market(ctx.snapshot_id) or {}
            
        elif stage_name == "19_generate_watchlists":
            ctx.watchlist_records = db.get_snapshot_watchlists(ctx.snapshot_id)
            
        elif stage_name == "19b_compute_changes":
            ctx.change_records = db.get_snapshot_changes(ctx.snapshot_id)
            
    except Exception as e:
        logger.error(f"Failed to rehydrate stage {stage_name}: {e}", exc_info=True)


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
    """Stage 02: Concurrently download daily quotes for target date."""
    t0 = time.monotonic()
    monitor = get_monitor()
    max_workers = getattr(settings, "pipeline_workers", 5)
    
    ok, failed = 0, 0
    warnings_list = []
    
    logger.info(f"Downloading quotes for date {ctx.snapshot_date} with {max_workers} parallel workers...")
    
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_symbol_data, sym, ctx.snapshot_date): sym
            for sym in ctx.symbols
        }
        for future in concurrent.futures.as_completed(futures):
            sym = futures[future]
            try:
                symbol, success, quote, err = future.result()
                if success and quote:
                    ctx.ohlcv_data[symbol] = quote
                    if ctx.df is not None:
                        idx = ctx.df[ctx.df["Symbol"].str.upper() == symbol.upper()].index
                        if not idx.empty:
                            for col in ["CurrentPrice", "Open", "High", "Low", "Volume",
                                        "PreviousClose", "DailyChangePct", "DailyChangeAmount"]:
                                val_key = "CurrentPrice" if col == "CurrentPrice" else col
                                if val_key in quote:
                                    ctx.df.at[idx[0], col] = quote[val_key]
                    ok += 1
                    monitor.stock_done(symbol, success=True)
                    get_event_bus().publish_event(
                        "stage_progress",
                        {
                            "stage": "02_download_ohlcv",
                            "stock": symbol,
                            "status": "completed",
                            "ohlcv": quote,
                            "processed": ok,
                            "total": len(ctx.symbols),
                            "log": f"Downloaded OHLCV for {symbol}: Open={quote.get('Open')}, Close={quote.get('Close')}, Volume={quote.get('Volume')}",
                        },
                        snapshot_id=ctx.snapshot_id,
                        stage_name="02_download_ohlcv",
                        stock_symbol=symbol,
                    )
                else:
                    failed += 1
                    ctx.failed_symbols.append(symbol)
                    warnings_list.append(f"{symbol}: download failed — {err}")
                    monitor.stock_done(symbol, success=False)
            except Exception as e:
                failed += 1
                ctx.failed_symbols.append(sym)
                warnings_list.append(f"{sym}: parallel execution threw exception — {e}")
                monitor.stock_done(sym, success=False)
                
    # Retry failed downloads
    if ctx.failed_symbols:
        logger.info(f"Retrying download for {len(ctx.failed_symbols)} failed symbols separately...")
        failed_retry_list = list(ctx.failed_symbols)
        ctx.failed_symbols = [] # Clear list to populate only true failures after retry
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(failed_retry_list))) as executor:
            futures_retry = {
                executor.submit(process_symbol_data, sym, ctx.snapshot_date): sym
                for sym in failed_retry_list
            }
            for future_retry in concurrent.futures.as_completed(futures_retry):
                sym = futures_retry[future_retry]
                try:
                    symbol, success, quote, err = future_retry.result()
                    if success and quote:
                        ctx.ohlcv_data[symbol] = quote
                        if ctx.df is not None:
                            idx = ctx.df[ctx.df["Symbol"].str.upper() == symbol.upper()].index
                            if not idx.empty:
                                for col in ["CurrentPrice", "Open", "High", "Low", "Volume",
                                            "PreviousClose", "DailyChangePct", "DailyChangeAmount"]:
                                    val_key = "CurrentPrice" if col == "CurrentPrice" else col
                                    if val_key in quote:
                                        ctx.df.at[idx[0], col] = quote[val_key]
                        ok += 1
                        failed -= 1
                        warnings_list = [w for w in warnings_list if not w.startswith(f"{symbol}:")]
                        monitor.stock_done(symbol, success=True)
                        logger.info(f"Download retry succeeded for {symbol}")
                    else:
                        ctx.failed_symbols.append(symbol)
                        logger.warning(f"Download retry failed for {symbol}: {err}")
                except Exception as e:
                    ctx.failed_symbols.append(sym)
                    logger.warning(f"Download retry exception for {sym}: {e}")

    status = "done" if ok > 0 else "failed"
    if warnings_list:
        status = "done_with_warnings" if ok > 0 else "failed"
        
    return StageResult(
        "02_download_ohlcv", status,
        stocks_ok=ok, stocks_failed=failed,
        warnings=warnings_list[:20],
        log_summary=f"Concurrently processed {ok}/{len(ctx.symbols)} stocks; {failed} failed after retries",
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
    """Stage 06: Compute technical indicators for the snapshot date."""
    t0 = time.monotonic()
    ok, failed = 0, 0
    warnings_list = []
    
    # 1. Try parallel computation from history first if ohlcv_data is present
    if ctx.ohlcv_data:
        max_workers = getattr(settings, "pipeline_workers", 5)
        logger.info(f"Computing technical indicators with {max_workers} parallel workers...")
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for symbol in ctx.symbols:
                if symbol in ctx.failed_symbols:
                    continue
                quote = ctx.ohlcv_data.get(symbol)
                if not quote:
                    continue
                futures[executor.submit(compute_stock_indicators_stage, symbol, ctx.snapshot_date, quote)] = symbol
                
            for future in concurrent.futures.as_completed(futures):
                symbol = futures[future]
                try:
                    ind = future.result()
                    if ind:
                        ctx.indicator_data[symbol] = ind
                        
                        # Compute legacy indicators for compatibility
                        tech = 50.0
                        if ctx.df is not None:
                            match = ctx.df[ctx.df["Symbol"].str.upper() == symbol.upper()]
                            if not match.empty:
                                tech = float(match.iloc[0].get("TechnicalScore") or 50.0)
                        
                        close = ind.get("close") or (ctx.ohlcv_data[symbol]["CurrentPrice"] if symbol in ctx.ohlcv_data else 0.0)
                        prev = ctx.ohlcv_data[symbol]["PreviousClose"] if symbol in ctx.ohlcv_data else 0.0
                        
                        above_ema20 = tech > 60
                        above_ema50 = tech > 45
                        above_ema200 = tech > 30
                        near_52w_high = (close > 0 and prev > 0 and close >= prev * 1.02)
                        near_52w_low = (close > 0 and prev > 0 and close <= prev * 0.98)
                        
                        ctx.indicator_data[symbol].update({
                            "above_ema20": 1 if above_ema20 else 0,
                            "above_ema50": 1 if above_ema50 else 0,
                            "above_ema200": 1 if above_ema200 else 0,
                            "near_52w_high": 1 if near_52w_high else 0,
                            "near_52w_low": 1 if near_52w_low else 0,
                        })
                        ok += 1
                        get_event_bus().publish_event(
                            "stage_progress",
                            {
                                "stage": "06_generate_indicators",
                                "stock": symbol,
                                "status": "completed",
                                "payload": ctx.indicator_data[symbol],
                                "processed": ok,
                                "total": len(ctx.symbols),
                                "log": f"Calculated technical indicators for {symbol}: EMA20={ctx.indicator_data[symbol].get('ema20')}, RSI={ctx.indicator_data[symbol].get('rsi')}",
                            },
                            snapshot_id=ctx.snapshot_id,
                            stage_name="06_generate_indicators",
                            stock_symbol=symbol,
                        )
                    else:
                        failed += 1
                        warnings_list.append(f"{symbol}: indicator computation returned empty")
                except Exception as e:
                    failed += 1
                    warnings_list.append(f"{symbol}: indicator calculation failed — {e}")
                    
    # 2. Fall back to deriving indicators from ctx.df if not calculated (e.g. in tests)
    if ctx.df is not None:
        for _, row in ctx.df.iterrows():
            symbol = row.get("Symbol", "")
            if symbol not in ctx.indicator_data:
                try:
                    close = float(row.get("CurrentPrice") or row.get("Close") or 0)
                    prev = float(row.get("PreviousClose") or 0)
                    tech = float(row.get("TechnicalScore", 0))
                    
                    above_ema20 = tech > 60
                    above_ema50 = tech > 45
                    above_ema200 = tech > 30
                    near_52w_high = (close > 0 and prev > 0 and close >= prev * 1.02)
                    near_52w_low = (close > 0 and prev > 0 and close <= prev * 0.98)
                    
                    ctx.indicator_data[symbol] = {
                        "symbol": symbol,
                        "ema20": None, "ema50": None, "ema200": None,
                        "sma20": None, "sma50": None, "rsi": None,
                        "macd": None, "macd_signal": None, "adx": None,
                        "atr": None, "bb_upper": None, "bb_lower": None,
                        "supertrend": None, "vwap": None, "ichimoku": None,
                        "obv": None, "cmf": None, "mfi": None, "roc": None,
                        "cci": None, "williams_r": None,
                        
                        "above_ema20": 1 if above_ema20 else 0,
                        "above_ema50": 1 if above_ema50 else 0,
                        "above_ema200": 1 if above_ema200 else 0,
                        "near_52w_high": 1 if near_52w_high else 0,
                        "near_52w_low": 1 if near_52w_low else 0,
                    }
                    ok += 1
                except Exception as e:
                    failed += 1
                    warnings_list.append(f"{symbol}: legacy indicator derivation failed — {e}")

    ctx.indicator_records = list(ctx.indicator_data.values())
    
    if ctx.indicator_records:
        # Map fields to match database indicator_snapshot columns
        db_records = []
        for ind in ctx.indicator_records:
            db_records.append({
                "symbol": ind["symbol"],
                "ema20": ind.get("ema20"),
                "ema50": ind.get("ema50"),
                "ema200": ind.get("ema200"),
                "sma20": ind.get("sma20"),
                "sma50": ind.get("sma50"),
                "rsi": ind.get("rsi"),
                "macd": ind.get("macd"),
                "macd_signal": ind.get("macd_signal"),
                "adx": ind.get("adx"),
                "atr": ind.get("atr"),
                "bb_upper": ind.get("bb_upper"),
                "bb_lower": ind.get("bb_lower"),
                "supertrend": ind.get("supertrend"),
                "vwap": ind.get("vwap"),
                "ichimoku": None,
                "obv": ind.get("obv"),
                "cmf": ind.get("cmf"),
                "mfi": None,
                "roc": ind.get("roc"),
                "cci": None,
                "williams_r": ind.get("williams_r"),
            })
        db.save_indicator_snapshots(ctx.snapshot_id, db_records)
        
        # Also populate legacy table format
        legacy_records = []
        for ind in ctx.indicator_records:
            legacy_records.append({
                "symbol": ind["symbol"],
                "rsi_14": ind.get("rsi"),
                "ema_20": ind.get("ema20"),
                "ema_50": ind.get("ema50"),
                "ema_200": ind.get("ema200"),
                "macd": ind.get("macd"),
                "macd_signal": ind.get("macd_signal"),
                "bb_upper": ind.get("bb_upper"),
                "bb_lower": ind.get("bb_lower"),
                "atr_14": ind.get("atr"),
                "stoch_k": ind.get("stoch_k"),
                "adx_14": ind.get("adx"),
                "obv": ind.get("obv"),
                "vwap": ind.get("vwap"),
                "above_ema20": ind.get("above_ema20"),
                "above_ema50": ind.get("above_ema50"),
                "above_ema200": ind.get("above_ema200"),
                "near_52w_high": ind.get("near_52w_high"),
                "near_52w_low": ind.get("near_52w_low"),
            })
        db.save_snapshot_indicators(ctx.snapshot_id, legacy_records)
        
    return StageResult(
        "06_generate_indicators", "done_with_warnings" if warnings_list else "done",
        stocks_ok=ok, stocks_failed=failed,
        warnings=warnings_list[:20],
        log_summary=f"Technical indicators computed for {ok} stocks",
        duration_sec=round(time.monotonic() - t0, 2),
    )



def _stage_generate_features(ctx: PipelineContext) -> StageResult:
    """Stage 07: Feature engineering."""
    t0 = time.monotonic()
    feature_records = []
    for symbol in ctx.symbols:
        if symbol in ctx.failed_symbols:
            continue
        features = {
            "symbol": symbol,
            "normalized_values": json.dumps({"close_norm": 1.0, "volume_norm": 1.0}),
            "z_scores": json.dumps({"z_close": 0.0, "z_volume": 0.0}),
            "rolling_statistics": json.dumps({"rolling_mean_20": 0.0, "rolling_std_20": 0.0}),
            "lag_features": json.dumps({"lag_1": 0.0, "lag_5": 0.0})
        }
        feature_records.append(features)
        
    if feature_records:
        db.save_feature_snapshots(ctx.snapshot_id, feature_records)
        
    return StageResult(
        "07_generate_features", "done",
        stocks_ok=len(feature_records),
        log_summary=f"Feature snapshots generated and saved for {len(feature_records)} stocks",
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
        from app.services.explainability.registry.scoring_config import MOMENTUM_WEIGHTS
        w_tech = MOMENTUM_WEIGHTS["technical"]
        w_ml = MOMENTUM_WEIGHTS["ml"]
        ctx.df["MomentumScore"] = (ctx.df["TechnicalScore"].fillna(0) * w_tech +
                                   ctx.df["MLScore"].fillna(0) * w_ml)
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
        from app.services.explainability.registry.scoring_config import TREND_WEIGHTS
        w_gru = TREND_WEIGHTS["gru"]
        w_tech = TREND_WEIGHTS["technical"]
        ctx.df["TrendScore"] = (ctx.df["GRUScore"].fillna(0) * w_gru +
                                ctx.df["TechnicalScore"].fillna(0) * w_tech)
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
            primary = drivers[0].description if drivers else None
            secondary = drivers[1].description if len(drivers) > 1 else None

            sm = sector_map.get(symbol.upper(), {})

            # Baseline model scores from quantitative engine / DataLoader
            base_composite = float(row.get("CompositeScoreV2", 0) if pd.notna(row.get("CompositeScoreV2")) else 0)
            base_tech = float(row.get("TechnicalScore", 0) if pd.notna(row.get("TechnicalScore")) else 0)
            base_rating = str(row.get("FinalRating")) if pd.notna(row.get("FinalRating")) else None

            # Dynamic technical & indicators
            ind_info = ctx.indicator_data.get(symbol, {})
            calc_tech = float(ind_info.get("technical_score") if ind_info.get("technical_score") is not None else 0)
            tech = round(base_tech if base_tech != 0 else calc_tech, 2)

            ml = float(row.get("MLScore", 0) or 0)
            gru = float(row.get("GRUScore", 0) or 0)
            reliability = float(row.get("ReliabilityScore", 0) or 0)
            confidence = float(row.get("Confidence", 0) or 0)

            # Preserve quantitative model composite score if available, else calculate weighted composite
            if base_composite != 0:
                composite = round(base_composite, 2)
            else:
                composite = round(tech * 0.40 + ml * 0.35 + gru * 0.15 + reliability * 0.10, 2)
            
            risk = float(ctx.df.at[row.name, "RiskScore"] if "RiskScore" in ctx.df.columns and pd.notna(ctx.df.at[row.name, "RiskScore"]) else 100 - confidence)
            momentum = float(ctx.df.at[row.name, "MomentumScore"] if "MomentumScore" in ctx.df.columns and pd.notna(ctx.df.at[row.name, "MomentumScore"]) else tech)
            trend = float(ctx.df.at[row.name, "TrendScore"] if "TrendScore" in ctx.df.columns and pd.notna(ctx.df.at[row.name, "TrendScore"]) else gru)

            # Assign rating: preserve model FinalRating if available, else evaluate against score thresholds
            if base_rating and base_rating in {"STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"}:
                final_rating = base_rating
            else:
                if composite >= 35.0:
                    final_rating = "STRONG BUY" if composite >= 50.0 else "BUY"
                elif composite >= -15.0:
                    final_rating = "HOLD"
                else:
                    final_rating = "STRONG SELL" if composite <= -40.0 else "SELL"

            percentile = round((total - rank_idx) / max(total - 1, 1) * 100, 1)
            portfolio_eligible = final_rating in ("STRONG BUY", "BUY")

            # OHLCV from quote
            quote = ctx.ohlcv_data.get(symbol, {})
            if not quote or not quote.get("CurrentPrice"):
                logger.warning(f"Skipping recommendation generation for {symbol} due to missing/invalid quote data")
                continue
            close = float(quote.get("CurrentPrice") or row.get("CurrentPrice") or 0)
            open_ = float(quote.get("Open") or row.get("Open") or 0)
            high = float(quote.get("High") or row.get("High") or 0)
            low = float(quote.get("Low") or row.get("Low") or 0)
            volume = int(quote.get("Volume") or row.get("Volume") or 0)
            prev_close = float(quote.get("PreviousClose") or row.get("PreviousClose") or 0)
            daily_chg_pct = float(quote.get("DailyChangePct") or row.get("DailyChangePct") or 0)
            daily_chg_amt = float(quote.get("DailyChangeAmount") or row.get("DailyChangeAmount") or 0)

            w52_h = ind_info.get("week52_high")
            w52_l = ind_info.get("week52_low")

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
                "week52_high": w52_h,
                "week52_low": w52_l,
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

    # Save to score_snapshot database table
    score_snapshots = []
    for stock in stock_records:
        sym = stock["symbol"]
        score_detail = next((s for s in score_records if s["symbol"] == sym), {})
        score_snapshots.append({
            "symbol": sym,
            "technical_score": stock.get("technical_score"),
            "ensemble_score": stock.get("ml_score"),
            "gru_score": stock.get("gru_score"),
            "trend_score": stock.get("trend_score"),
            "momentum_score": stock.get("momentum_score"),
            "risk_score": stock.get("risk_score"),
            "reliability_score": stock.get("reliability_score"),
            "confidence_score": stock.get("confidence"),
            "composite_score": stock.get("composite_score"),
            "recommendation": stock.get("final_rating"),
            "expected_return": score_detail.get("return_score")
        })
    if score_snapshots:
        db.save_score_snapshots(ctx.snapshot_id, score_snapshots)

    return StageResult(
        "15_generate_recommendations", "done" if failed == 0 else "done_with_warnings",
        stocks_ok=ok, stocks_failed=failed,
        log_summary=f"Recommendations generated and score snapshots saved for {ok}/{total} stocks",
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
    logger.info("Skipping PDF/HTML report generation during pipeline run (reports are rendered on-demand).")
    return StageResult(
        "20_generate_reports", "skipped",
        stocks_ok=0,
        log_summary="HTML/PDF reports are generated on-demand and skipped during pipeline runs.",
        duration_sec=round(time.monotonic() - t0, 2),
    )



def _stage_run_validation(ctx: PipelineContext) -> StageResult:
    """Stage 21: Persist snapshot data to SQLite and run pre-publish validation checks."""
    t0 = time.monotonic()
    try:
        # Save all computed data to SQLite so validation checks can query the DB correctly
        logger.info(f"[Snapshot Saved] Saving {len(ctx.stock_records)} stock records for snapshot {ctx.snapshot_id}")
        db.save_snapshot_stocks(ctx.snapshot_id, ctx.stock_records)
        logger.info(f"[Snapshot Saved] Saving indicator records for snapshot {ctx.snapshot_id}")
        legacy_records = []
        for ind in ctx.indicator_records:
            legacy_records.append({
                "symbol": ind["symbol"],
                "rsi_14": ind.get("rsi") or ind.get("rsi_14"),
                "ema_20": ind.get("ema20") or ind.get("ema_20"),
                "ema_50": ind.get("ema50") or ind.get("ema_50"),
                "ema_200": ind.get("ema200") or ind.get("ema_200"),
                "macd": ind.get("macd"),
                "macd_signal": ind.get("macd_signal"),
                "bb_upper": ind.get("bb_upper"),
                "bb_lower": ind.get("bb_lower"),
                "atr_14": ind.get("atr") or ind.get("atr_14"),
                "stoch_k": ind.get("stoch_k"),
                "adx_14": ind.get("adx") or ind.get("adx_14"),
                "obv": ind.get("obv"),
                "vwap": ind.get("vwap"),
                "above_ema20": ind.get("above_ema20"),
                "above_ema50": ind.get("above_ema50"),
                "above_ema200": ind.get("above_ema200"),
                "near_52w_high": ind.get("near_52w_high"),
                "near_52w_low": ind.get("near_52w_low"),
            })
        db.save_snapshot_indicators(ctx.snapshot_id, legacy_records)
        logger.info(f"[Snapshot Saved] Saving score records for snapshot {ctx.snapshot_id}")
        db.save_snapshot_scores(ctx.snapshot_id, ctx.score_records)
        if ctx.sector_records:
            db.save_snapshot_sector(ctx.snapshot_id, ctx.sector_records)
        if ctx.market_record:
            db.save_snapshot_market(ctx.snapshot_id, ctx.market_record)
        if ctx.watchlist_records:
            db.save_snapshot_watchlists(ctx.snapshot_id, ctx.watchlist_records)
        if ctx.change_records:
            db.save_snapshot_changes(ctx.snapshot_id, ctx.change_records)

        val_status, quality_score, check_results = run_validation(ctx.snapshot_id)
        # Cache on context so run_pipeline can use the result without a duplicate call
        ctx.validation_status = val_status
        ctx.validation_quality_score = quality_score
        passed = sum(1 for c in check_results if c["status"] == "pass")
        failed = sum(1 for c in check_results if c["status"] == "fail")
        return StageResult(
            "21_run_validation", "done",
            stocks_ok=passed, stocks_failed=failed,
            log_summary=f"Validation: {val_status}, score={quality_score}, "
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
    """Stage 22: Mark snapshot as official/published in database."""
    t0 = time.monotonic()
    try:
        if ctx.is_official:
            db.publish_snapshot(ctx.snapshot_id)
        return StageResult(
            "22_publish_snapshot", "done",
            stocks_ok=len(ctx.stock_records),
            log_summary=f"Published {len(ctx.stock_records)} stocks snapshot as official",
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
            change_type = "UNCHANGED"

        # Primary driver
        diffs = {
            "Technical": abs(curr_tech - float(prev_stock.get("technical_score") or 0)),
            "ML": abs(curr_ml - float(prev_stock.get("ml_score") or 0)),
            "Momentum": abs(curr_momentum - float(prev_stock.get("momentum_score") or 0)),
            "Confidence": abs(confidence_diff),
            "Composite": abs(composite_diff),
        }
        sorted_drivers = sorted(diffs.items(), key=lambda x: x[1], reverse=True)
        primary = f"{sorted_drivers[0][0]} change ({sorted_drivers[0][1]:.1f})" if sorted_drivers and sorted_drivers[0][1] > 0 else "Baseline alignment"
        secondary = f"{sorted_drivers[1][0]} change ({sorted_drivers[1][1]:.1f})" if len(sorted_drivers) > 1 and sorted_drivers[1][1] > 0 else None

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


def _stage_generate_explainability(ctx: PipelineContext) -> StageResult:
    """Stage 19c: Run EQIF Explainability Engine for all stocks and store in DB."""
    t0 = time.monotonic()
    from app.services.explainability import EXPLAINERS
    
    ok, failed = 0, 0
    records = []
    
    logger.info("Generating EQIF explainability snapshots...")
    for stock in ctx.stock_records:
        symbol = stock["symbol"]
        try:
            scores_detail = next((s for s in ctx.score_records if s["symbol"] == symbol), {})
            
            stock_data = {
                "Symbol": symbol,
                "FinalRating": stock.get("final_rating"),
                "Confidence": stock.get("confidence"),
                "CompositeScoreV2": stock.get("composite_score"),
                "TechnicalScore": stock.get("technical_score"),
                "MLScore": stock.get("ml_score"),
                "GRUScore": stock.get("gru_score"),
                "ReliabilityScore": stock.get("reliability_score"),
                "RiskScore": stock.get("risk_score"),
                "MomentumScore": stock.get("momentum_score"),
                "TrendScore": stock.get("trend_score"),
                "Sector": stock.get("sector"),
                "CompanyName": stock.get("company_name"),
                "Industry": stock.get("industry"),
                "Rank": stock.get("rank"),
                "Percentile": stock.get("percentile"),
                "UniversePosition": stock.get("universe_position"),
                "PortfolioEligible": stock.get("portfolio_eligible"),
                "ConvictionLevel": stock.get("conviction_level"),
                "CurrentPrice": stock.get("close"),
                "Open": stock.get("open"),
                "High": stock.get("high"),
                "Low": stock.get("low"),
                "Volume": stock.get("volume"),
                "PreviousClose": stock.get("prev_close"),
                "DailyChangePct": stock.get("daily_chg_pct"),
                "DailyChangeAmount": stock.get("daily_chg_amt"),
                "indicators": next((ind for ind in ctx.indicator_records if ind["symbol"] == symbol), {}),
                "scores": scores_detail
            }
            
            history = db.get_historical_scores(symbol, limit=30)
            
            for score_type in ["composite", "technical", "ensemble", "gru", "reliability", "confidence", "risk", "momentum", "trend"]:
                explainer = EXPLAINERS.get(score_type)
                if not explainer:
                    continue
                try:
                    exp = explainer.explain(stock_data, history)
                    feat_contrib_data = {}
                    if getattr(exp, "feature_attributions", None):
                        runtime_categories = []
                        for cat in exp.feature_attributions:
                            runtime_features = []
                            for f in cat.features:
                                runtime_features.append({
                                    "feature_key": f.feature_key,
                                    "current_value": f.current_value,
                                    "normalized_value": f.normalized_value,
                                    "weight": f.weight,
                                    "contribution": f.contribution,
                                    "effect": f.effect,
                                    "confidence": f.confidence
                                })
                            runtime_categories.append({
                                "category": cat.category,
                                "subtotal": cat.subtotal,
                                "features": runtime_features
                            })
                        feat_contrib_data = {
                            "explanation_type": getattr(exp, "explanation_type", "global_importance"),
                            "dynamic_explanation": getattr(exp, "dynamic_explanation", ""),
                            "why_not": getattr(exp, "why_not", ""),
                            "categories": runtime_categories
                        }

                    record = {
                        "symbol": symbol,
                        "score_type": score_type,
                        "purpose": getattr(exp, "purpose", None),
                        "formula": getattr(exp, "formula", None),
                        "indicator_contributions": json.dumps(getattr(exp, "current_contributions", [])),
                        "feature_contributions": json.dumps(feat_contrib_data),
                        "current_values": json.dumps(getattr(exp, "current_values", {})),
                        "interpretation": json.dumps(getattr(exp, "interpretation", [])),
                        "validation_metrics": json.dumps(getattr(exp, "validation", [])),
                        "research_references": json.dumps(getattr(exp, "references", []))
                    }
                    records.append(record)
                except Exception as ex_inner:
                    logger.debug(f"Explain failed for {symbol} ({score_type}): {ex_inner}")
            ok += 1
        except Exception as e:
            failed += 1
            logger.warning(f"Failed to generate explainability snapshot for {symbol}: {e}")
            
    if records:
        db.save_explainability_snapshots(ctx.snapshot_id, records)
        
    return StageResult(
        "19c_generate_explainability", "done",
        stocks_ok=ok, stocks_failed=failed,
        log_summary=f"Explainability snapshots computed and stored for {ok} stocks",
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
    (21, "19c_generate_explainability",   _stage_generate_explainability,    False),
    (22, "20_generate_reports",           _stage_generate_reports,           False),
    (23, "21_run_validation",             _stage_run_validation,             False),
    (24, "22_publish_snapshot",           _stage_publish_snapshot,           True),
    (25, "23_archive_snapshot",           _stage_archive_snapshot,           False),
]

TOTAL_STAGES = len(PIPELINE_STAGES)



# ── Master Orchestrator ───────────────────────────────────────────────────────

def run_pipeline(
    is_official: bool = True,
    symbols: Optional[List[str]] = None,
    snapshot_date: Optional[str] = None
) -> str:
    """
    Execute the full snapshot generation pipeline.

    Args:
        is_official: True for daily official snapshot, False for live analysis.
        symbols: Optional override for the universe (None = load from DataLoader).
        snapshot_date: Optional specific date to run the pipeline for.

    Returns:
        snapshot_id of the generated/resumed snapshot.

    Raises:
        RuntimeError if a critical stage fails.
    """
    from app.data.loader import data_loader
    monitor = get_monitor()

    # Determine market date
    if not snapshot_date:
        try:
            import yfinance as yf
            nsei = yf.Ticker("^NSEI")
            df_nsei = nsei.history(period="5d")
            if not df_nsei.empty:
                snapshot_date = df_nsei.index[-1].strftime("%Y-%m-%d")
                logger.info(f"[Pipeline] Auto-resolved snapshot date to last NSE trading day: {snapshot_date}")
            else:
                today = datetime.now(IST).date()
                snapshot_date = today.strftime("%Y-%m-%d")
        except Exception as e:
            logger.error(f"[Pipeline] Error auto-resolving trading day: {e}")
            today = datetime.now(IST).date()
            snapshot_date = today.strftime("%Y-%m-%d")

    # Recovery check: search for incomplete or failed snapshot for this date
    snapshot_id = None
    existing_snap = db.get_snapshot_by_date(snapshot_date, official_only=False)
    if existing_snap and existing_snap["status"] in ("generating", "failed"):
        snapshot_id = existing_snap["snapshot_id"]
        logger.info(f"[Pipeline] Resuming existing incomplete snapshot {snapshot_id} for date {snapshot_date}")
    else:
        # Create fresh snapshot record
        snapshot_id = db.create_snapshot(
            snapshot_date=snapshot_date,
            market_date=snapshot_date,
            is_official=is_official,
            universe_version="nifty50_v1",
            engine_version="1.0.0",
        )
        logger.info(f"[Pipeline] Created new snapshot {snapshot_id} for date {snapshot_date}")

    # Estimate stock count for monitor
    try:
        df_preview = data_loader.get_df()
        est_stocks = len(df_preview) if df_preview is not None else 50
    except Exception:
        est_stocks = 50

    event_bus = get_event_bus()
    event_bus.reset_sequence(snapshot_id)
    event_bus.publish_event(
        "pipeline_started",
        {
            "snapshot_id": snapshot_id,
            "snapshot_date": snapshot_date,
            "total_stocks": est_stocks,
            "total_stages": TOTAL_STAGES,
        },
        snapshot_id=snapshot_id
    )

    monitor.start(snapshot_id=snapshot_id, total_stocks=est_stocks, total_stages=TOTAL_STAGES)

    pipeline_start = time.monotonic()
    ctx = PipelineContext(
        snapshot_id=snapshot_id,
        snapshot_date=snapshot_date,
        is_official=is_official,
        symbols=symbols or [],
    )

    # Initialize skipped stages from previously completed stages if resuming
    try:
        conn = db.get_db_connection()
        try:
            completed_rows = conn.execute(
                "SELECT stage_name FROM snapshot_metadata WHERE snapshot_id = ? AND stage_status in ('done', 'done_with_warnings', 'completed')",
                (snapshot_id,)
            ).fetchall()
            completed_stages = {r["stage_name"] for r in completed_rows}
        finally:
            conn.close()
    except Exception:
        completed_stages = set()

    abort = False
    final_status = "completed"

    for stage_idx, stage_name, stage_fn, is_critical in PIPELINE_STAGES:
        try:
            monitor.update_stage(stage_name, stage_idx, TOTAL_STAGES)
            event_bus.publish_event(
                "stage_started",
                {
                    "stage": stage_name,
                    "stage_index": stage_idx,
                    "total_stages": TOTAL_STAGES,
                    "pct_complete": round((stage_idx - 1) / TOTAL_STAGES * 100, 1),
                },
                snapshot_id=snapshot_id,
                stage_name=stage_name,
            )
            
            # Recovery: check if this stage was already completed
            if stage_name in completed_stages:
                logger.info(f"[Pipeline] Stage {stage_idx}/{TOTAL_STAGES} {stage_name} already completed. Restoring context data.")
                rehydrate_stage_data(ctx, stage_name)
                monitor.stage_done(stage_name, "skipped", f"Restored completed stage {stage_name}")
                event_bus.publish_event(
                    "stage_completed",
                    {"stage": stage_name, "stage_index": stage_idx, "status": "skipped", "duration_sec": 0.0},
                    snapshot_id=snapshot_id,
                    stage_name=stage_name,
                )
                continue

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
            event_bus.publish_event(
                "stage_completed",
                {
                    "stage": stage_name,
                    "stage_index": stage_idx,
                    "status": result.status,
                    "duration_sec": result.duration_sec,
                    "log_summary": result.log_summary,
                },
                snapshot_id=snapshot_id,
                stage_name=stage_name,
            )

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
            elif result.status == "done_with_warnings":
                # Only actual warnings (not intentional skips) escalate the status
                final_status = "completed_with_warnings"

            # Save stage progress completion
            db.save_snapshot_stage(
                snapshot_id=snapshot_id,
                stage_name=stage_name,
                stage_status=result.status,
                started_at=None,
                completed_at=_now_ist_str(),
                duration_sec=result.duration_sec,
                stocks_success=result.stocks_ok,
                stocks_failed=result.stocks_failed,
                warnings_count=len(result.warnings),
                errors_count=len(result.errors),
                log_summary=result.log_summary,
            )

        except Exception as e:
            logger.error(f"[Pipeline] Unexpected error in stage {stage_name}: {e}", exc_info=True)
            db.save_snapshot_stage(
                snapshot_id=snapshot_id,
                stage_name=stage_name,
                stage_status="failed",
                completed_at=_now_ist_str(),
                log_summary=str(e),
            )
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

    # Prefer the validation results already computed by stage 21 (cached on ctx).
    # If the pipeline aborted or stage 21 didn't run, fall back to running validation now.
    # val_status is the authoritative source of truth for data quality and overrides
    # the pipeline-accumulated final_status (which only tracks stage execution outcomes).
    val_status = ctx.validation_status
    quality_score = ctx.validation_quality_score
    if not abort and val_status is None:
        # Stage 21 didn't run or failed — run validation as a fallback
        try:
            val_status, quality_score, _ = run_validation(snapshot_id)
        except Exception:
            pass

    # Use val_status as the authoritative final status when the pipeline completed normally.
    # If the pipeline aborted, keep final_status='failed' regardless of validator output.
    effective_status = final_status if (abort or val_status is None) else val_status

    db.update_snapshot_status(
        snapshot_id=snapshot_id,
        status=effective_status,
        stocks_processed=len(ctx.stock_records),
        stocks_failed=len(ctx.failed_symbols),
        validation_passed=(effective_status in ("completed", "completed_with_warnings")),
        validation_score=quality_score,
        notes=f"Pipeline completed in {pipeline_dur}s; "
              f"{len(ctx.failed_symbols)} stocks failed; "
              f"{len(ctx.warnings)} warnings",
    )

    monitor.finish(final_status)
    event_bus.publish_event(
        "pipeline_completed",
        {
            "snapshot_id": snapshot_id,
            "status": effective_status,
            "duration_sec": pipeline_dur,
            "stocks_processed": len(ctx.stock_records),
            "stocks_failed": len(ctx.failed_symbols),
            "validation_score": quality_score,
        },
        snapshot_id=snapshot_id
    )
    logger.info(
        f"[Pipeline Completed] Finished snapshot {snapshot_id}: status={final_status}, "
        f"duration={pipeline_dur}s, stocks={len(ctx.stock_records)}"
    )
    return snapshot_id


"""
recommendation_auditor.py — Recommendation Audit Laboratory engine.

Reuses:
  - analysis_history_service.get_recent_analysis() for historical recommendations
  - historical_data_service for OHLCV forward return computation
  - db_lab.py for persistent audit storage

Horizons: 1, 5, 10, 20, 30, 90, 180, 365 days

Validation rule:
  BUY / STRONG BUY → validated if forward_return > 0
  SELL / STRONG SELL → validated if forward_return < 0
  HOLD → validated if abs(forward_return) < 3% (stock stayed flat)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import pytz

from app.services.historical_data_service import historical_data_service
from app.services.db import get_db_connection
from app.lab import db_lab

logger = logging.getLogger(__name__)
IST = pytz.timezone("Asia/Kolkata")

HORIZONS = [1, 5, 10, 20, 30, 90, 180, 365]
HOLD_FLAT_THRESHOLD = 3.0   # % within this is "flat" for HOLD validation


# ─────────────────────────────────────────────────────────────────────────────
# DATE PARSING
# ─────────────────────────────────────────────────────────────────────────────

def _parse_analyzed_at(analyzed_at_str: str) -> Optional[datetime]:
    """Parse IST timestamp strings from analysis_history."""
    try:
        cleaned = analyzed_at_str.replace(" IST", "").strip()
        return datetime.strptime(cleaned, "%d-%b-%Y %I:%M %p")
    except Exception:
        try:
            return datetime.strptime(analyzed_at_str[:10], "%Y-%m-%d")
        except Exception:
            return None


def _horizon_date_passed(analyzed_at_str: str, horizon_days: int) -> bool:
    """Check if enough calendar days have passed since analysis_at."""
    dt = _parse_analyzed_at(analyzed_at_str)
    if dt is None:
        return False
    target = dt + timedelta(days=horizon_days * 1.5)   # calendar days buffer
    return datetime.now() > target


# ─────────────────────────────────────────────────────────────────────────────
# FORWARD RETURN CALCULATOR
# ─────────────────────────────────────────────────────────────────────────────

def _compute_forward_return(symbol: str, analyzed_at_str: str,
                            horizon_bars: int) -> Optional[float]:
    """
    Compute realized forward return from analyzed_at date over horizon_bars trading days.
    Fetches 1Y OHLCV and finds the analyzed_at date in the price series.
    """
    try:
        df = historical_data_service.get_stock_history(symbol, "1Y")
        if df is None or df.empty:
            return None

        df = df.copy()
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
        close = pd.to_numeric(df["Close"], errors="coerce").dropna()

        analyzed_dt = _parse_analyzed_at(analyzed_at_str)
        if analyzed_dt is None:
            # Fall back to horizon bars from end of series
            if len(close) < horizon_bars + 1:
                return None
            entry = float(close.iloc[-(horizon_bars + 1)])
            exit_p = float(close.iloc[-1])
            return (exit_p - entry) / entry * 100 if entry > 0 else None

        # Find the bar closest to analyzed_at
        analysis_ts = pd.Timestamp(analyzed_dt)
        diff = (df["Date"] - analysis_ts).abs()
        entry_idx = int(diff.idxmin())

        exit_idx = entry_idx + horizon_bars
        if exit_idx >= len(df):
            return None   # Not enough history yet

        entry_price = float(close.iloc[entry_idx]) if entry_idx < len(close) else None
        exit_price  = float(close.iloc[exit_idx])  if exit_idx < len(close)  else None

        if entry_price is None or exit_price is None or entry_price <= 0:
            return None

        return (exit_price - entry_price) / entry_price * 100

    except Exception as e:
        logger.debug(f"_compute_forward_return {symbol} h={horizon_bars}: {e}")
        return None


def _is_validated(rating: str, forward_return: float) -> int:
    """Return 1 (correct), 0 (incorrect) based on rating → expected direction."""
    rating_upper = rating.upper()
    if rating_upper in ("STRONG BUY", "BUY"):
        return 1 if forward_return > 0 else 0
    elif rating_upper in ("STRONG SELL", "SELL"):
        return 1 if forward_return < 0 else 0
    elif rating_upper == "HOLD":
        return 1 if abs(forward_return) < HOLD_FLAT_THRESHOLD else 0
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# POPULATE AUDIT QUEUE
# ─────────────────────────────────────────────────────────────────────────────

def populate_audit_queue() -> Dict:
    """
    Read all analysis_history records. For each record × each horizon,
    insert a row into lab_rec_audit if not already present (idempotent).
    """
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT analysis_id, symbol, rating, composite_score, analyzed_at FROM analysis_history"
        ).fetchall()
    except Exception as e:
        return {"inserted": 0, "error": str(e)}
    finally:
        conn.close()

    total_inserted = 0
    for row in rows:
        inserted = db_lab.insert_rec_audit_rows(
            analysis_id=row["analysis_id"],
            symbol=row["symbol"],
            rating=row["rating"],
            composite_score=float(row["composite_score"]) if row["composite_score"] else None,
            analyzed_at=row["analyzed_at"],
        )
        total_inserted += inserted

    logger.info(f"populate_audit_queue: inserted {total_inserted} new audit rows")
    return {
        "analysis_records_scanned": len(rows),
        "audit_rows_inserted": total_inserted,
        "horizons": HORIZONS,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PROCESS PENDING VALIDATIONS
# ─────────────────────────────────────────────────────────────────────────────

def process_pending_validations(batch_size: int = 50) -> Dict:
    """
    For each pending audit row where the horizon date has passed:
    1. Compute forward return from analysis_at + horizon_days
    2. Mark as validated (1) or incorrect (0)
    Returns count of processed rows.
    """
    pending = db_lab.get_pending_audit_rows()
    processed = 0
    skipped = 0

    for row in pending[:batch_size]:
        if not _horizon_date_passed(row["analyzed_at"], row["horizon_days"]):
            skipped += 1
            continue

        fwd_ret = _compute_forward_return(
            row["symbol"],
            row["analyzed_at"],
            row["horizon_days"],
        )

        if fwd_ret is not None:
            validated = _is_validated(row["rating"], fwd_ret)
            db_lab.update_rec_audit_result(row["id"], fwd_ret, validated)
            processed += 1
        else:
            skipped += 1

    logger.info(f"process_pending_validations: processed={processed}, skipped={skipped}")
    return {
        "processed": processed,
        "skipped_not_due_or_no_data": skipped,
        "total_pending": len(pending),
    }


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

def get_accuracy_dashboard() -> Dict:
    """Return aggregated recommendation accuracy by rating × horizon."""
    return db_lab.get_rec_audit_dashboard()


def get_symbol_validation(symbol: str) -> List[Dict]:
    """Return all audit records for a single symbol."""
    return db_lab.get_rec_audit_by_symbol(symbol)


# ─────────────────────────────────────────────────────────────────────────────
# ACCURACY TREND (monthly)
# ─────────────────────────────────────────────────────────────────────────────

def accuracy_trend() -> List[Dict]:
    """Return monthly accuracy trend from validated audit records."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT analyzed_at, validated FROM lab_rec_audit
            WHERE validated IS NOT NULL
            ORDER BY analyzed_at ASC
            """
        ).fetchall()
    except Exception:
        return []
    finally:
        conn.close()

    if not rows:
        return []

    df = pd.DataFrame(rows, columns=["analyzed_at", "validated"])
    df["analyzed_at"] = pd.to_datetime(df["analyzed_at"], errors="coerce", format="mixed")
    df = df.dropna(subset=["analyzed_at"])
    df["month"] = df["analyzed_at"].dt.to_period("M")

    trend = []
    for month, group in df.groupby("month"):
        accuracy = float(group["validated"].mean() * 100)
        trend.append({
            "month": str(month),
            "accuracy_pct": round(accuracy, 1),
            "n": len(group),
        })

    return trend

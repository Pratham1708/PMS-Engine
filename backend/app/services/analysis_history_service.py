"""
analysis_history_service.py — Manage Stock Analysis Runs History.
Interacts with the SQLite database to record, list, and fetch analysis history entries.
Generates unique UUIDs and computes freshness classifications.
"""

import logging
import uuid
from datetime import datetime
import pytz
from typing import List, Dict, Any, Optional

from app.services.db import get_db_connection

logger = logging.getLogger(__name__)
IST = pytz.timezone("Asia/Kolkata")


def get_freshness_status(analyzed_at_str: str) -> str:
    """
    Calculate freshness classification based on days since analysis:
    - Fresh: 0–1 days old
    - Recent: 1–7 days old
    - Aging: 7–30 days old
    - Stale: 30+ days old
    """
    try:
        # Strip ' IST' suffix for parsing
        cleaned = analyzed_at_str.replace(" IST", "").strip()
        # Parse timestamp: e.g. "08-Jun-2026 11:45 AM" or "08-Jun-2026 11:45 PM"
        dt = datetime.strptime(cleaned, "%d-%b-%Y %I:%M %p")
        
        # Naive datetime comparison in IST
        now = datetime.now(IST).replace(tzinfo=None)
        diff = now - dt
        days = diff.total_seconds() / 86400.0
        
        if days < 0:
            return "Fresh"
        if days <= 1.0:
            return "Fresh"
        if days <= 7.0:
            return "Recent"
        if days <= 30.0:
            return "Aging"
        return "Stale"
    except Exception as e:
        logger.error(f"Error parsing freshness timestamp '{analyzed_at_str}': {e}")
        return "Stale"


def record_analysis(symbol: str, rating: str, confidence: float, composite_score: float) -> str:
    """
    Record a new stock analysis run in the database.
    Generates a unique UUID and returns it.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    analysis_id = str(uuid.uuid4())
    try:
        analyzed_at = datetime.now(IST).strftime("%d-%b-%Y %I:%M %p IST")
        cursor.execute(
            """
            INSERT INTO analysis_history (analysis_id, symbol, rating, confidence, composite_score, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (analysis_id, symbol.upper(), rating, confidence, composite_score, analyzed_at)
        )
        conn.commit()
        logger.info(f"Recorded analysis {analysis_id} for {symbol}: {rating} at {analyzed_at}")
        return analysis_id
    except Exception as e:
        logger.error(f"Error logging analysis for {symbol}: {e}")
        return ""
    finally:
        conn.close()


def get_analysis_history(symbol: str) -> List[Dict[str, Any]]:
    """Retrieve all historical analysis runs for a given symbol, sorted by newest first."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT analysis_id, rating, confidence, composite_score, analyzed_at
            FROM analysis_history
            WHERE UPPER(symbol) = ?
            ORDER BY analyzed_at DESC
            """,
            (symbol.upper(),)
        )
        rows = cursor.fetchall()
        return [
            {
                "analysis_id": row["analysis_id"],
                "rating": row["rating"],
                "confidence": row["confidence"],
                "composite_score": row["composite_score"],
                "analyzed_at": row["analyzed_at"],
                "status": get_freshness_status(row["analyzed_at"]),
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Error retrieving analysis history for {symbol}: {e}")
        return []
    finally:
        conn.close()


def get_last_analysis(symbol: str) -> Optional[Dict[str, Any]]:
    """Retrieve the single most recent analysis run for a given symbol, if any exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT analysis_id, rating, confidence, composite_score, analyzed_at
            FROM analysis_history
            WHERE UPPER(symbol) = ?
            ORDER BY analyzed_at DESC
            LIMIT 1
            """,
            (symbol.upper(),)
        )
        row = cursor.fetchone()
        if row:
            analyzed_at_str = row["analyzed_at"]
            return {
                "analysis_id": row["analysis_id"],
                "rating": row["rating"],
                "confidence": row["confidence"],
                "composite_score": row["composite_score"],
                "analyzed_at": analyzed_at_str,
                "status": get_freshness_status(analyzed_at_str),
            }
        return None
    except Exception as e:
        logger.error(f"Error retrieving last analysis for {symbol}: {e}")
        return None
    finally:
        conn.close()


def get_recent_analysis(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve recently analyzed stocks.
    Returns the latest analysis run for each analyzed stock symbol,
    ordered by analysis timestamp descending.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Group by symbol and fetch the row with the maximum ID / timestamp for each
        cursor.execute(
            f"""
            SELECT analysis_id, symbol, rating, confidence, composite_score, analyzed_at
            FROM analysis_history
            WHERE analysis_id IN (
                SELECT analysis_id
                FROM (
                    SELECT symbol, analysis_id, ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY analyzed_at DESC) as rn
                    FROM analysis_history
                )
                WHERE rn = 1
            )
            ORDER BY analyzed_at DESC
            LIMIT {limit}
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "analysis_id": row["analysis_id"],
                "symbol": row["symbol"],
                "rating": row["rating"],
                "confidence": row["confidence"],
                "composite_score": row["composite_score"],
                "analyzed_at": row["analyzed_at"],
                "status": get_freshness_status(row["analyzed_at"]),
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Error retrieving recent analysis runs: {e}")
        return []
    finally:
        conn.close()

"""
user_stock_service.py — Manage User Research Universe (My Stocks).
Interacts with the SQLite database to add, remove, and list user stocks.
"""

import logging
from datetime import datetime
import pytz
from typing import List, Dict, Any

from app.services.db import get_db_connection, is_in_security_master, get_security_master_entry
from app.data.loader import data_loader

logger = logging.getLogger(__name__)
IST = pytz.timezone("Asia/Kolkata")


def is_valid_symbol(symbol: str) -> bool:
    """
    Verify if a symbol is covered in the Nifty 50 universe (data_loader)
    OR exists in the broader security_master table.
    """
    # First check the pre-computed Nifty 50 DataFrame
    df = data_loader.get_df()
    if not df.empty and symbol.upper() in df["Symbol"].str.upper().tolist():
        return True
    # Fall back to security_master (broader universe)
    return is_in_security_master(symbol)


def get_canonical_symbol(symbol: str) -> str:
    """
    Retrieve the exact capitalised case of the symbol.
    Checks data_loader first, then security_master.
    """
    # Check data_loader (Nifty 50)
    df = data_loader.get_df()
    if not df.empty:
        matches = df[df["Symbol"].str.upper() == symbol.upper()]
        if not matches.empty:
            return str(matches.iloc[0]["Symbol"])

    # Check security_master for canonical casing
    entry = get_security_master_entry(symbol)
    if entry:
        return entry["symbol"]

    return symbol.upper()


def is_in_data_loader(symbol: str) -> bool:
    """Check if a symbol exists in the pre-computed Nifty 50 data_loader DataFrame."""
    df = data_loader.get_df()
    if df.empty:
        return False
    return symbol.upper() in df["Symbol"].str.upper().tolist()


def get_my_stocks() -> List[Dict[str, Any]]:
    """
    Retrieve all user interest stocks.
    Returns list of dicts with symbol and added_at.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT symbol, added_at FROM my_stocks ORDER BY added_at DESC")
        rows = cursor.fetchall()
        return [{"symbol": row["symbol"], "added_at": row["added_at"]} for row in rows]
    except Exception as e:
        logger.error(f"Error fetching user stocks: {e}")
        return []
    finally:
        conn.close()


def add_to_my_stocks(symbol: str) -> bool:
    """
    Add a stock symbol to the user's interest list.
    Validates symbol existence in data_loader (Nifty 50) OR the security_master.
    """
    if not is_valid_symbol(symbol):
        logger.warning(f"Symbol {symbol} is not valid in Nifty 50 or security master")
        return False

    canonical = get_canonical_symbol(symbol)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        added_at = datetime.now(IST).strftime("%Y-%m-%d %I:%M:%S %p IST")
        cursor.execute(
            "INSERT OR REPLACE INTO my_stocks (symbol, added_at) VALUES (?, ?)",
            (canonical, added_at)
        )
        conn.commit()
        logger.info(f"Added {canonical} to user interest stocks")
        return True
    except Exception as e:
        logger.error(f"Error adding symbol {symbol} to db: {e}")
        return False
    finally:
        conn.close()


def remove_from_my_stocks(symbol: str) -> bool:
    """Remove a stock symbol from the user's interest list."""
    canonical = get_canonical_symbol(symbol)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM my_stocks WHERE symbol = ?", (canonical,))
        conn.commit()
        logger.info(f"Removed {canonical} from user interest stocks")
        return True
    except Exception as e:
        logger.error(f"Error removing symbol {symbol} from db: {e}")
        return False
    finally:
        conn.close()

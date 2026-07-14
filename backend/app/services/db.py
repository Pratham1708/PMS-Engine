"""
db.py — Persistent Database Gateway supporting PostgreSQL & SQLite.
Handles connection pooling, session management, transactions, and auto-reconnect.
Includes transparent SQLite-to-PostgreSQL SQL query translation for legacy compatibility.
"""

import os
import re
import uuid
import logging
import sqlite3
from typing import Optional, List, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from app.config import settings
from app.models.orm import Base, SECURITY_MASTER_SEED

logger = logging.getLogger(__name__)

# Determine active database configuration
DATABASE_URL = getattr(settings, "database_url", "")
IS_POSTGRES = DATABASE_URL.startswith("postgresql")

# Connection Pool settings
engine = None
SessionLocal = None

DB_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data")
)
DB_PATH = os.path.join(DB_DIR, "pms_engine.db")

if IS_POSTGRES:
    logger.info("Database: Configuring production PostgreSQL connection pool.")
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=1800,
        pool_pre_ping=True,  # Automatic reconnect / check if connection is alive
    )
    SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
else:
    logger.info(f"Database: Configuring local development SQLite at {DB_PATH}")
    os.makedirs(DB_DIR, exist_ok=True)
    sqlite_url = f"sqlite:///{DB_PATH}"
    engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False}
    )
    SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


# ── SQL Dialect Translation Layer ───────────────────────────────────────────

def translate_sqlite_to_pg(sql: str) -> str:
    """Translate standard SQLite SQL statements into PostgreSQL dialect."""
    if not sql:
        return sql

    # 1. Translate parameter markers (? -> %s)
    # Be careful to handle string literals if any exist, but for simple parameter markers:
    sql_pg = sql.replace('?', '%s')

    # 2. Translate named parameters (:name -> %(name)s)
    sql_pg = re.sub(r'(?<!:):([a-zA-Z0-9_]+)', r'%(\1)s', sql_pg)

    # 3. Translate SQLite date/time functions
    sql_pg = re.sub(r'datetime\((.*?)\)', r'\1', sql_pg, flags=re.IGNORECASE)

    # 4. Translate SQLite INSERT OR IGNORE INTO
    if "INSERT OR IGNORE INTO" in sql_pg.upper():
        sql_pg = re.sub(
            r'INSERT\s+OR\s+IGNORE\s+INTO\s+',
            'INSERT INTO ',
            sql_pg,
            flags=re.IGNORECASE
        )
        sql_pg += " ON CONFLICT DO NOTHING"

    # 5. Translate SQLite INSERT OR REPLACE INTO (ON CONFLICT DO UPDATE)
    if "INSERT OR REPLACE INTO" in sql_pg.upper():
        match = re.search(
            r'INSERT\s+OR\s+REPLACE\s+INTO\s+(\w+)\s*\((.*?)\)\s*VALUES\s*(.*)',
            sql_pg,
            flags=re.IGNORECASE | re.DOTALL
        )
        if match:
            table_name = match.group(1).lower()
            columns_str = match.group(2)
            values_str = match.group(3)

            conflict_targets = {
                "my_stocks": "symbol",
                "report_history": "report_id",
                "snapshot_stock": "snapshot_id, symbol",
                "snapshot_indicator": "snapshot_id, symbol",
                "snapshot_score": "snapshot_id, symbol",
                "snapshot_sector": "snapshot_id, sector",
                "snapshot_market": "snapshot_id",
                "lab_reports": "report_id",
                "lab_rec_audit": "analysis_id, horizon_days",
                "indicator_snapshot": "snapshot_id, symbol",
                "feature_snapshot": "snapshot_id, symbol",
                "score_snapshot": "snapshot_id, symbol",
                "explainability_snapshot": "snapshot_id, symbol",
                "report_snapshot": "snapshot_id"
            }
            conflict_target = conflict_targets.get(table_name)
            if conflict_target:
                cols = [c.strip() for c in columns_str.split(',')]
                conflict_cols = [c.strip().lower() for c in conflict_target.split(',')]
                update_cols = [c for c in cols if c.lower() not in conflict_cols]
                update_set_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])
                sql_pg = f"INSERT INTO {table_name} ({columns_str}) VALUES {values_str} ON CONFLICT ({conflict_target}) DO UPDATE SET {update_set_clause}"
            else:
                sql_pg = f"INSERT INTO {table_name} ({columns_str}) VALUES {values_str}"

    return sql_pg


class CompatibleRow(dict):
    """A dictionary subclass that also allows positional/index access (e.g., row[0])."""
    def __init__(self, data, tuple_data=None):
        super().__init__(data)
        self._tuple = tuple_data if tuple_data is not None else tuple(data.values())

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._tuple[key]
        return super().__getitem__(key)


class DBCursorWrapper:
    """Wrapper around raw DB cursors to enforce dict-like row formatting and query translation."""
    def __init__(self, raw_cursor, is_postgres: bool):
        self.raw_cursor = raw_cursor
        self.is_postgres = is_postgres

    def execute(self, sql: str, params: Any = None):
        sql_to_run = translate_sqlite_to_pg(sql) if self.is_postgres else sql
        if params is not None:
            self.raw_cursor.execute(sql_to_run, params)
        else:
            self.raw_cursor.execute(sql_to_run)
        return self

    def executemany(self, sql: str, params_list: List[Any]):
        sql_to_run = translate_sqlite_to_pg(sql) if self.is_postgres else sql
        self.raw_cursor.executemany(sql_to_run, params_list)
        return self

    def fetchone(self) -> Optional[CompatibleRow]:
        row = self.raw_cursor.fetchone()
        if row is None:
            return None
        return CompatibleRow(dict(row), tuple(row))

    def fetchall(self) -> List[CompatibleRow]:
        rows = self.raw_cursor.fetchall()
        return [CompatibleRow(dict(r), tuple(r)) for r in rows]

    @property
    def lastrowid(self):
        return getattr(self.raw_cursor, "lastrowid", None)

    def close(self):
        self.raw_cursor.close()



class DBConnectionWrapper:
    """Wrapper around raw SQLite or PostgreSQL connection objects."""
    def __init__(self, raw_conn, is_postgres: bool):
        self.raw_conn = raw_conn
        self.is_postgres = is_postgres

    def cursor(self) -> DBCursorWrapper:
        if self.is_postgres:
            import psycopg2.extras
            cursor = self.raw_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        else:
            cursor = self.raw_conn.cursor()
        return DBCursorWrapper(cursor, self.is_postgres)

    def execute(self, sql: str, params: Any = None) -> DBCursorWrapper:
        cursor = self.cursor()
        cursor.execute(sql, params)
        return cursor

    def executemany(self, sql: str, params_list: List[Any]) -> DBCursorWrapper:
        cursor = self.cursor()
        cursor.executemany(sql, params_list)
        return cursor

    def commit(self):
        self.raw_conn.commit()

    def rollback(self):
        try:
            self.raw_conn.rollback()
        except Exception:
            pass

    def close(self):
        self.raw_conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


def get_db_connection() -> DBConnectionWrapper:
    """Return a wrapper connection for SQLite or PostgreSQL (for raw SQL compatibility)."""
    if IS_POSTGRES:
        conn = engine.raw_connection()
        return DBConnectionWrapper(conn, is_postgres=True)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return DBConnectionWrapper(conn, is_postgres=False)


def get_db_session():
    """Return a thread-scoped SQLAlchemy Session instance."""
    return SessionLocal()


# ── Database Initialization ──

def init_db() -> None:
    """Create all database tables and seed them with Security Master data."""
    logger.info("Initializing database schemas...")
    try:
        # Create all tables (legacy and new)
        Base.metadata.create_all(bind=engine)
        
        # Seed security master if empty
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            r = cursor.execute("SELECT COUNT(*) FROM security_master").fetchone()
            count = r[list(r.keys())[0]] if r else 0
            if count == 0:
                logger.info(f"Seeding security_master with {len(SECURITY_MASTER_SEED)} stocks...")
                cursor.executemany(
                    "INSERT INTO security_master (symbol, company_name, sector, industry, exchange) VALUES (?, ?, ?, ?, 'NSE')",
                    [(s[0], s[1], s[2], s[3]) for s in SECURITY_MASTER_SEED]
                )
                conn.commit()
            logger.info("Database schemas initialized and seeded successfully.")
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error during database initialization: {e}", exc_info=True)
        raise e


# ── Security Master Query Functions ──

def search_security_master(query: str) -> List[Dict[str, Any]]:
    """Search security master by symbol or company name."""
    conn = get_db_connection()
    try:
        term = f"%{query.strip()}%"
        rows = conn.execute(
            """
            SELECT symbol, company_name, sector, industry, exchange, isin, market_cap_category 
            FROM security_master
            WHERE symbol ILIKE ? OR company_name ILIKE ?
            ORDER BY symbol ASC
            """ if IS_POSTGRES else
            """
            SELECT symbol, company_name, sector, industry 
            FROM security_master
            WHERE symbol LIKE ? OR company_name LIKE ?
            ORDER BY symbol ASC
            """,
            (term, term)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def is_in_security_master(symbol: str) -> bool:
    """Check if a symbol exists in the security master."""
    conn = get_db_connection()
    try:
        sym = symbol.strip().upper()
        row = conn.execute(
            "SELECT 1 FROM security_master WHERE UPPER(symbol) = ?",
            (sym,)
        ).fetchone()
        if row:
            return True
        if not sym.endswith(".NS"):
            row = conn.execute(
                "SELECT 1 FROM security_master WHERE UPPER(symbol) = ?",
                (sym + ".NS",)
            ).fetchone()
            return row is not None
        return False
    finally:
        conn.close()


def get_security_master_entry(symbol: str) -> Optional[Dict[str, Any]]:
    """Get a single security master entry by symbol."""
    conn = get_db_connection()
    try:
        sym = symbol.strip().upper()
        row = conn.execute(
            "SELECT symbol, company_name, sector, industry FROM security_master WHERE UPPER(symbol) = ?",
            (sym,)
        ).fetchone()
        if row:
            return dict(row)
        if not sym.endswith(".NS"):
            row = conn.execute(
                "SELECT symbol, company_name, sector, industry FROM security_master WHERE UPPER(symbol) = ?",
                (sym + ".NS",)
            ).fetchone()
            if row:
                return dict(row)
        return None
    finally:
        conn.close()


# ── Report History Query Functions ──

def add_report_to_history(
    report_id: str,
    report_type: str,
    symbol: Optional[str],
    generated_at: str,
    analysis_id: Optional[str],
    file_path: str,
    report_version: str = "1.0"
) -> None:
    """Insert a generated report record into database history."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO report_history 
            (report_id, report_type, symbol, generated_at, analysis_id, file_path, report_version) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (report_id, report_type, symbol, generated_at, analysis_id, file_path, report_version)
        )
        conn.commit()
    finally:
        conn.close()


def get_report_from_history(report_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve report metadata by ID."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM report_history WHERE report_id = ?",
            (report_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_reports_from_history() -> List[Dict[str, Any]]:
    """List all reports in history sorted by datetime generated_at descending."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM report_history ORDER BY generated_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_latest_report(report_type: str, symbol: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve the latest generated report of a type (and optional symbol)."""
    conn = get_db_connection()
    try:
        if symbol:
            row = conn.execute(
                """
                SELECT * FROM report_history 
                WHERE report_type = ? AND UPPER(symbol) = ? 
                ORDER BY generated_at DESC LIMIT 1
                """,
                (report_type, symbol.upper())
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT * FROM report_history 
                WHERE report_type = ? 
                ORDER BY generated_at DESC LIMIT 1
                """,
                (report_type,)
            ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── Phase 13 Snapshot Helper Functions ──

def _now_ist() -> str:
    """Return current IST datetime as ISO string."""
    import pytz
    from datetime import datetime
    return datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()


def create_snapshot(
    snapshot_date: str,
    market_date: str,
    is_official: bool = True,
    universe_version: str = "nifty50_v1",
    engine_version: str = "1.0.0",
    pipeline_run_id: Optional[str] = None,
    indicator_version: str = "1.0.0",
    scoring_version: str = "1.0.0",
    ml_model_version: str = "gru_v1",
    feature_version: str = "1.0.0",
    software_build: str = "2026.07.14",
) -> str:
    """Create a new snapshot record and return its snapshot_id."""
    snapshot_id = str(uuid.uuid4())
    if not pipeline_run_id:
        pipeline_run_id = str(uuid.uuid4())
    now = _now_ist()
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO snapshots
            (snapshot_id, pipeline_run_id, snapshot_date, market_date, generated_at, is_official,
             status, universe_version, engine_version, indicator_version, scoring_version,
             ml_model_version, feature_version, software_build, pipeline_started_at)
            VALUES (?, ?, ?, ?, ?, ?, 'generating', ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (snapshot_id, pipeline_run_id, snapshot_date, market_date, now,
             1 if is_official else 0, universe_version, engine_version,
             indicator_version, scoring_version, ml_model_version,
             feature_version, software_build, now)
        )
        conn.commit()
        return snapshot_id
    finally:
        conn.close()



def update_snapshot_status(
    snapshot_id: str,
    status: str,
    stocks_processed: int = 0,
    stocks_failed: int = 0,
    validation_passed: bool = False,
    validation_score: Optional[float] = None,
    notes: Optional[str] = None,
) -> None:
    """Update status, counts, and final timestamps on a snapshot."""
    now = _now_ist()
    conn = get_db_connection()
    try:
        conn.execute(
            """
            UPDATE snapshots SET
                status = ?, stocks_processed = ?, stocks_failed = ?,
                validation_passed = ?, validation_score = ?,
                pipeline_ended_at = ?, notes = ?
            WHERE snapshot_id = ?
            """,
            (status, stocks_processed, stocks_failed,
             1 if validation_passed else 0, validation_score,
             now, notes, snapshot_id)
        )
        conn.commit()
    finally:
        conn.close()


def publish_snapshot(snapshot_id: str) -> None:
    """Mark a snapshot as officially published."""
    now = _now_ist()
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE snapshots SET published_at = ? WHERE snapshot_id = ?",
            (now, snapshot_id)
        )
        conn.commit()
    finally:
        conn.close()


def set_snapshot_pipeline_duration(snapshot_id: str, duration_sec: float) -> None:
    """Store total pipeline duration on the snapshot record."""
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE snapshots SET pipeline_duration_sec = ? WHERE snapshot_id = ?",
            (duration_sec, snapshot_id)
        )
        conn.commit()
    finally:
        conn.close()


def save_snapshot_stage(
    snapshot_id: str,
    stage_name: str,
    stage_status: str,
    started_at: Optional[str] = None,
    completed_at: Optional[str] = None,
    duration_sec: Optional[float] = None,
    stocks_success: int = 0,
    stocks_failed: int = 0,
    warnings_count: int = 0,
    errors_count: int = 0,
    log_summary: Optional[str] = None,
) -> None:
    """Insert or update a pipeline stage record in snapshot_metadata."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT id FROM snapshot_metadata WHERE snapshot_id = ? AND stage_name = ?",
            (snapshot_id, stage_name)
        ).fetchall()
        if rows:
            conn.execute(
                """
                UPDATE snapshot_metadata SET
                    stage_status = ?, started_at = ?, completed_at = ?,
                    duration_sec = ?, stocks_success = ?, stocks_failed = ?,
                    warnings_count = ?, errors_count = ?, log_summary = ?
                WHERE snapshot_id = ? AND stage_name = ?
                """,
                (stage_status, started_at, completed_at, duration_sec,
                 stocks_success, stocks_failed, warnings_count, errors_count,
                 log_summary, snapshot_id, stage_name)
            )
        else:
            conn.execute(
                """
                INSERT INTO snapshot_metadata
                (snapshot_id, stage_name, stage_status, started_at, completed_at,
                 duration_sec, stocks_success, stocks_failed, warnings_count, errors_count, log_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (snapshot_id, stage_name, stage_status, started_at, completed_at,
                 duration_sec, stocks_success, stocks_failed, warnings_count, errors_count, log_summary)
            )
        conn.commit()
    finally:
        conn.close()


def get_snapshot_stage(snapshot_id: str, stage_name: str) -> Optional[Dict[str, Any]]:
    """Return pipeline stage timeline status for a snapshot."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM snapshot_metadata WHERE snapshot_id = ? AND stage_name = ?",
            (snapshot_id, stage_name)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def save_snapshot_stocks(snapshot_id: str, records: List[Dict[str, Any]]) -> int:
    """Bulk insert stock records for a snapshot. Returns count inserted."""
    if not records:
        return 0
    
    default_record = {
        "company_name": None, "sector": None, "industry": None,
        "open": None, "high": None, "low": None, "close": None, "volume": None,
        "prev_close": None, "daily_chg_pct": None, "daily_chg_amt": None,
        "week52_high": None, "week52_low": None,
        "technical_score": None, "ml_score": None, "gru_score": None,
        "risk_score": None, "momentum_score": None, "trend_score": None,
        "confidence": None, "composite_score": None, "reliability_score": None,
        "final_rating": None, "portfolio_eligible": None, "conviction_level": None,
        "rank": None, "percentile": None, "universe_position": None,
        "data_source": "yfinance", "download_status": "success", "data_warnings": None
    }
    
    conn = get_db_connection()
    try:
        conn.executemany(
            """
            INSERT OR REPLACE INTO snapshot_stock
            (snapshot_id, symbol, company_name, sector, industry,
             open, high, low, close, volume, prev_close, daily_chg_pct, daily_chg_amt,
             week52_high, week52_low,
             technical_score, ml_score, gru_score, risk_score, momentum_score,
             trend_score, confidence, composite_score, reliability_score,
             final_rating, portfolio_eligible, conviction_level, rank, percentile,
             universe_position, data_source, download_status, data_warnings)
            VALUES
            (:snapshot_id, :symbol, :company_name, :sector, :industry,
             :open, :high, :low, :close, :volume, :prev_close, :daily_chg_pct, :daily_chg_amt,
             :week52_high, :week52_low,
             :technical_score, :ml_score, :gru_score, :risk_score, :momentum_score,
             :trend_score, :confidence, :composite_score, :reliability_score,
             :final_rating, :portfolio_eligible, :conviction_level, :rank, :percentile,
             :universe_position, :data_source, :download_status, :data_warnings)
            """,
            [{**default_record, **r, "snapshot_id": snapshot_id} for r in records]
        )
        conn.commit()
        return len(records)
    finally:
        conn.close()


def save_snapshot_indicators(snapshot_id: str, records: List[Dict[str, Any]]) -> int:
    """Bulk insert indicator records for a snapshot."""
    if not records:
        return 0
    
    default_record = {
        "rsi_14": None, "ema_20": None, "ema_50": None, "ema_200": None,
        "macd": None, "macd_signal": None, "bb_upper": None, "bb_lower": None,
        "atr_14": None, "stoch_k": None, "adx_14": None, "obv": None, "vwap": None,
        "above_ema20": 0, "above_ema50": 0, "above_ema200": 0,
        "near_52w_high": 0, "near_52w_low": 0
    }
    
    conn = get_db_connection()
    try:
        conn.executemany(
            """
            INSERT OR REPLACE INTO snapshot_indicator
            (snapshot_id, symbol, rsi_14, ema_20, ema_50, ema_200,
             macd, macd_signal, bb_upper, bb_lower, atr_14, stoch_k,
             adx_14, obv, vwap, above_ema20, above_ema50, above_ema200,
             near_52w_high, near_52w_low)
            VALUES
            (:snapshot_id, :symbol, :rsi_14, :ema_20, :ema_50, :ema_200,
             :macd, :macd_signal, :bb_upper, :bb_lower, :atr_14, :stoch_k,
             :adx_14, :obv, :vwap, :above_ema20, :above_ema50, :above_ema200,
             :near_52w_high, :near_52w_low)
            """,
            [{**default_record, **r, "snapshot_id": snapshot_id} for r in records]
        )
        conn.commit()
        return len(records)
    finally:
        conn.close()


def save_snapshot_scores(snapshot_id: str, records: List[Dict[str, Any]]) -> int:
    """Bulk insert score breakdown records for a snapshot."""
    if not records:
        return 0
    
    default_record = {
        "trend_component": None, "momentum_component": None,
        "volatility_component": None, "volume_component": None,
        "lgbm_signal": None, "rf_signal": None, "xgb_signal": None,
        "gru_hold": None, "gru_long": None, "gru_short": None, "return_score": None,
        "primary_driver": None, "secondary_driver": None,
        "w_technical": 0.40, "w_ml": 0.35, "w_gru": 0.15, "w_reliability": 0.10
    }
    
    conn = get_db_connection()
    try:
        conn.executemany(
            """
            INSERT OR REPLACE INTO snapshot_score
            (snapshot_id, symbol, trend_component, momentum_component,
             volatility_component, volume_component, lgbm_signal, rf_signal,
             xgb_signal, gru_hold, gru_long, gru_short, return_score,
             primary_driver, secondary_driver, w_technical, w_ml, w_gru, w_reliability)
            VALUES
            (:snapshot_id, :symbol, :trend_component, :momentum_component,
             :volatility_component, :volume_component, :lgbm_signal, :rf_signal,
             :xgb_signal, :gru_hold, :gru_long, :gru_short, :return_score,
             :primary_driver, :secondary_driver, :w_technical, :w_ml, :w_gru, :w_reliability)
            """,
            [{**default_record, **r, "snapshot_id": snapshot_id} for r in records]
        )
        conn.commit()
        return len(records)
    finally:
        conn.close()


def save_snapshot_sector(snapshot_id: str, records: List[Dict[str, Any]]) -> int:
    """Bulk insert sector aggregates for a snapshot."""
    if not records:
        return 0
    conn = get_db_connection()
    try:
        conn.executemany(
            """
            INSERT OR REPLACE INTO snapshot_sector
            (snapshot_id, sector, stock_count, avg_composite, avg_confidence,
             avg_technical, avg_momentum, avg_trend, avg_risk,
             strong_buy_count, buy_count, hold_count, sell_count, strong_sell_count,
             bullish_pct, bearish_pct, sector_rank, top_stock, weakest_stock, avg_daily_chg_pct)
            VALUES
            (:snapshot_id, :sector, :stock_count, :avg_composite, :avg_confidence,
             :avg_technical, :avg_momentum, :avg_trend, :avg_risk,
             :strong_buy_count, :buy_count, :hold_count, :sell_count, :strong_sell_count,
             :bullish_pct, :bearish_pct, :sector_rank, :top_stock, :weakest_stock, :avg_daily_chg_pct)
            """,
            [{**r, "snapshot_id": snapshot_id} for r in records]
        )
        conn.commit()
        return len(records)
    finally:
        conn.close()


def save_snapshot_market(snapshot_id: str, data: Dict[str, Any]) -> None:
    """Insert universe-wide market breadth record for a snapshot."""
    data["snapshot_id"] = snapshot_id
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO snapshot_market
            (snapshot_id, total_stocks, advancing_stocks, declining_stocks, unchanged_stocks,
             advance_decline_ratio, advance_volume, decline_volume,
             stocks_above_ema20, stocks_above_ema50, stocks_above_ema200,
             pct_above_ema20, pct_above_ema50, pct_above_ema200,
             week52_high_count, week52_low_count,
             avg_composite, avg_confidence, avg_rsi, avg_momentum, avg_daily_chg_pct,
             bullish_pct, bearish_pct, market_regime,
             strong_buy_count, buy_count, hold_count, sell_count, strong_sell_count,
             india_vix, pcr, fii_activity, dii_activity)
            VALUES
            (:snapshot_id, :total_stocks, :advancing_stocks, :declining_stocks, :unchanged_stocks,
             :advance_decline_ratio, :advance_volume, :decline_volume,
             :stocks_above_ema20, :stocks_above_ema50, :stocks_above_ema200,
             :pct_above_ema20, :pct_above_ema50, :pct_above_ema200,
             :week52_high_count, :week52_low_count,
             :avg_composite, :avg_confidence, :avg_rsi, :avg_momentum, :avg_daily_chg_pct,
             :bullish_pct, :bearish_pct, :market_regime,
             :strong_buy_count, :buy_count, :hold_count, :sell_count, :strong_sell_count,
             :india_vix, :pcr, :fii_activity, :dii_activity)
            """,
            data
        )
        conn.commit()
    finally:
        conn.close()


def save_snapshot_watchlists(snapshot_id: str, records: List[Dict[str, Any]]) -> int:
    """Bulk insert watchlist membership records for a snapshot."""
    if not records:
        return 0
    conn = get_db_connection()
    try:
        conn.executemany(
            """
            INSERT OR IGNORE INTO snapshot_watchlist
            (snapshot_id, watchlist_name, symbol, rank_in_list, score_used, reason)
            VALUES (:snapshot_id, :watchlist_name, :symbol, :rank_in_list, :score_used, :reason)
            """,
            [{**r, "snapshot_id": snapshot_id} for r in records]
        )
        conn.commit()
        return len(records)
    finally:
        conn.close()


def save_snapshot_changes(snapshot_id: str, records: List[Dict[str, Any]]) -> int:
    """Bulk insert recommendation change records for a snapshot."""
    if not records:
        return 0
    conn = get_db_connection()
    try:
        conn.executemany(
            """
            INSERT INTO snapshot_change
            (snapshot_id, prev_snapshot_id, symbol, change_type,
             prev_rating, new_rating, composite_diff, confidence_diff,
             technical_diff, ml_diff, momentum_diff, trend_diff, risk_diff,
             primary_driver, secondary_driver, is_significant)
            VALUES
            (:snapshot_id, :prev_snapshot_id, :symbol, :change_type,
             :prev_rating, :new_rating, :composite_diff, :confidence_diff,
             :technical_diff, :ml_diff, :momentum_diff, :trend_diff, :risk_diff,
             :primary_driver, :secondary_driver, :is_significant)
            """,
            [{**r, "snapshot_id": snapshot_id} for r in records]
        )
        conn.commit()
        return len(records)
    finally:
        conn.close()


def save_snapshot_validations(snapshot_id: str, records: List[Dict[str, Any]]) -> int:
    """Bulk insert validation check results for a snapshot."""
    if not records:
        return 0
    conn = get_db_connection()
    try:
        conn.executemany(
            """
            INSERT INTO snapshot_validation
            (snapshot_id, check_name, status, detail, affected_count, threshold, actual_value)
            VALUES (:snapshot_id, :check_name, :status, :detail, :affected_count, :threshold, :actual_value)
            """,
            [{**r, "snapshot_id": snapshot_id} for r in records]
        )
        conn.commit()
        return len(records)
    finally:
        conn.close()


def link_snapshot_report(
    snapshot_id: str,
    report_type: str,
    html_path: Optional[str] = None,
    pdf_path: Optional[str] = None,
    symbol: Optional[str] = None,
    file_size_kb: Optional[float] = None,
) -> None:
    """Insert a report link for a snapshot."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO snapshot_report
            (snapshot_id, report_type, symbol, html_path, pdf_path, generated_at, file_size_kb)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (snapshot_id, report_type, symbol, html_path, pdf_path, _now_ist(), file_size_kb)
        )
        conn.commit()
    finally:
        conn.close()


# ── Snapshot Query Functions ──

def get_latest_snapshot(official_only: bool = True) -> Optional[Dict[str, Any]]:
    """Return the most recent completed snapshot record."""
    conn = get_db_connection()
    try:
        query = """
            SELECT * FROM snapshots
            WHERE status IN ('completed', 'completed_with_warnings')
        """
        if official_only:
            query += " AND is_official = 1"
        query += " ORDER BY snapshot_date DESC, generated_at DESC LIMIT 1"
        row = conn.execute(query).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_snapshot_by_id(snapshot_id: str) -> Optional[Dict[str, Any]]:
    """Return snapshot record by ID."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM snapshots WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_snapshot_by_date(snapshot_date: str, official_only: bool = True) -> Optional[Dict[str, Any]]:
    """Return snapshot for a specific market date."""
    conn = get_db_connection()
    try:
        query = """
            SELECT * FROM snapshots
            WHERE snapshot_date = ?
            AND status IN ('completed', 'completed_with_warnings')
        """
        params: tuple = (snapshot_date,)
        if official_only:
            query += " AND is_official = 1"
        query += " ORDER BY generated_at DESC LIMIT 1"
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_snapshot_dates(official_only: bool = True, limit: int = 365) -> List[Dict[str, Any]]:
    """List all available snapshot dates, newest first."""
    conn = get_db_connection()
    try:
        query = """
            SELECT *
            FROM snapshots
            WHERE status IN ('completed', 'completed_with_warnings')
        """
        if official_only:
            query += " AND is_official = 1"
        query += f" ORDER BY snapshot_date DESC, generated_at DESC LIMIT {limit}"
        rows = conn.execute(query).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_snapshot_stocks(snapshot_id: str) -> List[Dict[str, Any]]:
    """Return all stock records for a snapshot."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM snapshot_stock WHERE snapshot_id = ? ORDER BY rank ASC",
            (snapshot_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_snapshot_stock(snapshot_id: str, symbol: str) -> Optional[Dict[str, Any]]:
    """Return a single stock record from a snapshot."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM snapshot_stock WHERE snapshot_id = ? AND UPPER(symbol) = UPPER(?)",
            (snapshot_id, symbol)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_snapshot_indicators(snapshot_id: str, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return indicator records for a snapshot (all stocks or single symbol)."""
    conn = get_db_connection()
    try:
        if symbol:
            rows = conn.execute(
                "SELECT * FROM snapshot_indicator WHERE snapshot_id = ? AND UPPER(symbol) = UPPER(?)",
                (snapshot_id, symbol)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM snapshot_indicator WHERE snapshot_id = ?", (snapshot_id,)
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_snapshot_scores(snapshot_id: str, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return score breakdown records for a snapshot."""
    conn = get_db_connection()
    try:
        if symbol:
            rows = conn.execute(
                "SELECT * FROM snapshot_score WHERE snapshot_id = ? AND UPPER(symbol) = UPPER(?)",
                (snapshot_id, symbol)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM snapshot_score WHERE snapshot_id = ?", (snapshot_id,)
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_snapshot_sector(snapshot_id: str) -> List[Dict[str, Any]]:
    """Return sector aggregates for a snapshot, sorted by rank."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM snapshot_sector WHERE snapshot_id = ? ORDER BY sector_rank ASC",
            (snapshot_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_snapshot_market(snapshot_id: str) -> Optional[Dict[str, Any]]:
    """Return market breadth record for a snapshot."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM snapshot_market WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_snapshot_watchlists(
    snapshot_id: str, watchlist_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Return watchlist records for a snapshot, optionally filtered by name."""
    conn = get_db_connection()
    try:
        if watchlist_name:
            rows = conn.execute(
                """
                SELECT * FROM snapshot_watchlist
                WHERE snapshot_id = ? AND watchlist_name = ?
                ORDER BY rank_in_list ASC
                """,
                (snapshot_id, watchlist_name)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM snapshot_watchlist WHERE snapshot_id = ? ORDER BY watchlist_name, rank_in_list",
                (snapshot_id,)
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_snapshot_changes(
    snapshot_id: str, change_type: Optional[str] = None, significant_only: bool = False
) -> List[Dict[str, Any]]:
    """Return recommendation change records for a snapshot."""
    conn = get_db_connection()
    try:
        query = "SELECT * FROM snapshot_change WHERE snapshot_id = ?"
        params: list = [snapshot_id]
        if change_type:
            query += " AND change_type = ?"
            params.append(change_type)
        if significant_only:
            query += " AND is_significant = 1"
        query += " ORDER BY ABS(composite_diff) DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_snapshot_validations(snapshot_id: str) -> List[Dict[str, Any]]:
    """Return all validation check results for a snapshot."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM snapshot_validation WHERE snapshot_id = ? ORDER BY check_name",
            (snapshot_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_snapshot_pipeline(snapshot_id: str) -> List[Dict[str, Any]]:
    """Return pipeline stage execution timeline for a snapshot."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM snapshot_metadata WHERE snapshot_id = ? ORDER BY id ASC",
            (snapshot_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_snapshot_reports(snapshot_id: str) -> List[Dict[str, Any]]:
    """Return all report links for a snapshot."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM snapshot_report WHERE snapshot_id = ? ORDER BY report_type",
            (snapshot_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_snapshot_status_summary() -> Dict[str, Any]:
    """Return high-level snapshot system status."""
    conn = get_db_connection()
    try:
        latest = conn.execute(
            """
            SELECT *
            FROM snapshots
            WHERE is_official = 1
            AND status IN ('completed', 'completed_with_warnings')
            ORDER BY snapshot_date DESC, generated_at DESC LIMIT 1
            """
        ).fetchone()
        total = conn.execute(
            "SELECT COUNT(*) FROM snapshots WHERE is_official = 1"
        ).fetchone()[0]
        in_progress = conn.execute(
            "SELECT COUNT(*) FROM snapshots WHERE status = 'generating'"
        ).fetchone()[0]
        return {
            "latest_snapshot": dict(latest) if latest else None,
            "total_snapshots": total,
            "in_progress": in_progress,
        }
    finally:
        conn.close()


def get_previous_official_snapshot(before_snapshot_id: str) -> Optional[Dict[str, Any]]:
    """Return the official snapshot immediately before the given one."""
    conn = get_db_connection()
    try:
        current = conn.execute(
            "SELECT snapshot_date FROM snapshots WHERE snapshot_id = ?",
            (before_snapshot_id,)
        ).fetchone()
        if not current:
            return None
        row = conn.execute(
            """
            SELECT * FROM snapshots
            WHERE is_official = 1
            AND status IN ('completed', 'completed_with_warnings')
            AND snapshot_date < ?
            ORDER BY snapshot_date DESC, generated_at DESC LIMIT 1
            """,
            (current["snapshot_date"],)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_stock_history_across_snapshots(symbol: str, limit: int = 90) -> List[Dict[str, Any]]:
    """Return a stock's scores/ratings across the last N official snapshots."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT ss.snapshot_date, sk.final_rating, sk.composite_score,
                   sk.confidence, sk.technical_score, sk.ml_score, sk.close, sk.daily_chg_pct
            FROM snapshot_stock sk
            JOIN snapshots ss ON ss.snapshot_id = sk.snapshot_id
            WHERE UPPER(sk.symbol) = UPPER(?)
            AND ss.is_official = 1
            AND ss.status IN ('completed', 'completed_with_warnings')
            ORDER BY ss.snapshot_date DESC
            LIMIT ?
            """,
            (symbol, limit)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_historical_scores(symbol: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Return historical scores for a stock across snapshots."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT ss.snapshot_date, 
                   sk.technical_score, 
                   sk.ml_score, 
                   sk.gru_score, 
                   sk.risk_score, 
                   sk.momentum_score, 
                   sk.trend_score, 
                   sk.confidence, 
                   sk.composite_score, 
                   sk.reliability_score
            FROM snapshot_stock sk
            JOIN snapshots ss ON ss.snapshot_id = sk.snapshot_id
            WHERE UPPER(sk.symbol) = UPPER(?)
            AND ss.status IN ('completed', 'completed_with_warnings', 'published')
            ORDER BY ss.snapshot_date DESC
            LIMIT ?
            """,
            (symbol, limit)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ── New Phase 13A Schema CRUD Methods ──

def save_market_daily(records: List[Dict[str, Any]]) -> int:
    """Save daily OHLCV quotes to market_daily table."""
    if not records:
        return 0
    conn = get_db_connection()
    try:
        conn.executemany(
            """
            INSERT OR REPLACE INTO market_daily
            (symbol, trading_date, open, high, low, close, adjusted_close, volume, delivery_volume, vwap, previous_close, last_trading_date)
            VALUES (:symbol, :trading_date, :open, :high, :low, :close, :adjusted_close, :volume, :delivery_volume, :vwap, :previous_close, :last_trading_date)
            """,
            records
        )
        conn.commit()
        return len(records)
    finally:
        conn.close()


def save_indicator_snapshots(snapshot_id: str, records: List[Dict[str, Any]]) -> int:
    """Save technical indicator computations to indicator_snapshot table."""
    if not records:
        return 0
    conn = get_db_connection()
    try:
        conn.executemany(
            """
            INSERT OR REPLACE INTO indicator_snapshot
            (snapshot_id, symbol, ema20, ema50, ema200, sma20, sma50, rsi, macd, macd_signal, adx, atr, bb_upper, bb_lower, supertrend, vwap, ichimoku, obv, cmf, mfi, roc, cci, williams_r)
            VALUES (:snapshot_id, :symbol, :ema20, :ema50, :ema200, :sma20, :sma50, :rsi, :macd, :macd_signal, :adx, :atr, :bb_upper, :bb_lower, :supertrend, :vwap, :ichimoku, :obv, :cmf, :mfi, :roc, :cci, :williams_r)
            """,
            [{**r, "snapshot_id": snapshot_id} for r in records]
        )
        conn.commit()
        return len(records)
    finally:
        conn.close()


def save_feature_snapshots(snapshot_id: str, records: List[Dict[str, Any]]) -> int:
    """Save engineered feature mappings to feature_snapshot table."""
    if not records:
        return 0
    conn = get_db_connection()
    try:
        conn.executemany(
            """
            INSERT OR REPLACE INTO feature_snapshot
            (snapshot_id, symbol, normalized_values, z_scores, rolling_statistics, lag_features)
            VALUES (:snapshot_id, :symbol, :normalized_values, :z_scores, :rolling_statistics, :lag_features)
            """,
            [{**r, "snapshot_id": snapshot_id} for r in records]
        )
        conn.commit()
        return len(records)
    finally:
        conn.close()


def save_score_snapshots(snapshot_id: str, records: List[Dict[str, Any]], strategy_id: str = "pms_default") -> int:
    """Save score records to score_snapshot table."""
    if not records:
        return 0
    conn = get_db_connection()
    try:
        conn.executemany(
            """
            INSERT OR REPLACE INTO score_snapshot
            (snapshot_id, symbol, strategy_id, technical_score, ensemble_score, gru_score, trend_score, momentum_score, risk_score, reliability_score, confidence_score, composite_score, recommendation, expected_return, custom_metrics)
            VALUES (:snapshot_id, :symbol, :strategy_id, :technical_score, :ensemble_score, :gru_score, :trend_score, :momentum_score, :risk_score, :reliability_score, :confidence_score, :composite_score, :recommendation, :expected_return, :custom_metrics)
            """,
            [{**r, "snapshot_id": snapshot_id, "strategy_id": r.get("strategy_id") or strategy_id, "custom_metrics": r.get("custom_metrics")} for r in records]
        )
        conn.commit()
        return len(records)
    finally:
        conn.close()


def save_explainability_snapshots(snapshot_id: str, records: List[Dict[str, Any]], strategy_id: str = "pms_default") -> int:
    """Save explainability details to explainability_snapshot table."""
    if not records:
        return 0
    conn = get_db_connection()
    try:
        conn.executemany(
            """
            INSERT OR REPLACE INTO explainability_snapshot
            (snapshot_id, symbol, strategy_id, score_type, purpose, formula, indicator_contributions, feature_contributions, current_values, interpretation, validation_metrics, research_references)
            VALUES (:snapshot_id, :symbol, :strategy_id, :score_type, :purpose, :formula, :indicator_contributions, :feature_contributions, :current_values, :interpretation, :validation_metrics, :research_references)
            """,
            [{**r, "snapshot_id": snapshot_id, "strategy_id": r.get("strategy_id") or strategy_id} for r in records]
        )
        conn.commit()
        return len(records)
    finally:
        conn.close()



def save_report_snapshots(snapshot_id: str, records: List[Dict[str, Any]]) -> int:
    """Save report snapshot files registry to report_snapshot table."""
    if not records:
        return 0
    conn = get_db_connection()
    try:
        conn.executemany(
            """
            INSERT OR REPLACE INTO report_snapshot
            (snapshot_id, html_report_path, pdf_report_path, generation_timestamp, status)
            VALUES (:snapshot_id, :html_report_path, :pdf_report_path, :generation_timestamp, :status)
            """,
            [{**r, "snapshot_id": snapshot_id} for r in records]
        )
        conn.commit()
        return len(records)
    finally:
        conn.close()


def get_indicator_snapshot(snapshot_id: str, symbol: str) -> Optional[Dict[str, Any]]:
    """Query a single indicator snapshot from database."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM indicator_snapshot WHERE snapshot_id = ? AND UPPER(symbol) = UPPER(?)",
            (snapshot_id, symbol)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_feature_snapshot(snapshot_id: str, symbol: str) -> Optional[Dict[str, Any]]:
    """Query a single feature snapshot from database."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM feature_snapshot WHERE snapshot_id = ? AND UPPER(symbol) = UPPER(?)",
            (snapshot_id, symbol)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_score_snapshot(snapshot_id: str, symbol: str) -> Optional[Dict[str, Any]]:
    """Query a single score snapshot from database."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM score_snapshot WHERE snapshot_id = ? AND UPPER(symbol) = UPPER(?)",
            (snapshot_id, symbol)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_explainability_snapshot(snapshot_id: str, symbol: str) -> Optional[Dict[str, Any]]:
    """Query explainability details from database."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM explainability_snapshot WHERE snapshot_id = ? AND UPPER(symbol) = UPPER(?)",
            (snapshot_id, symbol)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

"""
db.py — SQLite Connection and Schema Initialization.
Manages the application's local SQLite database.
"""

import os
import sqlite3
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Locate database inside backend data directory
DB_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data")
)
DB_PATH = os.path.join(DB_DIR, "pms_engine.db")


def get_db_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Security Master Seed Data ──
# Nifty 50 + 67 additional popular Indian stocks = 117 total
SECURITY_MASTER_SEED = [
    # ── Nifty 50 ──
    ("RELIANCE.NS", "Reliance Industries Ltd", "Energy", "Oil & Gas Refining"),
    ("TCS.NS", "Tata Consultancy Services Ltd", "Technology", "IT Services"),
    ("HDFCBANK.NS", "HDFC Bank Ltd", "Financial Services", "Private Banks"),
    ("INFY.NS", "Infosys Ltd", "Technology", "IT Services"),
    ("ICICIBANK.NS", "ICICI Bank Ltd", "Financial Services", "Private Banks"),
    ("HINDUNILVR.NS", "Hindustan Unilever Ltd", "Consumer Staples", "FMCG"),
    ("ITC.NS", "ITC Ltd", "Consumer Staples", "FMCG"),
    ("SBIN.NS", "State Bank of India", "Financial Services", "Public Banks"),
    ("BHARTIARTL.NS", "Bharti Airtel Ltd", "Communication", "Telecom"),
    ("KOTAKBANK.NS", "Kotak Mahindra Bank Ltd", "Financial Services", "Private Banks"),
    ("LT.NS", "Larsen & Toubro Ltd", "Industrials", "Construction & Engineering"),
    ("AXISBANK.NS", "Axis Bank Ltd", "Financial Services", "Private Banks"),
    ("ASIANPAINT.NS", "Asian Paints Ltd", "Consumer Discretionary", "Paints"),
    ("MARUTI.NS", "Maruti Suzuki India Ltd", "Consumer Discretionary", "Automobiles"),
    ("TITAN.NS", "Titan Company Ltd", "Consumer Discretionary", "Jewellery"),
    ("SUNPHARMA.NS", "Sun Pharmaceutical Industries Ltd", "Healthcare", "Pharmaceuticals"),
    ("BAJFINANCE.NS", "Bajaj Finance Ltd", "Financial Services", "NBFCs"),
    ("WIPRO.NS", "Wipro Ltd", "Technology", "IT Services"),
    ("ULTRACEMCO.NS", "UltraTech Cement Ltd", "Materials", "Cement"),
    ("HCLTECH.NS", "HCL Technologies Ltd", "Technology", "IT Services"),
    ("NESTLEIND.NS", "Nestle India Ltd", "Consumer Staples", "FMCG"),
    ("POWERGRID.NS", "Power Grid Corp of India Ltd", "Utilities", "Power Transmission"),
    ("NTPC.NS", "NTPC Ltd", "Utilities", "Power Generation"),
    ("TECHM.NS", "Tech Mahindra Ltd", "Technology", "IT Services"),
    ("M&M.NS", "Mahindra & Mahindra Ltd", "Consumer Discretionary", "Automobiles"),
    ("ONGC.NS", "Oil & Natural Gas Corp Ltd", "Energy", "Oil & Gas Exploration"),
    ("TATAMOTORS.NS", "Tata Motors Ltd", "Consumer Discretionary", "Automobiles"),
    ("JSWSTEEL.NS", "JSW Steel Ltd", "Materials", "Steel"),
    ("ADANIENT.NS", "Adani Enterprises Ltd", "Industrials", "Conglomerate"),
    ("ADANIPORTS.NS", "Adani Ports & SEZ Ltd", "Industrials", "Port Services"),
    ("BAJAJFINSV.NS", "Bajaj Finserv Ltd", "Financial Services", "Holding Company"),
    ("TATASTEEL.NS", "Tata Steel Ltd", "Materials", "Steel"),
    ("COALINDIA.NS", "Coal India Ltd", "Energy", "Coal Mining"),
    ("HINDALCO.NS", "Hindalco Industries Ltd", "Materials", "Aluminium"),
    ("GRASIM.NS", "Grasim Industries Ltd", "Materials", "Cement & Textiles"),
    ("CIPLA.NS", "Cipla Ltd", "Healthcare", "Pharmaceuticals"),
    ("DIVISLAB.NS", "Divi's Laboratories Ltd", "Healthcare", "Pharmaceuticals"),
    ("DRREDDY.NS", "Dr. Reddy's Laboratories Ltd", "Healthcare", "Pharmaceuticals"),
    ("EICHERMOT.NS", "Eicher Motors Ltd", "Consumer Discretionary", "Automobiles"),
    ("APOLLOHOSP.NS", "Apollo Hospitals Enterprise Ltd", "Healthcare", "Hospitals"),
    ("SBILIFE.NS", "SBI Life Insurance Co Ltd", "Financial Services", "Insurance"),
    ("BRITANNIA.NS", "Britannia Industries Ltd", "Consumer Staples", "FMCG"),
    ("INDUSINDBK.NS", "IndusInd Bank Ltd", "Financial Services", "Private Banks"),
    ("HEROMOTOCO.NS", "Hero MotoCorp Ltd", "Consumer Discretionary", "Automobiles"),
    ("BPCL.NS", "Bharat Petroleum Corp Ltd", "Energy", "Oil & Gas Refining"),
    ("TATACONSUM.NS", "Tata Consumer Products Ltd", "Consumer Staples", "FMCG"),
    ("BAJAJ-AUTO.NS", "Bajaj Auto Ltd", "Consumer Discretionary", "Automobiles"),
    ("SHRIRAMFIN.NS", "Shriram Finance Ltd", "Financial Services", "NBFCs"),
    ("HDFCLIFE.NS", "HDFC Life Insurance Co Ltd", "Financial Services", "Insurance"),
    ("LTIM.NS", "LTIMindtree Ltd", "Technology", "IT Services"),

    # ── Additional Popular Indian Stocks ──
    ("ZOMATO.NS", "Zomato Ltd", "Consumer Discretionary", "Internet & E-Commerce"),
    ("ONE97COMM.NS", "Paytm (One97 Communications Ltd)", "Technology", "Fintech"),
    ("FSN.NS", "Nykaa (FSN E-Commerce Ventures Ltd)", "Consumer Discretionary", "E-Commerce"),
    ("DMART.NS", "Avenue Supermarts Ltd (DMart)", "Consumer Staples", "Retail"),
    ("HAL.NS", "Hindustan Aeronautics Ltd", "Industrials", "Aerospace & Defence"),
    ("BEL.NS", "Bharat Electronics Ltd", "Industrials", "Defence Electronics"),
    ("IRCTC.NS", "Indian Railway Catering & Tourism Corp", "Industrials", "Travel & Tourism"),
    ("JIOFIN.NS", "Jio Financial Services Ltd", "Financial Services", "NBFCs"),
    ("SUZLON.NS", "Suzlon Energy Ltd", "Utilities", "Renewable Energy"),
    ("LICI.NS", "Life Insurance Corp of India", "Financial Services", "Insurance"),
    ("MRF.NS", "MRF Ltd", "Consumer Discretionary", "Tyres"),
    ("PIDILITIND.NS", "Pidilite Industries Ltd", "Materials", "Adhesives & Chemicals"),
    ("SIEMENS.NS", "Siemens Ltd", "Industrials", "Electrical Equipment"),
    ("ABB.NS", "ABB India Ltd", "Industrials", "Electrical Equipment"),
    ("HAVELLS.NS", "Havells India Ltd", "Consumer Discretionary", "Electrical Equipment"),
    ("VOLTAS.NS", "Voltas Ltd", "Consumer Discretionary", "Consumer Electronics"),
    ("TRENT.NS", "Trent Ltd", "Consumer Discretionary", "Retail"),
    ("PAGEIND.NS", "Page Industries Ltd", "Consumer Discretionary", "Textiles"),
    ("GODREJCP.NS", "Godrej Consumer Products Ltd", "Consumer Staples", "FMCG"),
    ("MARICO.NS", "Marico Ltd", "Consumer Staples", "FMCG"),
    ("COLPAL.NS", "Colgate-Palmolive (India) Ltd", "Consumer Staples", "FMCG"),
    ("DABUR.NS", "Dabur India Ltd", "Consumer Staples", "FMCG"),
    ("BIOCON.NS", "Biocon Ltd", "Healthcare", "Biotechnology"),
    ("LUPIN.NS", "Lupin Ltd", "Healthcare", "Pharmaceuticals"),
    ("TORNTPHARM.NS", "Torrent Pharmaceuticals Ltd", "Healthcare", "Pharmaceuticals"),
    ("AUROPHARMA.NS", "Aurobindo Pharma Ltd", "Healthcare", "Pharmaceuticals"),
    ("PERSISTENT.NS", "Persistent Systems Ltd", "Technology", "IT Services"),
    ("COFORGE.NS", "Coforge Ltd", "Technology", "IT Services"),
    ("MPHASIS.NS", "Mphasis Ltd", "Technology", "IT Services"),
    ("LTTS.NS", "L&T Technology Services Ltd", "Technology", "IT Services"),
    ("INDIGO.NS", "InterGlobe Aviation Ltd (IndiGo)", "Industrials", "Airlines"),
    ("TATAELXSI.NS", "Tata Elxsi Ltd", "Technology", "IT Services"),
    ("POLYCAB.NS", "Polycab India Ltd", "Industrials", "Cables & Wires"),
    ("CUMMINSIND.NS", "Cummins India Ltd", "Industrials", "Industrial Engines"),
    ("BALKRISIND.NS", "Balkrishna Industries Ltd", "Consumer Discretionary", "Tyres"),
    ("PIIND.NS", "PI Industries Ltd", "Materials", "Agrochemicals"),
    ("SOLARINDS.NS", "Solar Industries India Ltd", "Industrials", "Explosives"),
    ("TATAPOWER.NS", "Tata Power Co Ltd", "Utilities", "Power Generation"),
    ("ADANIPOWER.NS", "Adani Power Ltd", "Utilities", "Power Generation"),
    ("ADANIGREEN.NS", "Adani Green Energy Ltd", "Utilities", "Renewable Energy"),
    ("ADANIENSOL.NS", "Adani Energy Solutions Ltd", "Utilities", "Power Transmission"),
    ("VEDL.NS", "Vedanta Ltd", "Materials", "Mining & Metals"),
    ("JINDALSTEL.NS", "Jindal Steel & Power Ltd", "Materials", "Steel"),
    ("SAIL.NS", "Steel Authority of India Ltd", "Materials", "Steel"),
    ("NMDC.NS", "NMDC Ltd", "Materials", "Mining"),
    ("IRFC.NS", "Indian Railway Finance Corp Ltd", "Financial Services", "NBFCs"),
    ("PNB.NS", "Punjab National Bank", "Financial Services", "Public Banks"),
    ("BANKBARODA.NS", "Bank of Baroda", "Financial Services", "Public Banks"),
    ("CANBK.NS", "Canara Bank", "Financial Services", "Public Banks"),
    ("IDFCFIRSTB.NS", "IDFC First Bank Ltd", "Financial Services", "Private Banks"),
    ("FEDERALBNK.NS", "Federal Bank Ltd", "Financial Services", "Private Banks"),
    ("BANDHANBNK.NS", "Bandhan Bank Ltd", "Financial Services", "Private Banks"),
    ("YESBANK.NS", "Yes Bank Ltd", "Financial Services", "Private Banks"),
    ("MANAPPURAM.NS", "Manappuram Finance Ltd", "Financial Services", "NBFCs"),
    ("MUTHOOTFIN.NS", "Muthoot Finance Ltd", "Financial Services", "NBFCs"),
    ("SRF.NS", "SRF Ltd", "Materials", "Chemicals"),
    ("UPL.NS", "UPL Ltd", "Materials", "Agrochemicals"),
    ("DEEPAKNTR.NS", "Deepak Nitrite Ltd", "Materials", "Chemicals"),
    ("ATUL.NS", "Atul Ltd", "Materials", "Chemicals"),
    ("ASTRAL.NS", "Astral Ltd", "Industrials", "Pipes & Fittings"),
    ("CROMPTON.NS", "Crompton Greaves Consumer Electricals", "Consumer Discretionary", "Electrical Equipment"),
    ("WHIRLPOOL.NS", "Whirlpool of India Ltd", "Consumer Discretionary", "Consumer Electronics"),
    ("BATAINDIA.NS", "Bata India Ltd", "Consumer Discretionary", "Footwear"),
    ("VBL.NS", "Varun Beverages Ltd", "Consumer Staples", "Beverages"),
    ("CONCOR.NS", "Container Corp of India Ltd", "Industrials", "Logistics"),
    ("DLF.NS", "DLF Ltd", "Real Estate", "Real Estate Development"),
    ("GODREJPROP.NS", "Godrej Properties Ltd", "Real Estate", "Real Estate Development"),
    ("OBEROIRLTY.NS", "Oberoi Realty Ltd", "Real Estate", "Real Estate Development"),
    ("PRESTIGE.NS", "Prestige Estates Projects Ltd", "Real Estate", "Real Estate Development"),
]


def init_db() -> None:
    """Create database tables if they do not exist."""
    # Ensure data directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    
    logger.info(f"Initializing SQLite database at: {DB_PATH}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Table 1: my_stocks (user research universe)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS my_stocks (
                symbol TEXT PRIMARY KEY,
                added_at TEXT NOT NULL
            )
        """)
        
        # Table 2: analysis_history (user-driven analysis runs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                analysis_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                rating TEXT NOT NULL,
                confidence REAL NOT NULL,
                composite_score REAL NOT NULL,
                analyzed_at TEXT NOT NULL
            )
        """)
        
        # Table 3: security_master (expanded stock universe)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_master (
                symbol TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                sector TEXT DEFAULT '—',
                industry TEXT DEFAULT '—'
            )
        """)
        
        # Table 4: report_history (Phase 12C Research Reports)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS report_history (
                report_id TEXT PRIMARY KEY,
                report_type TEXT NOT NULL,
                symbol TEXT,
                generated_at TEXT NOT NULL,
                analysis_id TEXT,
                file_path TEXT NOT NULL,
                report_version TEXT DEFAULT '1.0'
            )
        """)
        
        # Seed the security master with 117 Indian stocks
        cursor.executemany(
            "INSERT OR IGNORE INTO security_master (symbol, company_name, sector, industry) VALUES (?, ?, ?, ?)",
            SECURITY_MASTER_SEED
        )

        # ── Phase 12 Quant Research Laboratory Tables ──────────────────────

        # Table 5: lab_experiments — master experiment registry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lab_experiments (
                experiment_id        TEXT PRIMARY KEY,
                lab_module           TEXT NOT NULL,
                name                 TEXT NOT NULL,
                symbol               TEXT,
                params_json          TEXT,
                version              INTEGER DEFAULT 1,
                status               TEXT DEFAULT 'pending',
                started_at           TEXT,
                completed_at         TEXT,
                error_msg            TEXT,
                reproducibility_seed INTEGER DEFAULT 42
            )
        """)

        # Table 6: lab_metrics — key-value metric store (many per experiment)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lab_metrics (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                metric_name   TEXT NOT NULL,
                metric_value  REAL,
                metric_str    TEXT,
                FOREIGN KEY (experiment_id) REFERENCES lab_experiments(experiment_id)
            )
        """)

        # Table 7: lab_charts — JSON chart data blobs (one per chart type per experiment)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lab_charts (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id    TEXT NOT NULL,
                chart_type       TEXT NOT NULL,
                chart_data_json  TEXT NOT NULL,
                FOREIGN KEY (experiment_id) REFERENCES lab_experiments(experiment_id)
            )
        """)

        # Table 8: lab_rec_audit — recommendation audit records (one per rec × horizon)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lab_rec_audit (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id     TEXT NOT NULL,
                symbol          TEXT NOT NULL,
                rating          TEXT NOT NULL,
                composite_score REAL,
                analyzed_at     TEXT NOT NULL,
                horizon_days    INTEGER NOT NULL,
                forward_return  REAL,
                validated       INTEGER,
                validated_at    TEXT,
                UNIQUE(analysis_id, horizon_days)
            )
        """)

        # Table 9: lab_reports — lab-specific generated reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lab_reports (
                report_id     TEXT PRIMARY KEY,
                experiment_id TEXT,
                report_type   TEXT NOT NULL,
                generated_at  TEXT NOT NULL,
                html_path     TEXT NOT NULL,
                pdf_path      TEXT
            )
        """)

        # Table 10: lab_weight_snapshots — composite weight optimization snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lab_weight_snapshots (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                w_technical   REAL,
                w_ml          REAL,
                w_gru         REAL,
                w_reliability REAL,
                target_metric TEXT,
                metric_value  REAL,
                recorded_at   TEXT
            )
        """)

        # Alter table statements to add incremental fields for versioning and pipeline state
        for col_def in [
            ("engine_version", "TEXT"),
            ("dataset_version", "TEXT"),
            ("model_version", "TEXT"),
            ("indicator_version", "TEXT"),
            ("pipeline_stage", "TEXT DEFAULT 'Idea'"),
            ("is_paused", "INTEGER DEFAULT 0")
        ]:
            try:
                cursor.execute(f"ALTER TABLE lab_experiments ADD COLUMN {col_def[0]} {col_def[1]}")
            except sqlite3.OperationalError:
                pass  # column already exists

        # Table 11: lab_drift_alerts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lab_drift_alerts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type    TEXT NOT NULL,
                metric_name   TEXT NOT NULL,
                threshold     REAL,
                current_value REAL,
                message       TEXT,
                recorded_at   TEXT
            )
        """)

        conn.commit()

        # Ensure lab reports directory exists
        lab_reports_dir = os.path.join(DB_DIR, "reports", "lab")
        os.makedirs(lab_reports_dir, exist_ok=True)

        # Log how many stocks are in the security master
        count = cursor.execute("SELECT COUNT(*) FROM security_master").fetchone()[0]
        logger.info(f"Database tables initialized successfully. Security Master: {count} stocks. Lab tables: ready.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise e
    finally:
        conn.close()


# ── Security Master Query Functions ──

def search_security_master(query: str) -> List[Dict[str, Any]]:
    """Search security master by symbol or company name (case-insensitive LIKE)."""
    conn = get_db_connection()
    try:
        term = f"%{query.strip()}%"
        rows = conn.execute(
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
        # Try exact match first, then with .NS suffix
        sym = symbol.strip().upper()
        row = conn.execute(
            "SELECT 1 FROM security_master WHERE UPPER(symbol) = ?",
            (sym,)
        ).fetchone()
        if row:
            return True
        # Try with .NS suffix
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
        # Try with .NS suffix
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
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO report_history 
            (report_id, report_type, symbol, generated_at, analysis_id, file_path, report_version) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (report_id, report_type, symbol, generated_at, analysis_id, file_path, report_version)
        )
        conn.commit()
        logger.info(f"Recorded report {report_id} of type {report_type} in history")
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
            "SELECT * FROM report_history ORDER BY datetime(generated_at) DESC, generated_at DESC"
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
                ORDER BY datetime(generated_at) DESC, generated_at DESC LIMIT 1
                """,
                (report_type, symbol.upper())
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT * FROM report_history 
                WHERE report_type = ? 
                ORDER BY datetime(generated_at) DESC, generated_at DESC LIMIT 1
                """,
                (report_type,)
            ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

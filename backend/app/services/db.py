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

        # ── Phase 13 Daily Research snapshot & publishing platform tables ────

        # Table 12: snapshots (Master snapshot registry)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id           TEXT PRIMARY KEY,
                snapshot_date         TEXT NOT NULL,
                market_date           TEXT NOT NULL,
                generated_at          TEXT NOT NULL,
                is_official           INTEGER DEFAULT 1,
                status                TEXT DEFAULT 'generating',
                stocks_processed      INTEGER DEFAULT 0,
                stocks_failed         INTEGER DEFAULT 0,
                universe_version      TEXT,
                engine_version        TEXT,
                indicator_version     TEXT,
                scoring_version       TEXT,
                ml_model_version      TEXT,
                feature_version       TEXT,
                software_build        TEXT,
                pipeline_started_at   TEXT,
                pipeline_ended_at     TEXT,
                pipeline_duration_sec REAL,
                validation_passed     INTEGER DEFAULT 0,
                validation_score      REAL,
                published_at          TEXT,
                notes                 TEXT
            )
        """)

        # Table 13: snapshot_stock (Per-stock price + scores + rating)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshot_stock (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id        TEXT NOT NULL,
                symbol             TEXT NOT NULL,
                company_name       TEXT,
                sector             TEXT,
                industry           TEXT,
                open               REAL,
                high               REAL,
                low                REAL,
                close              REAL,
                volume             INTEGER,
                prev_close         REAL,
                daily_chg_pct      REAL,
                daily_chg_amt      REAL,
                week52_high        REAL,
                week52_low         REAL,
                technical_score    REAL,
                ml_score           REAL,
                gru_score          REAL,
                risk_score         REAL,
                momentum_score     REAL,
                trend_score        REAL,
                confidence         REAL,
                composite_score    REAL,
                reliability_score  REAL,
                final_rating       TEXT,
                portfolio_eligible INTEGER,
                conviction_level   TEXT,
                rank               INTEGER,
                percentile         REAL,
                universe_position  TEXT,
                data_source        TEXT,
                download_status    TEXT,
                data_warnings      TEXT,
                UNIQUE(snapshot_id, symbol),
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
            )
        """)

        # Table 14: snapshot_indicator (Derived indicator values)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshot_indicator (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id   TEXT NOT NULL,
                symbol        TEXT NOT NULL,
                rsi_14        REAL,
                ema_20        REAL,
                ema_50        REAL,
                ema_200       REAL,
                macd          REAL,
                macd_signal   REAL,
                bb_upper      REAL,
                bb_lower      REAL,
                atr_14        REAL,
                stoch_k       REAL,
                adx_14        REAL,
                obv           REAL,
                vwap          REAL,
                above_ema20   INTEGER,
                above_ema50   INTEGER,
                above_ema200  INTEGER,
                near_52w_high INTEGER,
                near_52w_low  INTEGER,
                UNIQUE(snapshot_id, symbol),
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
            )
        """)

        # Table 15: snapshot_score (Attributed score weights & details)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshot_score (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id          TEXT NOT NULL,
                symbol               TEXT NOT NULL,
                trend_component      REAL,
                momentum_component   REAL,
                volatility_component REAL,
                volume_component     REAL,
                lgbm_signal          REAL,
                rf_signal            REAL,
                xgb_signal           REAL,
                gru_hold             REAL,
                gru_long             REAL,
                gru_short            REAL,
                return_score         REAL,
                primary_driver       TEXT,
                secondary_driver     TEXT,
                w_technical          REAL,
                w_ml                 REAL,
                w_gru                REAL,
                w_reliability        REAL,
                UNIQUE(snapshot_id, symbol),
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
            )
        """)

        # Table 16: snapshot_sector (Aggregated sector performance stats)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshot_sector (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id         TEXT NOT NULL,
                sector              TEXT NOT NULL,
                stock_count         INTEGER,
                avg_composite       REAL,
                avg_confidence      REAL,
                avg_technical       REAL,
                avg_momentum        REAL,
                avg_trend           REAL,
                avg_risk            REAL,
                strong_buy_count    INTEGER,
                buy_count           INTEGER,
                hold_count          INTEGER,
                sell_count          INTEGER,
                strong_sell_count   INTEGER,
                bullish_pct         REAL,
                bearish_pct         REAL,
                sector_rank         INTEGER,
                top_stock           TEXT,
                weakest_stock       TEXT,
                avg_daily_chg_pct   REAL,
                UNIQUE(snapshot_id, sector),
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
            )
        """)

        # Table 17: snapshot_market (Universe-wide breadth metrics)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshot_market (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id             TEXT NOT NULL UNIQUE,
                total_stocks            INTEGER,
                advancing_stocks        INTEGER,
                declining_stocks        INTEGER,
                unchanged_stocks        INTEGER,
                advance_decline_ratio   REAL,
                advance_volume          INTEGER,
                decline_volume          INTEGER,
                stocks_above_ema20      INTEGER,
                stocks_above_ema50      INTEGER,
                stocks_above_ema200     INTEGER,
                pct_above_ema20         REAL,
                pct_above_ema50         REAL,
                pct_above_ema200        REAL,
                week52_high_count       INTEGER,
                week52_low_count        INTEGER,
                avg_composite           REAL,
                avg_confidence          REAL,
                avg_rsi                 REAL,
                avg_momentum            REAL,
                avg_daily_chg_pct       REAL,
                bullish_pct             REAL,
                bearish_pct             REAL,
                market_regime           TEXT,
                strong_buy_count        INTEGER,
                buy_count               INTEGER,
                hold_count              INTEGER,
                sell_count              INTEGER,
                strong_sell_count       INTEGER,
                india_vix               REAL,
                pcr                     REAL,
                fii_activity            REAL,
                dii_activity            REAL,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
            )
        """)

        # Table 18: snapshot_watchlist (Automatic smart watchlist items)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshot_watchlist (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id    TEXT NOT NULL,
                watchlist_name TEXT NOT NULL,
                symbol         TEXT NOT NULL,
                rank_in_list   INTEGER,
                score_used     REAL,
                reason         TEXT,
                UNIQUE(snapshot_id, watchlist_name, symbol),
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
            )
        """)

        # Table 19: snapshot_change (Recommendation diff records)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshot_change (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id          TEXT NOT NULL,
                prev_snapshot_id     TEXT,
                symbol               TEXT NOT NULL,
                change_type          TEXT NOT NULL,
                prev_rating          TEXT,
                new_rating           TEXT,
                composite_diff       REAL,
                confidence_diff      REAL,
                technical_diff       REAL,
                ml_diff              REAL,
                momentum_diff        REAL,
                trend_diff           REAL,
                risk_diff            REAL,
                primary_driver       TEXT,
                secondary_driver     TEXT,
                is_significant       INTEGER,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
            )
        """)

        # Table 20: snapshot_report (Snapshot report files registry)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshot_report (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id    TEXT NOT NULL,
                report_type    TEXT NOT NULL,
                symbol         TEXT,
                html_path      TEXT,
                pdf_path       TEXT,
                generated_at   TEXT,
                file_size_kb   REAL,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
            )
        """)

        # Table 21: snapshot_validation (Quality validation rules results)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshot_validation (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id    TEXT NOT NULL,
                check_name     TEXT NOT NULL,
                status         TEXT,
                detail         TEXT,
                affected_count INTEGER,
                threshold      REAL,
                actual_value   REAL,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
            )
        """)

        # Table 22: snapshot_metadata (Detailed pipeline metrics & timings)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshot_metadata (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id     TEXT NOT NULL,
                stage_name      TEXT NOT NULL,
                stage_status    TEXT,
                started_at      TEXT,
                completed_at    TEXT,
                duration_sec    REAL,
                stocks_success  INTEGER,
                stocks_failed   INTEGER,
                warnings_count  INTEGER,
                errors_count    INTEGER,
                log_summary     TEXT,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
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


# ── Phase 13 Snapshot Helper Functions ─────────────────────────────────────

import uuid
import json


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
) -> str:
    """Create a new snapshot record and return its snapshot_id."""
    snapshot_id = str(uuid.uuid4())
    now = _now_ist()
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO snapshots
            (snapshot_id, snapshot_date, market_date, generated_at, is_official,
             status, universe_version, engine_version, pipeline_started_at)
            VALUES (?, ?, ?, ?, ?, 'generating', ?, ?, ?)
            """,
            (snapshot_id, snapshot_date, market_date, now,
             1 if is_official else 0, universe_version, engine_version, now)
        )
        conn.commit()
        logger.info(f"[Snapshot] Created snapshot {snapshot_id} for {snapshot_date}")
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
        # Try update first, then insert
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


# ── Snapshot Query Functions ─────────────────────────────────────────────────

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


import os
import sys
import sqlite3
import json
import csv
import logging
import pandas as pd
import requests

# Add backend directory to sys.path so we can import from app
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import yfinance as yf
from app.services.market_data_validator import MarketDataValidator

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s"
)
logger = logging.getLogger("market_verifier")

# Database Path
DB_PATH = os.path.abspath(os.path.join(backend_dir, "data", "pms_engine.db"))
CSV_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "market_verification_report.csv")
JSON_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "market_verification_report.json")

TICKERS = [
    "HCLTECH",
    "RELIANCE",
    "TCS",
    "INFY",
    "ICICIBANK",
    "HDFCBANK",
    "LT",
    "ITC",
    "SBIN",
    "BHARTIARTL"
]

def get_db_connection():
    if not os.path.exists(DB_PATH):
        logger.error(f"Database file not found at {DB_PATH}")
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_latest_db_prices():
    """Retrieve the latest prices stored in SQLite snapshot_stock."""
    conn = get_db_connection()
    if not conn:
        return {}
    
    prices = {}
    try:
        # Get latest official snapshot
        cursor = conn.cursor()
        cursor.execute("SELECT snapshot_id, snapshot_date FROM snapshots ORDER BY snapshot_date DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            logger.warning("No snapshots found in SQLite database.")
            return {}
        
        snapshot_id = row["snapshot_id"]
        logger.info(f"Latest database snapshot ID: {snapshot_id} (Date: {row['snapshot_date']})")
        
        cursor.execute("""
            SELECT symbol, open, high, low, close, volume, prev_close 
            FROM snapshot_stock 
            WHERE snapshot_id = ?
        """, (snapshot_id,))
        
        for r in cursor.fetchall():
            sym_clean = r["symbol"].replace(".NS", "").upper()
            prices[sym_clean] = {
                "Open": r["open"],
                "High": r["high"],
                "Low": r["low"],
                "Close": r["close"],
                "Volume": r["volume"],
                "PrevClose": r["prev_close"]
            }
    except Exception as e:
        logger.error(f"Error reading database: {e}")
    finally:
        conn.close()
    return prices

def fetch_yahoo_finance_web_price(symbol: str) -> float:
    """Fetch real-time price from Yahoo Finance Chart API representing Yahoo Finance Web."""
    try:
        ticker = f"{symbol}.NS"
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()
        data = res.json()
        meta = data['chart']['result'][0]['meta']
        return float(meta['regularMarketPrice'])
    except Exception as e:
        logger.warning(f"Failed to fetch Yahoo Web price for {symbol}: {e}")
        return 0.0

def main():
    logger.info("Executing PMS Engine Market Data Diagnostic & Validation run...")
    
    db_prices = fetch_latest_db_prices()
    
    comparison_records = []
    has_validation_failures = False
    
    for symbol in TICKERS:
        ticker_ns = f"{symbol}.NS"
        logger.info(f"Analyzing stock: {symbol} (yf: {ticker_ns})")
        
        # 1. Download fresh historical daily data
        try:
            df_dl = yf.download(ticker_ns, period="1mo", interval="1d", progress=False)
            if df_dl.empty:
                logger.error(f"yfinance returned empty dataframe for {ticker_ns}")
                comparison_records.append({
                    "Ticker": symbol,
                    "Provider": "yfinance",
                    "Latest_Close": 0.00,
                    "Latest_Date": "N/A",
                    "Volume": 0,
                    "Validation_Result": "FAILED",
                    "Issues_Found": "Empty download from yfinance"
                })
                has_validation_failures = True
                continue
                
            # Reset index so Date is a column
            df_dl = df_dl.reset_index()
            if isinstance(df_dl.columns, pd.MultiIndex):
                df_dl.columns = [col[0] for col in df_dl.columns]
                
            df_dl = df_dl.rename(columns={"Close": "Close", "Open": "Open", "High": "High", "Low": "Low", "Volume": "Volume"})
            df_dl["Date"] = pd.to_datetime(df_dl["Date"]).dt.strftime("%Y-%m-%d")
            
            # Select required columns
            df_clean = df_dl[["Date", "Open", "High", "Low", "Close", "Volume"]]
            
            # 2. Run dataset validation
            is_valid, validation_errors = MarketDataValidator.validate_historical_df(df_clean, symbol, "1M")
            validation_str = "PASSED" if is_valid else "FAILED"
            issues_str = "; ".join(validation_errors) if validation_errors else "None"
            
            if not is_valid:
                has_validation_failures = True
                
            last_row = df_clean.iloc[-1]
            latest_close = float(last_row["Close"])
            latest_date = str(last_row["Date"])
            volume = int(last_row["Volume"])
            
            comparison_records.append({
                "Ticker": symbol,
                "Provider": "yfinance",
                "Latest_Close": round(latest_close, 2),
                "Latest_Date": latest_date,
                "Volume": volume,
                "Validation_Result": validation_str,
                "Issues_Found": issues_str
            })
            
        except Exception as e:
            logger.error(f"Failed to fetch or validate yfinance data for {ticker_ns}: {e}")
            comparison_records.append({
                "Ticker": symbol,
                "Provider": "yfinance",
                "Latest_Close": 0.00,
                "Latest_Date": "N/A",
                "Volume": 0,
                "Validation_Result": "FAILED",
                "Issues_Found": str(e)
            })
            has_validation_failures = True
            continue
            
    # Write to CSV
    if comparison_records:
        keys = comparison_records[0].keys()
        with open(CSV_OUTPUT_PATH, 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(comparison_records)
        logger.info(f"Diagnostic report saved to CSV: {CSV_OUTPUT_PATH}")
        
        # Write to JSON
        with open(JSON_OUTPUT_PATH, 'w') as f:
            json.dump(comparison_records, f, indent=4)
        logger.info(f"Diagnostic report saved to JSON: {JSON_OUTPUT_PATH}")
        
        # Print Verification Report Table
        print("\n" + "="*95)
        print("                        MARKET DATA DIAGNOSTIC REPORT")
        print("="*95)
        print(f"{'Ticker':<12} | {'Provider':<10} | {'Latest Close':<12} | {'Latest Date':<12} | {'Volume':<12} | {'Result':<8} | {'Issues':<20}")
        print("-"*95)
        for r in comparison_records:
            print(f"{r['Ticker']:<12} | {r['Provider']:<10} | {r['Latest_Close']:<12.2f} | {r['Latest_Date']:<12} | {r['Volume']:<12} | {r['Validation_Result']:<8} | {r['Issues_Found'][:20]}")
        print("="*95 + "\n")
        
    if has_validation_failures:
        logger.error("One or more stocks failed data validation.")
        sys.exit(1)
    else:
        logger.info("All stocks passed data validation.")
        sys.exit(0)

if __name__ == "__main__":
    main()

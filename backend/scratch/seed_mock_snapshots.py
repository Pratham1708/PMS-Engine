import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.services import db

def main():
    print("Seeding mock snapshots for Phase 13C testing...")
    
    # Clean up existing test snapshots
    conn = db.get_db_connection()
    try:
        conn.execute("DELETE FROM snapshots WHERE snapshot_date IN ('2026-07-13', '2026-07-14')")
        conn.execute("DELETE FROM snapshot_stock WHERE snapshot_id IN (SELECT snapshot_id FROM snapshots WHERE snapshot_date IN ('2026-07-13', '2026-07-14'))")
        conn.execute("DELETE FROM snapshot_score WHERE snapshot_id IN (SELECT snapshot_id FROM snapshots WHERE snapshot_date IN ('2026-07-13', '2026-07-14'))")
        conn.execute("DELETE FROM snapshot_indicator WHERE snapshot_id IN (SELECT snapshot_id FROM snapshots WHERE snapshot_date IN ('2026-07-13', '2026-07-14'))")
        conn.execute("DELETE FROM snapshot_sector WHERE snapshot_id IN (SELECT snapshot_id FROM snapshots WHERE snapshot_date IN ('2026-07-13', '2026-07-14'))")
        conn.commit()
    finally:
        conn.close()

    # 1. Create baseline snapshot (2026-07-13)
    sid1 = db.create_snapshot("2026-07-13", "2026-07-13", is_official=True)
    
    # 2. Create comparison snapshot (2026-07-14)
    sid2 = db.create_snapshot("2026-07-14", "2026-07-14", is_official=True)
    
    # Mock data specs
    # TCS: BUY (72) -> STRONG BUY (85)
    # INFY: BUY (68) -> HOLD (52)
    # RELIANCE: HOLD (48) -> HOLD (49)
    # HDFCBANK: SELL (28) -> BUY (62)
    # ICICIBANK: BUY (65) -> SELL (31)
    
    stocks1 = [
        {"symbol": "TCS.NS", "company_name": "Tata Consultancy Services", "sector": "Technology", "industry": "IT Services", "close": 3500.0, "volume": 100000, "technical_score": 70.0, "momentum_score": 75.0, "trend_score": 68.0, "risk_score": 25.0, "ml_score": 65.0, "gru_score": 60.0, "reliability_score": 75.0, "confidence": 75.0, "composite_score": 72.0, "final_rating": "BUY", "rank": 10},
        {"symbol": "INFY.NS", "company_name": "Infosys Ltd", "sector": "Technology", "industry": "IT Services", "close": 1500.0, "volume": 120000, "technical_score": 68.0, "momentum_score": 70.0, "trend_score": 65.0, "risk_score": 30.0, "ml_score": 62.0, "gru_score": 58.0, "reliability_score": 70.0, "confidence": 70.0, "composite_score": 68.0, "final_rating": "BUY", "rank": 12},
        {"symbol": "RELIANCE.NS", "company_name": "Reliance Industries", "sector": "Energy", "industry": "Refining", "close": 2400.0, "volume": 200000, "technical_score": 45.0, "momentum_score": 48.0, "trend_score": 46.0, "risk_score": 50.0, "ml_score": 49.0, "gru_score": 45.0, "reliability_score": 50.0, "confidence": 50.0, "composite_score": 48.0, "final_rating": "HOLD", "rank": 25},
        {"symbol": "HDFCBANK.NS", "company_name": "HDFC Bank Ltd", "sector": "Financial Services", "industry": "Private Banks", "close": 1600.0, "volume": 150000, "technical_score": 25.0, "momentum_score": 28.0, "trend_score": 26.0, "risk_score": 70.0, "ml_score": 30.0, "gru_score": 28.0, "reliability_score": 35.0, "confidence": 30.0, "composite_score": 28.0, "final_rating": "SELL", "rank": 40},
        {"symbol": "ICICIBANK.NS", "company_name": "ICICI Bank Ltd", "sector": "Financial Services", "industry": "Private Banks", "close": 900.0, "volume": 180000, "technical_score": 64.0, "momentum_score": 66.0, "trend_score": 62.0, "risk_score": 35.0, "ml_score": 60.0, "gru_score": 55.0, "reliability_score": 65.0, "confidence": 65.0, "composite_score": 65.0, "final_rating": "BUY", "rank": 15}
    ]
    
    stocks2 = [
        {"symbol": "TCS.NS", "company_name": "Tata Consultancy Services", "sector": "Technology", "industry": "IT Services", "close": 3600.0, "volume": 110000, "technical_score": 85.0, "momentum_score": 88.0, "trend_score": 82.0, "risk_score": 15.0, "ml_score": 80.0, "gru_score": 75.0, "reliability_score": 85.0, "confidence": 85.0, "composite_score": 85.0, "final_rating": "STRONG BUY", "rank": 2},
        {"symbol": "INFY.NS", "company_name": "Infosys Ltd", "sector": "Technology", "industry": "IT Services", "close": 1420.0, "volume": 130000, "technical_score": 50.0, "momentum_score": 52.0, "trend_score": 48.0, "risk_score": 45.0, "ml_score": 51.0, "gru_score": 45.0, "reliability_score": 55.0, "confidence": 55.0, "composite_score": 52.0, "final_rating": "HOLD", "rank": 22},
        {"symbol": "RELIANCE.NS", "company_name": "Reliance Industries", "sector": "Energy", "industry": "Refining", "close": 2420.0, "volume": 210000, "technical_score": 46.0, "momentum_score": 49.0, "trend_score": 47.0, "risk_score": 49.0, "ml_score": 50.0, "gru_score": 46.0, "reliability_score": 51.0, "confidence": 51.0, "composite_score": 49.0, "final_rating": "HOLD", "rank": 24},
        {"symbol": "HDFCBANK.NS", "company_name": "HDFC Bank Ltd", "sector": "Financial Services", "industry": "Private Banks", "close": 1750.0, "volume": 160000, "technical_score": 60.0, "momentum_score": 62.0, "trend_score": 58.0, "risk_score": 38.0, "ml_score": 58.0, "gru_score": 52.0, "reliability_score": 60.0, "confidence": 62.0, "composite_score": 62.0, "final_rating": "BUY", "rank": 11},
        {"symbol": "ICICIBANK.NS", "company_name": "ICICI Bank Ltd", "sector": "Financial Services", "industry": "Private Banks", "close": 820.0, "volume": 190000, "technical_score": 30.0, "momentum_score": 32.0, "trend_score": 28.0, "risk_score": 68.0, "ml_score": 32.0, "gru_score": 25.0, "reliability_score": 34.0, "confidence": 32.0, "composite_score": 31.0, "final_rating": "SELL", "rank": 35}
    ]
    
    # Save stocks
    db.save_snapshot_stocks(sid1, stocks1)
    db.save_snapshot_stocks(sid2, stocks2)
    
    # Save scores with return_score
    scores1 = [
        {"symbol": s["symbol"], "return_score": s["composite_score"] * 0.15, "w_technical": 0.40, "w_ml": 0.35, "w_gru": 0.15, "w_reliability": 0.10} for s in stocks1
    ]
    scores2 = [
        {"symbol": s["symbol"], "return_score": s["composite_score"] * 0.15, "w_technical": 0.40, "w_ml": 0.35, "w_gru": 0.15, "w_reliability": 0.10} for s in stocks2
    ]
    db.save_snapshot_scores(sid1, scores1)
    db.save_snapshot_scores(sid2, scores2)
    
    # Save indicators
    indicators1 = [
        {"symbol": "TCS.NS", "rsi_14": 48.0, "above_ema20": 0, "above_ema50": 0, "above_ema200": 0},
        {"symbol": "INFY.NS", "rsi_14": 52.0, "above_ema20": 1, "above_ema50": 1, "above_ema200": 1},
        {"symbol": "RELIANCE.NS", "rsi_14": 46.0, "above_ema20": 0, "above_ema50": 0, "above_ema200": 0},
        {"symbol": "HDFCBANK.NS", "rsi_14": 30.0, "above_ema20": 0, "above_ema50": 0, "above_ema200": 0},
        {"symbol": "ICICIBANK.NS", "rsi_14": 62.0, "above_ema20": 1, "above_ema50": 1, "above_ema200": 1}
    ]
    indicators2 = [
        {"symbol": "TCS.NS", "rsi_14": 65.0, "above_ema20": 1, "above_ema50": 1, "above_ema200": 1},
        {"symbol": "INFY.NS", "rsi_14": 42.0, "above_ema20": 0, "above_ema50": 0, "above_ema200": 0},
        {"symbol": "RELIANCE.NS", "rsi_14": 47.0, "above_ema20": 0, "above_ema50": 0, "above_ema200": 0},
        {"symbol": "HDFCBANK.NS", "rsi_14": 61.0, "above_ema20": 1, "above_ema50": 1, "above_ema200": 1},
        {"symbol": "ICICIBANK.NS", "rsi_14": 31.0, "above_ema20": 0, "above_ema50": 0, "above_ema200": 0}
    ]
    db.save_snapshot_indicators(sid1, indicators1)
    db.save_snapshot_indicators(sid2, indicators2)
    
    # Save sector details
    def make_sec_rec(sec, count, comp, rank):
        return {
            "sector": sec, "stock_count": count, "avg_composite": comp, "sector_rank": rank,
            "avg_confidence": 70.0, "avg_technical": 50.0, "avg_momentum": 50.0, "avg_trend": 50.0,
            "avg_risk": 30.0, "strong_buy_count": 0, "buy_count": 1, "hold_count": 0,
            "sell_count": 0, "strong_sell_count": 0, "bullish_pct": 50.0, "bearish_pct": 50.0,
            "top_stock": None, "weakest_stock": None, "avg_daily_chg_pct": 0.0
        }

    sectors1 = [
        make_sec_rec("Technology", 2, 70.0, 1),
        make_sec_rec("Financial Services", 2, 46.5, 2),
        make_sec_rec("Energy", 1, 48.0, 3)
    ]
    sectors2 = [
        make_sec_rec("Technology", 2, 68.5, 1),
        make_sec_rec("Financial Services", 2, 46.5, 2),
        make_sec_rec("Energy", 1, 49.0, 3)
    ]
    db.save_snapshot_sector(sid1, sectors1)
    db.save_snapshot_sector(sid2, sectors2)

    # Set to completed
    db.update_snapshot_status(sid1, "completed", 5, 0, True, 90.0)
    db.update_snapshot_status(sid2, "completed", 5, 0, True, 95.0)
    
    db.publish_snapshot(sid1)
    db.publish_snapshot(sid2)

    print(f"Mock Snapshots Seeding Complete!")
    print(f"Snapshot A (2026-07-13): ID={sid1}")
    print(f"Snapshot B (2026-07-14): ID={sid2}")

if __name__ == "__main__":
    main()

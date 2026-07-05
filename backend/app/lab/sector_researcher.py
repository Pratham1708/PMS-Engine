"""
sector_researcher.py — Sector analysis for the Quant Research Laboratory.

Reuses:
  - security_master (existing DB table) for sector/industry groupings
  - data_loader.get_df() for current scores
  - historical_data_service for price returns

Provides:
  - Sector score distribution (average scores per sector)
  - Sector rotation signal (momentum-based)
  - Sector correlation matrix (price returns)
  - Top picks per sector
  - Sector performance ranking
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from app.data.loader import data_loader
from app.services.historical_data_service import historical_data_service
from app.services.db import get_db_connection

logger = logging.getLogger(__name__)

SCORE_COLUMNS = ["TechnicalScore", "MLScore", "GRUScore", "ReliabilityScore", "CompositeScoreV2"]


# ─────────────────────────────────────────────────────────────────────────────
# SECTOR MAP BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def _build_sector_map() -> Dict[str, str]:
    """Return {symbol → sector} from security_master table."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT symbol, sector FROM security_master"
        ).fetchall()
        return {r["symbol"]: r["sector"] for r in rows}
    except Exception as e:
        logger.error(f"_build_sector_map: {e}")
        return {}
    finally:
        conn.close()


def _build_industry_map() -> Dict[str, str]:
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT symbol, industry FROM security_master"
        ).fetchall()
        return {r["symbol"]: r["industry"] for r in rows}
    except Exception:
        return {}
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# SECTOR SCORE ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def sector_score_analysis() -> Dict:
    """Average scores per sector + number of stocks + rating distribution."""
    df = data_loader.get_df()
    sector_map = _build_sector_map()
    industry_map = _build_industry_map()

    if df.empty:
        return {}

    df = df.copy()
    df["sector"]   = df["Symbol"].map(sector_map).fillna("Unknown")
    df["industry"] = df["Symbol"].map(industry_map).fillna("Unknown")

    for col in SCORE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Per-sector aggregation
    agg_cols = [c for c in SCORE_COLUMNS if c in df.columns]
    sector_stats = df.groupby("sector").agg(
        n_stocks=("Symbol", "count"),
        **{f"avg_{c}": (c, "mean") for c in agg_cols},
        **{f"top_{c}": (c, "max") for c in agg_cols},
    ).reset_index()

    # Rating distribution per sector
    if "FinalRating" in df.columns:
        rating_dist = df.groupby(["sector", "FinalRating"]).size().unstack(fill_value=0)
        rating_dict = rating_dist.to_dict(orient="index")
    else:
        rating_dict = {}

    # Top 3 stocks per sector
    top_picks = {}
    for sector, group in df.groupby("sector"):
        if "CompositeScoreV2" in df.columns:
            top = group.nlargest(3, "CompositeScoreV2")[["Symbol", "CompositeScoreV2", "FinalRating"] if "FinalRating" in df.columns else ["Symbol", "CompositeScoreV2"]]
            top_picks[sector] = top.to_dict(orient="records")
        else:
            top_picks[sector] = group["Symbol"].head(3).tolist()

    sectors_list = []
    for _, row in sector_stats.iterrows():
        sector = row["sector"]
        entry = {
            "sector": sector,
            "n_stocks": int(row["n_stocks"]),
            "top_picks": top_picks.get(sector, []),
            "rating_distribution": rating_dict.get(sector, {}),
        }
        for col in agg_cols:
            v = row.get(f"avg_{col}")
            entry[f"avg_{col}"] = round(float(v), 2) if pd.notna(v) else None
        sectors_list.append(entry)

    # Sort by avg_CompositeScoreV2 descending
    if "CompositeScoreV2" in agg_cols:
        sectors_list.sort(key=lambda x: x.get("avg_CompositeScoreV2") or -999, reverse=True)

    return {
        "sectors": sectors_list,
        "total_stocks": int(len(df)),
        "total_sectors": int(len(sectors_list)),
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECTOR RETURN PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────

def sector_return_performance(period: str = "1Y") -> Dict:
    """
    Compute average price return per sector for the given period.
    Returns sector ranking by return.
    """
    df = data_loader.get_df()
    sector_map = _build_sector_map()

    if df.empty:
        return {}

    symbols = df["Symbol"].tolist()
    sector_returns: Dict[str, List[float]] = {}

    for symbol in symbols:
        sector = sector_map.get(symbol, "Unknown")
        try:
            hist = historical_data_service.get_stock_history(symbol, period)
            if hist is None or hist.empty or len(hist) < 2:
                continue
            close = pd.to_numeric(hist["Close"], errors="coerce").dropna()
            if len(close) < 2:
                continue
            ret = float((close.iloc[-1] - close.iloc[0]) / close.iloc[0] * 100)
            sector_returns.setdefault(sector, []).append(ret)
        except Exception:
            pass

    result = []
    for sector, returns in sector_returns.items():
        if not returns:
            continue
        result.append({
            "sector": sector,
            "avg_return_pct": round(float(np.mean(returns)), 2),
            "median_return_pct": round(float(np.median(returns)), 2),
            "best_stock_return": round(float(max(returns)), 2),
            "worst_stock_return": round(float(min(returns)), 2),
            "n_stocks": len(returns),
            "positive_pct": round(float(sum(r > 0 for r in returns) / len(returns) * 100), 1),
        })

    result.sort(key=lambda x: x["avg_return_pct"], reverse=True)

    # Assign rank
    for i, entry in enumerate(result):
        entry["rank"] = i + 1

    return {"period": period, "sector_returns": result}


# ─────────────────────────────────────────────────────────────────────────────
# SECTOR CORRELATION MATRIX
# ─────────────────────────────────────────────────────────────────────────────

def sector_correlation_matrix(period: str = "1Y") -> Dict:
    """
    Compute pairwise sector return correlations using proxy single-stock per sector.
    """
    df = data_loader.get_df()
    sector_map = _build_sector_map()

    if df.empty:
        return {}

    df = df.copy()
    df["sector"] = df["Symbol"].map(sector_map).fillna("Unknown")

    # Pick one representative stock per sector (highest composite score)
    if "CompositeScoreV2" in df.columns:
        df["CompositeScoreV2"] = pd.to_numeric(df["CompositeScoreV2"], errors="coerce")
        reps = df.groupby("sector")["CompositeScoreV2"].idxmax()
        rep_symbols = {
            sector: df.loc[idx, "Symbol"]
            for sector, idx in reps.items()
            if not pd.isna(idx)
        }
    else:
        rep_symbols = df.groupby("sector").first()["Symbol"].to_dict()

    # Fetch prices
    price_data = {}
    for sector, symbol in rep_symbols.items():
        try:
            hist = historical_data_service.get_stock_history(symbol, period)
            if hist is None or hist.empty:
                continue
            hist["Date"] = pd.to_datetime(hist["Date"], errors="coerce")
            hist["Close"] = pd.to_numeric(hist["Close"], errors="coerce")
            hist = hist.dropna(subset=["Date", "Close"]).set_index("Date")["Close"]
            price_data[sector] = hist
        except Exception:
            pass

    if not price_data:
        return {"correlation": []}

    price_matrix = pd.DataFrame(price_data).ffill().dropna(how="all")
    returns_matrix = price_matrix.pct_change().dropna(how="all")

    corr = returns_matrix.corr()

    flat = []
    for a in corr.index:
        for b in corr.columns:
            v = corr.loc[a, b]
            flat.append({
                "sector_a": a,
                "sector_b": b,
                "correlation": round(float(v), 4) if not pd.isna(v) else None,
            })

    return {
        "correlation": flat,
        "sectors": list(corr.index),
        "period": period,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECTOR ROTATION SIGNAL
# ─────────────────────────────────────────────────────────────────────────────

def sector_rotation_signal() -> List[Dict]:
    """
    Compute 1M vs 3M momentum for each sector.
    Signal: 1M > 3M = accelerating (rotate IN); 1M < 3M = decelerating (rotate OUT).
    """
    score_data  = sector_score_analysis()
    return_1m   = sector_return_performance("1M")
    return_3m   = sector_return_performance("3M")

    ret_1m = {r["sector"]: r["avg_return_pct"] for r in return_1m.get("sector_returns", [])}
    ret_3m = {r["sector"]: r["avg_return_pct"] for r in return_3m.get("sector_returns", [])}

    all_sectors = set(ret_1m.keys()) | set(ret_3m.keys())
    result = []
    for sector in all_sectors:
        r1 = ret_1m.get(sector, 0)
        r3 = ret_3m.get(sector, 0)
        momentum = r1 - r3
        result.append({
            "sector": sector,
            "return_1m": round(r1, 2),
            "return_3m": round(r3, 2),
            "momentum_diff": round(momentum, 2),
            "signal": "ROTATE IN" if momentum > 1 else ("ROTATE OUT" if momentum < -1 else "NEUTRAL"),
        })

    result.sort(key=lambda x: x["momentum_diff"], reverse=True)
    return result

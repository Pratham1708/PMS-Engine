"""
pms_score_validator.py — Validates the complete PMS Engine scoring pipeline.

Reuses:
  - data_loader.get_df() for existing computed scores
  - historical_data_service for forward returns

Methodology: Information Coefficient (Spearman rank correlation) between
each sub-score and realized forward return at 1M, 3M, and 6M horizons.

This module does NOT modify any production scores.
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from app.data.loader import data_loader
from app.services.historical_data_service import historical_data_service

logger = logging.getLogger(__name__)

SCORE_COLUMNS = [
    "TechnicalScore",
    "MLScore",
    "GRUScore",
    "ReliabilityScore",
    "CompositeScoreV2",
    "Confidence",
]

VALIDATION_HORIZONS = ["1M", "3M", "6M"]

HORIZON_BARS = {"1M": 21, "3M": 63, "6M": 126}


# ─────────────────────────────────────────────────────────────────────────────
# FORWARD RETURN FETCHER
# ─────────────────────────────────────────────────────────────────────────────

def _get_forward_return(symbol: str, horizon: str) -> Optional[float]:
    """
    Fetch 1Y history and compute forward return over the most recent horizon period.
    Uses latest available data (the first bar is horizon-periods ago; last bar is today).
    """
    try:
        df = historical_data_service.get_stock_history(symbol, "1Y")
        if df is None or df.empty or len(df) < HORIZON_BARS[horizon]:
            return None
        close = pd.to_numeric(df["Close"], errors="coerce").dropna()
        n_bars = HORIZON_BARS[horizon]
        if len(close) < n_bars + 1:
            return None
        entry = float(close.iloc[-(n_bars + 1)])
        exit_p = float(close.iloc[-1])
        if entry <= 0:
            return None
        return (exit_p - entry) / entry * 100
    except Exception as e:
        logger.debug(f"_get_forward_return {symbol} {horizon}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# INFORMATION COEFFICIENT
# ─────────────────────────────────────────────────────────────────────────────

def _spearman_ic(scores: pd.Series, forward_returns: pd.Series) -> Optional[float]:
    """Spearman rank correlation between scores and forward returns."""
    valid = pd.concat([scores, forward_returns], axis=1).dropna()
    if len(valid) < 5:
        return None
    rank_scores = valid.iloc[:, 0].rank()
    rank_returns = valid.iloc[:, 1].rank()
    n = len(valid)
    d = rank_scores - rank_returns
    ic = 1 - 6 * (d ** 2).sum() / (n * (n ** 2 - 1))
    return float(ic)


def _t_stat(ic: float, n: int) -> float:
    """t-statistic for testing if IC is significantly different from 0."""
    if n <= 2 or ic is None:
        return 0.0
    return ic * np.sqrt(n - 2) / np.sqrt(max(1 - ic ** 2, 1e-10))


def _hit_rate(scores: pd.Series, forward_returns: pd.Series) -> float:
    """Fraction of stocks where high score → positive return (rank agreement)."""
    valid = pd.concat([scores, forward_returns], axis=1).dropna()
    if len(valid) < 5:
        return 0.5
    score_above_median = valid.iloc[:, 0] > valid.iloc[:, 0].median()
    return_positive = valid.iloc[:, 1] > 0
    return float((score_above_median == return_positive).mean())


# ─────────────────────────────────────────────────────────────────────────────
# QUARTILE ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def _quartile_returns(scores: pd.Series, forward_returns: pd.Series) -> Dict:
    """Average forward return for top and bottom quartile stocks."""
    valid = pd.concat([scores, forward_returns], axis=1).dropna()
    valid.columns = ["score", "fwd_return"]
    if len(valid) < 8:
        return {}
    q25 = valid["score"].quantile(0.25)
    q75 = valid["score"].quantile(0.75)
    top_q  = valid[valid["score"] >= q75]["fwd_return"].mean()
    bot_q  = valid[valid["score"] <= q25]["fwd_return"].mean()
    return {
        "top_quartile_avg_return": round(float(top_q), 2) if not pd.isna(top_q) else None,
        "bottom_quartile_avg_return": round(float(bot_q), 2) if not pd.isna(bot_q) else None,
        "quartile_spread": round(float(top_q - bot_q), 2) if not (pd.isna(top_q) or pd.isna(bot_q)) else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PER-SCORE VALIDATOR
# ─────────────────────────────────────────────────────────────────────────────

def validate_score(score_column: str, horizon: str = "1M") -> Dict:
    """
    Compute IC, hit_rate, t_stat, quartile analysis for a single score column
    against realized forward returns.
    """
    df = data_loader.get_df()
    if df.empty or score_column not in df.columns:
        return {"error": f"{score_column} not found in data"}

    symbols = df["Symbol"].tolist()
    scores_list = []
    returns_list = []

    for symbol in symbols:
        score_row = df[df["Symbol"] == symbol]
        if score_row.empty:
            continue
        score_val = float(score_row.iloc[0][score_column])
        fwd_ret = _get_forward_return(symbol, horizon)
        if fwd_ret is not None:
            scores_list.append(score_val)
            returns_list.append(fwd_ret)

    n = len(scores_list)
    if n < 5:
        return {
            "score_column": score_column,
            "horizon": horizon,
            "n": n,
            "ic": None,
            "hit_rate": None,
            "t_stat": None,
            "significant": False,
            "error": "Insufficient data points",
        }

    scores_series  = pd.Series(scores_list)
    returns_series = pd.Series(returns_list)

    ic = _spearman_ic(scores_series, returns_series)
    t  = _t_stat(ic, n) if ic else 0.0
    hr = _hit_rate(scores_series, returns_series)
    qr = _quartile_returns(scores_series, returns_series)

    return {
        "score_column": score_column,
        "horizon": horizon,
        "n": n,
        "ic": round(ic, 4) if ic is not None else None,
        "hit_rate": round(hr, 4),
        "t_stat": round(t, 4),
        "significant": abs(t) > 1.96,   # 95% confidence
        "p_value_approx": round(2 * (1 - min(abs(t) / 10, 0.9999)), 4),
        **qr,
    }


# ─────────────────────────────────────────────────────────────────────────────
# RATING MONOTONICITY TEST
# ─────────────────────────────────────────────────────────────────────────────

def validate_final_rating(horizon: str = "1M") -> Dict:
    """
    Test: STRONG BUY > BUY > HOLD > SELL > STRONG SELL in terms of forward returns?
    Returns per-rating statistics + monotonicity flag.
    """
    df = data_loader.get_df()
    if df.empty:
        return {}

    rating_order = ["STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"]
    symbols = df["Symbol"].tolist()

    rating_returns: Dict[str, List[float]] = {r: [] for r in rating_order}

    for symbol in symbols:
        row = df[df["Symbol"] == symbol]
        if row.empty:
            continue
        rating = str(row.iloc[0].get("FinalRating", "")).upper()
        fwd_ret = _get_forward_return(symbol, horizon)
        if fwd_ret is not None and rating in rating_returns:
            rating_returns[rating].append(fwd_ret)

    per_rating = {}
    avg_returns_ordered = []
    for rating in rating_order:
        rets = rating_returns[rating]
        if not rets:
            per_rating[rating] = {"n": 0, "avg_return": None, "std": None}
            avg_returns_ordered.append(None)
        else:
            avg = float(np.mean(rets))
            per_rating[rating] = {
                "n": len(rets),
                "avg_return": round(avg, 2),
                "std": round(float(np.std(rets)), 2),
                "min": round(float(min(rets)), 2),
                "max": round(float(max(rets)), 2),
            }
            avg_returns_ordered.append(avg)

    # Monotonicity: are avg_returns in descending order?
    valid_returns = [r for r in avg_returns_ordered if r is not None]
    is_monotone = all(
        valid_returns[i] >= valid_returns[i + 1]
        for i in range(len(valid_returns) - 1)
    ) if len(valid_returns) >= 2 else False

    return {
        "horizon": horizon,
        "per_rating": per_rating,
        "monotonicity": is_monotone,
        "rating_order": rating_order,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SCORE DISTRIBUTION
# ─────────────────────────────────────────────────────────────────────────────

def score_distribution(score_column: str) -> Dict:
    """Return histogram bins for a score column across the universe."""
    df = data_loader.get_df()
    if df.empty or score_column not in df.columns:
        return {}
    vals = pd.to_numeric(df[score_column], errors="coerce").dropna()
    counts, edges = np.histogram(vals, bins=10)
    hist = []
    for i in range(len(counts)):
        hist.append({
            "min": round(float(edges[i]), 2),
            "max": round(float(edges[i + 1]), 2),
            "count": int(counts[i]),
            "label": f"{edges[i]:.1f}–{edges[i+1]:.1f}",
        })
    return {
        "score_column": score_column,
        "mean": round(float(vals.mean()), 2),
        "std": round(float(vals.std()), 2),
        "min": round(float(vals.min()), 2),
        "max": round(float(vals.max()), 2),
        "histogram": hist,
    }


# ─────────────────────────────────────────────────────────────────────────────
# FULL ENGINE VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def full_engine_validation(horizon: str = "1M") -> Dict:
    """Run all score validators. Returns consolidated results dict."""
    results = {}
    for col in SCORE_COLUMNS:
        try:
            results[col] = validate_score(col, horizon)
        except Exception as e:
            logger.error(f"validate_score {col}: {e}")
            results[col] = {"error": str(e)}

    try:
        results["FinalRating"] = validate_final_rating(horizon)
    except Exception as e:
        results["FinalRating"] = {"error": str(e)}

    return {
        "horizon": horizon,
        "score_validations": results,
        "score_distributions": {
            col: score_distribution(col) for col in SCORE_COLUMNS
        },
    }

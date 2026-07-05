"""
model_researcher.py — ML Model comparison for the Quant Research Laboratory.

Compares RF, XGBoost, LightGBM, GRU models using existing score columns.
Does NOT retrain models. Evaluates historical prediction quality using
analysis_history records matched to OHLCV forward returns.

Extensible: add new model → add entry to MODEL_REGISTRY.
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from app.data.loader import data_loader
from app.services.historical_data_service import historical_data_service
from app.services.db import get_db_connection

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# MODEL REGISTRY — extensible
# ─────────────────────────────────────────────────────────────────────────────

MODEL_REGISTRY = {
    "gru": {
        "label":       "GRU Neural Network",
        "score_col":   "GRUScore",
        "prob_cols":   ["GRU_LONG", "GRU_HOLD", "GRU_SHORT"],
        "category":    "Deep Learning",
        "description": "Gated Recurrent Unit sequence model trained on 60-day OHLCV windows.",
    },
    "ml_ensemble": {
        "label":       "ML Tabular Ensemble (RF + XGBoost + LightGBM)",
        "score_col":   "MLScore",
        "prob_cols":   [],
        "category":    "Ensemble",
        "description": "Weighted ensemble of Random Forest, XGBoost, and LightGBM.",
    },
    "technical": {
        "label":       "Technical Scoring Engine",
        "score_col":   "TechnicalScore",
        "prob_cols":   [],
        "category":    "Rule-Based",
        "description": "Multi-indicator technical scoring system (RSI, MACD, ADX, Bollinger, etc.).",
    },
    "reliability": {
        "label":       "Reliability & Signal Quality Index",
        "score_col":   "ReliabilityScore",
        "prob_cols":   [],
        "category":    "Quality",
        "description": "Data quality and signal noise assessment metric.",
    },
    "composite": {
        "label":       "Composite Score V2",
        "score_col":   "CompositeScoreV2",
        "prob_cols":   [],
        "category":    "Composite",
        "description": "Weighted composite of all sub-scores.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS (reused from pms_score_validator logic)
# ─────────────────────────────────────────────────────────────────────────────

def _get_forward_return(symbol: str, horizon_bars: int = 21) -> Optional[float]:
    try:
        df = historical_data_service.get_stock_history(symbol, "1Y")
        if df is None or df.empty or len(df) < horizon_bars + 1:
            return None
        close = pd.to_numeric(df["Close"], errors="coerce").dropna()
        if len(close) < horizon_bars + 1:
            return None
        entry = float(close.iloc[-(horizon_bars + 1)])
        exit_p = float(close.iloc[-1])
        return (exit_p - entry) / entry * 100 if entry > 0 else None
    except Exception:
        return None


def _spearman_ic(scores: pd.Series, returns: pd.Series) -> Optional[float]:
    valid = pd.concat([scores, returns], axis=1).dropna()
    n = len(valid)
    if n < 5:
        return None
    d = valid.iloc[:, 0].rank() - valid.iloc[:, 1].rank()
    return float(1 - 6 * (d ** 2).sum() / (n * (n ** 2 - 1)))


def _hit_rate(scores: pd.Series, returns: pd.Series) -> float:
    valid = pd.concat([scores, returns], axis=1).dropna()
    if len(valid) < 5:
        return 0.5
    return float((
        (valid.iloc[:, 0] > valid.iloc[:, 0].median()) ==
        (valid.iloc[:, 1] > 0)
    ).mean())


# ─────────────────────────────────────────────────────────────────────────────
# SINGLE MODEL ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def analyse_model(model_name: str, horizon_bars: int = 21) -> Dict:
    """Compute IC, hit_rate, distribution for a single model."""
    if model_name not in MODEL_REGISTRY:
        return {"error": f"Unknown model: {model_name}"}

    meta = MODEL_REGISTRY[model_name]
    score_col = meta["score_col"]
    df = data_loader.get_df()

    if df.empty or score_col not in df.columns:
        return {"error": f"Score column {score_col} not in data"}

    scores_list = []
    returns_list = []

    for _, row in df.iterrows():
        symbol = row["Symbol"]
        score = float(row[score_col]) if pd.notna(row[score_col]) else None
        fwd_ret = _get_forward_return(symbol, horizon_bars)
        if score is not None and fwd_ret is not None:
            scores_list.append(score)
            returns_list.append(fwd_ret)

    n = len(scores_list)
    if n < 5:
        return {"model": model_name, "n": n, "error": "Insufficient data"}

    scores_s  = pd.Series(scores_list)
    returns_s = pd.Series(returns_list)

    ic = _spearman_ic(scores_s, returns_s)
    t_stat = ic * np.sqrt(n - 2) / np.sqrt(max(1 - ic ** 2, 1e-10)) if ic else 0.0

    return {
        "model":       model_name,
        "label":       meta["label"],
        "score_col":   score_col,
        "category":    meta["category"],
        "description": meta["description"],
        "n":           n,
        "ic":          round(ic, 4) if ic else None,
        "hit_rate":    round(_hit_rate(scores_s, returns_s), 4),
        "t_stat":      round(float(t_stat), 4),
        "significant": abs(t_stat) > 1.96,
        "score_mean":  round(float(scores_s.mean()), 2),
        "score_std":   round(float(scores_s.std()), 2),
        "horizon_bars": horizon_bars,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MODEL COMPARISON
# ─────────────────────────────────────────────────────────────────────────────

def compare_all_models(horizon_bars: int = 21) -> Dict:
    """Run analyse_model for all models and return comparison table."""
    results = {}
    for model_name in MODEL_REGISTRY.keys():
        try:
            results[model_name] = analyse_model(model_name, horizon_bars)
        except Exception as e:
            logger.error(f"compare_all_models {model_name}: {e}")
            results[model_name] = {"model": model_name, "error": str(e)}
    return {
        "horizon_bars": horizon_bars,
        "models": results,
        "model_list": list(MODEL_REGISTRY.keys()),
    }


# ─────────────────────────────────────────────────────────────────────────────
# CALIBRATION CURVE
# ─────────────────────────────────────────────────────────────────────────────

def model_calibration(model_name: str, n_bins: int = 10) -> Dict:
    """
    Reliability diagram: are high scores followed by high returns?
    Bins scores 0–100 into n_bins, computes avg forward return per bin.
    """
    if model_name not in MODEL_REGISTRY:
        return {"error": f"Unknown model: {model_name}"}

    meta = MODEL_REGISTRY[model_name]
    score_col = meta["score_col"]
    df = data_loader.get_df()

    scores_list, returns_list = [], []
    for _, row in df.iterrows():
        symbol = row["Symbol"]
        score = float(row[score_col]) if pd.notna(row.get(score_col)) else None
        fwd_ret = _get_forward_return(symbol)
        if score is not None and fwd_ret is not None:
            scores_list.append(score)
            returns_list.append(fwd_ret)

    if len(scores_list) < 5:
        return {"model": model_name, "bins": [], "n": len(scores_list)}

    scores_s  = pd.Series(scores_list)
    returns_s = pd.Series(returns_list)

    # Bin scores
    bins = pd.cut(scores_s, bins=n_bins)
    grouped = pd.DataFrame({"bin": bins, "return": returns_s}).groupby("bin")

    calibration_bins = []
    for b, g in grouped:
        mid = (b.left + b.right) / 2
        calibration_bins.append({
            "bin_mid": round(float(mid), 2),
            "avg_return": round(float(g["return"].mean()), 2),
            "count": len(g),
            "positive_rate": round(float((g["return"] > 0).mean() * 100), 1),
        })

    return {"model": model_name, "score_col": score_col, "bins": calibration_bins}


# ─────────────────────────────────────────────────────────────────────────────
# MODEL STABILITY (IC over time from analysis_history)
# ─────────────────────────────────────────────────────────────────────────────

def model_stability(model_name: str) -> Dict:
    """
    Rolling IC over time using analysis_history records.
    Groups analyses by month, computes monthly IC.
    """
    if model_name not in MODEL_REGISTRY:
        return {"error": f"Unknown model: {model_name}"}

    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT symbol, rating, composite_score, analyzed_at FROM analysis_history ORDER BY analyzed_at ASC"
        ).fetchall()
    except Exception:
        return {"model": model_name, "trend": []}
    finally:
        conn.close()

    if not rows:
        return {"model": model_name, "trend": []}

    df_hist = pd.DataFrame(rows, columns=["symbol", "rating", "composite_score", "analyzed_at"])
    df_hist["analyzed_at"] = pd.to_datetime(df_hist["analyzed_at"], errors="coerce", format="mixed")
    df_hist = df_hist.dropna(subset=["analyzed_at"])
    df_hist["month"] = df_hist["analyzed_at"].dt.to_period("M")

    score_col = MODEL_REGISTRY[model_name]["score_col"]
    universe_df = data_loader.get_df()

    trend = []
    for month, group in df_hist.groupby("month"):
        if len(group) < 3:
            continue
        # Get current score for each symbol
        scores_list, returns_list = [], []
        for _, r in group.iterrows():
            symbol = r["symbol"]
            score_row = universe_df[universe_df["Symbol"] == symbol]
            if score_row.empty or score_col not in score_row.columns:
                continue
            score = float(score_row.iloc[0][score_col])
            fwd = _get_forward_return(symbol)
            if fwd is not None:
                scores_list.append(score)
                returns_list.append(fwd)

        if len(scores_list) >= 3:
            ic = _spearman_ic(pd.Series(scores_list), pd.Series(returns_list))
            trend.append({
                "month": str(month),
                "ic": round(ic, 4) if ic else None,
                "n": len(scores_list),
            })

    return {"model": model_name, "score_col": score_col, "trend": trend}


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE IMPORTANCE (Permutation via existing scores)
# ─────────────────────────────────────────────────────────────────────────────

def feature_importance_from_scores() -> Dict:
    """
    Permutation importance using existing score columns:
    Shuffle each feature 10×, measure IC degradation with CompositeScoreV2.
    """
    df = data_loader.get_df()
    FEATURES = ["TechnicalScore", "MLScore", "GRUScore", "ReliabilityScore"]
    TARGET = "CompositeScoreV2"

    if df.empty or TARGET not in df.columns:
        return {}

    # Baseline IC: TechnicalScore + MLScore + GRUScore + ReliabilityScore vs CompositeScoreV2
    # (proxy: correlation between each feature and target)
    rng = np.random.default_rng(42)
    importance = {}

    for feat in FEATURES:
        if feat not in df.columns:
            continue
        baseline_corr = df[feat].corr(df[TARGET])
        if pd.isna(baseline_corr):
            importance[feat] = 0.0
            continue

        degradations = []
        for _ in range(10):
            shuffled = df[feat].sample(frac=1, random_state=int(rng.integers(1000))).reset_index(drop=True)
            temp_df = df.copy().reset_index(drop=True)
            temp_df[feat] = shuffled.values
            shuffled_corr = temp_df[feat].corr(temp_df[TARGET])
            degradation = abs(baseline_corr) - abs(shuffled_corr if not pd.isna(shuffled_corr) else 0)
            degradations.append(float(degradation))

        importance[feat] = round(float(np.mean(degradations)), 4)

    return {
        "importance": importance,
        "target": TARGET,
        "method": "permutation_correlation_degradation",
        "n_shuffles": 10,
    }


def model_regime_performance(model_name: str, regimes_df: pd.DataFrame) -> Dict:
    """
    Measure model prediction accuracy (IC and hit rate) under different market regimes.
    Uses historical analysis_history records to match score on date with the regime on that date.
    """
    if model_name not in MODEL_REGISTRY:
        return {"error": f"Unknown model: {model_name}"}

    meta = MODEL_REGISTRY[model_name]
    score_col = meta["score_col"]

    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT symbol, rating, composite_score, analyzed_at FROM analysis_history"
        ).fetchall()
    except Exception:
        return {"model": model_name, "regimes": {}}
    finally:
        conn.close()

    if not rows or regimes_df is None or regimes_df.empty:
        return {"model": model_name, "regimes": {}}

    df_hist = pd.DataFrame(rows, columns=["symbol", "rating", "composite_score", "analyzed_at"])
    df_hist["analyzed_at"] = pd.to_datetime(df_hist["analyzed_at"], errors="coerce", format="mixed")
    df_hist = df_hist.dropna(subset=["analyzed_at"])
    df_hist["Date"] = df_hist["analyzed_at"].dt.strftime("%Y-%m-%d")

    # Merge with regimes on Date
    regimes_df = regimes_df.copy()
    if "Date" in regimes_df.columns:
        regimes_df["Date"] = pd.to_datetime(regimes_df["Date"]).dt.strftime("%Y-%m-%d")
        merged = df_hist.merge(regimes_df[["Date", "primary_regime"]], on="Date", how="left")
    else:
        merged = df_hist.copy()
        merged["primary_regime"] = "Unknown"

    merged["primary_regime"] = merged["primary_regime"].fillna("Unknown")
    universe_df = data_loader.get_df()

    results = {}
    for regime, group in merged.groupby("primary_regime"):
        if len(group) < 3:
            continue
        scores_list = []
        returns_list = []
        for _, r in group.iterrows():
            symbol = r["symbol"]
            score_row = universe_df[universe_df["Symbol"] == symbol]
            if score_row.empty or score_col not in score_row.columns:
                continue
            score = float(score_row.iloc[0][score_col])
            fwd = _get_forward_return(symbol)
            if fwd is not None:
                scores_list.append(score)
                returns_list.append(fwd)

        if len(scores_list) >= 3:
            ic = _spearman_ic(pd.Series(scores_list), pd.Series(returns_list))
            hr = _hit_rate(pd.Series(scores_list), pd.Series(returns_list))
            results[regime] = {
                "ic": round(ic, 4) if ic else None,
                "hit_rate": round(hr, 4),
                "n": len(scores_list)
            }

    return {"model": model_name, "score_col": score_col, "regimes": results}


def model_comparison_report_data(horizon_bars: int = 21) -> Dict:
    """Consolidated model comparison report data."""
    comparison = compare_all_models(horizon_bars)
    importance = feature_importance_from_scores()
    
    # Load NIFTY 50 regimes as benchmark
    from app.lab.backtester import load_ohlcv
    from app.lab.regime_detector import detect_regimes
    
    regimes_df = None
    try:
        nifty_df = load_ohlcv("^NSEI", "3Y")
        if nifty_df is not None:
            regimes_df = detect_regimes(nifty_df)
    except Exception as e:
        logger.warning(f"Failed to load NIFTY regimes for model comparison: {e}")

    # Add regime performance and calibration for each model
    model_details = {}
    for model_name in MODEL_REGISTRY.keys():
        model_details[model_name] = {
            "calibration": model_calibration(model_name),
            "stability": model_stability(model_name),
            "regime_performance": model_regime_performance(model_name, regimes_df) if regimes_df is not None else {"model": model_name, "regimes": {}}
        }

    return {
        "comparison": comparison,
        "importance": importance,
        "details": model_details,
    }


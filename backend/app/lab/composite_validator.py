"""
composite_validator.py — Composite Score weighting research for the Quant Research Laboratory.

PURPOSE: Research and comparison ONLY. Does NOT modify production weights.
         A clear warning banner is always shown on the frontend for this module.

Methods:
  - Current weight contribution analysis (partial correlation)
  - Grid search over weight combinations
  - Per-regime optimal weights (research artifact)
"""

import itertools
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.data.loader import data_loader
from app.lab.db_lab import save_weight_snapshot

logger = logging.getLogger(__name__)

# Estimated current production weights (used for baseline comparison)
CURRENT_WEIGHTS = {
    "TechnicalScore":   0.35,
    "MLScore":          0.30,
    "GRUScore":         0.25,
    "ReliabilityScore": 0.10,
}

SCORE_FEATURES = ["TechnicalScore", "MLScore", "GRUScore", "ReliabilityScore"]


def _simulate_composite(df: pd.DataFrame, weights: Dict[str, float]) -> pd.Series:
    """Compute alternative composite score from given weights dict."""
    total = sum(abs(w) for w in weights.values())
    if total == 0:
        return pd.Series(0, index=df.index)
    score = pd.Series(0.0, index=df.index)
    for col, w in weights.items():
        if col in df.columns:
            normalised_w = w / total
            score += df[col].fillna(0) * normalised_w
    return score


def _rank_ic(simulated_composite: pd.Series,
             actual_composite: pd.Series) -> float:
    """Spearman rank correlation between simulated and actual composite."""
    valid = pd.DataFrame({"sim": simulated_composite, "act": actual_composite}).dropna()
    if len(valid) < 5:
        return 0.0
    d = valid["sim"].rank() - valid["act"].rank()
    n = len(valid)
    return float(1 - 6 * (d ** 2).sum() / (n * (n ** 2 - 1)))


# ─────────────────────────────────────────────────────────────────────────────
# CURRENT WEIGHT ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def current_weight_analysis() -> Dict:
    """
    Partial correlation analysis: how much does each sub-score uniquely
    contribute to CompositeScoreV2?
    """
    df = data_loader.get_df()
    available = [f for f in SCORE_FEATURES if f in df.columns]
    TARGET = "CompositeScoreV2"

    if TARGET not in df.columns or not available:
        return {}

    # For each feature: compute semi-partial correlation with CompositeScoreV2
    # (correlation while controlling for all other features)
    result = {}
    feature_df = df[available + [TARGET]].dropna()
    n = len(feature_df)

    for feat in available:
        others = [f for f in available if f != feat]
        X = feature_df[others].values
        y = feature_df[TARGET].values
        f = feature_df[feat].values

        # OLS: residualize y on others
        X_intercept = np.column_stack([np.ones(n), X])
        try:
            beta_y = np.linalg.lstsq(X_intercept, y, rcond=None)[0]
            y_resid = y - X_intercept @ beta_y

            # Correlate residual y with feature f
            corr = float(np.corrcoef(y_resid, f)[0, 1])
        except Exception:
            corr = 0.0

        result[feat] = {
            "semi_partial_correlation": round(corr, 4),
            "current_weight": CURRENT_WEIGHTS.get(feat, 0.0),
            "estimated_contribution_pct": round(abs(corr) * 100, 2),
        }

    return {
        "current_weights": CURRENT_WEIGHTS,
        "partial_correlations": result,
        "note": "These are research findings. Production weights are unchanged.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# WEIGHT GRID SEARCH
# ─────────────────────────────────────────────────────────────────────────────

def weight_grid_search(
    step: float = 0.10,
    target_metric: str = "rank_ic",
    experiment_id: Optional[str] = None,
) -> Dict:
    """
    Enumerate weight combinations where all weights >= 0 and sum == 1.0.
    For each: compute simulated composite and measure rank IC with actual CompositeScoreV2.

    Returns: top 20 combinations + optimization surface.
    """
    df = data_loader.get_df()
    available = [f for f in SCORE_FEATURES if f in df.columns]
    TARGET = "CompositeScoreV2"

    if TARGET not in df.columns or not available:
        return {}

    feature_df = df[available + [TARGET]].dropna()
    actual = feature_df[TARGET]

    # Generate all weight combinations
    n_features = len(available)
    n_steps = int(round(1.0 / step)) + 1
    raw_values = np.round(np.arange(0, 1 + step / 2, step), 6)

    combos = []
    for combo in itertools.product(raw_values, repeat=n_features):
        if abs(sum(combo) - 1.0) < 1e-6:
            combos.append(combo)

    logger.info(f"weight_grid_search: {len(combos)} combinations (step={step})")

    all_results = []
    best_combo = None
    best_score = float("-inf")

    for combo in combos:
        weights = dict(zip(available, combo))
        try:
            sim = _simulate_composite(feature_df, weights)
            ic = _rank_ic(sim, actual)
            score = ic  # higher is better

            result_row = {
                "weights": weights,
                target_metric: round(ic, 4),
            }
            all_results.append(result_row)

            if score > best_score:
                best_score = score
                best_combo = weights

            if experiment_id:
                save_weight_snapshot(experiment_id, weights, target_metric, ic)

        except Exception as e:
            logger.debug(f"weight combo {combo} failed: {e}")

    all_results.sort(key=lambda x: x.get(target_metric, 0), reverse=True)
    top20 = all_results[:20]

    # Build 2D optimization surface (first 2 features)
    surface = []
    if len(available) >= 2:
        from app.lab.chart_builder import param_heatmap
        surface_input = [
            {"params": {available[0]: r["weights"][available[0]],
                        available[1]: r["weights"][available[1]]},
             target_metric: r[target_metric]}
            for r in all_results
        ]
        surface = param_heatmap(surface_input, available[0], available[1], target_metric)

    return {
        "best_weights": best_combo,
        "best_metric_value": round(best_score, 4),
        "target_metric": target_metric,
        "total_combinations": len(all_results),
        "top_results": [
            {
                **{k: round(float(v), 3) for k, v in r["weights"].items()},
                target_metric: r[target_metric],
            }
            for r in top20
        ],
        "optimization_surface": surface,
        "features": available,
        "research_note": "⚠️ Research only. Production weights are unchanged.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# REGIME-OPTIMAL WEIGHTS (research artifact)
# ─────────────────────────────────────────────────────────────────────────────

def regime_optimal_weights(regimes_df: Optional[pd.DataFrame] = None) -> Dict:
    """
    For each regime: find weight combination that maximises rank IC with actual composite.
    Returns per-regime optimal weights (research artifact — clearly labeled).
    """
    df = data_loader.get_df()
    available = [f for f in SCORE_FEATURES if f in df.columns]
    TARGET = "CompositeScoreV2"

    if TARGET not in df.columns:
        return {}

    # If no regime data, simulate simple regimes based on composite score distribution
    if regimes_df is None:
        composite = df[TARGET]
        q33, q67 = composite.quantile(0.33), composite.quantile(0.67)
        df = df.copy()
        df["_regime"] = "Medium"
        df.loc[composite >= q67, "_regime"] = "High Score Universe"
        df.loc[composite <= q33, "_regime"] = "Low Score Universe"
        regimes_df = df[["Symbol", "_regime"]].rename(columns={"_regime": "regime"})

    # Merge regimes with score data
    if "Symbol" in df.columns and "regime" in regimes_df.columns:
        merge_key = "Symbol" if "Symbol" in regimes_df.columns else None
        if merge_key:
            merged = df.merge(regimes_df[["Symbol", "regime"]], on="Symbol", how="left")
        else:
            merged = df.copy()
            merged["regime"] = "All"
    else:
        merged = df.copy()
        merged["regime"] = "All"

    results = {}
    step = 0.25  # coarse grid for speed

    for regime, group in merged.groupby("regime"):
        if len(group) < 5:
            continue
        feature_df = group[available + [TARGET]].dropna()
        if len(feature_df) < 5:
            continue

        actual = feature_df[TARGET]
        best_weights = None
        best_ic = float("-inf")

        raw_values = [0.0, 0.25, 0.50, 0.75, 1.0]
        for combo in itertools.product(raw_values, repeat=len(available)):
            if abs(sum(combo) - 1.0) > 0.01:
                continue
            weights = dict(zip(available, combo))
            sim = _simulate_composite(feature_df, weights)
            ic = _rank_ic(sim, actual)
            if ic > best_ic:
                best_ic = ic
                best_weights = weights

        results[regime] = {
            "optimal_weights": best_weights,
            "ic": round(best_ic, 4),
            "n": len(feature_df),
            "research_note": "Research artifact. Not applied to production.",
        }

    return {
        "regime_weights": results,
        "research_note": "⚠️ Research only. Production weights unchanged.",
    }

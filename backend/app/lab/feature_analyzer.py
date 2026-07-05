"""
feature_analyzer.py — Feature research for the Quant Research Laboratory.

Analyzes existing PMS Engine score features:
  TechnicalScore, MLScore, GRUScore, ReliabilityScore,
  GRU_LONG, GRU_SHORT, GRU_HOLD, ReturnScore

Methods (all pure pandas/numpy):
  - Permutation importance
  - Mutual information (histogram binning)
  - Pearson correlation matrix
  - Variance Inflation Factor (OLS)
  - SHAP proxy (marginal contribution)
  - Feature drift over time (from analysis_history)
  - Redundancy groups (|r| > 0.85)
  - Stability (coefficient of variation)
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from app.data.loader import data_loader

logger = logging.getLogger(__name__)

FEATURES = [
    "TechnicalScore",
    "MLScore",
    "GRUScore",
    "ReliabilityScore",
    "GRU_LONG",
    "GRU_SHORT",
    "GRU_HOLD",
    "ReturnScore",
]

TARGET = "CompositeScoreV2"
REDUNDANCY_THRESHOLD = 0.85


def _get_feature_df() -> pd.DataFrame:
    """Return numeric feature columns from the in-memory DataFrame."""
    df = data_loader.get_df()
    available = [f for f in FEATURES if f in df.columns and not df[f].isna().all()]
    feature_df = df[available + ([TARGET] if TARGET in df.columns else [])].copy()
    for col in feature_df.columns:
        feature_df[col] = pd.to_numeric(feature_df[col], errors="coerce")
    return feature_df.dropna(subset=available)


# ─────────────────────────────────────────────────────────────────────────────
# PERMUTATION IMPORTANCE
# ─────────────────────────────────────────────────────────────────────────────

def permutation_importance(target: str = TARGET, n_shuffles: int = 10) -> Dict:
    """
    Shuffle each feature, measure Spearman rank correlation drop with target.
    Returns {feature → importance_score}.
    """
    feature_df = _get_feature_df()
    available = [f for f in FEATURES if f in feature_df.columns]
    if target not in feature_df.columns or not available:
        return {}

    rng = np.random.default_rng(42)
    importance = {}

    baseline_target = feature_df[target].rank()

    for feat in available:
        baseline_corr = feature_df[feat].corr(feature_df[target], method="spearman")
        if pd.isna(baseline_corr):
            importance[feat] = 0.0
            continue

        degradations = []
        for i in range(n_shuffles):
            shuffled = feature_df[feat].sample(
                frac=1, random_state=int(rng.integers(10_000))
            ).reset_index(drop=True)
            temp = feature_df.copy().reset_index(drop=True)
            temp[feat] = shuffled.values
            shuffled_corr = temp[feat].corr(temp[target], method="spearman")
            deg = abs(baseline_corr) - abs(shuffled_corr if not pd.isna(shuffled_corr) else 0)
            degradations.append(float(deg))

        importance[feat] = round(float(np.mean(degradations)), 4)

    sorted_imp = dict(sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True))
    return {
        "importance": [{"feature": k, "importance": v} for k, v in sorted_imp.items()],
        "importance_dict": sorted_imp,
        "target": target,
        "method": "permutation_spearman",
        "n_shuffles": n_shuffles,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MUTUAL INFORMATION (histogram binning, no sklearn)
# ─────────────────────────────────────────────────────────────────────────────

def mutual_information(target: str = TARGET, bins: int = 10) -> Dict:
    """Compute mutual information between each feature and target via histogram binning."""
    feature_df = _get_feature_df()
    available = [f for f in FEATURES if f in feature_df.columns]
    if target not in feature_df.columns:
        return {}

    mi_scores = {}
    for feat in available:
        valid = feature_df[[feat, target]].dropna()
        if len(valid) < 5:
            mi_scores[feat] = 0.0
            continue

        x = valid[feat].values
        y = valid[target].values

        # Discretize both to bins
        x_bins = pd.cut(pd.Series(x), bins=bins, labels=False)
        y_bins = pd.cut(pd.Series(y), bins=bins, labels=False)

        # Joint probability
        n = len(x)
        joint = pd.crosstab(x_bins, y_bins) / n
        px = joint.sum(axis=1)
        py = joint.sum(axis=0)

        mi = 0.0
        for i in joint.index:
            for j in joint.columns:
                pxy = joint.loc[i, j]
                if pxy > 0 and px[i] > 0 and py[j] > 0:
                    mi += float(pxy * np.log(pxy / (px[i] * py[j])))

        mi_scores[feat] = round(max(0.0, mi), 4)

    sorted_mi = dict(sorted(mi_scores.items(), key=lambda x: x[1], reverse=True))
    return {
        "mutual_information": [{"feature": k, "mi": v} for k, v in sorted_mi.items()],
        "mi_scores": sorted_mi,
        "target": target,
        "method": "histogram_binning",
        "bins": bins,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CORRELATION MATRIX
# ─────────────────────────────────────────────────────────────────────────────

def correlation_matrix() -> Dict:
    """Pairwise Pearson correlation matrix for all features + target."""
    feature_df = _get_feature_df()
    available = [f for f in FEATURES if f in feature_df.columns]
    if TARGET in feature_df.columns:
        available.append(TARGET)

    corr = feature_df[available].corr(method="pearson")

    flat = []
    for col in corr.columns:
        for idx in corr.index:
            v = corr.loc[idx, col]
            flat.append({
                "feature_a": str(idx),
                "feature_b": str(col),
                "correlation": round(float(v), 4) if not pd.isna(v) else None,
            })

    return {
        "correlation_flat": flat,
        "features": available,
        "method": "pearson",
    }


# ─────────────────────────────────────────────────────────────────────────────
# VARIANCE INFLATION FACTOR (VIF)
# ─────────────────────────────────────────────────────────────────────────────

def variance_inflation_factor() -> Dict:
    """Compute VIF for each feature. VIF = 1/(1-R²) from OLS regression."""
    feature_df = _get_feature_df()
    available = [f for f in FEATURES if f in feature_df.columns]
    if len(available) < 2:
        return {}

    vif_scores = {}
    X = feature_df[available].dropna()

    for i, feat in enumerate(available):
        y = X[feat].values
        others = X.drop(columns=[feat]).values
        # Add intercept
        X_mat = np.column_stack([np.ones(len(others)), others])
        try:
            # OLS: beta = (X'X)^-1 X'y
            betas = np.linalg.lstsq(X_mat, y, rcond=None)[0]
            y_pred = X_mat @ betas
            ss_res = ((y - y_pred) ** 2).sum()
            ss_tot = ((y - y.mean()) ** 2).sum()
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
            vif = 1 / (1 - r2) if r2 < 1 else float("inf")
            vif_scores[feat] = round(float(min(vif, 999)), 2)
        except Exception:
            vif_scores[feat] = None

    vif_list = [
        {
            "feature": k,
            "vif": v,
            "risk": "High" if v and v > 10 else ("Moderate" if v and v > 5 else "Low"),
        }
        for k, v in vif_scores.items()
    ]

    return {"vif": vif_list, "method": "ols_r_squared"}


# ─────────────────────────────────────────────────────────────────────────────
# SHAP PROXY
# ─────────────────────────────────────────────────────────────────────────────

def shap_proxy(target: str = TARGET) -> Dict:
    """
    Approximate SHAP values using marginal contribution.
    For each feature: compute how much it contributes to
    pushing target above or below mean when it is above/below its mean.

    Valid for additive composite structures.
    """
    feature_df = _get_feature_df()
    available = [f for f in FEATURES if f in feature_df.columns]
    if target not in feature_df.columns:
        return {}

    target_mean = feature_df[target].mean()
    shap_values = {}

    for feat in available:
        feat_mean = feature_df[feat].mean()
        feat_std  = feature_df[feat].std()
        if feat_std == 0:
            shap_values[feat] = 0.0
            continue

        # SHAP proxy: Cov(feature, target) / Var(total) — linear approximation
        covariance = feature_df[[feat, target]].cov().loc[feat, target]
        total_var  = feature_df[target].var()
        if total_var == 0:
            shap_values[feat] = 0.0
        else:
            # Marginal SHAP = covariance contribution (linear assumption)
            shap_values[feat] = round(float(covariance / total_var), 4)

    return {
        "shap_values": dict(sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)),
        "target": target,
        "method": "linear_shap_proxy",
        "note": "Approximation valid for additive composite score structure",
    }


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE DRIFT
# ─────────────────────────────────────────────────────────────────────────────

def feature_drift() -> Dict:
    """
    Track mean/std of each feature in analysis_history over time.
    Flags features where mean shifts > 0.5 std over available history.
    """
    from app.services.db import get_db_connection
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT symbol, composite_score, confidence, analyzed_at FROM analysis_history ORDER BY analyzed_at ASC"
        ).fetchall()
    except Exception:
        return {"drift": [], "note": "No analysis history found"}
    finally:
        conn.close()

    if not rows:
        return {"drift": [], "note": "No analysis history found"}

    df_hist = pd.DataFrame(rows, columns=["symbol", "composite_score", "confidence", "analyzed_at"])
    df_hist["analyzed_at"] = pd.to_datetime(df_hist["analyzed_at"], errors="coerce", format="mixed")
    df_hist = df_hist.dropna(subset=["analyzed_at"])
    df_hist["month"] = df_hist["analyzed_at"].dt.to_period("M")

    drift_results = []
    for col in ["composite_score", "confidence"]:
        if col not in df_hist.columns:
            continue
        monthly = df_hist.groupby("month")[col].mean()
        if len(monthly) < 2:
            continue
        drift = monthly.diff().dropna()
        drift_results.append({
            "feature": col,
            "monthly_means": [
                {"month": str(p), "mean": round(float(v), 2)}
                for p, v in monthly.items()
            ],
            "drift_detected": bool(drift.abs().max() > 0.5 * monthly.std()),
            "max_drift": round(float(drift.abs().max()), 2),
        })

    return {"drift": drift_results}


# ─────────────────────────────────────────────────────────────────────────────
# REDUNDANCY GROUPS
# ─────────────────────────────────────────────────────────────────────────────

def feature_redundancy(threshold: float = REDUNDANCY_THRESHOLD) -> Dict:
    """Cluster features by correlation. |r| > threshold = redundant group."""
    feature_df = _get_feature_df()
    available = [f for f in FEATURES if f in feature_df.columns]
    if len(available) < 2:
        return {"groups": []}

    corr = feature_df[available].corr().abs()

    visited = set()
    groups = []
    for feat in available:
        if feat in visited:
            continue
        group = [feat]
        visited.add(feat)
        for other in available:
            if other not in visited and corr.loc[feat, other] >= threshold:
                group.append(other)
                visited.add(other)
        if len(group) > 1:
            groups.append({"features": group, "max_correlation": round(float(corr.loc[group[0], group[1]]), 4)})

    return {"groups": groups, "threshold": threshold}


# ─────────────────────────────────────────────────────────────────────────────
# STABILITY (coefficient of variation)
# ─────────────────────────────────────────────────────────────────────────────

def feature_stability() -> Dict:
    """
    Coefficient of variation (CV = std/mean) per feature across universe.
    High CV = unstable/noisy feature.
    """
    feature_df = _get_feature_df()
    available = [f for f in FEATURES if f in feature_df.columns]

    result = []
    for feat in available:
        vals = feature_df[feat].dropna()
        mean_ = float(vals.mean())
        std_  = float(vals.std())
        cv = std_ / abs(mean_) if mean_ != 0 else 0.0
        result.append({
            "feature": feat,
            "mean": round(mean_, 2),
            "std": round(std_, 2),
            "min": round(float(vals.min()), 2),
            "max": round(float(vals.max()), 2),
            "cv": round(cv, 4),
            "stability": "Low" if cv > 0.5 else ("Medium" if cv > 0.2 else "High"),
            "null_count": int(pd.to_numeric(data_loader.get_df().get(feat, pd.Series()), errors="coerce").isna().sum()),
        })

    return {"stability": result}


# ─────────────────────────────────────────────────────────────────────────────
# FULL ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def full_feature_analysis() -> Dict:
    """Run all feature analyses and return consolidated result."""
    return {
        "importance": permutation_importance(),
        "mutual_information": mutual_information(),
        "correlation": correlation_matrix(),
        "vif": variance_inflation_factor(),
        "shap_proxy": shap_proxy(),
        "drift": feature_drift(),
        "redundancy": feature_redundancy(),
        "stability": feature_stability(),
    }

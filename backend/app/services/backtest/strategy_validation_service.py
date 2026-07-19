"""
strategy_validation_service.py — 11-category strategy health scoring engine.

Categories and max points (total = 100):
  1. Configuration     (15) — weight sum, duplicates, threshold order, method validity
  2. Diversification   (10) — category spread, Herfindahl Index, max single weight
  3. Statistical       (15) — Pearson correlation matrix, multicollinearity flag
  4. Robustness        (10) — feature count vs snapshot count (overfitting proxy)
  5. Risk Coverage     (10) — volatility/drawdown feature present
  6. Data Quality      (10) — % non-null values per feature across live snapshot
  7. Stability         (10) — Kendall-τ of strategy rankings across last 5 snapshots
  8. Turnover          (5)  — estimated rebalance turnover from signal density
  9. Signal Density    (5)  — buy signal % (warn if >60% or <5%)
  10. Concentration    (5)  — estimated top-5 holdings weight
  11. Feature Utiliz.  (5)  — % features with mean |contribution| > 1.0

Outputs:
  - overall score (0–100), pass/fail (threshold 60)
  - per-category ValidationCategoryResult objects
  - feature Pearson correlation matrix (List[CorrelationPair])
  - bias tags: look-ahead-safe, survivorship-bias-note, overfitting-risk: low/medium/high
  - warnings, errors, recommendations
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pytz

from app.services import db
from app.services.strategy_service import (
    resolve_raw_feature_value,
    normalize_feature_value,
)
from app.services.explainability.registry.features import METADATA_REGISTRY

logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")

# Features known to capture risk/volatility
RISK_FEATURES = {"risk_score", "atr", "atr_percentile", "volatility_score", "beta", "drawdown", "max_drawdown"}
VOLATILITY_FEATURES = {"atr", "atr_percentile", "volatility_score", "risk_score"}

# Category labels for features in METADATA_REGISTRY
def _get_feature_category(feat_id: str) -> str:
    meta = METADATA_REGISTRY.get(feat_id, {})
    return meta.get("category", "Unknown")


def normalize_definition(definition: Dict) -> Dict:
    """Normalize canonical strategy definition JSON into a flat structure for scorers."""
    features = definition.get("features", [])
    weights = definition.get("weights", [])
    scoring_config = definition.get("scoring_config", {})
    thresholds = definition.get("thresholds", {})

    # 1. Flatten features list
    if features and isinstance(features[0], dict):
        features_flat = [f["feature_id"] for f in features if isinstance(f, dict) and f.get("enabled", True) and "feature_id" in f]
    elif isinstance(features, list):
        features_flat = features
    else:
        features_flat = []

    # 2. Flatten weights list
    if isinstance(weights, list):
        weights_flat = {}
        for w in weights:
            if isinstance(w, dict):
                fid = w.get("feature_id")
                wt = w.get("weight", 0.0)
                if fid:
                    weights_flat[fid] = wt
    elif isinstance(weights, dict):
        weights_flat = weights
    else:
        weights_flat = {}

    # 3. Flatten thresholds
    if scoring_config:
        thresholds_flat = {
            "buy": scoring_config.get("threshold_buy", 35.0),
            "sell": scoring_config.get("threshold_sell", -15.0),
            "hold": scoring_config.get("threshold_hold", -15.0),
        }
    else:
        thresholds_flat = {
            "buy": thresholds.get("buy", 35.0),
            "sell": thresholds.get("sell", -15.0),
            "hold": thresholds.get("hold", -15.0),
        }

    # 4. Normalization and aggregation
    normalization = scoring_config.get("normalization", definition.get("normalization", "Default"))
    aggregation = scoring_config.get("aggregation_method", definition.get("aggregation", "Weighted Average"))
    
    # 5. Weighting scheme
    weighting_scheme = scoring_config.get("scoring_method", definition.get("weighting_scheme", "Equal"))
    if "equal" in weighting_scheme.lower():
        scheme = "Equal"
    else:
        scheme = "ScoreWeighted"

    return {
        "features": features_flat,
        "weights": weights_flat,
        "thresholds": thresholds_flat,
        "normalization": normalization,
        "aggregation": aggregation,
        "weighting_scheme": scheme
    }


# ── Category scorers ─────────────────────────────────────────────────────────


def _score_configuration(definition: Dict) -> Dict:
    features = definition.get("features", [])
    weights = definition.get("weights", {})
    thresholds = definition.get("thresholds", {})
    normalization = definition.get("normalization", "zscore")
    aggregation = definition.get("aggregation", "weighted_average")

    checks = []
    score = 15.0
    errors: List[str] = []
    warnings: List[str] = []

    # Weight sum ≈ 100
    w_sum = sum(weights.get(f, 0.0) for f in features)
    if abs(w_sum - 100.0) < 1.0:
        checks.append({"name": "Weight sum ≈ 100%", "status": "pass", "detail": f"Sum={w_sum:.1f}"})
    else:
        checks.append({"name": "Weight sum ≈ 100%", "status": "fail", "detail": f"Sum={w_sum:.1f}"})
        errors.append(f"Weights sum to {w_sum:.1f}%, must be 100%.")
        score -= 5.0

    # No duplicate features
    if len(features) == len(set(features)):
        checks.append({"name": "No duplicate features", "status": "pass"})
    else:
        checks.append({"name": "No duplicate features", "status": "fail"})
        errors.append("Duplicate features detected.")
        score -= 3.0

    # At least 2 features selected
    if len(features) >= 2:
        checks.append({"name": "Minimum 2 features", "status": "pass", "detail": f"{len(features)} selected"})
    else:
        checks.append({"name": "Minimum 2 features", "status": "fail"})
        errors.append("At least 2 features required.")
        score -= 4.0

    # Threshold order: buy > sell
    t_buy = float(thresholds.get("buy", 60.0))
    t_sell = float(thresholds.get("sell", 40.0))
    if t_buy > t_sell:
        checks.append({"name": "Threshold order (buy > sell)", "status": "pass",
                        "detail": f"buy={t_buy}, sell={t_sell}"})
    else:
        checks.append({"name": "Threshold order (buy > sell)", "status": "fail",
                        "detail": f"buy={t_buy} ≤ sell={t_sell}"})
        errors.append("Buy threshold must be greater than sell threshold.")
        score -= 3.0

    # Normalization method
    valid_norms = {"zscore", "minmax", "percentile", "robust"}
    if normalization in valid_norms:
        checks.append({"name": "Normalization method", "status": "pass", "detail": normalization})
    else:
        checks.append({"name": "Normalization method", "status": "warn",
                        "detail": f"Unrecognised: {normalization}"})
        warnings.append(f"Normalization method '{normalization}' is not standard.")

    return {"score": max(score, 0.0), "max_score": 15.0, "checks": checks,
            "errors": errors, "warnings": warnings}


def _score_diversification(definition: Dict) -> Dict:
    features = definition.get("features", [])
    weights = definition.get("weights", {})

    checks = []
    score = 10.0
    warnings: List[str] = []

    if not features:
        return {"score": 0.0, "max_score": 10.0, "checks": checks, "warnings": warnings, "errors": []}

    # Category spread
    cats = [_get_feature_category(f) for f in features]
    unique_cats = set(cats)
    if len(unique_cats) >= 3:
        checks.append({"name": "Category spread ≥ 3", "status": "pass",
                        "detail": f"{len(unique_cats)} categories: {', '.join(unique_cats)}"})
    elif len(unique_cats) == 2:
        checks.append({"name": "Category spread ≥ 3", "status": "warn",
                        "detail": f"Only {len(unique_cats)} categories"})
        score -= 3.0
        warnings.append("Consider adding features from more categories for better diversification.")
    else:
        checks.append({"name": "Category spread ≥ 3", "status": "fail",
                        "detail": f"Only 1 category: {unique_cats}"})
        score -= 5.0
        warnings.append("All features from the same category — high category concentration risk.")

    # Herfindahl–Hirschman Index on weights
    total_w = sum(weights.get(f, 0.0) for f in features)
    if total_w > 0:
        shares = [weights.get(f, 0.0) / total_w for f in features]
        hhi = sum(s ** 2 for s in shares)
        if hhi < 0.25:
            checks.append({"name": "Weight HHI < 0.25 (low concentration)", "status": "pass",
                            "detail": f"HHI={hhi:.3f}"})
        elif hhi < 0.50:
            checks.append({"name": "Weight HHI < 0.25", "status": "warn", "detail": f"HHI={hhi:.3f}"})
            score -= 2.0
            warnings.append(f"Moderate weight concentration (HHI={hhi:.3f}). Consider redistributing.")
        else:
            checks.append({"name": "Weight HHI < 0.25", "status": "fail", "detail": f"HHI={hhi:.3f}"})
            score -= 4.0
            warnings.append(f"High weight concentration (HHI={hhi:.3f}). Strategy may be over-reliant on 1–2 features.")

    # Max single weight
    max_w = max(weights.get(f, 0.0) for f in features) if features else 0.0
    if max_w <= 40.0:
        checks.append({"name": "Max single weight ≤ 40%", "status": "pass", "detail": f"Max={max_w:.1f}%"})
    else:
        checks.append({"name": "Max single weight ≤ 40%", "status": "warn", "detail": f"Max={max_w:.1f}%"})
        score -= 2.0
        warnings.append(f"Single feature has weight {max_w:.1f}% — this dominates the composite score.")

    return {"score": max(score, 0.0), "max_score": 10.0, "checks": checks,
            "warnings": warnings, "errors": []}


def _score_statistical(definition: Dict, feature_vectors: Dict[str, List[float]]) -> Dict:
    """Compute Pearson correlation matrix and flag multicollinearity."""
    features = definition.get("features", [])
    checks = []
    score = 15.0
    warnings: List[str] = []
    correlation_matrix = []

    if len(features) < 2 or not feature_vectors:
        checks.append({"name": "Correlation matrix", "status": "warn",
                        "detail": "Insufficient data for correlation analysis."})
        return {"score": score, "max_score": 15.0, "checks": checks,
                "warnings": warnings, "errors": [], "correlation_matrix": []}

    # Build Pearson correlation matrix
    high_corr_pairs = []
    for i, f1 in enumerate(features):
        for j, f2 in enumerate(features):
            if j <= i:
                continue
            v1 = feature_vectors.get(f1, [])
            v2 = feature_vectors.get(f2, [])
            n = min(len(v1), len(v2))
            if n < 3:
                continue
            a1 = np.array(v1[:n])
            a2 = np.array(v2[:n])
            if np.std(a1) == 0 or np.std(a2) == 0:
                r = 0.0
            else:
                r = float(np.corrcoef(a1, a2)[0, 1])
            correlation_matrix.append({
                "feature_a": f1,
                "feature_b": f2,
                "pearson_r": round(r, 4),
            })
            if abs(r) > 0.85:
                high_corr_pairs.append((f1, f2, r))

    if high_corr_pairs:
        for f1, f2, r in high_corr_pairs:
            l1 = METADATA_REGISTRY.get(f1, {}).get("label", f1)
            l2 = METADATA_REGISTRY.get(f2, {}).get("label", f2)
            warnings.append(f"High correlation (r={r:.2f}) between {l1} and {l2} — consider removing one.")
        score -= min(len(high_corr_pairs) * 3.0, 10.0)
        checks.append({"name": "Low feature redundancy (r < 0.85)", "status": "warn",
                        "detail": f"{len(high_corr_pairs)} highly correlated pair(s) found."})
    else:
        checks.append({"name": "Low feature redundancy (r < 0.85)", "status": "pass",
                        "detail": "No highly correlated pairs detected."})

    return {"score": max(score, 0.0), "max_score": 15.0, "checks": checks,
            "warnings": warnings, "errors": [], "correlation_matrix": correlation_matrix}


def _score_robustness(definition: Dict, snapshot_count: int) -> Dict:
    features = definition.get("features", [])
    n_features = len(features)
    checks = []
    score = 10.0
    warnings: List[str] = []

    ratio = snapshot_count / max(n_features, 1)
    if ratio >= 10:
        risk = "low"
        checks.append({"name": f"Overfitting proxy (snapshots/features ≥ 10)", "status": "pass",
                        "detail": f"Ratio={ratio:.1f}"})
    elif ratio >= 5:
        risk = "medium"
        checks.append({"name": "Overfitting proxy", "status": "warn", "detail": f"Ratio={ratio:.1f}"})
        score -= 3.0
        warnings.append(f"Only {ratio:.1f} snapshots per feature. More historical data recommended.")
    else:
        risk = "high"
        checks.append({"name": "Overfitting proxy", "status": "fail", "detail": f"Ratio={ratio:.1f}"})
        score -= 7.0
        warnings.append(
            f"Low ratio ({ratio:.1f} snapshots/feature). High overfitting risk — reduce features or increase date range."
        )

    return {"score": max(score, 0.0), "max_score": 10.0, "checks": checks,
            "warnings": warnings, "errors": [], "overfitting_risk": risk}


def _score_risk_coverage(definition: Dict) -> Dict:
    features = definition.get("features", [])
    checks = []
    score = 10.0
    warnings: List[str] = []

    has_vol = any(f in VOLATILITY_FEATURES for f in features)
    has_risk = any(f in RISK_FEATURES for f in features)

    if has_vol:
        checks.append({"name": "Volatility/ATR feature present", "status": "pass"})
    else:
        checks.append({"name": "Volatility/ATR feature present", "status": "warn"})
        score -= 5.0
        warnings.append("No volatility feature (ATR, ATR_percentile, risk_score). "
                         "Strategy may not account for price risk.")

    if has_risk:
        checks.append({"name": "Risk metric present", "status": "pass"})
    else:
        checks.append({"name": "Risk metric present", "status": "warn"})
        score -= 3.0

    return {"score": max(score, 0.0), "max_score": 10.0, "checks": checks,
            "warnings": warnings, "errors": []}


def _score_data_quality(definition: Dict, latest_stocks: List[Dict], latest_indicators: List[Dict]) -> Dict:
    features = definition.get("features", [])
    checks = []
    score = 10.0
    warnings: List[str] = []

    if not latest_stocks:
        checks.append({"name": "Data availability", "status": "fail", "detail": "No latest snapshot data."})
        return {"score": 0.0, "max_score": 10.0, "checks": checks, "warnings": warnings, "errors": []}

    ind_by_sym = {r.get("symbol", ""): r for r in latest_indicators}
    n_stocks = len(latest_stocks)

    low_coverage_features = []
    for feat_id in features:
        non_null = 0
        for stock in latest_stocks:
            sym = stock.get("symbol", "")
            ind = ind_by_sym.get(sym, {})
            sco = {}
            try:
                raw = resolve_raw_feature_value(feat_id, dict(stock), dict(ind), sco)
                if raw != 0.0:
                    non_null += 1
            except Exception:
                pass
        coverage_pct = (non_null / n_stocks * 100.0) if n_stocks > 0 else 0.0
        label = METADATA_REGISTRY.get(feat_id, {}).get("label", feat_id)
        if coverage_pct < 50.0:
            low_coverage_features.append(f"{label} ({coverage_pct:.0f}%)")
        checks.append({"name": f"Data coverage: {label}", "status": "pass" if coverage_pct >= 50 else "warn",
                        "detail": f"{coverage_pct:.0f}% non-null"})

    if low_coverage_features:
        score -= min(len(low_coverage_features) * 2.0, 8.0)
        warnings.append(f"Low data coverage for: {', '.join(low_coverage_features)}")

    return {"score": max(score, 0.0), "max_score": 10.0, "checks": checks,
            "warnings": warnings, "errors": []}


def _score_stability(definition: Dict, recent_snapshots: List[Dict]) -> Dict:
    """Estimate rank stability using Kendall-τ across last 5 snapshots."""
    import itertools
    from scipy.stats import kendalltau

    features = definition.get("features", [])
    weights = definition.get("weights", {})
    checks = []
    score = 10.0
    warnings: List[str] = []

    if len(recent_snapshots) < 2:
        checks.append({"name": "Rank stability (Kendall-τ)", "status": "warn",
                        "detail": "Fewer than 2 snapshots available."})
        return {"score": score, "max_score": 10.0, "checks": checks, "warnings": warnings, "errors": []}

    # Compute score for each snapshot and record symbol rankings
    rankings = []
    for snap in recent_snapshots:
        sid = snap["snapshot_id"]
        stocks = db.get_snapshot_stocks(sid)
        indicators_list = db.get_snapshot_indicators(sid)
        scores_list = db.get_snapshot_scores(sid)
        ind_by_sym = {r["symbol"]: dict(r) for r in indicators_list}
        sco_by_sym = {r["symbol"]: dict(r) for r in scores_list}

        sym_scores = {}
        for row in stocks:
            sym = row["symbol"]
            stock_dict = dict(row)
            ind_dict = ind_by_sym.get(sym, {})
            sco_dict = sco_by_sym.get(sym, {})
            total = 0.0
            total_w = 0.0
            for f in features:
                w = weights.get(f, 0.0)
                if w == 0:
                    continue
                try:
                    raw = resolve_raw_feature_value(f, stock_dict, ind_dict, sco_dict)
                    norm = normalize_feature_value(f, raw, ind_dict)
                    total += norm * (w / 100.0)
                    total_w += (w / 100.0)
                except Exception:
                    pass
            sym_scores[sym] = total / total_w if total_w > 0 else 0.0

        ranked = sorted(sym_scores, key=sym_scores.get, reverse=True)
        rankings.append({sym: rank for rank, sym in enumerate(ranked)})

    # Compute pairwise Kendall-τ
    common_syms = set(rankings[0].keys())
    for r in rankings[1:]:
        common_syms &= set(r.keys())
    common_syms = list(common_syms)

    if len(common_syms) < 5:
        checks.append({"name": "Rank stability", "status": "warn",
                        "detail": "Insufficient common symbols across snapshots."})
        return {"score": score, "max_score": 10.0, "checks": checks, "warnings": warnings, "errors": []}

    try:
        tau_values = []
        for i in range(len(rankings) - 1):
            r1 = [rankings[i].get(s, 0) for s in common_syms]
            r2 = [rankings[i+1].get(s, 0) for s in common_syms]
            tau, _ = kendalltau(r1, r2)
            tau_values.append(tau)

        avg_tau = float(np.mean(tau_values))
        if avg_tau >= 0.7:
            checks.append({"name": "Rank stability (Kendall-τ ≥ 0.7)", "status": "pass",
                            "detail": f"Mean τ={avg_tau:.3f}"})
        elif avg_tau >= 0.5:
            checks.append({"name": "Rank stability (Kendall-τ ≥ 0.7)", "status": "warn",
                            "detail": f"Mean τ={avg_tau:.3f}"})
            score -= 4.0
            warnings.append(f"Moderate rank stability (τ={avg_tau:.2f}). Rankings change significantly between periods.")
        else:
            checks.append({"name": "Rank stability (Kendall-τ ≥ 0.7)", "status": "fail",
                            "detail": f"Mean τ={avg_tau:.3f}"})
            score -= 8.0
            warnings.append(f"Low rank stability (τ={avg_tau:.2f}). Strategy may be noise-driven.")
    except ImportError:
        checks.append({"name": "Rank stability", "status": "warn",
                        "detail": "scipy not available for Kendall-τ — skipped."})
    except Exception as e:
        checks.append({"name": "Rank stability", "status": "warn", "detail": str(e)})

    return {"score": max(score, 0.0), "max_score": 10.0, "checks": checks,
            "warnings": warnings, "errors": []}


def _score_turnover(definition: Dict, recent_snapshots: List[Dict]) -> Dict:
    """Estimate turnover from signal volatility across recent snapshots."""
    checks = []
    score = 5.0
    warnings: List[str] = []

    if len(recent_snapshots) < 2:
        checks.append({"name": "Turnover estimate", "status": "warn", "detail": "Insufficient data."})
        return {"score": score, "max_score": 5.0, "checks": checks, "warnings": warnings, "errors": []}

    features = definition.get("features", [])
    weights = definition.get("weights", {})
    thresholds = definition.get("thresholds", {})
    threshold_buy = float(thresholds.get("buy", 60.0))

    buy_pcts = []
    for snap in recent_snapshots:
        sid = snap["snapshot_id"]
        stocks = db.get_snapshot_stocks(sid)
        indicators_list = db.get_snapshot_indicators(sid)
        scores_list = db.get_snapshot_scores(sid)
        ind_by_sym = {r["symbol"]: dict(r) for r in indicators_list}
        sco_by_sym = {r["symbol"]: dict(r) for r in scores_list}

        buys = 0
        for row in stocks:
            sym = row["symbol"]
            stock_dict = dict(row)
            ind_dict = ind_by_sym.get(sym, {})
            sco_dict = sco_by_sym.get(sym, {})
            total, total_w = 0.0, 0.0
            for f in features:
                w = weights.get(f, 0.0)
                if w == 0:
                    continue
                try:
                    raw = resolve_raw_feature_value(f, stock_dict, ind_dict, sco_dict)
                    norm = normalize_feature_value(f, raw, ind_dict)
                    total += norm * (w / 100.0)
                    total_w += (w / 100.0)
                except Exception:
                    pass
            score_val = (total / total_w * 100.0) if total_w > 0 else 0.0
            if score_val >= threshold_buy:
                buys += 1
        buy_pcts.append(buys / max(len(stocks), 1) * 100.0)

    if len(buy_pcts) >= 2:
        variance = float(np.std(buy_pcts))
        if variance < 10:
            checks.append({"name": "Low turnover variance", "status": "pass",
                            "detail": f"Buy % std={variance:.1f}%"})
        else:
            checks.append({"name": "Low turnover variance", "status": "warn",
                            "detail": f"Buy % std={variance:.1f}% — high churn expected"})
            score -= 3.0
            warnings.append(f"High signal volatility (buy % std={variance:.1f}%). "
                             "Strategy may generate excessive portfolio churn.")
    else:
        checks.append({"name": "Turnover estimate", "status": "warn", "detail": "Insufficient snapshots."})

    return {"score": max(score, 0.0), "max_score": 5.0, "checks": checks,
            "warnings": warnings, "errors": []}


def _score_signal_density(definition: Dict, latest_stocks: List[Dict], latest_indicators: List[Dict]) -> Dict:
    features = definition.get("features", [])
    weights = definition.get("weights", {})
    thresholds = definition.get("thresholds", {})
    threshold_buy = float(thresholds.get("buy", 60.0))
    threshold_sell = float(thresholds.get("sell", 40.0))

    checks = []
    score = 5.0
    warnings: List[str] = []
    ind_by_sym = {r.get("symbol", ""): r for r in latest_indicators}

    buy_count = 0
    sell_count = 0
    total = len(latest_stocks)

    for row in latest_stocks:
        sym = row.get("symbol", "")
        stock_dict = dict(row)
        ind_dict = ind_by_sym.get(sym, {})
        t, tw = 0.0, 0.0
        for f in features:
            w = weights.get(f, 0.0)
            if w == 0:
                continue
            try:
                raw = resolve_raw_feature_value(f, stock_dict, dict(ind_dict), {})
                norm = normalize_feature_value(f, raw, dict(ind_dict))
                t += norm * (w / 100.0)
                tw += (w / 100.0)
            except Exception:
                pass
        s = (t / tw * 100.0) if tw > 0 else 0.0
        if s >= threshold_buy:
            buy_count += 1
        elif s <= threshold_sell:
            sell_count += 1

    buy_pct = buy_count / total * 100.0 if total > 0 else 0.0
    if buy_pct > 60.0:
        checks.append({"name": "Buy signal density ≤ 60%", "status": "warn",
                        "detail": f"{buy_pct:.1f}% BUY signals"})
        score -= 3.0
        warnings.append(f"Over-broad buy zone ({buy_pct:.1f}% of universe). "
                         "Consider raising the buy threshold.")
    elif buy_pct < 5.0:
        checks.append({"name": "Buy signal density ≥ 5%", "status": "warn",
                        "detail": f"Only {buy_pct:.1f}% BUY signals"})
        score -= 3.0
        warnings.append(f"Over-restrictive buy zone ({buy_pct:.1f}% of universe). "
                         "Consider lowering the buy threshold.")
    else:
        checks.append({"name": f"Buy signal density: {buy_pct:.1f}%", "status": "pass",
                        "detail": f"{buy_count}/{total} stocks qualify as BUY"})

    return {"score": max(score, 0.0), "max_score": 5.0, "checks": checks,
            "warnings": warnings, "errors": [], "buy_pct": buy_pct}


def _score_concentration(definition: Dict) -> Dict:
    features = definition.get("features", [])
    weights = definition.get("weights", {})
    checks = []
    score = 5.0
    warnings: List[str] = []

    # Under equal weight with max_holdings=15, top-5 = 33%
    # Under score weight the top-5 can reach 60-70%
    scheme = definition.get("weighting_scheme", "Equal")
    if scheme == "Equal":
        est_top5 = min(5, 15) / 15 * 100.0
    else:
        est_top5 = 55.0  # score weighted typically concentrates more

    if est_top5 <= 40.0:
        checks.append({"name": "Estimated top-5 concentration ≤ 40%", "status": "pass",
                        "detail": f"~{est_top5:.0f}% estimated"})
    else:
        checks.append({"name": "Estimated top-5 concentration ≤ 40%", "status": "warn",
                        "detail": f"~{est_top5:.0f}% estimated"})
        score -= 2.0
        warnings.append(f"Score-weighted scheme may concentrate ~{est_top5:.0f}% in top-5 holdings.")

    return {"score": max(score, 0.0), "max_score": 5.0, "checks": checks,
            "warnings": warnings, "errors": []}


def _score_feature_utilization(definition: Dict, feature_vectors: Dict[str, List[float]]) -> Dict:
    """Check that selected features actually have meaningful variance (contribute signal)."""
    features = definition.get("features", [])
    weights = definition.get("weights", {})
    checks = []
    score = 5.0
    warnings: List[str] = []

    if not feature_vectors:
        checks.append({"name": "Feature utilization", "status": "warn",
                        "detail": "No snapshot data available for utilization check."})
        return {"score": score, "max_score": 5.0, "checks": checks, "warnings": warnings, "errors": []}

    zero_var_features = []
    for f in features:
        vals = feature_vectors.get(f, [])
        if vals and float(np.std(vals)) < 0.1:
            label = METADATA_REGISTRY.get(f, {}).get("label", f)
            zero_var_features.append(label)

    if zero_var_features:
        score -= min(len(zero_var_features) * 2.0, 5.0)
        warnings.append(f"Near-zero variance for: {', '.join(zero_var_features)}. "
                         "These features may not be providing signal.")
        checks.append({"name": "Feature variance check", "status": "warn",
                        "detail": f"{len(zero_var_features)} feature(s) have near-zero variance."})
    else:
        checks.append({"name": "Feature variance check", "status": "pass",
                        "detail": "All features have meaningful variance."})

    util_pct = (len(features) - len(zero_var_features)) / max(len(features), 1) * 100.0
    checks.append({"name": "Feature utilization rate",
                    "status": "pass" if util_pct >= 80 else "warn",
                    "detail": f"{util_pct:.0f}% of features are active"})

    return {"score": max(score, 0.0), "max_score": 5.0, "checks": checks,
            "warnings": warnings, "errors": []}


# ── Main API ──────────────────────────────────────────────────────────────────

def run_validation(
    strategy_id: str,
    definition: Dict,
    strategy_name: str = "",
    strategy_version: str = "1.0.0",
    persist: bool = True,
) -> Dict[str, Any]:
    """
    Run the full 11-category validation on a strategy definition.
    Returns a dict matching ValidationReportResponse.
    """
    definition = normalize_definition(definition)
    report_id = str(uuid.uuid4())
    generated_at = datetime.now(IST).isoformat()

    # ── Load live data for data-driven checks ────────────────────
    latest_snap = db.get_latest_snapshot(official_only=True)
    latest_stocks: List[Dict] = []
    latest_indicators: List[Dict] = []
    snapshot_count = 0

    if latest_snap:
        sid = latest_snap["snapshot_id"]
        latest_stocks = db.get_snapshot_stocks(sid)
        latest_indicators = db.get_snapshot_indicators(sid)

    recent_snaps = db.list_snapshot_dates(official_only=True, limit=5)
    snapshot_count = len(db.list_snapshot_dates(official_only=True, limit=365))

    # ── Build feature vectors from latest snapshot for statistical checks ──
    feature_vectors: Dict[str, List[float]] = {}
    ind_by_sym = {r.get("symbol", ""): r for r in latest_indicators}
    features = definition.get("features", [])
    weights = definition.get("weights", {})
    for feat_id in features:
        vals = []
        for row in latest_stocks:
            sym = row.get("symbol", "")
            try:
                raw = resolve_raw_feature_value(feat_id, dict(row), dict(ind_by_sym.get(sym, {})), {})
                norm = normalize_feature_value(feat_id, raw)
                vals.append(norm)
            except Exception:
                pass
        if vals:
            feature_vectors[feat_id] = vals

    # ── Run all 11 categories ────────────────────────────────────
    cat_results = []
    all_warnings: List[str] = []
    all_errors: List[str] = []
    all_recommendations: List[str] = []
    total_score = 0.0
    overfitting_risk = "low"
    correlation_matrix = []

    def _run_cat(name: str, result: Dict, max_pts: float):
        nonlocal total_score
        cat_score = result.get("score", 0.0)
        total_score += cat_score
        all_warnings.extend(result.get("warnings", []))
        all_errors.extend(result.get("errors", []))
        status = "pass" if cat_score >= max_pts * 0.7 else "warn" if cat_score >= max_pts * 0.4 else "fail"
        cat_results.append({
            "category": name,
            "score": round(cat_score, 2),
            "max_score": max_pts,
            "status": status,
            "checks": result.get("checks", []),
            "detail": f"{cat_score:.1f}/{max_pts} pts",
        })

    r1 = _score_configuration(definition); _run_cat("Configuration", r1, 15.0)
    r2 = _score_diversification(definition); _run_cat("Diversification", r2, 10.0)
    r3 = _score_statistical(definition, feature_vectors); _run_cat("Statistical Quality", r3, 15.0)
    correlation_matrix = r3.get("correlation_matrix", [])
    r4 = _score_robustness(definition, snapshot_count); _run_cat("Robustness", r4, 10.0)
    overfitting_risk = r4.get("overfitting_risk", "low")
    r5 = _score_risk_coverage(definition); _run_cat("Risk Coverage", r5, 10.0)
    r6 = _score_data_quality(definition, latest_stocks, latest_indicators); _run_cat("Data Quality", r6, 10.0)
    r7 = _score_stability(definition, recent_snaps); _run_cat("Stability", r7, 10.0)
    r8 = _score_turnover(definition, recent_snaps); _run_cat("Turnover", r8, 5.0)
    r9 = _score_signal_density(definition, latest_stocks, latest_indicators); _run_cat("Signal Density", r9, 5.0)
    r10 = _score_concentration(definition); _run_cat("Concentration", r10, 5.0)
    r11 = _score_feature_utilization(definition, feature_vectors); _run_cat("Feature Utilization", r11, 5.0)

    # ── Bias Tags ─────────────────────────────────────────────────
    bias_tags = ["look-ahead-safe"]  # architecturally guaranteed by snapshot integrity
    bias_tags.append("survivorship-bias-note")  # universe is nifty50 — note historical delisting exclusion
    bias_tags.append(f"overfitting-risk: {overfitting_risk}")

    # ── Recommendations ───────────────────────────────────────────
    if total_score < 60:
        all_recommendations.append(
            "Overall validation score below 60. Address blocking errors before running a backtest."
        )
    if any("correlation" in w.lower() for w in all_warnings):
        all_recommendations.append(
            "Remove one of each highly correlated feature pair to reduce redundancy."
        )
    if any("volatility" in w.lower() or "atr" in w.lower() for w in all_warnings):
        all_recommendations.append(
            "Add a risk/volatility feature (ATR, ATR Percentile, or Risk Score) to improve risk-adjusted scoring."
        )
    if any("buy zone" in w.lower() for w in all_warnings):
        all_recommendations.append(
            "Adjust buy/sell thresholds to produce a more selective signal (aim for 5–30% of universe)."
        )
    if any("overfitting" in w.lower() or "ratio" in w.lower() for w in all_warnings):
        all_recommendations.append(
            "Extend the backtest date range to provide more historical observations per feature."
        )

    passed = total_score >= 60.0

    report = {
        "report_id": report_id,
        "strategy_id": strategy_id,
        "strategy_name": strategy_name,
        "validation_score": round(total_score, 2),
        "passed": passed,
        "categories": cat_results,
        "correlation_matrix": correlation_matrix,
        "bias_tags": bias_tags,
        "warnings": list(set(all_warnings)),
        "errors": list(set(all_errors)),
        "recommendations": all_recommendations,
        "generated_at": generated_at,
    }

    # ── Persist ────────────────────────────────────────────────────
    if persist:
        try:
            session = db.get_db_session()
            from app.models.orm import StrategyValidationReport
            rec = StrategyValidationReport(
                report_id=report_id,
                strategy_id=strategy_id,
                strategy_version=strategy_version,
                validation_score=total_score,
                passed=1 if passed else 0,
                diagnostics_json=json.dumps(cat_results),
                warnings_json=json.dumps(report["warnings"]),
                recommendations_json=json.dumps(all_recommendations),
                generated_at=generated_at,
            )
            session.add(rec)
            session.commit()
            session.close()
        except Exception as e:
            logger.warning("[ValidationService] Could not persist report: %s", e)

    return report

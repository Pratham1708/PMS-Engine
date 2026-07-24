"""
strategy_service.py — Strategy orchestration service for CRUD, validation, execution, and explainability.
"""

import uuid
import json
import time
import re
import math
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

from app.models.orm import StrategyMaster, StrategyVersion
from app.models.schemas import (
    StrategyResponse, 
    StrategyDefinitionModel, 
    FeatureSelectionModel, 
    WeightAllocationModel, 
    ScoringConfigModel,
    StrategyVersionModel,
    CompareMetricRecord,
    ExplainScoreResponse,
    Contribution,
    ValidationMetric,
    ResearchReference,
    ScoreInterpretation,
    FeatureAttribution,
    CategoryContribution,
    FeatureMetadata,
    NormalizationExplain,
    StrategyCreateRequest,
    StrategyUpdateRequest
)
from app.services import db
from app.services.strategy_validator import validate_strategy_config
from app.services.strategy_runtime import build_runtime_config

# Import registries
from app.services.explainability.registry.features import METADATA_REGISTRY
from app.services.explainability.registry.formulas import FORMULA_REGISTRY
from app.services.explainability.registry.normalization import NORMALIZATION_REGISTRY
from app.services.explainability.registry.references import REFERENCE_REGISTRY
from app.services.explainability.registry import (
    COMPOSITE_WEIGHTS,
    TECHNICAL_WEIGHTS,
    TECHNICAL_TREND_WEIGHTS,
    TECHNICAL_MOMENTUM_WEIGHTS,
    TECHNICAL_VOLUME_WEIGHTS,
    TECHNICAL_VOLATILITY_WEIGHTS,
    TECHNICAL_BREAKOUT_WEIGHTS,
    GRU_WEIGHTS,
    GRU_PATTERN_WEIGHTS,
    ENSEMBLE_WEIGHTS,
    TREND_WEIGHTS,
    MOMENTUM_WEIGHTS,
    RISK_WEIGHTS,
    RELIABILITY_WEIGHTS,
    CONFIDENCE_WEIGHTS
)


# ── Feature Registry Dynamic Resolution ──

def get_default_weight_for_feature(feature_id: str) -> float:
    """Find default weight from registry files for a given feature."""
    # Composite level
    if feature_id in COMPOSITE_WEIGHTS:
        return COMPOSITE_WEIGHTS[feature_id] * 100.0
    # Technical subweights
    if feature_id in TECHNICAL_TREND_WEIGHTS:
        return TECHNICAL_TREND_WEIGHTS[feature_id] * 100.0
    if feature_id in TECHNICAL_MOMENTUM_WEIGHTS:
        return TECHNICAL_MOMENTUM_WEIGHTS[feature_id] * 100.0
    if feature_id in TECHNICAL_VOLUME_WEIGHTS:
        return TECHNICAL_VOLUME_WEIGHTS[feature_id] * 100.0
    if feature_id in TECHNICAL_VOLATILITY_WEIGHTS:
        return TECHNICAL_VOLATILITY_WEIGHTS[feature_id] * 100.0
    if feature_id in TECHNICAL_BREAKOUT_WEIGHTS:
        return TECHNICAL_BREAKOUT_WEIGHTS[feature_id] * 100.0
    # GRU subweights
    if feature_id in GRU_PATTERN_WEIGHTS:
        return GRU_PATTERN_WEIGHTS[feature_id] * 100.0
    # Ensemble subweights
    if feature_id in ENSEMBLE_WEIGHTS:
        return ENSEMBLE_WEIGHTS[feature_id] * 100.0
    # Rollup rollups
    if feature_id == "technical":
        return 40.0
    if feature_id == "ml":
        return 35.0
    if feature_id == "gru":
        return 15.0
    if feature_id == "reliability":
        return 10.0
    return 0.0


def get_features_registry() -> List[Dict[str, Any]]:
    """Compile and return the aggregated, dynamic feature registry."""
    features_list = []
    for fid, meta in METADATA_REGISTRY.items():
        formula = FORMULA_REGISTRY.get(fid, {})
        norm = NORMALIZATION_REGISTRY.get(fid, {})
        ref = REFERENCE_REGISTRY.get(fid, {})
        
        feature_data = {
            "feature_id": fid,
            "display_name": meta.get("display_name", fid),
            "category": meta.get("category", "General"),
            "data_source": meta.get("data_source", "Unknown"),
            "description": meta.get("description", ""),
            "plain_formula": formula.get("plain_formula", ""),
            "latex_formula": formula.get("latex_formula", ""),
            "normalization_method": norm.get("method", "Default"),
            "normalization_logic": norm.get("logic", ""),
            "paper": ref.get("paper", ""),
            "author": ref.get("author", ""),
            "year": ref.get("year", ""),
            "link": ref.get("link", ""),
            "reference_description": ref.get("description", ""),
            "default_weight": get_default_weight_for_feature(fid),
            "units": "%" if fid in ["rsi", "mfi", "atr_percentile", "stoch_k"] else ("Ratio" if "ratio" in fid or "ma" in fid else "Score"),
            "supported_scoring_methods": ["Weighted Average", "Weighted Rank", "Percentile Rank", "Min-Max", "Z-Score"]
        }
        features_list.append(feature_data)
    return features_list


# ── Feature Value Resolver and Normalizer ──

def _build_feature_alias_map() -> Dict[str, str]:
    alias_map = {}
    for fid, meta in METADATA_REGISTRY.items():
        clean_key = re.sub(r'[^a-zA-Z0-9]', '', fid).lower()
        alias_map[clean_key] = fid
        display_name = meta.get("display_name", "")
        if display_name:
            clean_display = re.sub(r'[^a-zA-Z0-9]', '', display_name).lower()
            alias_map[clean_display] = fid
            words = [re.sub(r'[^a-zA-Z0-9]', '', w) for w in display_name.split()]
            for i in range(1, len(words) + 1):
                comb = "".join(words[:i]).lower()
                if comb and comb not in alias_map:
                    alias_map[comb] = fid

    manual_overrides = {
        "ensemblemlscore": "ml_score",
        "mlscore": "ml_score",
        "modelreliability": "reliability_score",
        "resistancebreakout": "resistance_break",
        "regimesimilarityindex": "similarity",
        "regimesimilarity": "similarity",
        "grudeepcomponent": "gru_score",
        "maximumhistoricaldrawdown": "drawdown",
        "maxdrawdown": "drawdown",
        "volumemovingaverageratio": "volume_ma",
        "sharperatio": "sharpe",
    }
    alias_map.update(manual_overrides)
    return alias_map

FEATURE_ALIAS_MAP = _build_feature_alias_map()

def get_canonical_feature_id(feature_id: str) -> str:
    clean = re.sub(r'[^a-zA-Z0-9]', '', feature_id).lower()
    return FEATURE_ALIAS_MAP.get(clean, feature_id)


def resolve_raw_feature_value(feature_id: str, indicators: dict, scores: dict, stock_row: dict) -> float:
    """
    Resolve raw feature value dynamically from database dictionaries using logical derivations
    from available OHLCV, indicators, and score components.
    """
    cid = get_canonical_feature_id(feature_id)
    
    # 1. Direct DB column checks
    if cid in indicators and indicators[cid] is not None:
        return float(indicators[cid])
    if cid in scores and scores[cid] is not None:
        return float(scores[cid])
    if cid in stock_row and stock_row[cid] is not None:
        return float(stock_row[cid])
        
    # Case-insensitive direct column checks
    ind_lower = {k.lower(): v for k, v in indicators.items()}
    if cid in ind_lower and ind_lower[cid] is not None:
        return float(ind_lower[cid])
    scores_lower = {k.lower(): v for k, v in scores.items()}
    if cid in scores_lower and scores_lower[cid] is not None:
        return float(scores_lower[cid])
    stock_lower = {k.lower(): v for k, v in stock_row.items()}
    if cid in stock_lower and stock_lower[cid] is not None:
        return float(stock_lower[cid])

    # Standard column mapping aliases
    col_map = {
        "rsi": indicators.get("rsi_14"),
        "atr": indicators.get("atr_14"),
        "adx": indicators.get("adx_14"),
        "ema20": indicators.get("above_ema20"),
        "ema50": indicators.get("above_ema50"),
        "ema200": indicators.get("above_ema200"),
        "rf": scores.get("rf_signal"),
        "xgb": scores.get("xgb_signal"),
        "lgb": scores.get("lgbm_signal"),
        "p_long": scores.get("gru_long"),
        "p_hold": scores.get("gru_hold"),
        "p_short": scores.get("gru_short"),
    }
    if cid in col_map and col_map[cid] is not None:
        return float(col_map[cid])

    # 2. Quantitative logical derivations from available OHLCV + Indicators + Scores
    close = float(stock_row.get("close") or 0.0)
    high = float(stock_row.get("high") or close)
    low = float(stock_row.get("low") or close)
    prev_close = float(stock_row.get("prev_close") or close)
    volume = float(stock_row.get("volume") or 0.0)
    w52_high = float(stock_row.get("week52_high") or high)
    w52_low = float(stock_row.get("week52_low") or low)
    chg_pct = float(stock_row.get("daily_chg_pct") or 0.0)

    rsi_14 = float(indicators.get("rsi_14") or 50.0)
    macd = float(indicators.get("macd") or 0.0)
    macd_sig = float(indicators.get("macd_signal") or 0.0)
    bb_upper = float(indicators.get("bb_upper") or close * 1.05)
    bb_lower = float(indicators.get("bb_lower") or close * 0.95)
    atr_14 = float(indicators.get("atr_14") or max(high - low, 0.01))
    stoch_k = float(indicators.get("stoch_k") or 50.0)
    adx_14 = float(indicators.get("adx_14") or 25.0)
    vwap = float(indicators.get("vwap") or close)
    above_ema20 = bool(indicators.get("above_ema20"))
    above_ema50 = bool(indicators.get("above_ema50"))
    above_ema200 = bool(indicators.get("above_ema200"))
    near_high = bool(indicators.get("near_52w_high"))
    near_low = bool(indicators.get("near_52w_low"))

    tech_score = float(stock_row.get("technical_score") or 50.0)
    ml_score = float(stock_row.get("ml_score") or 50.0)
    gru_score = float(stock_row.get("gru_score") or 50.0)
    risk_score = float(stock_row.get("risk_score") or 15.0)
    mom_score = float(stock_row.get("momentum_score") or 50.0)
    trend_score = float(stock_row.get("trend_score") or 50.0)
    comp_score = float(stock_row.get("composite_score") or 50.0)
    rel_score = float(stock_row.get("reliability_score") or 70.0)
    conf = float(stock_row.get("confidence") or 60.0)

    vol_comp = float(scores.get("volatility_component") or risk_score)
    volu_comp = float(scores.get("volume_component") or 10.0)

    if cid == "stoch_k":
        return stoch_k if stoch_k != 50.0 else max(0.0, min(100.0, (close - low) / (high - low + 1e-5) * 100.0))
    elif cid == "cci":
        return max(-100.0, min(100.0, (close - vwap) / (atr_14 + 1e-5) * 50.0))
    elif cid == "roc":
        return chg_pct
    elif cid == "williams_r":
        return max(-100.0, min(0.0, (high - close) / (high - low + 1e-5) * -100.0))
    elif cid == "obv":
        return float(indicators.get("obv") or (volume * (1.0 if chg_pct >= 0 else -1.0)))
    elif cid == "mfi":
        return max(0.0, min(100.0, rsi_14 * 0.7 + (30.0 if chg_pct > 0 else 0.0)))
    elif cid == "volume_ma":
        return max(0.1, volu_comp / 10.0)
    elif cid == "cmf":
        return max(-1.0, min(1.0, ((close - low) - (high - close)) / (high - low + 1e-5)))
    elif cid == "volume_breakout":
        return 1.0 if (volu_comp > 15.0 or (chg_pct > 1.5 and volume > 0)) else 0.0
    elif cid == "hist_vol":
        return abs(chg_pct) * math.sqrt(252.0)
    elif cid == "bb_width":
        return max(0.1, (bb_upper - bb_lower) / (vwap + 1e-5) * 100.0)
    elif cid == "atr_percentile":
        return max(0.0, min(100.0, (atr_14 / (close + 1e-5)) * 2000.0))
    elif cid == "resistance_break":
        return 1.0 if (near_high or close >= w52_high * 0.97) else 0.0
    elif cid == "support_holding":
        return 1.0 if (not near_low and close >= w52_low * 1.05) else 0.0
    elif cid == "donchian_breakout":
        return max(0.0, min(100.0, (close - w52_low) / (w52_high - w52_low + 1e-5) * 100.0))
    elif cid == "volume_confirmation":
        return 1.0 if (chg_pct > 0 and volu_comp > 10.0) else 0.0
    elif cid == "higher_highs":
        return 1.0 if (above_ema20 and chg_pct > 0) else 0.0
    elif cid == "higher_lows":
        return 1.0 if (above_ema50 and close > prev_close) else 0.0
    elif cid == "volume_expansion":
        return 1.0 if (chg_pct > 0 and volu_comp > 12.0) else 0.0
    elif cid == "volatility_compression":
        return 1.0 if (atr_14 / (close + 1e-5) < 0.015) else 0.0
    elif cid == "trend_persistence":
        return float(int(above_ema200) + int(above_ema50) + int(above_ema20))
    elif cid == "beta":
        return max(0.2, min(3.0, 1.0 + (vol_comp - 15.0) / 20.0))
    elif cid == "sharpe":
        return max(-2.0, min(4.0, (comp_score - 10.0) / (max(risk_score, 10.0))))
    elif cid == "volatility":
        return risk_score
    elif cid == "drawdown":
        return max(-80.0, min(0.0, (close - w52_high) / (w52_high + 1e-5) * 100.0))
    elif cid == "downside_dev":
        return max(0.0, abs(min(0.0, chg_pct)) * 15.8)
    elif cid == "var":
        return max(-10.0, -(chg_pct - 1.645 * max(risk_score / 10.0, 1.0)))
    elif cid == "cvar":
        return max(-15.0, -(chg_pct - 2.06 * max(risk_score / 10.0, 1.0)))
    elif cid == "confidence_inverse":
        return 100.0 - conf
    elif cid == "accuracy":
        return rel_score
    elif cid == "agreement":
        return max(0.0, 100.0 - abs(tech_score - ml_score))
    elif cid == "completeness":
        return 100.0 if stock_row.get("download_status") == "success" else 80.0
    elif cid == "similarity":
        return rel_score
    elif cid == "baseline":
        return conf
    elif cid == "consensus_boost":
        return 15.0 if (tech_score > 20 and ml_score > 20) else (-10.0 if (tech_score < -20 and ml_score < -20) else 0.0)
    elif cid == "supertrend":
        return 100.0 if (above_ema20 and rsi_14 > 45) else 0.0

    return comp_score


def normalize_feature_value(feature_id: str, raw_val: float, indicators: dict = None) -> float:
    """Normalize raw value to standard -100 to +100 range logically based on feature domain."""
    cid = get_canonical_feature_id(feature_id)
    
    # 1. Rollups and pre-normalized scores (-100 to +100)
    if cid in ["technical_score", "ml_score", "gru_score", "reliability_score", "risk_score", "momentum_score", "trend_score", "composite_score"]:
        return max(-100.0, min(100.0, raw_val))
        
    # 2. Binary / Flag features (0 or 1 -> -100 or +100)
    if cid in ["ema20", "ema50", "ema200", "resistance_break", "support_holding", "volume_breakout", "volume_confirmation", "higher_highs", "higher_lows", "volume_expansion", "volatility_compression"]:
        return 100.0 if (raw_val == 1 or raw_val > 0.5) else -100.0
        
    # 3. Oscillators centered around 50 (0 to 100 -> -100 to +100)
    if cid in ["rsi", "mfi", "stoch_k", "atr_percentile", "donchian_breakout", "accuracy", "agreement", "completeness", "similarity", "baseline"]:
        return max(-100.0, min(100.0, (raw_val - 50.0) * 2.0))
        
    # 4. Oscillators centered around 0 (williams_r: -100 to 0 -> -100 to +100)
    if cid == "williams_r":
        return max(-100.0, min(100.0, (raw_val + 50.0) * 2.0))
        
    # 5. Trend strength / ADX (0 to 100 -> thresholded or centered)
    if cid == "adx":
        return max(-100.0, min(100.0, (raw_val - 25.0) * 4.0))
        
    # 6. Supertrend (-100 or +100)
    if cid == "supertrend":
        return 100.0 if raw_val > 0 else -100.0
        
    # 7. MACD divergence
    if cid in ["macd", "macd_signal"]:
        if indicators:
            macd_val = float(indicators.get("macd") or 0.0)
            sig_val = float(indicators.get("macd_signal") or 0.0)
            return 100.0 if macd_val > sig_val else -100.0
        return 100.0 if raw_val > 0 else -100.0
        
    # 8. Unbounded indicators with scaling (CCI, ROC, CMF, Volume MA, Hist Vol, BB Width)
    if cid == "cci":
        return max(-100.0, min(100.0, raw_val))
    elif cid == "roc":
        return max(-100.0, min(100.0, raw_val * 5.0))
    elif cid == "obv":
        return 100.0 if raw_val > 0 else -100.0
    elif cid == "cmf":
        return max(-100.0, min(100.0, raw_val * 100.0))
    elif cid == "volume_ma":
        return max(-100.0, min(100.0, (raw_val - 1.0) * 100.0))
    elif cid in ["atr", "hist_vol", "bb_width"]:
        return max(-100.0, min(100.0, (raw_val - 10.0) * 5.0))
        
    # 9. Model probabilities (0 to 1 -> -100 to +100)
    if cid in ["rf", "xgb", "lgb", "p_long", "p_short", "p_hold"]:
        if abs(raw_val) <= 1.0:
            return max(-100.0, min(100.0, (raw_val - 0.5) * 200.0))
        return max(-100.0, min(100.0, raw_val * 2.0 if abs(raw_val) <= 50.0 else raw_val))
        
    # 10. Risk & Ratio metrics (Beta, Sharpe, Volatility, Drawdown, VaR, CVaR, Downside Dev)
    if cid == "beta":
        return max(-100.0, min(100.0, (raw_val - 1.0) * 100.0))
    elif cid == "sharpe":
        return max(-100.0, min(100.0, raw_val * 50.0))
    elif cid == "volatility":
        return max(-100.0, min(100.0, (raw_val - 15.0) * 5.0))
    elif cid == "drawdown":
        return max(-100.0, min(100.0, raw_val * 2.0))
    elif cid in ["downside_dev", "var", "cvar"]:
        return max(-100.0, min(100.0, raw_val * 10.0))
    elif cid == "trend_persistence":
        return max(-100.0, min(100.0, (raw_val - 1.5) * 66.6))
    elif cid in ["confidence_inverse", "consensus_boost"]:
        return max(-100.0, min(100.0, raw_val))

    return max(-100.0, min(100.0, raw_val))


# ── Strategy Execution & Scoring Engine ──

def execute_scoring_on_snapshot(definition: Dict[str, Any], snapshot_id: str = None) -> List[Dict[str, Any]]:
    """
    Score all stocks in the active universe using the strategy configuration and a target snapshot ID.
    Returns custom scores, ranks, ratings, and comparisons side-by-side with PMS Default.
    """
    if snapshot_id is None:
        latest = db.get_latest_snapshot()
        if not latest:
            raise ValueError("No snapshots found in database.")
        snapshot_id = latest["snapshot_id"]
        
    conn = db.get_db_connection()
    try:
        # Load indicators, scores detail, and stocks metadata
        ind_rows = conn.execute("SELECT * FROM snapshot_indicator WHERE snapshot_id = ?", (snapshot_id,)).fetchall()
        score_rows = conn.execute("SELECT * FROM snapshot_score WHERE snapshot_id = ?", (snapshot_id,)).fetchall()
        stock_rows = conn.execute("SELECT * FROM snapshot_stock WHERE snapshot_id = ?", (snapshot_id,)).fetchall()
        
        ind_map = {r["symbol"].upper(): dict(r) for r in ind_rows}
        score_map = {r["symbol"].upper(): dict(r) for r in score_rows}
        
        # Parse strategy config
        runtime_config = build_runtime_config(definition)
        features = runtime_config["features"]
        weights = runtime_config["weights"]
        t_buy = runtime_config["threshold_buy"]
        t_sell = runtime_config["threshold_sell"]
        scoring_method = runtime_config["scoring_method"]
        
        scored_stocks = []
        
        for stock_row in stock_rows:
            symbol = stock_row["symbol"]
            sym_upper = symbol.upper()
            
            indicators = ind_map.get(sym_upper, {})
            scores = score_map.get(sym_upper, {})
            
            # Compute custom score
            custom_score = 0.0
            for fid in features:
                raw_val = resolve_raw_feature_value(fid, indicators, scores, stock_row)
                norm_val = normalize_feature_value(fid, raw_val, indicators)
                weight = weights.get(fid, 0.0)
                custom_score += norm_val * weight
                
            # Keep score inside bounds [-100, 100]
            custom_score = max(min(custom_score, 100.0), -100.0)
            
            # Map rating from thresholds
            if custom_score >= t_buy:
                rating = "STRONG BUY" if custom_score >= t_buy + 20.0 else "BUY"
            elif custom_score <= t_sell:
                rating = "STRONG SELL" if custom_score <= t_sell - 20.0 else "SELL"
            else:
                rating = "HOLD"
                
            scored_stocks.append({
                "symbol": symbol,
                "company_name": stock_row.get("company_name", symbol),
                "sector": stock_row.get("sector", "—"),
                "current_price": stock_row.get("close"),
                "daily_change_pct": stock_row.get("daily_chg_pct"),
                
                # PMS Default
                "default_score": float(stock_row.get("composite_score") or 0.0),
                "default_rating": stock_row.get("final_rating", "HOLD"),
                "default_rank": int(stock_row.get("rank") or 0),
                
                # Custom strategy
                "custom_score": round(custom_score, 2),
                "custom_rating": rating,
                "custom_rank": 0,  # calculated below
            })
            
        # Assign custom ranks based on custom score descending
        scored_stocks.sort(key=lambda s: s["custom_score"], reverse=True)
        for idx, s in enumerate(scored_stocks, start=1):
            s["custom_rank"] = idx
            
            # Calc differences
            s["score_diff"] = round(s["custom_score"] - s["default_score"], 2)
            s["rank_diff"] = int(s["default_rank"] - s["custom_rank"])
            s["rating_diff"] = f"{s['default_rating']} → {s['custom_rating']}"
            s["expected_return_diff"] = round(s["custom_score"] * 0.1 - s["default_score"] * 0.1, 2)
            
        return scored_stocks
    finally:
        conn.close()


# ── EQIF Explainability Generator ──

def explain_custom_strategy_score(definition: Dict[str, Any], symbol: str, snapshot_id: str = None) -> ExplainScoreResponse:
    """
    Generate dynamic, identical explainability (EQIF payload) for a custom strategy.
    """
    if snapshot_id is None:
        latest = db.get_latest_snapshot()
        if not latest:
            raise ValueError("No snapshot ID provided and none found in DB.")
        snapshot_id = latest["snapshot_id"]
        
    conn = db.get_db_connection()
    try:
        sym_clean = symbol.strip().upper()
        sym_no_ns = sym_clean.replace(".NS", "")
        
        # Fetch data for symbol with flexible matching for .NS suffix
        stock_row = conn.execute(
            "SELECT * FROM snapshot_stock WHERE snapshot_id = ? AND (UPPER(symbol) = ? OR UPPER(symbol) = ? OR REPLACE(UPPER(symbol), '.NS', '') = ?)",
            (snapshot_id, sym_clean, f"{sym_no_ns}.NS", sym_no_ns)
        ).fetchone()
        
        if not stock_row:
            raise ValueError(f"Stock '{symbol}' not found in active snapshot.")
            
        real_symbol = stock_row["symbol"]
        ind_row = conn.execute("SELECT * FROM snapshot_indicator WHERE snapshot_id = ? AND UPPER(symbol) = UPPER(?)", (snapshot_id, real_symbol)).fetchone()
        score_row = conn.execute("SELECT * FROM snapshot_score WHERE snapshot_id = ? AND UPPER(symbol) = UPPER(?)", (snapshot_id, real_symbol)).fetchone()
        
        indicators = dict(ind_row) if ind_row else {}
        scores = dict(score_row) if score_row else {}
        
        # Build runtime profile
        runtime = build_runtime_config(definition)
        features = runtime["features"]
        weights = runtime["weights"]
        scoring_method = runtime["scoring_method"]
        t_buy = runtime["threshold_buy"]
        t_sell = runtime["threshold_sell"]
        t_hold = runtime["threshold_hold"]
        
        # Run validators
        val_res = validate_strategy_config(definition)
        health_score = val_res["health_score"]
        
        # Compute custom score and contributions
        custom_score = 0.0
        contributions: List[Contribution] = []
        category_contribs: Dict[str, float] = {}
        category_features: Dict[str, List[FeatureAttribution]] = {}
        current_values = {}
        
        for fid in features:
            raw_val = resolve_raw_feature_value(fid, indicators, scores, stock_row)
            norm_val = normalize_feature_value(fid, raw_val, indicators)
            weight = weights.get(fid, 0.0)
            contrib_amt = norm_val * weight
            custom_score += contrib_amt
            
            meta = METADATA_REGISTRY.get(fid, {})
            display_name = meta.get("display_name", fid)
            cat = meta.get("category", "General")
            
            current_values[fid] = raw_val
            category_contribs[cat] = category_contribs.get(cat, 0.0) + contrib_amt
            
            ref_dict = REFERENCE_REGISTRY.get(fid, {})
            ref_obj = ResearchReference(
                paper=ref_dict.get("paper", "PMS Quant Research"),
                author=ref_dict.get("author", "PMS Engine"),
                year=ref_dict.get("year", 2024),
                link=ref_dict.get("link"),
                description=ref_dict.get("description", "Factor evaluation rule.")
            )
            norm_obj = NormalizationExplain(
                method="Default",
                range="-100 to +100",
                logic="Standardized strategy scoring"
            )
            meta_obj = FeatureMetadata(
                data_source="Snapshot Market Data",
                plain_formula=f"raw({fid}) * weight",
                latex_formula=r"\text{Raw} \times \text{Weight}",
                normalization=norm_obj,
                reference=ref_obj
            )
            
            feat_item = FeatureAttribution(
                feature_key=fid,
                name=display_name,
                current_value=f"{raw_val:+.2f}" if isinstance(raw_val, float) else str(raw_val),
                normalized_value=round(norm_val, 2),
                weight=weight,
                contribution=round(contrib_amt, 2),
                effect="positive" if contrib_amt > 0 else ("negative" if contrib_amt < 0 else "neutral"),
                explanation=f"{display_name} contributes {contrib_amt:+.2f} points to custom score.",
                confidence="High",
                metadata=meta_obj
            )
            if cat not in category_features:
                category_features[cat] = []
            category_features[cat].append(feat_item)
            
            contributions.append(Contribution(
                name=display_name,
                value=round(raw_val, 2),
                weight=weight,
                contribution=round(contrib_amt, 2),
                direction="positive" if contrib_amt > 0 else ("negative" if contrib_amt < 0 else "neutral"),
                description=meta.get("description", "")
            ))
            
        custom_score = max(min(custom_score, 100.0), -100.0)
        
        # Map rating
        if custom_score >= t_buy:
            custom_rating = "STRONG BUY" if custom_score >= t_buy + 20.0 else "BUY"
        elif custom_score <= t_sell:
            custom_rating = "STRONG SELL" if custom_score <= t_sell - 20.0 else "SELL"
        else:
            custom_rating = "HOLD"
            
        # Validation metrics
        validation = [
            ValidationMetric(metric="Strategy Health Score", value=f"{health_score}/100", description="Validator Audit Score"),
            ValidationMetric(metric="Complexity", value=val_res["complexity"], description="Classification based on features count"),
            ValidationMetric(metric="Estimated Behavior", value=val_res["estimated_behavior"], description="Volatility risk profiling"),
        ]
        
        # Score interpretations
        interpretations = [
            ScoreInterpretation(range=f"{t_buy} to 100", meaning="BUY / STRONG BUY", action="Qualifies for model portfolio allocation under strategy rules."),
            ScoreInterpretation(range=f"{t_sell} to {t_buy}", meaning="HOLD / Neutral", action="Maintain existing exposures, risk-reward does not support immediate new capital."),
            ScoreInterpretation(range=f"Below {t_sell}", meaning="SELL / STRONG SELL", action="Exit or reduce holdings; check risk rules.")
        ]
        
        # Expose research references
        references: List[ResearchReference] = []
        for fid in features:
            ref = REFERENCE_REGISTRY.get(fid, {})
            if ref and ref.get("paper"):
                references.append(ResearchReference(
                    paper=ref["paper"],
                    author=ref.get("author", "Unknown"),
                    year=ref.get("year", 2000),
                    link=ref.get("link"),
                    description=ref.get("description", "")
                ))
                
        # Build category rollups for visualizations
        feature_attributions: List[CategoryContribution] = []
        for cat, subtotal in category_contribs.items():
            feature_attributions.append(CategoryContribution(
                category=f"{cat} ({round(subtotal, 1)}%)",
                subtotal=round(subtotal, 2),
                features=category_features.get(cat, [])
            ))
            
        # Narrative explanations
        narratives = []
        if custom_score > 30:
            narratives.append(f"The symbol {symbol} exhibits strong positive alignment with the custom strategy config. Core positive drivers include contributions from features under the {list(category_contribs.keys())[0]} category.")
        else:
            narratives.append(f"The symbol {symbol} displays sideways consolidation/reversal characteristics under this strategy.")
        
        dynamic_explanation = " ".join(narratives)
        why_not = "The strategy did not reach max potential score due to dragging feature contributions in secondary categories." if custom_score < 80 else "The strategy score is at solid constructive levels."
        
        return ExplainScoreResponse(
            score_type="composite",
            symbol=symbol,
            current_value=round(custom_score, 2),
            purpose=definition.get("strategy_name", "Custom Strategy"),
            formula=f"Custom Weighted Sum Score (Scoring Method: {scoring_method})",
            factors=[METADATA_REGISTRY[fid]["display_name"] for fid in features if fid in METADATA_REGISTRY],
            validation=validation,
            interpretation=interpretations,
            limitations=["Calculated on transient inputs.", "Backtesting history validation not yet executed."],
            references=references[:10],  # cap to 10
            current_values=current_values,
            current_contributions=contributions,
            dynamic_explanation=dynamic_explanation,
            why_not=why_not,
            historical_context=[],
            explanation_type="global_importance",
            feature_attributions=feature_attributions
        )
    finally:
        conn.close()


def seed_default_strategies_if_empty(db_session: Session):
    """Seed standard default strategies into database if empty."""
    try:
        count = db_session.query(StrategyMaster).count()
        if count > 0:
            return

        now_str = datetime.now().isoformat()

        default_strats = [
            {
                "id": "strat_balanced_default",
                "name": "Institutional Balanced Alpha Strategy",
                "description": "Multi-factor strategy balancing technical indicators, machine learning signals, and reliability scores.",
                "type": "Stock",
                "definition": {
                    "features": [
                        {"feature_id": "rsi", "feature_group": "Technical", "enabled": True},
                        {"feature_id": "macd", "feature_group": "Technical", "enabled": True},
                        {"feature_id": "ml_score", "feature_group": "Machine Learning", "enabled": True},
                        {"feature_id": "reliability_score", "feature_group": "Quality", "enabled": True}
                    ],
                    "weights": [
                        {"feature_id": "rsi", "weight": 25.0, "normalization_method": "Percentile Rank"},
                        {"feature_id": "macd", "weight": 25.0, "normalization_method": "Z-Score"},
                        {"feature_id": "ml_score", "weight": 30.0, "normalization_method": "Default"},
                        {"feature_id": "reliability_score", "weight": 20.0, "normalization_method": "Default"}
                    ],
                    "scoring_config": {
                        "scoring_method": "Weighted Average",
                        "threshold_buy": 35.0,
                        "threshold_hold": -15.0,
                        "threshold_sell": -15.0
                    }
                }
            },
            {
                "id": "strat_momentum_default",
                "name": "Momentum & Breakout Strategy",
                "description": "Trend-following strategy prioritizing technical momentum, RSI, ADX, and breakout signals.",
                "type": "Stock",
                "definition": {
                    "features": [
                        {"feature_id": "rsi", "feature_group": "Technical", "enabled": True},
                        {"feature_id": "adx", "feature_group": "Technical", "enabled": True},
                        {"feature_id": "ema20", "feature_group": "Technical", "enabled": True},
                        {"feature_id": "stoch_k", "feature_group": "Technical", "enabled": True}
                    ],
                    "weights": [
                        {"feature_id": "rsi", "weight": 35.0, "normalization_method": "Percentile Rank"},
                        {"feature_id": "adx", "weight": 25.0, "normalization_method": "Default"},
                        {"feature_id": "ema20", "weight": 20.0, "normalization_method": "Default"},
                        {"feature_id": "stoch_k", "weight": 20.0, "normalization_method": "Percentile Rank"}
                    ],
                    "scoring_config": {
                        "scoring_method": "Weighted Average",
                        "threshold_buy": 40.0,
                        "threshold_hold": -10.0,
                        "threshold_sell": -20.0
                    }
                }
            }
        ]

        for s in default_strats:
            strat_obj = StrategyMaster(
                strategy_id=s["id"],
                strategy_name=s["name"],
                description=s["description"],
                strategy_type=s["type"],
                strategy_prompt="",
                strategy_definition=json.dumps(s["definition"]),
                visibility="Public",
                version="1.0.0",
                status="Published",
                created_at=now_str,
                updated_at=now_str
            )
            ver_obj = StrategyVersion(
                strategy_id=s["id"],
                version="1.0.0",
                timestamp=now_str,
                change_summary="System default seed strategy.",
                created_by="system"
            )
            db_session.add(strat_obj)
            db_session.add(ver_obj)

        db_session.commit()
    except Exception as e:
        logger.error(f"Failed to seed default strategies: {e}")
        db_session.rollback()


def get_strategies(db_session: Session) -> List[StrategyMaster]:
    """Retrieve all strategy master records, seeding defaults if empty."""
    seed_default_strategies_if_empty(db_session)
    return db_session.query(StrategyMaster).order_by(StrategyMaster.created_at.desc()).all()


def get_strategy_by_id(db_session: Session, strategy_id: str) -> Optional[StrategyMaster]:
    """Retrieve strategy master by UUID."""
    return db_session.query(StrategyMaster).filter(StrategyMaster.strategy_id == strategy_id).first()


def create_strategy(db_session: Session, request: StrategyCreateRequest) -> StrategyMaster:
    """Create a new strategy config and insert default version."""
    strategy_id = str(uuid.uuid4())
    now_str = datetime.now().isoformat()
    
    definition_json = json.dumps(request.strategy_definition.model_dump())
    
    strategy = StrategyMaster(
        strategy_id=strategy_id,
        strategy_name=request.strategy_name,
        description=request.description,
        strategy_type=request.strategy_type,
        strategy_prompt=request.strategy_prompt,
        strategy_definition=definition_json,
        visibility=request.visibility,
        version="1.0.0",
        status="Draft",
        created_at=now_str,
        updated_at=now_str
    )
    
    version = StrategyVersion(
        strategy_id=strategy_id,
        version="1.0.0",
        timestamp=now_str,
        change_summary="Initial strategy creation.",
        created_by="user"
    )
    
    db_session.add(strategy)
    db_session.add(version)
    db_session.commit()
    db_session.refresh(strategy)
    return strategy


def update_strategy(db_session: Session, strategy_id: str, request: StrategyUpdateRequest) -> Optional[StrategyMaster]:
    """Update strategy config and increment version if configuration changes."""
    strategy = get_strategy_by_id(db_session, strategy_id)
    if not strategy:
        return None
        
    now_str = datetime.now().isoformat()
    is_changed = False
    
    if request.strategy_name is not None and request.strategy_name != strategy.strategy_name:
        strategy.strategy_name = request.strategy_name
        is_changed = True
    if request.description is not None:
        strategy.description = request.description
    if request.strategy_type is not None:
        strategy.strategy_type = request.strategy_type
    if request.strategy_prompt is not None:
        strategy.strategy_prompt = request.strategy_prompt
    if request.visibility is not None:
        strategy.visibility = request.visibility
    if request.status is not None:
        strategy.status = request.status
        
    if request.strategy_definition is not None:
        new_def_json = json.dumps(request.strategy_definition.model_dump())
        if new_def_json != strategy.strategy_definition:
            strategy.strategy_definition = new_def_json
            is_changed = True
            
    if is_changed:
        # Increment minor version
        v_parts = strategy.version.split('.')
        new_v = f"{v_parts[0]}.{int(v_parts[1]) + 1}.0"
        strategy.version = new_v
        strategy.updated_at = now_str
        
        # Save version history
        version = StrategyVersion(
            strategy_id=strategy_id,
            version=new_v,
            timestamp=now_str,
            change_summary=request.change_summary or "Configuration modified.",
            created_by="user"
        )
        db_session.add(version)
        
    db_session.commit()
    db_session.refresh(strategy)
    return strategy


def duplicate_strategy(db_session: Session, strategy_id: str, new_name: str = None) -> Optional[StrategyMaster]:
    """Duplicate / clone an existing strategy configuration."""
    source = get_strategy_by_id(db_session, strategy_id)
    if not source:
        return None
        
    clone_id = str(uuid.uuid4())
    now_str = datetime.now().isoformat()
    
    strategy = StrategyMaster(
        strategy_id=clone_id,
        strategy_name=new_name or f"Copy of {source.strategy_name}",
        description=source.description,
        strategy_type=source.strategy_type,
        strategy_prompt=source.strategy_prompt,
        strategy_definition=source.strategy_definition,
        visibility="Private",
        version="1.0.0",
        status="Draft",
        created_at=now_str,
        updated_at=now_str
    )
    
    version = StrategyVersion(
        strategy_id=clone_id,
        version="1.0.0",
        timestamp=now_str,
        change_summary=f"Cloned from {source.strategy_name} ({strategy_id}).",
        created_by="user"
    )
    
    db_session.add(strategy)
    db_session.add(version)
    db_session.commit()
    db_session.refresh(strategy)
    return strategy


def delete_strategy(db_session: Session, strategy_id: str) -> bool:
    """Delete strategy and its cascade records."""
    strategy = get_strategy_by_id(db_session, strategy_id)
    if not strategy:
        return False
    db_session.delete(strategy)
    db_session.commit()
    return True

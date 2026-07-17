"""
strategy_service.py — Strategy orchestration service for CRUD, validation, execution, and explainability.
"""

import uuid
import json
import time
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

def resolve_raw_feature_value(feature_id: str, indicators: dict, scores: dict, stock_row: dict) -> float:
    """Resolve raw feature value from loaded database dictionaries."""
    # 1. Match in indicators (case-insensitive keys)
    val = indicators.get(feature_id)
    if val is not None:
        return float(val)
        
    alt_keys_ind = {
        "rsi": "rsi_14",
        "atr": "atr_14",
        "adx": "adx_14",
        "ema20": "above_ema20",
        "ema50": "above_ema50",
        "ema200": "above_ema200",
    }
    alt_key = alt_keys_ind.get(feature_id)
    if alt_key and indicators.get(alt_key) is not None:
        return float(indicators[alt_key])
        
    # 2. Match in scores
    val = scores.get(feature_id)
    if val is not None:
        return float(val)
        
    alt_keys_score = {
        "rf": "rf_signal",
        "xgb": "xgb_signal",
        "lgb": "lgbm_signal",
        "p_long": "gru_long",
        "p_hold": "gru_hold",
        "p_short": "gru_short",
        "technical_score": "technical_score",
        "ml_score": "ensemble_score",
        "gru_score": "gru_score",
        "reliability_score": "reliability_score",
        "confidence_score": "confidence",
        "risk_score": "risk_score",
        "momentum_score": "momentum_score",
        "trend_score": "trend_score",
        "composite_score": "composite_score",
    }
    alt_key = alt_keys_score.get(feature_id)
    if alt_key and scores.get(alt_key) is not None:
        return float(scores[alt_key])
        
    # 3. Match in stock_row
    val = stock_row.get(feature_id)
    if val is not None:
        return float(val)
        
    defaults = {
        "rsi": 50.0,
        "adx": 20.0,
        "stoch_k": 50.0,
        "cci": 0.0,
        "roc": 0.0,
        "williams_r": -50.0,
        "cmf": 0.0,
        "atr_percentile": 50.0,
        "reliability_score": 70.0,
        "confidence": 50.0,
        "confidence_score": 50.0,
    }
    return float(defaults.get(feature_id, 0.0))


def normalize_feature_value(feature_id: str, raw_val: float, indicators: dict = None) -> float:
    """Normalize raw value to standard -100 to +100 range."""
    # Rollups are already normalized
    if feature_id in ["technical_score", "ml_score", "gru_score", "reliability_score", "risk_score", "momentum_score", "trend_score", "composite_score"]:
        return raw_val
        
    if feature_id in ["ema20", "ema50", "ema200"]:
        return 100.0 if raw_val == 1 or raw_val > 0 else -100.0
    elif feature_id == "adx":
        return 100.0 if raw_val > 25 else -100.0
    elif feature_id == "supertrend":
        return 100.0 if raw_val == 1 or raw_val > 0 else -100.0
    elif feature_id in ["rsi", "mfi"]:
        return (raw_val - 50.0) * 2.0
    elif feature_id in ["macd", "macd_signal"]:
        if indicators:
            macd_val = float(indicators.get("macd") or 0.0)
            sig_val = float(indicators.get("macd_signal") or 0.0)
            return 100.0 if macd_val > sig_val else -100.0
        return 100.0 if raw_val > 0 else -100.0
    elif feature_id in ["stoch_k", "williams_r"]:
        if feature_id == "williams_r":
            return (raw_val + 50.0) * 2.0
        return (raw_val - 50.0) * 2.0
    elif feature_id == "cci":
        return max(min(raw_val, 100.0), -100.0)
    elif feature_id == "roc":
        return max(min(raw_val * 5.0, 100.0), -100.0)
    elif feature_id == "obv":
        return 100.0 if raw_val > 0 else -100.0
    elif feature_id == "cmf":
        return max(min(raw_val * 100.0, 100.0), -100.0)
    elif feature_id == "volume_ma":
        return max(min((raw_val - 1.0) * 100.0, 100.0), -100.0)
    elif feature_id == "volume_breakout":
        return 100.0 if raw_val == 1 or raw_val > 0 else -100.0
    elif feature_id in ["atr", "atr_percentile", "hist_vol"]:
        return (raw_val - 50.0) * 2.0
    elif feature_id in ["rf", "xgb", "lgb"]:
        return raw_val * 2.0 if abs(raw_val) <= 50.0 else raw_val
    elif feature_id in ["p_long", "p_short", "p_hold"]:
        return (raw_val - 0.5) * 200.0
        
    return raw_val


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
        symbol = symbol.strip().upper()
        # Fetch data for symbol
        ind_row = conn.execute("SELECT * FROM snapshot_indicator WHERE snapshot_id = ? AND UPPER(symbol) = ?", (snapshot_id, symbol)).fetchone()
        score_row = conn.execute("SELECT * FROM snapshot_score WHERE snapshot_id = ? AND UPPER(symbol) = ?", (snapshot_id, symbol)).fetchone()
        stock_row = conn.execute("SELECT * FROM snapshot_stock WHERE snapshot_id = ? AND UPPER(symbol) = ?", (snapshot_id, symbol)).fetchone()
        
        if not stock_row:
            raise ValueError(f"Stock '{symbol}' not found in active snapshot.")
            
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
        category_features: Dict[str, List[Dict[str, Any]]] = {}
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
            
            feat_item = {
                "feature_key": fid,
                "current_value": f"{raw_val:+.2f}" if isinstance(raw_val, float) else str(raw_val),
                "normalized_value": round(norm_val, 2),
                "weight": weight,
                "contribution": round(contrib_amt, 2),
                "effect": "positive" if contrib_amt > 0 else ("negative" if contrib_amt < 0 else "neutral"),
                "confidence": "High"
            }
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
        feature_attributions: List[FeatureAttribution] = []
        for cat, subtotal in category_contribs.items():
            feature_attributions.append(FeatureAttribution(
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


# ── SQLAlchemy CRUD Service Methods ──

def get_strategies(db_session: Session) -> List[StrategyMaster]:
    """Retrieve all strategy master records."""
    return db_session.query(StrategyMaster).order_by(StrategyMaster.created_at.desc()).all() if hasattr(StrategyMaster, "created_at") else db_session.query(StrategyMaster).all()


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

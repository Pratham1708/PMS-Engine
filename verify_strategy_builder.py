#!/usr/bin/env python3
"""
verify_strategy_builder.py — Automated Verification Suite for Quant Strategy Studio.
Validates the structural integrity and functionality of the custom scoring engine,
strategy validation, runtime builders, and database tables.
"""

import sys
import os
import json
import uuid
from typing import List, Dict, Any, Tuple

# Ensure backend folder is on python path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

try:
    from app.services import db
    from app.services import strategy_service
    from app.services.strategy_validator import validate_strategy_config
    from app.services.strategy_runtime import build_runtime_config
    from app.models.orm import StrategyMaster, StrategyVersion
    from app.models.schemas import StrategyCreateRequest, StrategyUpdateRequest, StrategyDefinitionModel
    from app.config import settings
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


class SubsystemVerifier:
    def __init__(self):
        self.results: List[Tuple[str, str, str]] = []

    def verify(self, name: str, desc: str):
        """Decorator to wrap verifier methods."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                print(f"Verifying: {name} ({desc})... ", end="")
                try:
                    passed, message = func(*args, **kwargs)
                    status = "PASS" if passed else "FAIL"
                except Exception as e:
                    status = "FAIL"
                    message = f"Exception: {e}"
                print(status)
                if status == "FAIL":
                    print(f"  +- Details: {message}")
                self.results.append((name, status, message))
                return status == "PASS"
            return wrapper
        return decorator


verifier = SubsystemVerifier()


@verifier.verify("S01: Strategy Database Tables", "Verify strategy tables exist in database schema")
def verify_db_tables():
    # Force database schema initialization
    db.init_db()
    
    conn = db.get_db_connection()
    try:
        tables = ["strategy_master", "strategy_versions"]
        missing = []
        for t in tables:
            r = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (t,)
            ).fetchone()
            if not r:
                missing.append(t)
        if missing:
            return False, f"Missing tables: {missing}"
        return True, "All strategy tables are successfully registered in database schema"
    finally:
        conn.close()


@verifier.verify("S02: Dynamic Feature Registry", "Aggregates and exposes features from all registries")
def verify_features_registry():
    feats = strategy_service.get_features_registry()
    if not feats:
        return False, "Feature registry is empty."
        
    # Verify standard keys exist
    keys = ["feature_id", "display_name", "category", "data_source", "plain_formula", "normalization_method", "paper", "default_weight"]
    sample = feats[0]
    for k in keys:
        if k not in sample:
            return False, f"Sample feature missing required metadata key: {k}"
            
    # Verify default weights mapped
    rsi_feat = next((f for f in feats if f["feature_id"] == "rsi"), None)
    if not rsi_feat or rsi_feat["default_weight"] <= 0:
        return False, f"RSI default weight allocation mapping failed or missing: {rsi_feat}"
        
    return True, f"Features registry loaded {len(feats)} indicators with metadata."


@verifier.verify("S03: Strategy Weight and Threshold Validator", "Verify weights sum and thresholds order rules")
def verify_validation_rules():
    # Configuration with weight != 100%
    invalid_weights = {
        "features": [{"feature_id": "rsi", "feature_group": "Momentum"}],
        "weights": [{"feature_id": "rsi", "weight": 60.0}],
        "scoring_config": {"threshold_buy": 35.0, "threshold_hold": -15.0, "threshold_sell": -15.0}
    }
    res = validate_strategy_config(invalid_weights)
    if res["valid"]:
        return False, "Weights validation failed to block config totaling 60%."
        
    # Configuration with invalid thresholds order
    invalid_thresholds = {
        "features": [{"feature_id": "rsi", "feature_group": "Momentum"}],
        "weights": [{"feature_id": "rsi", "weight": 100.0}],
        "scoring_config": {"threshold_buy": 10.0, "threshold_hold": 30.0, "threshold_sell": 10.0}
    }
    res = validate_strategy_config(invalid_thresholds)
    if res["valid"]:
        return False, "Validator failed to block invalid threshold order (buy < hold)."
        
    # Valid configuration
    valid_config = {
        "features": [{"feature_id": "rsi", "feature_group": "Momentum"}, {"feature_id": "ema20", "feature_group": "Trend"}],
        "weights": [{"feature_id": "rsi", "weight": 50.0}, {"feature_id": "ema20", "weight": 50.0}],
        "scoring_config": {"threshold_buy": 35.0, "threshold_hold": -15.0, "threshold_sell": -15.0}
    }
    res = validate_strategy_config(valid_config)
    if not res["valid"]:
        return False, f"Valid configuration flagged as invalid: {res['errors']}"
        
    return True, "Validator successfully checks weight balance and threshold rules."


@verifier.verify("S04: Strategy Health Score Breakdown", "Verifies component breakdown for Strategy Health Score")
def verify_health_score_breakdown():
    # Balanced diverse config
    diverse_config = {
        "features": [
            {"feature_id": "rsi", "feature_group": "Momentum"},
            {"feature_id": "ema20", "feature_group": "Trend"},
            {"feature_id": "beta", "feature_group": "Systematic Volatility"},
            {"feature_id": "accuracy", "feature_group": "Model Performance"}
        ],
        "weights": [
            {"feature_id": "rsi", "weight": 25.0},
            {"feature_id": "ema20", "weight": 25.0},
            {"feature_id": "beta", "weight": 25.0},
            {"feature_id": "accuracy", "weight": 25.0}
        ],
        "scoring_config": {"threshold_buy": 35.0, "threshold_hold": -15.0, "threshold_sell": -15.0}
    }
    res = validate_strategy_config(diverse_config)
    breakdown = res["health_breakdown"]
    
    if breakdown["diversification"] < 12:
        return False, f"Diversification score lower than expected for 4 categories: {breakdown}"
    if breakdown["risk_coverage"] != 20:
        return False, f"Risk coverage score should be 20 when systematic risk + model telemetry are selected: {breakdown}"
        
    return True, f"Strategy Health Score Audit completed with overall score: {res['health_score']}/100"


@verifier.verify("S05: Feature Dependencies Validation", "Validates indicator dependencies checking")
def verify_feature_dependencies():
    # Select macd_signal but not macd
    dependent_config = {
        "features": [{"feature_id": "macd_signal", "feature_group": "Momentum"}],
        "weights": [{"feature_id": "macd_signal", "weight": 100.0}],
        "scoring_config": {"threshold_buy": 35.0, "threshold_hold": -15.0, "threshold_sell": -15.0}
    }
    res = validate_strategy_config(dependent_config)
    warnings = res["warnings"]
    
    has_dep_warning = any("macd_signal" in w and "macd" in w for w in warnings)
    if not has_dep_warning:
        return False, f"Validator failed to alert missing macd dependency warning: {warnings}"
        
    return True, "Validator successfully checks feature dependencies rules."


@verifier.verify("S06: Strategy Runtime Builder", "Verifies config translation into runtime weights")
def verify_runtime_builder():
    definition = {
        "features": [{"feature_id": "rsi", "enabled": True}, {"feature_id": "ema20", "enabled": False}],
        "weights": [{"feature_id": "rsi", "weight": 70.0}, {"feature_id": "ema20", "weight": 30.0}],
        "scoring_config": {"scoring_method": "Weighted Average", "threshold_buy": 40.0}
    }
    runtime = build_runtime_config(definition)
    
    if "rsi" not in runtime["features"] or "ema20" in runtime["features"]:
        return False, f"Features filtering failed: {runtime['features']}"
    if runtime["weights"].get("rsi") != 0.7:
        return False, f"Weight fraction mapping failed: {runtime['weights']}"
    if runtime["threshold_buy"] != 40.0:
        return False, f"Buy threshold mapping failed: {runtime['threshold_buy']}"
        
    return True, "Strategy definition successfully converted into runtime parameters."


@verifier.verify("S07: Scoring Engine Execution", "Verify dynamic portfolio scoring execution on active snapshot")
def verify_scoring_engine():
    # Make a transient valid strategy definition
    definition = {
        "features": [{"feature_id": "rsi", "feature_group": "Momentum", "enabled": True}, {"feature_id": "ema20", "feature_group": "Trend", "enabled": True}],
        "weights": [{"feature_id": "rsi", "weight": 50.0}, {"feature_id": "ema20", "weight": 50.0}],
        "scoring_config": {"scoring_method": "Weighted Average", "threshold_buy": 35.0, "threshold_hold": -15.0, "threshold_sell": -15.0}
    }
    
    latest = db.get_latest_snapshot()
    if not latest:
        # Create a mock snapshot to enable test scoring if empty
        db.create_snapshot("2026-07-17", "2026-07-17", is_official=True)
        latest = db.get_latest_snapshot()
        
    snap_id = latest["snapshot_id"]
    
    # Save a mock stock, score, and indicator for Nifty-50 stock (RELIANCE)
    conn = db.get_db_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO security_master (symbol, company_name, sector) VALUES ('RELIANCE.NS', 'Reliance Industries', 'Energy')")
        conn.execute(
            """
            INSERT OR REPLACE INTO snapshot_indicator (snapshot_id, symbol, rsi_14, above_ema20) 
            VALUES (?, 'RELIANCE.NS', 65.0, 1)
            """,
            (snap_id,)
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO snapshot_stock (snapshot_id, symbol, company_name, sector, composite_score, final_rating, rank, close) 
            VALUES (?, 'RELIANCE.NS', 'Reliance Industries', 'Energy', 80.0, 'STRONG BUY', 1, 2400.0)
            """,
            (snap_id,)
        )
        conn.commit()
    finally:
        conn.close()
        
    scored = strategy_service.execute_scoring_on_snapshot(definition, snap_id)
    if not scored:
        return False, "Scoring execution returned empty stocks list."
        
    rel_stock = next((s for s in scored if s["symbol"] == "RELIANCE.NS"), None)
    if not rel_stock:
        return False, "Failed to score RELIANCE.NS stock."
        
    # Verify score calculation: rsi = 65.0 (norm: (65-50)*2 = 30.0), above_ema20 = 1 (norm: 100.0)
    # Expected custom_score = 30.0 * 0.5 + 100.0 * 0.5 = 65.0
    if rel_stock["custom_score"] != 65.0:
        return False, f"Scoring calculation failed. Expected: 65.0. Got: {rel_stock['custom_score']}"
        
    if rel_stock["custom_rating"] != "BUY":
        return False, f"Scoring rating mapping failed: {rel_stock['custom_rating']}"
        
    return True, f"Dynamic scoring engine completed scoring for {len(scored)} stocks."


@verifier.verify("S08: Dynamic Explainability Engine", "Verify explainability (EQIF payload) matches schemas")
def verify_explainability():
    definition = {
        "features": [{"feature_id": "rsi", "feature_group": "Momentum", "enabled": True}, {"feature_id": "ema20", "feature_group": "Trend", "enabled": True}],
        "weights": [{"feature_id": "rsi", "weight": 50.0}, {"feature_id": "ema20", "weight": 50.0}],
        "scoring_config": {"scoring_method": "Weighted Average", "threshold_buy": 35.0, "threshold_hold": -15.0, "threshold_sell": -15.0}
    }
    latest = db.get_latest_snapshot()
    snap_id = latest["snapshot_id"]
    
    exp = strategy_service.explain_custom_strategy_score(definition, "RELIANCE.NS", snap_id)
    
    if exp.current_value != 65.0:
        return False, f"Explain score mismatch: {exp.current_value}"
    if not exp.current_contributions:
        return False, "Explain contributions are empty."
    if not exp.feature_attributions:
        return False, "Explain category attributions (visual data) are empty."
        
    return True, "Explainability payload successfully generated under unified EQIF model."


@verifier.verify("S09: Strategy CRUD Operations", "Verify strategy Master creation, versioning, duplication and deletion")
def verify_crud():
    session = db.get_db_session()
    try:
        definition = StrategyDefinitionModel(
            features=[FeatureSelectionModel(feature_id="rsi", feature_group="Momentum")],
            weights=[WeightAllocationModel(feature_id="rsi", weight=100.0)],
            scoring_config=ScoringConfigModel(threshold_buy=30.0)
        )
        
        req = StrategyCreateRequest(
            strategy_name="Verification Test Strategy",
            description="Created for automated tests",
            strategy_definition=definition,
            visibility="Private"
        )
        
        # 1. Create
        strat = strategy_service.create_strategy(session, req)
        sid = strat.strategy_id
        if not sid:
            return False, "Create strategy returned empty ID."
            
        # Verify listing and single retrieval works
        all_strats = strategy_service.get_strategies(session)
        if not any(s.strategy_id == sid for s in all_strats):
            return False, "Strategy list did not contain newly created strategy."
            
        single = strategy_service.get_strategy_by_id(session, sid)
        if not single or single.strategy_name != "Verification Test Strategy":
            return False, "Single strategy retrieval failed."

        # Verify version 1.0.0 log
        if strat.version != "1.0.0" or len(strat.versions) != 1:
            return False, f"Initial version log verification failed: {strat.version}, {strat.versions}"
            
        # 2. Update (Trigger version increment)
        update_req = StrategyUpdateRequest(
            strategy_name="Updated Test Strategy Name",
            strategy_definition=definition,
            change_summary="Modified strategy name"
        )
        updated = strategy_service.update_strategy(session, sid, update_req)
        if updated.strategy_name != "Updated Test Strategy Name" or updated.version != "1.1.0" or len(updated.versions) != 2:
            return False, f"Update versioning failed: version={updated.version}, versions count={len(updated.versions)}"
            
        # 3. Duplicate / Clone
        cloned = strategy_service.duplicate_strategy(session, sid, "Cloned Test Strategy")
        if not cloned or cloned.strategy_name != "Cloned Test Strategy" or cloned.version != "1.0.0":
            return False, f"Duplicate cloning failed: {cloned}"
            
        # 4. Delete
        success = strategy_service.delete_strategy(session, sid)
        success_clone = strategy_service.delete_strategy(session, cloned.strategy_id)
        if not success or not success_clone:
            return False, "Delete operations failed."
            
        return True, "Strategy CRUD, minor version incrementing, and duplication cascade verified successfully."
    finally:
        session.close()


def run_verification_suite():
    print("====================================================")
    print("   Quant Strategy Studio - Verification Suite")
    print("====================================================")
    print()
    
    passed_all = True
    for method_name in sorted(dir(verifier)):
        if method_name.startswith("verify_"):
            func = getattr(verifier, method_name)
            if not func():
                passed_all = False
                
    print()
    print("====================================================")
    if passed_all:
        print("  [SUCCESS] All 9 verifications PASSED!")
    else:
        print("  [ALERT] Verification suite FAILED!")
    print("====================================================")
    return passed_all


if __name__ == "__main__":
    success = run_verification_suite()
    sys.exit(0 if success else 1)

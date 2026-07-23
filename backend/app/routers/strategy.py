"""
strategy.py — FastAPI Router for Quant Strategy Studio REST APIs.
"""

import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from sqlalchemy.orm import Session

from app.services import db
from app.services import strategy_service
from app.services.strategy_validator import validate_strategy_config
from app.models.schemas import (
    StrategyResponse,
    StrategyCreateRequest,
    StrategyUpdateRequest,
    StrategyValidationResponse,
    ExplainScoreResponse,
    StrategyExecuteResponse,
    CompareMetricRecord,
    StrategyDefinitionModel
)

router = APIRouter(prefix="/api/strategies", tags=["strategy-studio"])


def get_db_session_dep():
    """Dependency for SQLAlchemy Session injection."""
    session = db.get_db_session()
    try:
        yield session
    finally:
        session.close()


def normalize_strategy_definition(defn: dict) -> dict:
    if not isinstance(defn, dict):
        defn = {}

    raw_feats = defn.get("features", [])
    norm_feats = []
    if isinstance(raw_feats, list):
        for f in raw_feats:
            if isinstance(f, str):
                norm_feats.append({"feature_id": f, "feature_group": "General", "enabled": True})
            elif isinstance(f, dict) and "feature_id" in f:
                norm_feats.append({
                    "feature_id": f["feature_id"],
                    "feature_group": f.get("feature_group", "General"),
                    "enabled": bool(f.get("enabled", True))
                })
    defn["features"] = norm_feats

    raw_wts = defn.get("weights", [])
    norm_wts = []
    if isinstance(raw_wts, dict):
        for fid, wt in raw_wts.items():
            norm_wts.append({
                "feature_id": fid,
                "weight": float(wt),
                "normalization_method": "Default",
                "contribution_method": "Additive"
            })
    elif isinstance(raw_wts, list):
        for w in raw_wts:
            if isinstance(w, dict) and "feature_id" in w:
                norm_wts.append({
                    "feature_id": w["feature_id"],
                    "weight": float(w.get("weight", 0.0)),
                    "normalization_method": w.get("normalization_method", "Default"),
                    "contribution_method": w.get("contribution_method", "Additive")
                })
    defn["weights"] = norm_wts

    sc = defn.get("scoring_config", {})
    if not isinstance(sc, dict):
        sc = {}
    defn["scoring_config"] = {
        "scoring_method": sc.get("scoring_method", "Weighted Average"),
        "aggregation_method": sc.get("aggregation_method", "Additive"),
        "threshold_buy": float(sc.get("threshold_buy", 35.0)),
        "threshold_hold": float(sc.get("threshold_hold", -15.0)),
        "threshold_sell": float(sc.get("threshold_sell", -15.0)),
        "normalization": sc.get("normalization", "Default"),
        "recommendation_method": sc.get("recommendation_method", "Standard")
    }

    return defn


def orm_to_pydantic_response(orm_model) -> StrategyResponse:
    """Helper to convert ORM StrategyMaster into Pydantic StrategyResponse."""
    try:
        defn_dict = json.loads(orm_model.strategy_definition)
    except Exception:
        defn_dict = {}
        
    defn_dict = normalize_strategy_definition(defn_dict)

    versions_list = []
    for v in orm_model.versions:
        versions_list.append({
            "version": v.version,
            "timestamp": v.timestamp,
            "change_summary": v.change_summary,
            "created_by": v.created_by
        })
        
    return StrategyResponse(
        strategy_id=orm_model.strategy_id,
        owner_id=orm_model.owner_id,
        strategy_name=orm_model.strategy_name,
        description=orm_model.description,
        strategy_type=orm_model.strategy_type or "Stock",
        strategy_prompt=orm_model.strategy_prompt,
        strategy_definition=defn_dict,
        visibility=orm_model.visibility or "Private",
        version=orm_model.version or "1.0.0",
        status=orm_model.status or "Draft",
        created_at=orm_model.created_at,
        updated_at=orm_model.updated_at,
        versions=versions_list
    )


@router.get("", response_model=List[StrategyResponse])
async def list_strategies(session: Session = Depends(get_db_session_dep)):
    """List all saved strategies."""
    items = strategy_service.get_strategies(session)
    return [orm_to_pydantic_response(item) for item in items]


@router.post("", response_model=StrategyResponse)
async def create_strategy(
    req: StrategyCreateRequest, 
    session: Session = Depends(get_db_session_dep)
):
    """Save a new strategy configuration."""
    # Check if config is valid before saving
    val_res = validate_strategy_config(req.strategy_definition.model_dump())
    if not val_res["valid"]:
        raise HTTPException(
            status_code=420, 
            detail=f"Invalid strategy configuration: {', '.join(val_res['errors'])}"
        )
        
    item = strategy_service.create_strategy(session, req)
    return orm_to_pydantic_response(item)


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: str, session: Session = Depends(get_db_session_dep)):
    """Fetch strategy details by ID."""
    item = strategy_service.get_strategy_by_id(session, strategy_id)
    if not item:
        raise HTTPException(status_code=404, detail="Strategy not found.")
    return orm_to_pydantic_response(item)


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str, 
    req: StrategyUpdateRequest, 
    session: Session = Depends(get_db_session_dep)
):
    """Update an existing strategy configuration."""
    if req.strategy_definition is not None:
        # Check validation if definition is updated
        val_res = validate_strategy_config(req.strategy_definition.model_dump())
        if not val_res["valid"]:
            raise HTTPException(
                status_code=420, 
                detail=f"Invalid strategy configuration: {', '.join(val_res['errors'])}"
            )
            
    item = strategy_service.update_strategy(session, strategy_id, req)
    if not item:
        raise HTTPException(status_code=404, detail="Strategy not found.")
    return orm_to_pydantic_response(item)


@router.post("/{strategy_id}/duplicate", response_model=StrategyResponse)
async def duplicate_strategy(
    strategy_id: str, 
    new_name: Optional[str] = Query(None, description="Optional new name for duplicate"),
    session: Session = Depends(get_db_session_dep)
):
    """Clone/duplicate an existing strategy configuration."""
    item = strategy_service.duplicate_strategy(session, strategy_id, new_name)
    if not item:
        raise HTTPException(status_code=404, detail="Source strategy not found.")
    return orm_to_pydantic_response(item)


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: str, session: Session = Depends(get_db_session_dep)):
    """Delete a strategy configuration."""
    success = strategy_service.delete_strategy(session, strategy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Strategy not found.")
    return {"status": "success", "message": "Strategy deleted."}


@router.get("/features/registry")
async def get_features_registry():
    """Retrieve Dynamic Features metadata aggregated from registries."""
    return strategy_service.get_features_registry()


@router.post("/validate", response_model=StrategyValidationResponse)
async def validate_transient_config(definition: StrategyDefinitionModel):
    """Verify a transient strategy configuration and return diagnostics."""
    res = validate_strategy_config(definition.model_dump())
    return res


@router.post("/preview", response_model=ExplainScoreResponse)
async def preview_stock_explanation(
    definition: StrategyDefinitionModel,
    symbol: str = Query(..., description="Ticker symbol to preview"),
    snapshot_id: Optional[str] = Query(None, description="Target snapshot ID")
):
    """Generate dynamic preview explainability (EQIF payload) for a single symbol."""
    try:
        res = strategy_service.explain_custom_strategy_score(
            definition.model_dump(), 
            symbol, 
            snapshot_id
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explainability preview failed: {e}")


@router.post("/execute", response_model=StrategyExecuteResponse)
async def execute_transient_scoring(
    definition: StrategyDefinitionModel,
    snapshot_id: Optional[str] = Query(None, description="Target snapshot ID")
):
    """Execute custom strategy scoring across the Nifty 50 active universe."""
    try:
        latest = db.get_latest_snapshot()
        snap_id = snapshot_id or (latest["snapshot_id"] if latest else "latest")
        
        scored_stocks = strategy_service.execute_scoring_on_snapshot(
            definition.model_dump(), 
            snapshot_id
        )
        
        return StrategyExecuteResponse(
            strategy_id="transient_preview",
            strategy_name="Transient Sandbox Strategy",
            snapshot_id=snap_id,
            status="success",
            total_stocks=len(scored_stocks),
            stocks=[CompareMetricRecord(**s) for s in scored_stocks]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dynamic strategy scoring execution failed: {e}")



@router.post("/test-stock")
async def test_stock_strategy(
    body: dict = Body(..., example={"strategy": {}, "symbol": "RELIANCE", "snapshot_id": None})
):
    """
    Test the current strategy against a single stock.
    Returns full score, recommendation, confidence, and feature-level breakdown.
    Used by the Stock Analysis Drawer for per-stock explainability.
    """
    try:
        definition = body.get("strategy", {})
        symbol = body.get("symbol", "").strip().upper()
        snapshot_id = body.get("snapshot_id", None)

        if not symbol:
            raise HTTPException(status_code=422, detail="symbol is required")
        if not definition:
            raise HTTPException(status_code=422, detail="strategy definition is required")

        # Normalize the definition
        definition = normalize_strategy_definition(definition)

        # Execute explainability for this single stock
        explain_result = strategy_service.explain_custom_strategy_score(
            definition, symbol, snapshot_id
        )

        # Also get rank if a full-universe cached run is available
        rank = None
        total = None
        try:
            all_stocks = strategy_service.execute_scoring_on_snapshot(definition, snapshot_id)
            total = len(all_stocks)
            for idx, s in enumerate(all_stocks, 1):
                if s["symbol"].upper() == symbol:
                    rank = idx
                    break
        except Exception:
            pass  # rank is optional

        # Derive sub-scores from contributions if available
        contribs = explain_result.current_contributions or []
        technical_score = None
        ml_score = None
        gru_score = None
        risk_score = None

        # Pull from current_values if present
        cv = explain_result.current_values or {}
        if "technical_score" in cv:
            technical_score = round(float(cv["technical_score"]), 2)
        if "ml_score" in cv:
            ml_score = round(float(cv["ml_score"]), 2)
        if "gru_score" in cv:
            gru_score = round(float(cv["gru_score"]), 2)
        if "risk_score" in cv:
            risk_score = round(float(cv["risk_score"]), 2)

        strategy_score = round(explain_result.current_value or 0.0, 2)
        recommendation = explain_result.interpretation[0].meaning if explain_result.interpretation else "HOLD"

        # Determine actual recommendation from score vs thresholds
        from app.services.strategy_runtime import build_runtime_config
        runtime = build_runtime_config(definition)
        t_buy = runtime["threshold_buy"]
        t_sell = runtime["threshold_sell"]
        if strategy_score >= t_buy:
            recommendation = "STRONG BUY" if strategy_score >= t_buy + 20.0 else "BUY"
        elif strategy_score <= t_sell:
            recommendation = "STRONG SELL" if strategy_score <= t_sell - 20.0 else "SELL"
        else:
            recommendation = "HOLD"

        # Confidence: map score → 0-100 confidence
        confidence = min(100.0, max(0.0, abs(strategy_score)))

        # Feature breakdown: one item per contribution
        feature_breakdown = []
        for c in contribs:
            feature_breakdown.append({
                "name": c.name,
                "raw_value": c.value,
                "weight": c.weight,
                "contribution": c.contribution,
                "direction": c.direction,
                "description": c.description,
            })

        return {
            "symbol": symbol,
            "strategy_score": strategy_score,
            "recommendation": recommendation,
            "confidence": round(confidence, 2),
            "rank": rank,
            "total_stocks": total,
            "feature_breakdown": feature_breakdown,
            "technical_score": technical_score,
            "ml_score": ml_score,
            "gru_score": gru_score,
            "risk_score": risk_score,
            "explanation": {
                "dynamic_explanation": explain_result.dynamic_explanation,
                "why_not": explain_result.why_not,
                "feature_attributions": [
                    {
                        "category": fa.category,
                        "subtotal": fa.subtotal,
                        "features": fa.features,
                    }
                    for fa in (explain_result.feature_attributions or [])
                ],
                "current_values": cv,
            }
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stock strategy test failed: {e}")


@router.get("/snapshots/list")
async def list_available_snapshots(limit: int = Query(10, description="Max snapshots to return")):
    """
    Return available snapshot IDs and dates for the Historical Snapshots tab.
    """
    try:
        snapshots = db.list_snapshot_dates(official_only=True, limit=limit)
        return [
            {
                "snapshot_id": s["snapshot_id"],
                "snapshot_date": s["snapshot_date"],
                "market_date": s.get("market_date", s["snapshot_date"]),
                "generated_at": s.get("generated_at", ""),
                "stocks_processed": s.get("stocks_processed", 0),
            }
            for s in snapshots
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list snapshots: {e}")

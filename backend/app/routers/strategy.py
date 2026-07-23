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

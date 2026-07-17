import logging
import json
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    ExplainScoreResponse,
    NormalizationExplain,
    ResearchReference as ResearchReferenceSchema,
    FeatureMetadata,
    FeatureAttribution,
    CategoryContribution,
    Contribution,
    ValidationMetric,
    ScoreInterpretation
)
from app.services import db, stock_service
from app.services.explainability import EXPLAINERS
from app.services.explainability.base import enrich_runtime_contributions
from app.services.explainability.registry import (
    METADATA_REGISTRY,
    FORMULA_REGISTRY,
    NORMALIZATION_REGISTRY,
    REFERENCE_REGISTRY
)
from app.services.user_stock_service import get_canonical_symbol

logger = logging.getLogger(__name__)
router = APIRouter(tags=["explain"])


def get_indicators_for_stock(snapshot_id: str, symbol: str) -> dict:
    conn = db.get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM snapshot_indicator WHERE snapshot_id = ? AND UPPER(symbol) = ?",
            (snapshot_id, symbol.upper())
        ).fetchone()
        return dict(row) if row else {}
    except Exception as e:
        logger.warning(f"Failed to fetch indicators for {symbol} under snapshot {snapshot_id}: {e}")
        return {}
    finally:
        conn.close()

def get_scores_detail_for_stock(snapshot_id: str, symbol: str) -> dict:
    conn = db.get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM snapshot_score WHERE snapshot_id = ? AND UPPER(symbol) = ?",
            (snapshot_id, symbol.upper())
        ).fetchone()
        return dict(row) if row else {}
    except Exception as e:
        logger.warning(f"Failed to fetch scores detail for {symbol} under snapshot {snapshot_id}: {e}")
        return {}
    finally:
        conn.close()

@router.get("/explain/{score_type}", response_model=ExplainScoreResponse)
async def explain_score(
    score_type: str,
    symbol: Optional[str] = Query(None, description="Ticker symbol of the stock"),
    strategy_id: Optional[str] = Query(None, description="Strategy ID to explain (default 'pms_default')")
):
    """
    Expose the explanation methodology, visual formula, parameters, 
    and dynamic narrative for any score. Optionally takes a symbol.
    """
    normalized_type = score_type.lower().strip()
    
    # If strategy_id is provided and not pms_default, execute custom strategy explanation
    if strategy_id and strategy_id != "pms_default" and symbol:
        from app.services import strategy_service
        from app.services.db import get_db_session
        session = get_db_session()
        try:
            strat = strategy_service.get_strategy_by_id(session, strategy_id)
            if not strat:
                raise HTTPException(status_code=404, detail=f"Custom strategy '{strategy_id}' not found.")
            defn = json.loads(strat.strategy_definition)
            latest_snap = db.get_latest_snapshot()
            snap_id = latest_snap["snapshot_id"] if latest_snap else None
            return strategy_service.explain_custom_strategy_score(defn, symbol, snap_id)
        finally:
            session.close()

    if normalized_type not in EXPLAINERS:
        raise HTTPException(
            status_code=404, 
            detail=f"Score type '{score_type}' is not recognized. Supported scores: {list(EXPLAINERS.keys())}"
        )
        
    explainer = EXPLAINERS[normalized_type]
    
    # Try serving from pre-calculated explainability_snapshot first
    if symbol:
        canonical_symbol = get_canonical_symbol(symbol)
        latest_snap = db.get_latest_snapshot()
        if latest_snap:
            snap_id = latest_snap["snapshot_id"]
            conn = db.get_db_connection()
            try:
                row = conn.execute(
                    """
                    SELECT * FROM explainability_snapshot 
                    WHERE snapshot_id = ? AND UPPER(symbol) = UPPER(?) AND LOWER(score_type) = LOWER(?)
                    """,
                    (snap_id, canonical_symbol, normalized_type)
                ).fetchone()
                if row:
                    import json
                    from app.models.schemas import Contribution, ValidationMetric, ResearchReference, ScoreInterpretation
                    
                    def load_json(val, default):
                        if not val:
                            return default
                        try:
                            return json.loads(val)
                        except Exception:
                            return default

                    contribs = load_json(row.get("indicator_contributions"), [])
                    val_metrics = load_json(row.get("validation_metrics"), [])
                    refs = load_json(row.get("research_references"), [])
                    interpretations = load_json(row.get("interpretation"), [])
                    feat_vals = load_json(row.get("current_values"), {})
                    
                    current_contributions = [Contribution(**c) for c in contribs]
                    validation = [ValidationMetric(**v) for v in val_metrics]
                    references = [ResearchReference(**r) for r in refs]
                    interpretation = [ScoreInterpretation(**i) for i in interpretations]

                    # Load the feature contributions column
                    feat_contribs_json = row.get("feature_contributions")
                    feature_attributions = None
                    explanation_type = "global_importance"
                    dynamic_explanation = ""
                    why_not = ""
                    
                    if feat_contribs_json:
                        try:
                            feat_contribs_data = json.loads(feat_contribs_json)
                            if isinstance(feat_contribs_data, dict):
                                explanation_type = feat_contribs_data.get("explanation_type", "global_importance")
                                dynamic_explanation = feat_contribs_data.get("dynamic_explanation") or ""
                                why_not = feat_contribs_data.get("why_not") or ""
                                runtime_categories = feat_contribs_data.get("categories", [])
                                feature_attributions = enrich_runtime_contributions(runtime_categories)
                            elif isinstance(feat_contribs_data, list):
                                # If legacy format, wrap it
                                feature_attributions = enrich_runtime_contributions(feat_contribs_data)
                        except Exception as ex:
                            logger.warning(f"Failed to parse or enrich feature contributions: {ex}")

                    stock_detail = stock_service.get_stock(canonical_symbol)
                    current_value = 0.0
                    if stock_detail:
                        score_field_map = {
                            "composite": "CompositeScoreV2",
                            "technical": "TechnicalScore",
                            "ensemble": "MLScore",
                            "gru": "GRUScore",
                            "reliability": "ReliabilityScore",
                            "confidence": "Confidence",
                            "risk": "RiskScore",
                            "momentum": "MomentumScore",
                            "trend": "TrendScore"
                        }
                        f = score_field_map.get(normalized_type)
                        if f and hasattr(stock_detail, f):
                            current_value = getattr(stock_detail, f)
                            
                    logger.info(f"Serving pre-calculated explainability snapshot for {canonical_symbol} ({score_type})")
                    return ExplainScoreResponse(
                        score_type=score_type,
                        symbol=canonical_symbol,
                        purpose=row.get("purpose") or "",
                        formula=row.get("formula") or "",
                        current_value=float(current_value) if current_value is not None else 0.0,
                        current_values=feat_vals,
                        current_contributions=current_contributions,
                        interpretation=interpretation,
                        validation=validation,
                        references=references,
                        limitations=[],
                        factors=[],
                        dynamic_explanation=dynamic_explanation,
                        why_not=why_not,
                        explanation_type=explanation_type,
                        feature_attributions=feature_attributions
                    )
            except Exception as e:
                logger.warning(f"Error querying explainability_snapshot from database: {e}", exc_info=True)
            finally:
                conn.close()

    # Fallback to runtime calculation
    stock_data = {}
    history = []
    
    if symbol:
        canonical_symbol = get_canonical_symbol(symbol)
        stock_detail = stock_service.get_stock(canonical_symbol)
        if not stock_detail:
            raise HTTPException(
                status_code=404,
                detail=f"Stock '{symbol}' not found in active universe."
            )
            
        stock_data = stock_detail.model_dump()
        history = db.get_historical_scores(canonical_symbol, limit=30)
        
        latest_snap = db.get_latest_snapshot()
        if latest_snap:
            snap_id = latest_snap["snapshot_id"]
            stock_data["indicators"] = get_indicators_for_stock(snap_id, canonical_symbol)
            stock_data["scores"] = get_scores_detail_for_stock(snap_id, canonical_symbol)
            
        scores_dict = stock_data.get("scores") or {}
        stock_data["GRU_LONG"] = scores_dict.get("gru_long") or stock_data.get("GRU_LONG")
        stock_data["GRU_HOLD"] = scores_dict.get("gru_hold") or stock_data.get("GRU_HOLD")
        stock_data["GRU_SHORT"] = scores_dict.get("gru_short") or stock_data.get("GRU_SHORT")
        stock_data["ReturnScore"] = scores_dict.get("return_score") or stock_data.get("ReturnScore")
        
        logger.info(f"Fallback: calculating runtime explanation for {symbol} ({score_type})")

    try:
        response = explainer.explain(stock_data, history)
        return response
    except Exception as e:
        logger.error(f"Failed to generate explainability payload for {score_type}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal explainability computation error: {str(e)}"
        )



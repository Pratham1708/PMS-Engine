import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import ExplainScoreResponse
from app.services import db, stock_service
from app.services.explainability import EXPLAINERS
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
    symbol: Optional[str] = Query(None, description="Ticker symbol of the stock")
):
    """
    Expose the explanation methodology, visual formula, parameters, 
    and dynamic narrative for any score. Optionally takes a symbol.
    """
    normalized_type = score_type.lower().strip()
    if normalized_type not in EXPLAINERS:
        raise HTTPException(
            status_code=404, 
            detail=f"Score type '{score_type}' is not recognized. Supported scores: {list(EXPLAINERS.keys())}"
        )
        
    explainer = EXPLAINERS[normalized_type]
    
    # 1. Base stock data container
    stock_data = {}
    history = []
    
    if symbol:
        canonical_symbol = get_canonical_symbol(symbol)
        # Fetch stock details from stock_service (which handles snapshot and cache fallback)
        stock_detail = stock_service.get_stock(canonical_symbol)
        if not stock_detail:
            raise HTTPException(
                status_code=404,
                detail=f"Stock '{symbol}' not found in active universe."
            )
            
        stock_data = stock_detail.model_dump()
        
        # Load historical scores (up to last 30 snapshots)
        history = db.get_historical_scores(canonical_symbol, limit=30)
        
        # Query indicators and weights if database has snapshots
        latest_snap = db.get_latest_snapshot()
        if latest_snap:
            snap_id = latest_snap["snapshot_id"]
            stock_data["indicators"] = get_indicators_for_stock(snap_id, canonical_symbol)
            stock_data["scores"] = get_scores_detail_for_stock(snap_id, canonical_symbol)
            
        # Map GRU probabilities directly if present in DB
        scores_dict = stock_data.get("scores") or {}
        stock_data["GRU_LONG"] = scores_dict.get("gru_long") or stock_data.get("GRU_LONG")
        stock_data["GRU_HOLD"] = scores_dict.get("gru_hold") or stock_data.get("GRU_HOLD")
        stock_data["GRU_SHORT"] = scores_dict.get("gru_short") or stock_data.get("GRU_SHORT")
        stock_data["ReturnScore"] = scores_dict.get("return_score") or stock_data.get("ReturnScore")
        
        logger.info(
            f"[API ROUTE DEBUG] Loaded stock detail payload for symbol {symbol}: "
            f"TechnicalScore={stock_data.get('TechnicalScore')}, "
            f"MLScore={stock_data.get('MLScore')}, GRUScore={stock_data.get('GRUScore')}, "
            f"ReliabilityScore={stock_data.get('ReliabilityScore')}"
        )

            
    # 2. Run explanation generation
    try:
        response = explainer.explain(stock_data, history)
        logger.info(
            f"[API ROUTE DEBUG] Explainer [{score_type}] completed successfully. "
            f"current_value={response.current_value}, "
            f"current_values={response.current_values}, "
            f"contributions_count={len(response.current_contributions)}"
        )
        return response
    except Exception as e:
        logger.error(f"Failed to generate explainability payload for {score_type}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal explainability computation error: {str(e)}"
        )


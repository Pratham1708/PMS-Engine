"""
trade_engine.py — Engine 7: Build the trade log with per-trade attribution.

Responsibilities:
  - Convert raw closed trade dicts from portfolio_simulator into typed TradeRecord dicts.
  - Compute TradeAttribution (why_entered, why_exited, top_contributors, top_detractors)
    by running the scoring kernel contribution loop on entry/exit snapshot data.
  - Write full trade log to ctx.trade_log (overwriting the raw version).
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from app.services import db
from app.services.backtest.engines import StrategyExecutionContext
from app.services.strategy_service import (
    resolve_raw_feature_value,
    normalize_feature_value,
)
from app.services.explainability.registry.features import METADATA_REGISTRY

logger = logging.getLogger(__name__)


def _compute_attribution(
    features: List[str],
    weights: Dict[str, float],
    stock_row: Dict,
    indicators: Dict,
    scores: Dict,
    snapshot_id: str,
) -> Dict[str, Any]:
    """
    Compute contribution of each feature and produce attribution narrative.
    Returns {why_text, top_contributors, top_detractors, eqif_available}.
    """
    contributions = []
    for feat_id in features:
        w = weights.get(feat_id, 0.0)
        if w == 0.0:
            continue
        try:
            raw = resolve_raw_feature_value(feat_id, stock_row, indicators, scores)
            norm = normalize_feature_value(feat_id, raw, indicators)
            contrib = norm * (w / 100.0)
            label = METADATA_REGISTRY.get(feat_id, {}).get("label", feat_id)
            contributions.append({
                "feature_id": feat_id,
                "label": label,
                "contribution": round(contrib, 3),
                "raw_value": round(raw, 4),
                "normalized_value": round(norm, 4),
                "weight": w,
            })
        except Exception:
            pass

    contributions.sort(key=lambda x: x["contribution"], reverse=True)
    top_contributors = contributions[:3]
    top_detractors = sorted(contributions, key=lambda x: x["contribution"])[:3]

    # Narrative
    if top_contributors:
        why = "Entered on strength in: " + ", ".join(
            f"{c['label']} ({'+' if c['contribution'] >= 0 else ''}{c['contribution']:.2f})"
            for c in top_contributors[:2]
        )
    else:
        why = "Entry driven by composite score threshold breach."

    eqif_available = bool(snapshot_id and indicators and scores)

    return {
        "why_text": why,
        "top_contributors": top_contributors,
        "top_detractors": top_detractors,
        "entry_eqif_available": eqif_available,
    }


def run(ctx: StrategyExecutionContext) -> StrategyExecutionContext:
    """
    Process raw trade dicts into enriched TradeRecord dicts with attribution.
    """
    definition = ctx.definition
    features: List[str] = definition.get("features", [])
    weights: Dict[str, float] = definition.get("weights", {})

    enriched_trades: List[Dict] = []

    for raw_trade in ctx.trade_log:
        sym = raw_trade.get("symbol", "")
        entry_date = raw_trade.get("entry_date", "")
        exit_date = raw_trade.get("exit_date", "")
        entry_price = float(raw_trade.get("entry_price", 0.0))
        exit_price = float(raw_trade.get("exit_price", 0.0))
        entry_sid = raw_trade.get("entry_snapshot_id", "")
        exit_sid = raw_trade.get("exit_snapshot_id", "")

        # Compute return
        if entry_price > 0:
            return_pct = round((exit_price - entry_price) / entry_price * 100.0, 4)
        else:
            return_pct = 0.0

        # Holding days
        try:
            from datetime import datetime
            holding_days = (
                datetime.strptime(exit_date[:10], "%Y-%m-%d") -
                datetime.strptime(entry_date[:10], "%Y-%m-%d")
            ).days
        except Exception:
            holding_days = 0

        # Trade attribution from entry snapshot
        attribution = {
            "why_entered": "",
            "why_exited": "",
            "top_contributors": [],
            "top_detractors": [],
            "entry_eqif_available": False,
            "exit_eqif_available": False,
        }
        try:
            if entry_sid and features:
                # Get entry snapshot data for this symbol
                entry_universe = ctx.scored_universes.get(entry_sid, {})
                sym_data = entry_universe.get(sym, {})
                if sym_data:
                    stock_row = sym_data.get("_stock", {})
                    ind_row = sym_data.get("_indicators", {})
                    sco_row = sym_data.get("_scores", {})
                    entry_attr = _compute_attribution(features, weights, stock_row, ind_row, sco_row, entry_sid)
                    attribution["why_entered"] = entry_attr["why_text"]
                    attribution["top_contributors"] = entry_attr["top_contributors"]
                    attribution["top_detractors"] = entry_attr["top_detractors"]
                    attribution["entry_eqif_available"] = entry_attr["entry_eqif_available"]

            if exit_sid and features:
                exit_universe = ctx.scored_universes.get(exit_sid, {})
                sym_data_exit = exit_universe.get(sym, {})
                if sym_data_exit:
                    stock_row_x = sym_data_exit.get("_stock", {})
                    ind_row_x = sym_data_exit.get("_indicators", {})
                    sco_row_x = sym_data_exit.get("_scores", {})
                    exit_attr = _compute_attribution(features, weights, stock_row_x, ind_row_x, sco_row_x, exit_sid)
                    # Why exited: look at what turned negative
                    neg = [c for c in exit_attr["top_contributors"] if c["contribution"] < 0]
                    if neg:
                        attribution["why_exited"] = "Exited on weakness in: " + ", ".join(
                            f"{c['label']} ({c['contribution']:.2f})" for c in neg[:2]
                        )
                    else:
                        attribution["why_exited"] = f"Exited at rebalance — score {raw_trade.get('exit_score', 0.0):.1f}"
                    attribution["exit_eqif_available"] = exit_attr["entry_eqif_available"]
        except Exception as e:
            logger.debug("[TradeEngine] Attribution failed for %s: %s", sym, e)

        # Company name + sector from universe
        entry_universe = ctx.scored_universes.get(entry_sid, {})
        sym_info = entry_universe.get(sym, {})

        enriched_trades.append({
            "trade_id": str(uuid.uuid4()),
            "symbol": sym,
            "company_name": sym_info.get("company_name", sym),
            "sector": sym_info.get("sector", "Unknown"),
            "entry_date": entry_date,
            "exit_date": exit_date,
            "holding_days": holding_days,
            "entry_price": round(entry_price, 4),
            "exit_price": round(exit_price, 4),
            "entry_score": round(float(raw_trade.get("entry_score", 0.0)), 4),
            "exit_score": round(float(raw_trade.get("exit_score", 0.0)), 4),
            "entry_rating": raw_trade.get("entry_rating", "HOLD"),
            "exit_rating": raw_trade.get("exit_rating", "HOLD"),
            "return_pct": return_pct,
            "position_weight": round(float(raw_trade.get("position_weight", 0.0)), 4),
            "entry_snapshot_id": entry_sid,
            "exit_snapshot_id": exit_sid,
            "attribution": attribution,
        })

    ctx.trade_log = enriched_trades
    logger.info("[TradeEngine] Enriched %d trades with attribution.", len(enriched_trades))
    return ctx

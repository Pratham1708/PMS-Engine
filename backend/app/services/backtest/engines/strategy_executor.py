"""
strategy_executor.py — Engine 2: Score the entire universe per snapshot.

Responsibilities:
  - For each verified snapshot, load stock/indicator/score rows from DB.
  - Apply the unified scoring kernel (resolve_raw_feature_value + normalize_feature_value)
    imported directly from strategy_service — no duplicate logic.
  - Preserve archived pms composite_score and final_rating unchanged.
  - Write scored universe into ctx.scored_universes[snapshot_id].
  - Update execution log with stocks_scored count.
"""

import logging
from typing import Any, Dict, Optional

from app.services import db
from app.services.backtest.engines import StrategyExecutionContext
from app.services.strategy_service import (
    resolve_raw_feature_value,
    normalize_feature_value,
)

logger = logging.getLogger(__name__)


def _compute_custom_score(
    features: list,
    weights: Dict[str, float],
    aggregation: str,
    stock_row: Dict,
    indicators: Dict,
    scores: Dict,
) -> float:
    """
    Apply the strategy's selected features + weights to produce a custom composite score.
    Uses the same kernel as the live strategy service.
    """
    total_weight = 0.0
    weighted_sum = 0.0
    contributions = []

    for feat_id in features:
        w = weights.get(feat_id, 0.0)
        if w == 0.0:
            continue
        raw = resolve_raw_feature_value(feat_id, indicators, scores, stock_row)
        norm = normalize_feature_value(feat_id, raw, indicators)
        weighted_sum += norm * (w / 100.0)
        total_weight += (w / 100.0)
        contributions.append((feat_id, norm * (w / 100.0)))

    if total_weight == 0.0:
        return 0.0

    if aggregation == "weighted_average":
        return weighted_sum / total_weight * 100.0
    elif aggregation == "weighted_sum":
        return min(max(weighted_sum * 100.0, -100.0), 100.0)
    else:
        # Default: weighted average
        return weighted_sum / total_weight * 100.0


def _score_to_rating(score: float, threshold_buy: float, threshold_sell: float) -> str:
    """Map a score to a rating label."""
    if score >= threshold_buy + 10:
        return "STRONG BUY"
    elif score >= threshold_buy:
        return "BUY"
    elif score <= threshold_sell - 10:
        return "STRONG SELL"
    elif score <= threshold_sell:
        return "SELL"
    else:
        return "HOLD"


def run(ctx: StrategyExecutionContext) -> StrategyExecutionContext:
    """
    Score the full universe for every verified snapshot.
    Populates ctx.scored_universes.
    """
    definition = ctx.definition
    features: list = definition.get("features", [])
    weights: Dict[str, float] = definition.get("weights", {})
    thresholds = definition.get("thresholds", {})
    aggregation: str = definition.get("aggregation", "weighted_average")
    threshold_buy: float = float(thresholds.get("buy", 60.0))
    threshold_sell: float = float(thresholds.get("sell", 40.0))

    if not features:
        logger.error("[StrategyExecutor] No features selected in strategy definition.")
        return ctx

    for meta in ctx.snapshot_meta:
        sid = meta["snapshot_id"]
        date = meta["snapshot_date"]

        stocks = db.get_snapshot_stocks(sid)
        indicator_list = db.get_snapshot_indicators(sid)
        score_list = db.get_snapshot_scores(sid)

        # Index indicator and score rows by symbol for O(1) lookup
        ind_by_sym: Dict[str, Dict] = {r["symbol"]: dict(r) for r in indicator_list}
        sco_by_sym: Dict[str, Dict] = {r["symbol"]: dict(r) for r in score_list}

        universe: Dict[str, Dict] = {}
        for row in stocks:
            sym = row["symbol"]
            stock_dict = dict(row)
            ind_dict = ind_by_sym.get(sym, {})
            sco_dict = sco_by_sym.get(sym, {})

            # Custom strategy score
            custom_score = _compute_custom_score(
                features, weights, aggregation, stock_dict, ind_dict, sco_dict
            )
            custom_rating = _score_to_rating(custom_score, threshold_buy, threshold_sell)

            # Archived PMS scores (never recalculated)
            pms_score = float(stock_dict.get("composite_score") or 0.0)
            pms_rating = stock_dict.get("final_rating") or "HOLD"

            close = float(stock_dict.get("close") or 0.0)

            universe[sym] = {
                "custom_score": round(custom_score, 4),
                "custom_rating": custom_rating,
                "pms_score": round(pms_score, 4),
                "pms_rating": pms_rating,
                "close": close,
                "sector": stock_dict.get("sector") or "Unknown",
                "company_name": stock_dict.get("company_name") or sym,
                # Keep raw values for trade attribution
                "_stock": stock_dict,
                "_indicators": ind_dict,
                "_scores": sco_dict,
            }

        ctx.scored_universes[sid] = universe

        # Update execution log entry for this snapshot
        for entry in ctx.execution_log:
            if entry.snapshot_id == sid:
                entry.stocks_scored = len(universe)
                break
        else:
            # No existing entry (shouldn't happen, but be safe)
            from app.services.backtest.engines import ExecutionLogEntry
            ctx.execution_log.append(ExecutionLogEntry(
                snapshot_date=date,
                snapshot_id=sid,
                integrity_status="verified",
                stocks_scored=len(universe),
            ))

        logger.debug("[StrategyExecutor] %s: scored %d stocks", date, len(universe))

    logger.info("[StrategyExecutor] Scored universes for %d snapshots.", len(ctx.snapshot_meta))
    return ctx

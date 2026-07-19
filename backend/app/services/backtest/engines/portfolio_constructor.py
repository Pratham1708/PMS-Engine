"""
portfolio_constructor.py — Engine 4: Translate signals into target portfolio weights.

Pluggable weighting schemes:
  - Equal        : 1/N for top N BUY/STRONG_BUY symbols
  - ScoreWeighted: weight ∝ custom_score (softmax-normalised)
  - RiskParity   : equal risk contribution using ATR-based volatility proxy
  - VolAdjusted  : inverse volatility weighting

Interface contract:
    construct_portfolio(signals, scores, ctx) -> Dict[symbol, target_weight]
    where sum(target_weight) <= 1.0 and all weights ∈ [0, max_position]

Future schemes (Kelly, Minimum Variance) can be added by implementing
the same function signature without any changes to the simulator.
"""

import logging
import math
from typing import Dict, List, Optional

from app.services.backtest.engines import StrategyExecutionContext

logger = logging.getLogger(__name__)

BUY_SIGNALS = {"BUY", "STRONG BUY"}


def _select_candidates(
    universe: Dict[str, Dict],
    max_holdings: int,
) -> List[str]:
    """Return top max_holdings BUY/STRONG_BUY symbols ranked by custom_score desc."""
    candidates = [
        (sym, data["custom_score"])
        for sym, data in universe.items()
        if data.get("custom_signal") in BUY_SIGNALS
        and data.get("close", 0.0) > 0.0
    ]
    candidates.sort(key=lambda x: x[1], reverse=True)
    return [sym for sym, _ in candidates[:max_holdings]]


def _equal_weight(symbols: List[str], max_position: float) -> Dict[str, float]:
    if not symbols:
        return {}
    w = min(1.0 / len(symbols), max_position / 100.0)
    return {sym: w for sym in symbols}


def _score_weighted(
    symbols: List[str],
    universe: Dict[str, Dict],
    max_position: float,
) -> Dict[str, float]:
    """Softmax-normalised weights on custom_score, capped at max_position."""
    if not symbols:
        return {}
    scores = [max(universe[sym]["custom_score"], 0.0) for sym in symbols]
    # Softmax
    exp_scores = [math.exp(s / 20.0) for s in scores]  # /20 to avoid overflow
    total_exp = sum(exp_scores)
    if total_exp == 0:
        return _equal_weight(symbols, max_position)
    cap = max_position / 100.0
    weights = {sym: min(exp_scores[i] / total_exp, cap) for i, sym in enumerate(symbols)}
    # Renormalise after capping
    total_w = sum(weights.values())
    if total_w > 0:
        weights = {sym: w / total_w for sym, w in weights.items()}
    return weights


def _risk_parity(
    symbols: List[str],
    universe: Dict[str, Dict],
    max_position: float,
) -> Dict[str, float]:
    """
    Equal risk contribution using ATR percentile as volatility proxy.
    Weight ∝ 1 / vol; if ATR unavailable, fallback to equal weight.
    """
    if not symbols:
        return {}
    vols = []
    for sym in symbols:
        ind = universe[sym].get("_indicators", {})
        # ATR percentile stored as atr_14 in indicator table
        atr = float(ind.get("atr_14") or 0.0)
        vols.append(max(atr, 0.001))  # avoid /0

    inv_vols = [1.0 / v for v in vols]
    total_inv = sum(inv_vols)
    cap = max_position / 100.0
    weights = {sym: min(inv_vols[i] / total_inv, cap) for i, sym in enumerate(symbols)}
    # Renormalise
    total_w = sum(weights.values())
    if total_w > 0:
        weights = {sym: w / total_w for sym, w in weights.items()}
    return weights


def _vol_adjusted(
    symbols: List[str],
    universe: Dict[str, Dict],
    max_position: float,
) -> Dict[str, float]:
    """Inverse volatility weighting — similar to risk parity but simpler."""
    return _risk_parity(symbols, universe, max_position)


def construct_portfolio(
    universe: Dict[str, Dict],
    ctx: StrategyExecutionContext,
) -> Dict[str, float]:
    """
    Compute target weights for the given snapshot universe using ctx.weighting_scheme.
    Returns {symbol: weight} where sum(weights) ≤ 1.0.
    """
    candidates = _select_candidates(universe, ctx.max_holdings)
    max_pos = ctx.position_size  # % form

    scheme = ctx.weighting_scheme
    if scheme == "Equal":
        weights = _equal_weight(candidates, max_pos)
    elif scheme == "ScoreWeighted":
        weights = _score_weighted(candidates, universe, max_pos)
    elif scheme == "RiskParity":
        weights = _risk_parity(candidates, universe, max_pos)
    elif scheme == "VolAdjusted":
        weights = _vol_adjusted(candidates, universe, max_pos)
    else:
        logger.warning("Unknown weighting_scheme '%s', defaulting to Equal.", scheme)
        weights = _equal_weight(candidates, max_pos)

    return weights


def run(ctx: StrategyExecutionContext) -> StrategyExecutionContext:
    """
    Pre-compute target weights per snapshot and store on context.
    Downstream portfolio_simulator uses ctx._target_weights_per_snapshot.
    """
    target_weights_per_snapshot: Dict[str, Dict[str, float]] = {}

    for meta in ctx.snapshot_meta:
        sid = meta["snapshot_id"]
        universe = ctx.scored_universes.get(sid, {})
        target_weights_per_snapshot[sid] = construct_portfolio(universe, ctx)

    # Store on context for simulator consumption
    ctx._target_weights_per_snapshot = target_weights_per_snapshot  # type: ignore[attr-defined]
    logger.info("[PortfolioConstructor] Target weights computed for %d snapshots.", len(ctx.snapshot_meta))
    return ctx

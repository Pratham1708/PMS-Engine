"""
signal_engine.py — Engine 3: Convert scores → signals.

Responsibilities:
  - Annotate each symbol in scored_universes with custom_signal and pms_signal.
  - custom_signal derived from custom_score vs thresholds in strategy definition.
  - pms_signal = archived final_rating from snapshot_stock (no recalculation).
  - Compute signal density diagnostics per snapshot and update execution log.
  - Warn if buy_pct > 60% (over-broad) or < 5% (over-restrictive).
"""

import logging
from typing import Dict

from app.services.backtest.engines import StrategyExecutionContext

logger = logging.getLogger(__name__)

# Rating → numeric rank for sorting / filtering
_RATING_RANK = {
    "STRONG BUY": 5,
    "BUY": 4,
    "HOLD": 3,
    "SELL": 2,
    "STRONG SELL": 1,
}

BUY_SIGNALS = {"BUY", "STRONG BUY"}
SELL_SIGNALS = {"SELL", "STRONG SELL"}


def run(ctx: StrategyExecutionContext) -> StrategyExecutionContext:
    """
    Annotate scored_universes with custom_signal and pms_signal.
    Updates execution log entries with signal density stats.
    """
    definition = ctx.definition
    thresholds = definition.get("thresholds", {})
    threshold_buy: float = float(thresholds.get("buy", 60.0))
    threshold_sell: float = float(thresholds.get("sell", 40.0))

    for meta in ctx.snapshot_meta:
        sid = meta["snapshot_id"]
        date = meta["snapshot_date"]
        universe = ctx.scored_universes.get(sid, {})
        if not universe:
            continue

        buy_count = 0
        sell_count = 0
        total = len(universe)

        for sym, data in universe.items():
            custom_score = data["custom_score"]

            # Map to signal
            if custom_score >= threshold_buy + 10:
                custom_signal = "STRONG BUY"
            elif custom_score >= threshold_buy:
                custom_signal = "BUY"
            elif custom_score <= threshold_sell - 10:
                custom_signal = "STRONG SELL"
            elif custom_score <= threshold_sell:
                custom_signal = "SELL"
            else:
                custom_signal = "HOLD"

            data["custom_signal"] = custom_signal
            data["custom_signal_rank"] = _RATING_RANK.get(custom_signal, 3)

            # PMS signal: use archived rating (no recalculation)
            data["pms_signal"] = data.get("pms_rating", "HOLD")
            data["pms_signal_rank"] = _RATING_RANK.get(data["pms_signal"], 3)

            if custom_signal in BUY_SIGNALS:
                buy_count += 1
            elif custom_signal in SELL_SIGNALS:
                sell_count += 1

        buy_pct = (buy_count / total * 100.0) if total > 0 else 0.0
        sell_pct = (sell_count / total * 100.0) if total > 0 else 0.0
        signal_density_notes = []

        if buy_pct > 60.0:
            signal_density_notes.append(
                f"WARN: Over-broad buy zone — {buy_pct:.1f}% of universe is BUY/STRONG_BUY. "
                "Consider raising the buy threshold."
            )
        elif buy_pct < 5.0:
            signal_density_notes.append(
                f"WARN: Over-restrictive — only {buy_pct:.1f}% of universe is BUY/STRONG_BUY. "
                "Consider lowering the buy threshold."
            )

        # Update execution log entry
        for entry in ctx.execution_log:
            if entry.snapshot_id == sid:
                entry.signals_generated = total
                entry.buy_signals = buy_count
                entry.sell_signals = sell_count
                entry.buy_pct = round(buy_pct, 2)
                if signal_density_notes:
                    entry.notes = (entry.notes + "; " + "; ".join(signal_density_notes)).strip("; ")
                break

        logger.debug("[SignalEngine] %s: %d buy / %d sell / %d total (%.1f%% buy)",
                     date, buy_count, sell_count, total, buy_pct)

    logger.info("[SignalEngine] Signal annotation complete for %d snapshots.", len(ctx.snapshot_meta))
    return ctx

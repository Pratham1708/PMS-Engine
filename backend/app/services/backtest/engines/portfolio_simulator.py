"""
portfolio_simulator.py — Engine 5: Simulate cash + position ledger across rebalance dates.

Responsibilities:
  - At each rebalance date: compute portfolio value, apply target weights, execute buys/sells.
  - Track transaction costs and slippage on every trade.
  - Record portfolio_ledger per date (for PortfolioTimeline).
  - Build both the custom strategy equity curve and the PMS default equity curve.
  - Measure turnover at each rebalance.
"""

import logging
from typing import Dict, List, Any

from app.services.backtest.engines import StrategyExecutionContext

logger = logging.getLogger(__name__)


def _apply_rebalance(
    cash: float,
    positions: Dict[str, Dict],      # symbol → {shares, entry_price, entry_date, entry_score, entry_sid}
    target_weights: Dict[str, float],
    universe: Dict[str, Dict],
    snapshot_date: str,
    snapshot_id: str,
    transaction_cost: float,
    slippage: float,
    ctx: StrategyExecutionContext,
) -> Dict[str, Any]:
    """
    Execute a single rebalance step. Returns updated {cash, positions, trades_opened, trades_closed, turnover_pct}.
    """
    # Current portfolio value
    port_value = cash
    for sym, pos in positions.items():
        price = universe.get(sym, {}).get("close", pos["entry_price"])
        port_value += pos["shares"] * price

    if port_value <= 0:
        port_value = ctx.initial_capital

    old_weights: Dict[str, float] = {}
    for sym, pos in positions.items():
        price = universe.get(sym, {}).get("close", pos["entry_price"])
        old_weights[sym] = (pos["shares"] * price) / port_value if port_value > 0 else 0.0

    # Turnover = |new - old| / 2
    all_syms = set(list(old_weights.keys()) + list(target_weights.keys()))
    turnover = sum(
        abs(target_weights.get(s, 0.0) - old_weights.get(s, 0.0)) for s in all_syms
    ) / 2.0

    trades_closed: List[Dict] = []
    trades_opened: List[Dict] = []

    # --- Sell positions not in target or weight reduced ---
    for sym in list(positions.keys()):
        target_w = target_weights.get(sym, 0.0)
        current_price = universe.get(sym, {}).get("close", positions[sym]["entry_price"])
        if current_price <= 0:
            continue

        if target_w == 0.0:
            # Full exit
            shares = positions[sym]["shares"]
            sell_price = current_price * (1.0 - slippage)
            proceeds = shares * sell_price * (1.0 - transaction_cost)
            cash += proceeds
            trades_closed.append({
                "symbol": sym,
                "exit_date": snapshot_date,
                "exit_price": current_price,
                "exit_snapshot_id": snapshot_id,
                "exit_score": universe.get(sym, {}).get("custom_score", 0.0),
                "exit_rating": universe.get(sym, {}).get("custom_rating", "HOLD"),
                **positions[sym],
            })
            del positions[sym]

    # --- Recalculate portfolio value after sells ---
    port_value = cash
    for sym, pos in positions.items():
        price = universe.get(sym, {}).get("close", pos["entry_price"])
        port_value += pos["shares"] * price

    # --- Buy / adjust positions in target ---
    for sym, target_w in target_weights.items():
        if target_w <= 0.0:
            continue
        current_price = universe.get(sym, {}).get("close", 0.0)
        if current_price <= 0:
            continue

        target_value = port_value * target_w
        current_value = (positions.get(sym, {}).get("shares", 0.0)) * current_price
        diff = target_value - current_value

        if diff > current_price * 0.5:  # meaningful buy (at least half a share worth)
            buy_price = current_price * (1.0 + slippage)
            cost = min(diff, cash)
            if cost <= 0:
                continue
            shares_bought = cost / buy_price
            actual_cost = shares_bought * buy_price * (1.0 + transaction_cost)
            if actual_cost > cash:
                shares_bought = cash / (buy_price * (1.0 + transaction_cost))
                actual_cost = cash

            cash -= actual_cost
            if sym in positions:
                # Average into existing position
                old_shares = positions[sym]["shares"]
                positions[sym]["shares"] = old_shares + shares_bought
            else:
                positions[sym] = {
                    "shares": shares_bought,
                    "entry_price": buy_price,
                    "entry_date": snapshot_date,
                    "entry_snapshot_id": snapshot_id,
                    "entry_score": universe.get(sym, {}).get("custom_score", 0.0),
                    "entry_rating": universe.get(sym, {}).get("custom_rating", "HOLD"),
                    "symbol": sym,
                }
                trades_opened.append(positions[sym])

    # Final portfolio value
    port_value = cash
    for sym, pos in positions.items():
        price = universe.get(sym, {}).get("close", pos["entry_price"])
        port_value += pos["shares"] * price

    return {
        "cash": cash,
        "positions": positions,
        "portfolio_value": port_value,
        "trades_closed": trades_closed,
        "trades_opened": trades_opened,
        "turnover_pct": round(turnover * 100.0, 2),
    }


def run(ctx: StrategyExecutionContext) -> StrategyExecutionContext:
    """
    Run the portfolio simulation across all rebalance snapshots.
    Populates ctx.portfolio_ledger, ctx.open_positions, and execution log.
    Also builds the PMS default equity curve using archived final_rating signals.
    """
    target_weights_map = getattr(ctx, "_target_weights_per_snapshot", {})

    # ── Custom strategy simulation ────────────────────────────────
    cash = ctx.initial_capital
    positions: Dict[str, Dict] = {}
    all_closed_trades: List[Dict] = []

    # ── PMS default simulation (parallel) ────────────────────────
    pms_cash = ctx.initial_capital
    pms_positions: Dict[str, Dict] = {}

    pms_eq: List[Dict] = []
    equity: List[Dict] = []

    for meta in ctx.snapshot_meta:
        sid = meta["snapshot_id"]
        date = meta["snapshot_date"]
        universe = ctx.scored_universes.get(sid, {})
        if not universe:
            equity.append({"date": date, "value": cash})
            pms_eq.append({"date": date, "value": pms_cash})
            continue

        target_weights = target_weights_map.get(sid, {})

        # ── Custom rebalance ──
        result = _apply_rebalance(
            cash, positions, target_weights, universe,
            date, sid, ctx.transaction_cost, ctx.slippage, ctx,
        )
        cash = result["cash"]
        positions = result["positions"]
        all_closed_trades.extend(result["trades_closed"])

        # ── PMS rebalance using archived BUY/STRONG_BUY ratings ──
        pms_universe = {sym: data for sym, data in universe.items()}
        pms_target = {}
        pms_candidates = [
            sym for sym, data in pms_universe.items()
            if data.get("pms_signal") in {"BUY", "STRONG BUY"} and data.get("close", 0) > 0
        ]
        pms_candidates = sorted(
            pms_candidates, key=lambda s: pms_universe[s]["pms_score"], reverse=True
        )[:ctx.max_holdings]
        if pms_candidates:
            w = 1.0 / len(pms_candidates)
            pms_target = {sym: min(w, ctx.position_size / 100.0) for sym in pms_candidates}

        pms_result = _apply_rebalance(
            pms_cash, pms_positions, pms_target, pms_universe,
            date, sid, ctx.transaction_cost, ctx.slippage, ctx,
        )
        pms_cash = pms_result["cash"]
        pms_positions = pms_result["positions"]

        # ── Record portfolio snapshot ──
        top_holdings = []
        port_val = result["portfolio_value"]
        for sym, pos in sorted(positions.items(),
                               key=lambda kv: kv[1]["shares"] * universe.get(kv[0], {}).get("close", 0),
                               reverse=True)[:5]:
            price = universe.get(sym, {}).get("close", pos["entry_price"])
            val = pos["shares"] * price
            top_holdings.append({
                "symbol": sym,
                "weight": round(val / port_val, 4) if port_val > 0 else 0.0,
                "score": universe.get(sym, {}).get("custom_score", 0.0),
                "rating": universe.get(sym, {}).get("custom_rating", "HOLD"),
            })

        sector_alloc: Dict[str, float] = {}
        for sym, pos in positions.items():
            sector = universe.get(sym, {}).get("sector", "Unknown")
            price = universe.get(sym, {}).get("close", pos["entry_price"])
            val = pos["shares"] * price
            sector_alloc[sector] = sector_alloc.get(sector, 0.0) + val
        if port_val > 0:
            sector_alloc = {k: round(v / port_val, 4) for k, v in sector_alloc.items()}

        cash_pct = round((cash / port_val * 100.0) if port_val > 0 else 100.0, 2)

        ctx.portfolio_ledger.append({
            "date": date,
            "snapshot_id": sid,
            "portfolio_value": round(port_val, 2),
            "cash": round(cash, 2),
            "cash_pct": cash_pct,
            "sector_allocation": sector_alloc,
            "top_holdings": top_holdings,
            "avg_score": round(
                sum(universe.get(sym, {}).get("custom_score", 0.0) for sym in positions) / len(positions), 2
            ) if positions else 0.0,
            "num_positions": len(positions),
            "turnover_pct": result["turnover_pct"],
        })

        equity.append({"date": date, "value": round(port_val, 2)})
        pms_eq.append({"date": date, "value": round(pms_result["portfolio_value"], 2)})

        # Update execution log
        for entry in ctx.execution_log:
            if entry.snapshot_id == sid:
                entry.trades_executed = len(result["trades_opened"]) + len(result["trades_closed"])
                entry.portfolio_value = round(port_val, 2)
                entry.turnover_pct = result["turnover_pct"]
                break

    # Close any still-open positions at end of simulation using last snapshot prices
    last_meta = ctx.snapshot_meta[-1] if ctx.snapshot_meta else None
    if last_meta:
        last_universe = ctx.scored_universes.get(last_meta["snapshot_id"], {})
        for sym, pos in list(positions.items()):
            price = last_universe.get(sym, {}).get("close", pos["entry_price"])
            all_closed_trades.append({
                "symbol": sym,
                "exit_date": last_meta["snapshot_date"],
                "exit_price": price,
                "exit_snapshot_id": last_meta["snapshot_id"],
                "exit_score": last_universe.get(sym, {}).get("custom_score", 0.0),
                "exit_rating": last_universe.get(sym, {}).get("custom_rating", "HOLD"),
                **pos,
            })

    ctx.open_positions = positions
    ctx.trade_log = all_closed_trades

    # Store both equity curves
    ctx.equity_curve = equity          # [{date, value}] — benchmark added by metrics_engine
    ctx.pms_equity_curve = pms_eq

    logger.info("[PortfolioSimulator] Simulation complete. Final value: %.2f | Trades: %d",
                equity[-1]["value"] if equity else 0.0, len(all_closed_trades))
    return ctx

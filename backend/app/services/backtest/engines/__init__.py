"""
backtest/engines/__init__.py
Defines StrategyExecutionContext — the single shared state object passed through
every backtest engine stage. All engines receive only this object and mutate
only their designated fields, returning the updated context.

Walk-forward reserved fields (Phase 14D):
  walk_forward_windows  — list of {train_start, train_end, test_start, test_end} dicts
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionLogEntry:
    snapshot_date: str
    snapshot_id: str
    integrity_status: str                      # verified | excluded | warned
    integrity_checks: Dict[str, bool] = field(default_factory=dict)
    stocks_scored: int = 0
    signals_generated: int = 0
    buy_signals: int = 0
    sell_signals: int = 0
    buy_pct: float = 0.0
    trades_executed: int = 0
    portfolio_value: float = 0.0
    turnover_pct: float = 0.0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_date": self.snapshot_date,
            "snapshot_id": self.snapshot_id,
            "integrity_status": self.integrity_status,
            "integrity_checks": self.integrity_checks,
            "stocks_scored": self.stocks_scored,
            "signals_generated": self.signals_generated,
            "buy_signals": self.buy_signals,
            "sell_signals": self.sell_signals,
            "buy_pct": self.buy_pct,
            "trades_executed": self.trades_executed,
            "portfolio_value": self.portfolio_value,
            "turnover_pct": self.turnover_pct,
            "notes": self.notes,
        }


@dataclass
class StrategyExecutionContext:
    """
    The shared mutable state object carried through all backtest engine stages.

    Usage:
        ctx = StrategyExecutionContext(...)
        ctx = snapshot_loader.run(ctx)
        ctx = strategy_executor.run(ctx)
        ... etc.
    """

    # ── Identity ──────────────────────────────────────────────────
    run_id: str
    strategy_id: str
    strategy_name: str
    strategy_version: str = "1.0.0"

    # ── Strategy configuration (from DB) ──────────────────────────
    definition: Dict[str, Any] = field(default_factory=dict)   # full strategy_definition JSON
    runtime_config: Dict[str, Any] = field(default_factory=dict)  # from build_runtime_config()

    # ── Simulation parameters ─────────────────────────────────────
    start_date: str = ""
    end_date: str = ""
    rebalance_freq: str = "Monthly"
    weighting_scheme: str = "Equal"
    initial_capital: float = 1_000_000.0
    max_holdings: int = 15
    position_size: float = 10.0               # max % per position
    transaction_cost: float = 0.001
    slippage: float = 0.001
    benchmark: str = "NIFTY50"

    # ── Loaded by snapshot_loader ─────────────────────────────────
    snapshot_dates: List[str] = field(default_factory=list)
    # {snapshot_id → {published, complete, engine_version, ...}}
    snapshot_integrity: Dict[str, Dict] = field(default_factory=dict)
    # [{snapshot_id, snapshot_date, engine_version, ml_model_version, feature_version}]
    snapshot_meta: List[Dict] = field(default_factory=list)

    # ── Loaded by strategy_executor ───────────────────────────────
    # {snapshot_id → {symbol → {custom_score, pms_score, close, sector, company_name, final_rating}}}
    scored_universes: Dict[str, Dict] = field(default_factory=dict)

    # ── Annotated by signal_engine ────────────────────────────────
    # Adds custom_signal and pms_signal to each scored_universes symbol dict in-place

    # ── Computed by portfolio_constructor + simulator ─────────────
    # [{date, snapshot_id, portfolio_value, cash, positions:{symbol:{shares,value,weight}}}]
    portfolio_ledger: List[Dict] = field(default_factory=list)
    open_positions: Dict[str, Dict] = field(default_factory=dict)  # symbol → position state

    # ── Loaded by benchmark_engine ────────────────────────────────
    # {date_str → benchmark_close_price}
    benchmark_prices: Dict[str, float] = field(default_factory=dict)
    benchmark_initial_price: float = 0.0

    # ── Populated by trade_engine ─────────────────────────────────
    trade_log: List[Dict] = field(default_factory=list)     # closed trades
    open_trades: Dict[str, Dict] = field(default_factory=dict)  # symbol → open trade

    # ── Computed by metrics_engine ────────────────────────────────
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    pms_default_metrics: Dict[str, Any] = field(default_factory=dict)
    benchmark_metrics_dict: Dict[str, Any] = field(default_factory=dict)
    equity_curve: List[Dict] = field(default_factory=list)  # [{date, custom, pms_default, benchmark}]
    pms_equity_curve: List[Dict] = field(default_factory=list)  # internal PMS simulation
    win_loss_histogram: List[Dict] = field(default_factory=list)
    sector_allocation_timeline: List[Dict] = field(default_factory=list)
    benchmark_comparison_table: List[Dict] = field(default_factory=list)

    # ── Computed by rolling_engine ────────────────────────────────
    rolling_metrics: Dict[str, Any] = field(default_factory=dict)

    # ── Execution log (populated by each engine) ──────────────────
    execution_log: List[ExecutionLogEntry] = field(default_factory=list)

    # ── Walk-forward reserved (Phase 14D) ─────────────────────────
    # Interface: List of {train_start, train_end, test_start, test_end} dicts.
    # WalkForwardOrchestrator (future) splits date range into these windows,
    # calls backtest_orchestrator.run(ctx) independently per window, then
    # aggregates window results into a walk-forward report.
    walk_forward_windows: Optional[List[Dict]] = None

    # ── Report versioning (frozen at run start) ───────────────────
    engine_version: str = "14C.1"
    feature_registry_version: str = "1.0.0"
    model_version_tag: str = "gru_v1"
    snapshot_version_tag: str = ""          # set by snapshot_loader from loaded meta

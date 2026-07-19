"""
backtest_orchestrator.py — Thin coordinator calling all 9 engine stages sequentially.

Architecture:
  BacktestRunRequest
        │
        ▼
  StrategyExecutionContext   (built from request + strategy definition)
        │
        ├── 1. snapshot_loader.py    — load + integrity verify snapshots
        ├── 2. strategy_executor.py  — score universe per snapshot (shared kernel)
        ├── 3. signal_engine.py      — scores → signals + density diagnostics
        ├── 4. portfolio_constructor.py — signals → target weights
        ├── 5. portfolio_simulator.py — simulate cash/position ledger
        ├── 6. benchmark_engine.py   — load benchmark return series
        ├── 7. metrics_engine.py     — compute all 30+ metrics for 3 series
        ├── 8. rolling_engine.py     — rolling CAGR/Vol/Sharpe/Alpha etc.
        └── 9. trade_engine.py       — trade log + attribution

Walk-Forward hook (Phase 14D):
  A future WalkForwardOrchestrator will split ctx.walk_forward_windows
  and call run_backtest() independently per window, then aggregate.
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import pytz

from app.models.schemas import BacktestRunRequest
from app.services import db
from app.services.backtest.engines import StrategyExecutionContext
from app.services.backtest.engines import snapshot_loader
from app.services.backtest.engines import strategy_executor
from app.services.backtest.engines import signal_engine
from app.services.backtest.engines import portfolio_constructor
from app.services.backtest.engines import portfolio_simulator
from app.services.backtest.engines import benchmark_engine
from app.services.backtest.engines import metrics_engine
from app.services.backtest.engines import rolling_engine
from app.services.backtest.engines import trade_engine
from app.services.strategy_runtime import build_runtime_config

logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")


def _now_ist() -> str:
    return datetime.now(IST).isoformat()


def _load_strategy(strategy_id: str, session) -> Optional[Dict]:
    """Load StrategyMaster from DB and return as dict."""
    from app.models.orm import StrategyMaster
    rec = session.query(StrategyMaster).filter(
        StrategyMaster.strategy_id == strategy_id
    ).first()
    if not rec:
        return None
    defn = {}
    if rec.strategy_definition:
        try:
            defn = json.loads(rec.strategy_definition)
        except Exception:
            pass
    return {
        "strategy_id": rec.strategy_id,
        "strategy_name": rec.strategy_name,
        "version": rec.version or "1.0.0",
        "definition": defn,
    }


def run_backtest(request: BacktestRunRequest) -> Dict[str, Any]:
    """
    Execute a full backtest run synchronously.
    Returns a serialisable dict matching BacktestDetailResponse.
    Stores results in strategy_backtest_runs table.
    """
    run_id = str(uuid.uuid4())
    created_at = _now_ist()
    t_start = time.time()

    session = db.get_db_session()
    try:
        # 1. Load strategy
        strategy = _load_strategy(request.strategy_id, session)
        if not strategy:
            return {"error": f"Strategy {request.strategy_id} not found.", "status": "failed"}

        definition = strategy["definition"]
        runtime_config = {}
        try:
            runtime_config = build_runtime_config(definition)
        except Exception as e:
            logger.warning("[BacktestOrchestrator] build_runtime_config failed: %s", e)

        # 2. Build execution context
        ctx = StrategyExecutionContext(
            run_id=run_id,
            strategy_id=request.strategy_id,
            strategy_name=strategy["strategy_name"],
            strategy_version=strategy["version"],
            definition=definition,
            runtime_config=runtime_config,
            start_date=request.start_date,
            end_date=request.end_date,
            rebalance_freq=request.rebalance_freq,
            weighting_scheme=request.weighting_scheme,
            initial_capital=request.initial_capital,
            max_holdings=request.max_holdings,
            position_size=request.position_size,
            transaction_cost=request.transaction_cost,
            slippage=request.slippage,
            benchmark=request.benchmark,
        )

        # ── Write pending record ──────────────────────────────────
        _save_run_record(run_id, request, strategy, "running", created_at, session)
        session.commit()

        # 3-11. Run engine stages
        try:
            ctx = snapshot_loader.run(ctx)
            ctx = strategy_executor.run(ctx)
            ctx = signal_engine.run(ctx)
            ctx = portfolio_constructor.run(ctx)
            ctx = portfolio_simulator.run(ctx)
            ctx = benchmark_engine.run(ctx)
            ctx = trade_engine.run(ctx)
            ctx = metrics_engine.run(ctx)
            ctx = rolling_engine.run(ctx)
        except snapshot_loader.InsufficientDataError as e:
            _update_run_status(run_id, "failed", str(e), session)
            session.commit()
            return {"error": str(e), "status": "failed", "run_id": run_id}
        except Exception as e:
            logger.exception("[BacktestOrchestrator] Engine error: %s", e)
            _update_run_status(run_id, "failed", str(e), session)
            session.commit()
            return {"error": str(e), "status": "failed", "run_id": run_id}

        execution_time = time.time() - t_start

        # ── Assemble result ───────────────────────────────────────
        result = _build_response(ctx, request, strategy, run_id, created_at, execution_time)

        # ── Persist results ───────────────────────────────────────
        _save_run_results(run_id, result, ctx, execution_time, session)
        session.commit()

        # ── Generate and save reports to disk ────────────────────
        try:
            from app.services.backtest import backtest_report_generator
            backtest_report_generator.save_json_report(run_id, result)
            backtest_report_generator.generate_html_report(run_id, result)
            backtest_report_generator.generate_pdf_report(run_id, result)
        except Exception as re:
            logger.error("[BacktestOrchestrator] Report generation failed: %s", re)

        logger.info("[BacktestOrchestrator] Run %s completed in %.2fs", run_id, execution_time)
        return result

    except Exception as e:
        logger.exception("[BacktestOrchestrator] Unexpected error: %s", e)
        try:
            _update_run_status(run_id, "failed", str(e), session)
            session.commit()
        except Exception:
            pass
        return {"error": str(e), "status": "failed", "run_id": run_id}
    finally:
        session.close()


def _build_response(
    ctx: StrategyExecutionContext,
    request: BacktestRunRequest,
    strategy: Dict,
    run_id: str,
    created_at: str,
    execution_time: float,
) -> Dict[str, Any]:
    """Assemble the full BacktestDetailResponse dict from context."""
    cm = ctx.custom_metrics
    pm = ctx.pms_default_metrics
    bm = ctx.benchmark_metrics_dict

    summary = {
        "total_return_pct": cm.get("returns", {}).get("total_return_pct", 0.0),
        "cagr_pct": cm.get("returns", {}).get("cagr_pct", 0.0),
        "sharpe_ratio": cm.get("risk", {}).get("sharpe_ratio", 0.0),
        "sortino_ratio": cm.get("risk", {}).get("sortino_ratio", 0.0),
        "max_drawdown_pct": cm.get("drawdown", {}).get("max_drawdown_pct", 0.0),
        "win_rate_pct": cm.get("trades", {}).get("win_rate_pct", 0.0),
        "profit_factor": cm.get("trades", {}).get("profit_factor", 0.0),
        "alpha_pct": cm.get("risk", {}).get("alpha_pct", 0.0),
        "beta": cm.get("risk", {}).get("beta", 0.0),
        "pms_total_return_pct": pm.get("returns", {}).get("total_return_pct", 0.0),
        "pms_cagr_pct": pm.get("returns", {}).get("cagr_pct", 0.0),
        "pms_sharpe_ratio": pm.get("risk", {}).get("sharpe_ratio", 0.0),
        "pms_max_drawdown_pct": pm.get("drawdown", {}).get("max_drawdown_pct", 0.0),
        "benchmark_total_return_pct": bm.get("returns", {}).get("total_return_pct", 0.0),
        "benchmark_cagr_pct": bm.get("returns", {}).get("cagr_pct", 0.0),
        "benchmark_sharpe_ratio": bm.get("risk", {}).get("sharpe_ratio", 0.0),
        "benchmark_max_drawdown_pct": bm.get("drawdown", {}).get("max_drawdown_pct", 0.0),
    }

    # Versioning
    snap_versions = list({m.get("engine_version", "") for m in ctx.snapshot_meta if m.get("engine_version")})
    versioning = {
        "backtest_version": "14C.1",
        "engine_version": ctx.engine_version,
        "strategy_version": ctx.strategy_version,
        "snapshot_version_range": ctx.snapshot_version_tag or "unknown",
        "feature_registry_version": ctx.feature_registry_version,
        "model_version": ctx.model_version_tag,
        "generated_at": created_at,
    }

    # Rolling metrics — merge into custom_metrics rolling key
    if ctx.rolling_metrics:
        cm["rolling"] = ctx.rolling_metrics.get("custom", {})
        pm["rolling"] = ctx.rolling_metrics.get("pms_default", {})
        bm["rolling"] = ctx.rolling_metrics.get("benchmark", {})
    else:
        cm["rolling"] = {}
        pm["rolling"] = {}
        bm["rolling"] = {}

    return {
        "run_id": run_id,
        "strategy_id": request.strategy_id,
        "strategy_name": strategy["strategy_name"],
        "status": "completed",
        "start_date": request.start_date,
        "end_date": request.end_date,
        "benchmark": request.benchmark,
        "rebalance_freq": request.rebalance_freq,
        "weighting_scheme": request.weighting_scheme,
        "initial_capital": request.initial_capital,
        "snapshots_used": len(ctx.snapshot_dates),
        "custom_metrics": cm,
        "pms_default_metrics": pm,
        "benchmark_metrics": bm,
        "equity_curve": ctx.equity_curve,
        "sector_allocation_timeline": ctx.sector_allocation_timeline,
        "win_loss_histogram": ctx.win_loss_histogram,
        "summary": summary,
        "trade_log": ctx.trade_log,
        "portfolio_timeline": ctx.portfolio_ledger,
        "benchmark_comparison_table": ctx.benchmark_comparison_table,
        "execution_log": [e.to_dict() for e in ctx.execution_log],
        "versioning": versioning,
        "created_at": created_at,
        "execution_time_sec": round(execution_time, 3),
    }


def _save_run_record(
    run_id: str, request: BacktestRunRequest, strategy: Dict,
    status: str, created_at: str, session
) -> None:
    from app.models.orm import StrategyBacktestRun
    rec = StrategyBacktestRun(
        run_id=run_id,
        strategy_id=request.strategy_id,
        strategy_version=strategy.get("version", "1.0.0"),
        start_date=request.start_date,
        end_date=request.end_date,
        benchmark=request.benchmark,
        rebalance_freq=request.rebalance_freq,
        universe="nifty50_v1",
        weighting_scheme=request.weighting_scheme,
        initial_capital=request.initial_capital,
        max_holdings=request.max_holdings,
        position_size=request.position_size,
        transaction_cost=request.transaction_cost,
        slippage=request.slippage,
        status=status,
        created_at=created_at,
        engine_version="14C.1",
    )
    session.add(rec)


def _update_run_status(run_id: str, status: str, error_msg: str, session) -> None:
    from app.models.orm import StrategyBacktestRun
    rec = session.query(StrategyBacktestRun).filter(
        StrategyBacktestRun.run_id == run_id
    ).first()
    if rec:
        rec.status = status
        rec.error_msg = error_msg


def _save_run_results(
    run_id: str, result: Dict, ctx: StrategyExecutionContext,
    execution_time: float, session
) -> None:
    from app.models.orm import StrategyBacktestRun
    rec = session.query(StrategyBacktestRun).filter(
        StrategyBacktestRun.run_id == run_id
    ).first()
    if not rec:
        return
    rec.status = "completed"
    rec.execution_time_sec = round(execution_time, 3)
    rec.snapshot_version_tag = ctx.snapshot_version_tag
    rec.summary_json = json.dumps(result.get("summary", {}))
    # Store metrics + equity curve (full detail) in metrics_json
    rec.metrics_json = json.dumps({
        "custom_metrics": result.get("custom_metrics", {}),
        "pms_default_metrics": result.get("pms_default_metrics", {}),
        "benchmark_metrics": result.get("benchmark_metrics", {}),
        "equity_curve": result.get("equity_curve", []),
        "trade_log": result.get("trade_log", []),
        "portfolio_timeline": result.get("portfolio_timeline", []),
        "benchmark_comparison_table": result.get("benchmark_comparison_table", []),
        "win_loss_histogram": result.get("win_loss_histogram", []),
        "sector_allocation_timeline": result.get("sector_allocation_timeline", []),
    })
    rec.execution_log_json = json.dumps(result.get("execution_log", []))

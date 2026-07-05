"""
optimizer.py — Grid-search parameter optimizer for the Quant Research Laboratory.

Pure Python: itertools.product over param ranges.
No Optuna, no sklearn. Deterministic with fixed random seed.

Walk-forward validation is used on each param set to prevent overfitting.
"""

import itertools
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

SUPPORTED_METRICS = [
    "sharpe_ratio",
    "cagr_pct",
    "win_rate_pct",
    "calmar_ratio",
    "max_drawdown_pct",   # minimise
    "profit_factor",
    "sortino_ratio",
]

# Metrics where lower is better (we negate them internally)
MINIMISE_METRICS = {"max_drawdown_pct"}


def _get_param_values(param_def: Dict, custom_range: Optional[Dict] = None) -> List[Any]:
    """
    Generate list of candidate values for a single parameter.
    custom_range overrides the default param_def with {min, max, step}.
    """
    if custom_range:
        mn = custom_range.get("min", param_def.get("min", 1))
        mx = custom_range.get("max", param_def.get("max", 50))
        step = custom_range.get("step", param_def.get("step", 1))
    else:
        mn = param_def.get("min", 1)
        mx = param_def.get("max", 50)
        step = param_def.get("step", 1)

    ptype = param_def.get("type", "int")
    values = []
    current = float(mn)
    while current <= float(mx) + 1e-9:
        values.append(int(round(current)) if ptype == "int" else round(current, 4))
        current += float(step)
    return values if values else [param_def.get("default", mn)]


def _score_experiment(metric_value: float, metric: str) -> float:
    """Normalise metric so that higher = better."""
    if metric in MINIMISE_METRICS:
        return -metric_value if metric_value is not None else float("-inf")
    return metric_value if metric_value is not None else float("-inf")


def grid_search(
    df,
    indicator_name: str,
    param_grid_override: Optional[Dict[str, Dict]] = None,
    target_metric: str = "sharpe_ratio",
    n_wf_splits: int = 3,
    max_combinations: int = 200,
) -> Dict:
    """
    Enumerate parameter combinations and evaluate each via walk-forward backtest.

    Args:
        df: OHLCV DataFrame
        indicator_name: name in INDICATOR_REGISTRY
        param_grid_override: {param_name: {min, max, step}} overrides
        target_metric: metric to optimise (see SUPPORTED_METRICS)
        n_wf_splits: number of walk-forward folds per combination
        max_combinations: cap to avoid runaway computation

    Returns dict:
        best_params, best_metric, all_results, optimization_surface, sensitivity
    """
    from app.lab.indicators import INDICATOR_REGISTRY
    from app.lab.backtester import run_walk_forward, generate_signals, run_backtest
    from app.lab.metrics import compute_all_metrics
    from app.lab.chart_builder import param_heatmap, sensitivity_chart

    if indicator_name not in INDICATOR_REGISTRY:
        raise KeyError(f"Unknown indicator: {indicator_name}")

    registry_params = INDICATOR_REGISTRY[indicator_name]["params"]
    if not registry_params:
        # Indicator has no configurable params — run single backtest
        return _single_run_result(df, indicator_name, {}, target_metric)

    # Build candidate values per parameter
    param_names = list(registry_params.keys())
    candidate_lists = []
    for pname in param_names:
        override = (param_grid_override or {}).get(pname)
        vals = _get_param_values(registry_params[pname], override)
        candidate_lists.append(vals)

    # All combinations
    all_combos = list(itertools.product(*candidate_lists))

    # Cap combinations
    if len(all_combos) > max_combinations:
        rng = np.random.default_rng(42)
        indices = rng.choice(len(all_combos), size=max_combinations, replace=False)
        all_combos = [all_combos[i] for i in sorted(indices)]

    logger.info(f"grid_search: {indicator_name}, {len(all_combos)} combinations, metric={target_metric}")

    all_results = []
    best_params = None
    best_score = float("-inf")
    best_metric_value = None

    for combo in all_combos:
        params = dict(zip(param_names, combo))
        try:
            wf_results = run_walk_forward(df, indicator_name, params, n_splits=n_wf_splits)
            if not wf_results:
                continue

            # Aggregate OOS metric across folds (mean)
            oos_vals = [r.get(target_metric) for r in wf_results if r.get(target_metric) is not None]
            if not oos_vals:
                continue
            metric_value = float(np.mean(oos_vals))
            score = _score_experiment(metric_value, target_metric)

            all_results.append({
                "params": params,
                target_metric: round(metric_value, 4),
                "n_folds": len(wf_results),
            })

            if score > best_score:
                best_score = score
                best_params = params
                best_metric_value = metric_value

        except Exception as e:
            logger.debug(f"combo {params} failed: {e}")
            continue

    if best_params is None:
        logger.warning(f"grid_search: no valid results for {indicator_name}")
        best_params = dict(zip(param_names, [p.get("default") for p in registry_params.values()]))
        best_metric_value = 0.0

    # Build chart data
    opt_surface = []
    sensitivity = {}

    if len(param_names) >= 2:
        opt_surface = param_heatmap(all_results, param_names[0], param_names[1], target_metric)

    for pname in param_names:
        sensitivity[pname] = sensitivity_chart(all_results, pname, target_metric)

    # Sort all_results by metric descending (best first)
    all_results.sort(key=lambda x: _score_experiment(x.get(target_metric, 0), target_metric),
                     reverse=True)

    return {
        "best_params": best_params,
        "best_metric_value": round(best_metric_value, 4) if best_metric_value else 0,
        "target_metric": target_metric,
        "total_combinations": len(all_results),
        "top_results": all_results[:20],      # top 20 for display
        "optimization_surface": opt_surface,
        "sensitivity": sensitivity,
    }


def _single_run_result(df, indicator_name, params, target_metric) -> Dict:
    """For indicators with no params, run a single walk-forward."""
    from app.lab.backtester import run_walk_forward
    wf = run_walk_forward(df, indicator_name, params)
    vals = [r.get(target_metric) for r in wf if r.get(target_metric) is not None]
    mv = float(np.mean(vals)) if vals else 0.0
    return {
        "best_params": params,
        "best_metric_value": round(mv, 4),
        "target_metric": target_metric,
        "total_combinations": 1,
        "top_results": [{"params": params, target_metric: round(mv, 4)}],
        "optimization_surface": [],
        "sensitivity": {},
    }

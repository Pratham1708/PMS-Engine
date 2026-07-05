"""
background_runner.py — Async background execution wrapper for long-running lab experiments.

Avoids blocking the FastAPI event loop by executing heavy CPU/IO calculations in a thread pool.
Handles state updates (pending -> running -> complete/failed) and error logging automatically.
"""

import asyncio
import logging
import traceback
from typing import Callable, Any, Dict

from app.lab.db_lab import (
    update_experiment_status,
    save_metrics,
    save_chart,
)

logger = logging.getLogger(__name__)


async def run_experiment_task(
    experiment_id: str,
    runner_fn: Callable[..., Dict[str, Any]],
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Executes a CPU-intensive lab runner function in a thread pool.
    Updates the SQLite lab_experiments status to 'running' at start,
    and 'complete' or 'failed' (with stack trace) on completion.
    
    The runner_fn should return a dictionary with:
      - "metrics": Dict[str, Any] (saved to lab_metrics)
      - "charts": Dict[str, List[Any]] (each key is chart_type, value is list/dict JSON serialized)
      - any optional extras (ignored or saved appropriately)
    """
    logger.info(f"Starting background experiment task {experiment_id}...")
    update_experiment_status(experiment_id, "running")

    loop = asyncio.get_running_loop()
    try:
        # Run CPU-intensive/blocking task in the default executor (thread pool)
        result = await loop.run_in_executor(
            None,
            lambda: runner_fn(*args, **kwargs)
        )

        if not isinstance(result, dict):
            raise ValueError(f"Runner function must return a dict, got {type(result)}")

        # Extract and save metrics
        metrics = result.get("metrics", {})
        if metrics:
            save_metrics(experiment_id, metrics)

        # Extract and save charts
        charts = result.get("charts", {})
        for chart_type, chart_data in charts.items():
            save_chart(experiment_id, chart_type, chart_data)

        update_experiment_status(experiment_id, "complete")
        logger.info(f"Background experiment task {experiment_id} completed successfully.")

    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"Error in background task {experiment_id}: {error_msg}")
        update_experiment_status(experiment_id, "failed", error_msg=error_msg[:1000])


"""
pipeline_monitor.py — Real-time pipeline execution monitor.

A thread-safe singleton that tracks the current state of snapshot pipeline
execution. The API router polls this to provide real-time progress to the UI.
No persistence — survives only while the backend process is running.
"""

import threading
import time
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class PipelineMonitor:
    """
    Thread-safe singleton that tracks the state of a running snapshot pipeline.

    Usage:
        monitor = PipelineMonitor.get_instance()
        monitor.start(snapshot_id="...", total_stocks=50, total_stages=23)
        monitor.update_stage("stage_02_download_ohlcv", 2, 23)
        monitor.stock_done("INFY.NS", success=True)
        monitor.finish("completed")
    """

    _instance: Optional["PipelineMonitor"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._state_lock = threading.Lock()
        self._reset()

    @classmethod
    def get_instance(cls) -> "PipelineMonitor":
        """Return the singleton monitor instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _reset(self) -> None:
        """Reset to idle state."""
        self.snapshot_id: Optional[str] = None
        self.current_stage: Optional[str] = None
        self.total_stages: int = 23
        self.completed_stages: int = 0
        self.pct_complete: float = 0.0
        self.stocks_total: int = 0
        self.stocks_completed: int = 0
        self.stocks_failed: int = 0
        self.elapsed_sec: float = 0.0
        self.est_remaining_sec: Optional[float] = None
        self.status: str = "idle"
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.started_at: Optional[str] = None
        self.stage_log: List[dict] = []
        self._start_time: Optional[float] = None
        self._stage_start_time: Optional[float] = None

    def start(self, snapshot_id: str, total_stocks: int, total_stages: int = 23) -> None:
        """Mark pipeline as started."""
        import pytz
        from datetime import datetime
        with self._state_lock:
            self._reset()
            self.snapshot_id = snapshot_id
            self.total_stages = total_stages
            self.stocks_total = total_stocks
            self.status = "running"
            self._start_time = time.monotonic()
            self.started_at = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()
        logger.info(f"[PipelineMonitor] Started: snapshot={snapshot_id}, stocks={total_stocks}")

    def update_stage(self, stage_name: str, stage_index: int, total_stages: int) -> None:
        """Update the current running stage."""
        with self._state_lock:
            if self._start_time:
                self.elapsed_sec = round(time.monotonic() - self._start_time, 1)
            self.current_stage = stage_name
            self.completed_stages = stage_index - 1
            self.pct_complete = round((stage_index - 1) / max(total_stages, 1) * 100, 1)
            self._stage_start_time = time.monotonic()
            self.stage_log.append({"stage": stage_name, "index": stage_index, "status": "running"})
            # Estimate remaining time
            if self.elapsed_sec > 0 and self.pct_complete > 0:
                total_est = self.elapsed_sec / (self.pct_complete / 100.0)
                self.est_remaining_sec = round(total_est - self.elapsed_sec, 1)

    def stage_done(self, stage_name: str, status: str = "done", log_summary: str = "") -> None:
        """Mark the current stage as completed."""
        with self._state_lock:
            if self._start_time:
                self.elapsed_sec = round(time.monotonic() - self._start_time, 1)
            self.completed_stages += 1
            self.pct_complete = round(self.completed_stages / max(self.total_stages, 1) * 100, 1)
            # Update last stage_log entry
            for entry in reversed(self.stage_log):
                if entry["stage"] == stage_name:
                    entry["status"] = status
                    entry["summary"] = log_summary
                    break

    def stock_done(self, symbol: str, success: bool = True) -> None:
        """Update stock completion counter."""
        with self._state_lock:
            if success:
                self.stocks_completed += 1
            else:
                self.stocks_failed += 1
            if self._start_time:
                self.elapsed_sec = round(time.monotonic() - self._start_time, 1)

    def add_warning(self, message: str) -> None:
        """Append a pipeline warning."""
        with self._state_lock:
            self.warnings.append(message)
            if len(self.warnings) > 50:
                self.warnings = self.warnings[-50:]

    def add_error(self, message: str) -> None:
        """Append a pipeline error."""
        with self._state_lock:
            self.errors.append(message)
            logger.error(f"[PipelineMonitor] Error: {message}")

    def finish(self, status: str) -> None:
        """Mark pipeline as finished with given status."""
        with self._state_lock:
            if self._start_time:
                self.elapsed_sec = round(time.monotonic() - self._start_time, 1)
            self.status = status
            self.current_stage = None
            self.pct_complete = 100.0
            self.est_remaining_sec = 0.0
        logger.info(
            f"[PipelineMonitor] Finished: status={status}, "
            f"elapsed={self.elapsed_sec}s, "
            f"stocks_ok={self.stocks_completed}, failed={self.stocks_failed}"
        )

    def to_dict(self) -> dict:
        """Serialize current state to dict for API response."""
        with self._state_lock:
            return {
                "snapshot_id": self.snapshot_id,
                "current_stage": self.current_stage,
                "total_stages": self.total_stages,
                "completed_stages": self.completed_stages,
                "pct_complete": self.pct_complete,
                "stocks_total": self.stocks_total,
                "stocks_completed": self.stocks_completed,
                "stocks_failed": self.stocks_failed,
                "elapsed_sec": self.elapsed_sec,
                "est_remaining_sec": self.est_remaining_sec,
                "status": self.status,
                "warnings": list(self.warnings),
                "errors": list(self.errors),
                "started_at": self.started_at,
                "stage_log": list(self.stage_log),
            }


# Module-level singleton accessor
def get_monitor() -> PipelineMonitor:
    """Get the global pipeline monitor singleton."""
    return PipelineMonitor.get_instance()

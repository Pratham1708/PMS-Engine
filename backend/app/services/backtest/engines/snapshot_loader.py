"""
snapshot_loader.py — Engine 1: Load and integrity-verify historical snapshots.

Responsibilities:
  1. Query list_snapshot_dates() for the requested date range.
  2. Apply rebalance_freq sampling (Daily/Weekly/Monthly/Quarterly).
  3. Run 8 integrity checks per snapshot — reject failures, warn on mismatches.
  4. Populate ctx.snapshot_dates, ctx.snapshot_meta, ctx.snapshot_integrity.
  5. Abort if fewer than 2 verified snapshots remain.
"""

import logging
from typing import List, Dict, Any

from app.services import db
from app.services.backtest.engines import StrategyExecutionContext, ExecutionLogEntry

logger = logging.getLogger(__name__)


class InsufficientDataError(Exception):
    """Raised when fewer than 2 verified snapshots are available for the requested range."""


# ── Rebalance frequency sampling ─────────────────────────────────────────────

def _iso_year_week(date_str: str) -> str:
    """Return ISO year-week key e.g. '2026-W03'."""
    from datetime import datetime
    d = datetime.strptime(date_str[:10], "%Y-%m-%d")
    return f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}"


def _year_month(date_str: str) -> str:
    return date_str[:7]  # YYYY-MM


def _year_quarter(date_str: str) -> str:
    from datetime import datetime
    d = datetime.strptime(date_str[:10], "%Y-%m-%d")
    q = (d.month - 1) // 3 + 1
    return f"{d.year}-Q{q}"


def _sample_by_frequency(snapshots: List[Dict], freq: str) -> List[Dict]:
    """
    Given an ordered list of snapshot dicts (newest first from DB),
    return the last snapshot per period bucket for the requested frequency.
    """
    if freq == "Daily":
        return snapshots

    if freq == "Weekly":
        key_fn = lambda s: _iso_year_week(s["snapshot_date"])
    elif freq == "Monthly":
        key_fn = lambda s: _year_month(s["snapshot_date"])
    elif freq == "Quarterly":
        key_fn = lambda s: _year_quarter(s["snapshot_date"])
    else:
        logger.warning("Unknown rebalance_freq '%s', defaulting to Monthly.", freq)
        key_fn = lambda s: _year_month(s["snapshot_date"])

    # snapshots is ordered newest→oldest; take the first occurrence per bucket
    # (first = latest date within that bucket)
    seen: Dict[str, Dict] = {}
    for s in snapshots:
        k = key_fn(s)
        if k not in seen:
            seen[k] = s

    # Return in chronological order (oldest first) for simulation
    return sorted(seen.values(), key=lambda s: s["snapshot_date"])


# ── Integrity verification ────────────────────────────────────────────────────

_REQUIRED_STATUSES = {"completed", "completed_with_warnings"}


def _verify_snapshot(snap: Dict, ctx: StrategyExecutionContext) -> Dict[str, Any]:
    """
    Run 8 integrity checks on a snapshot record.
    Returns {passed: bool, checks: {name: bool}, warnings: [str]}.
    """
    sid = snap["snapshot_id"]
    checks: Dict[str, bool] = {}
    warnings: List[str] = []

    # Check 1 — Published
    checks["published"] = snap.get("published_at") is not None

    # Check 2 — Status complete
    checks["complete"] = snap.get("status", "") in _REQUIRED_STATUSES

    # Check 3-5 — Required data tables have rows
    stock_rows = db.get_snapshot_stocks(sid)
    indicator_rows = db.get_snapshot_indicators(sid)
    score_rows = db.get_snapshot_scores(sid)
    checks["has_stock_rows"]      = len(stock_rows) > 0
    checks["has_indicator_rows"]  = len(indicator_rows) > 0
    checks["has_score_rows"]      = len(score_rows) > 0

    # Check 6 — Engine version match (warn-only)
    snap_ev = snap.get("engine_version", "")
    ctx_ev  = ctx.engine_version
    checks["engine_version_match"] = (snap_ev == ctx_ev or snap_ev == "")
    if not checks["engine_version_match"]:
        warnings.append(f"Snapshot engine_version={snap_ev} ≠ run engine_version={ctx_ev} (warn only)")

    # Check 7 — Feature registry version match (warn-only)
    snap_fv = snap.get("feature_version", "")
    checks["feature_registry_match"] = (snap_fv == "" or snap_fv == ctx.feature_registry_version)
    if not checks["feature_registry_match"]:
        warnings.append(f"Snapshot feature_version={snap_fv} ≠ {ctx.feature_registry_version} (warn only)")

    # Check 8 — ML model version match (warn-only)
    snap_mv = snap.get("ml_model_version", "")
    checks["model_version_match"] = (snap_mv == "" or snap_mv == ctx.model_version_tag)
    if not checks["model_version_match"]:
        warnings.append(f"Snapshot ml_model_version={snap_mv} ≠ {ctx.model_version_tag} (warn only)")

    # Blocking checks = checks 1–5
    blocking = ["published", "complete", "has_stock_rows", "has_indicator_rows", "has_score_rows"]
    passed = all(checks[k] for k in blocking)

    return {
        "passed": passed,
        "checks": checks,
        "warnings": warnings,
        "stock_rows": stock_rows,
        "indicator_rows": indicator_rows,
        "score_rows": score_rows,
    }


# ── Main entry point ──────────────────────────────────────────────────────────

def run(ctx: StrategyExecutionContext) -> StrategyExecutionContext:
    """
    Load and integrity-verify historical snapshots for the backtest date range.
    Populates:
      ctx.snapshot_dates
      ctx.snapshot_meta
      ctx.snapshot_integrity
      ctx.snapshot_version_tag
    """
    logger.info("[SnapshotLoader] Loading snapshots for %s → %s (freq=%s)",
                ctx.start_date, ctx.end_date, ctx.rebalance_freq)

    # 1. Fetch all completed snapshots in the requested date range
    all_snapshots = db.list_snapshot_dates(official_only=True, limit=365)
    in_range = [
        s for s in all_snapshots
        if ctx.start_date <= s["snapshot_date"][:10] <= ctx.end_date
    ]

    if not in_range:
        raise InsufficientDataError(
            f"No published snapshots found between {ctx.start_date} and {ctx.end_date}. "
            "Run the Daily Snapshot Pipeline first."
        )

    # 2. Apply rebalance frequency sampling
    sampled = _sample_by_frequency(in_range, ctx.rebalance_freq)
    logger.info("[SnapshotLoader] %d snapshots sampled after %s frequency filter",
                len(sampled), ctx.rebalance_freq)

    # 3. Integrity verification
    verified: List[Dict] = []
    engine_versions: List[str] = []

    for snap in sampled:
        result = _verify_snapshot(snap, ctx)
        sid = snap["snapshot_id"]
        ctx.snapshot_integrity[sid] = {
            "passed": result["passed"],
            "checks": result["checks"],
            "warnings": result["warnings"],
        }

        if result["passed"]:
            status = "verified" if not result["warnings"] else "warned"
            ev = snap.get("engine_version", "")
            if ev:
                engine_versions.append(ev)
            verified.append({
                "snapshot_id": sid,
                "snapshot_date": snap["snapshot_date"][:10],
                "engine_version": ev,
                "ml_model_version": snap.get("ml_model_version", ""),
                "feature_version": snap.get("feature_version", ""),
            })
        else:
            status = "excluded"
            logger.warning("[SnapshotLoader] Snapshot %s excluded — failed checks: %s",
                           sid, [k for k, v in result["checks"].items() if not v])

        notes_parts = [f"{k}={'✓' if v else '✗'}" for k, v in result["checks"].items()]
        if result["warnings"]:
            notes_parts += result["warnings"]

        ctx.execution_log.append(ExecutionLogEntry(
            snapshot_date=snap["snapshot_date"][:10],
            snapshot_id=sid,
            integrity_status=status,
            integrity_checks=result["checks"],
            notes="; ".join(notes_parts),
        ))

    # 4. Minimum threshold
    if len(verified) < 2:
        # Build detailed diagnostics report
        all_snaps = db.list_snapshot_dates(official_only=False, limit=365)
        published_cnt = sum(1 for s in all_snaps if s.get("status") in ("completed", "completed_with_warnings", "published"))
        draft_cnt = sum(1 for s in all_snaps if s.get("status") in ("draft", "generating", "running"))
        failed_cnt = sum(1 for s in all_snaps if s.get("status") == "failed")
        
        failure_reasons_lines = []
        # Check sampled snapshots that failed verification
        for snap in sampled:
            res = _verify_snapshot(snap, ctx)
            if not res["passed"]:
                date_str = snap["snapshot_date"][:10]
                failed_checks = [k for k, v in res["checks"].items() if not v]
                reasons = []
                for fc in failed_checks:
                    if fc == "has_score_rows":
                        reasons.append("Missing score records")
                    elif fc == "has_indicator_rows":
                        reasons.append("Indicator calculation incomplete")
                    elif fc == "has_stock_rows":
                        reasons.append("Missing stock records")
                    elif fc == "complete":
                        reasons.append("Snapshot status incomplete")
                    elif fc == "published":
                        reasons.append("Snapshot not published")
                    else:
                        reasons.append(f"Failed integrity check: {fc}")
                reason_str = ", ".join(reasons) if reasons else "Unknown failure"
                failure_reasons_lines.append(f"{date_str}\n  {reason_str}")
        
        reasons_block = "\n".join(failure_reasons_lines)
        if reasons_block:
            reasons_block = "\nFailure Reasons\n" + reasons_block
            
        raise InsufficientDataError(
            f"Only {len(verified)} snapshot(s) passed integrity checks for "
            f"{ctx.start_date}–{ctx.end_date}. At least 2 are required.\n\n"
            f"Found snapshots: {len(all_snaps)}\n"
            f"Published: {published_cnt}\n"
            f"Draft: {draft_cnt}\n"
            f"Failed: {failed_cnt}\n"
            f"{reasons_block}"
        )

    # 5. Populate context
    ctx.snapshot_meta = verified
    ctx.snapshot_dates = [s["snapshot_date"] for s in verified]

    # Compute snapshot_version_tag (min–max engine_version range)
    if engine_versions:
        ev_set = sorted(set(engine_versions))
        ctx.snapshot_version_tag = ev_set[0] if len(ev_set) == 1 else f"{ev_set[0]}–{ev_set[-1]}"

    logger.info("[SnapshotLoader] %d snapshots verified. Version range: %s",
                len(verified), ctx.snapshot_version_tag)
    return ctx

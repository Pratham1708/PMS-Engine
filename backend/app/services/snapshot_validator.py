"""
snapshot_validator.py — Pre-publish snapshot validation engine.

Runs 12 named checks against a completed (but not yet published) snapshot.
Each check writes a row to snapshot_validation in the DB.
Returns an overall validation result that determines snapshot status:
  - All critical checks pass → 'completed'
  - Only non-critical checks fail → 'completed_with_warnings'
  - Any critical check fails → 'failed'
"""

import logging
from typing import List, Dict, Any, Tuple

from app.services import db

logger = logging.getLogger(__name__)

# ── Check Definitions ────────────────────────────────────────────────────────

CHECKS = [
    # (check_name, is_critical, threshold_description)
    ("min_coverage",            True,  "≥80% of universe stocks downloaded"),
    ("no_duplicates",           True,  "0 duplicate symbols"),
    ("valid_composite_range",   True,  "composite_score in [-100, 100]"),
    ("valid_confidence_range",  True,  "confidence in [0, 100]"),
    ("valid_ratings",           True,  "only recognised rating values"),
    ("no_missing_composite",    True,  "0 null composite scores"),
    ("ohlcv_completeness",      False, "<30% missing OHLCV"),
    ("indicators_completeness", False, "<30% missing indicators"),
    ("data_freshness",          False, "download within 24h"),
    ("sector_coverage",         False, "sectors assigned for >50% of stocks"),
    ("portfolio_feasibility",   False, "at least 1 STRONG BUY or BUY stock"),
    ("changes_computed",        False, "recommendation changes computed if prev snapshot exists"),
]

KNOWN_RATINGS = {"STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"}


def _check_min_coverage(
    snapshot_id: str, stocks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    total = len(stocks)
    failed = sum(1 for s in stocks if s.get("download_status") == "failed")
    ok = total - failed
    coverage = (ok / total * 100) if total > 0 else 0.0
    passed = coverage >= 80.0
    return {
        "check_name": "min_coverage",
        "status": "pass" if passed else "fail",
        "detail": f"{ok}/{total} stocks downloaded ({coverage:.1f}%); threshold ≥80%",
        "affected_count": failed,
        "threshold": 80.0,
        "actual_value": round(coverage, 2),
    }


def _check_no_duplicates(
    snapshot_id: str, stocks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    symbols = [s.get("symbol", "").upper() for s in stocks]
    duplicates = len(symbols) - len(set(symbols))
    return {
        "check_name": "no_duplicates",
        "status": "pass" if duplicates == 0 else "fail",
        "detail": f"{duplicates} duplicate symbols found",
        "affected_count": duplicates,
        "threshold": 0,
        "actual_value": float(duplicates),
    }


def _check_valid_composite_range(
    snapshot_id: str, stocks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    out_of_range = [
        s["symbol"] for s in stocks
        if s.get("composite_score") is not None
        and not (-100 <= s["composite_score"] <= 100)
    ]
    return {
        "check_name": "valid_composite_range",
        "status": "pass" if not out_of_range else "fail",
        "detail": f"{len(out_of_range)} stocks with composite outside [-100, 100]: {out_of_range[:5]}",
        "affected_count": len(out_of_range),
        "threshold": None,
        "actual_value": float(len(out_of_range)),
    }


def _check_valid_confidence_range(
    snapshot_id: str, stocks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    out_of_range = [
        s["symbol"] for s in stocks
        if s.get("confidence") is not None
        and not (0 <= s["confidence"] <= 100)
    ]
    return {
        "check_name": "valid_confidence_range",
        "status": "pass" if not out_of_range else "fail",
        "detail": f"{len(out_of_range)} stocks with confidence outside [0, 100]",
        "affected_count": len(out_of_range),
        "threshold": None,
        "actual_value": float(len(out_of_range)),
    }


def _check_valid_ratings(
    snapshot_id: str, stocks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    invalid = [
        s["symbol"] for s in stocks
        if s.get("final_rating") and s["final_rating"].upper() not in KNOWN_RATINGS
    ]
    return {
        "check_name": "valid_ratings",
        "status": "pass" if not invalid else "fail",
        "detail": f"{len(invalid)} stocks with unrecognised rating",
        "affected_count": len(invalid),
        "threshold": None,
        "actual_value": float(len(invalid)),
    }


def _check_no_missing_composite(
    snapshot_id: str, stocks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    missing = [s["symbol"] for s in stocks if s.get("composite_score") is None]
    return {
        "check_name": "no_missing_composite",
        "status": "pass" if not missing else "fail",
        "detail": f"{len(missing)} stocks missing composite_score",
        "affected_count": len(missing),
        "threshold": 0,
        "actual_value": float(len(missing)),
    }


def _check_ohlcv_completeness(
    snapshot_id: str, stocks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    missing_ohlcv = [
        s["symbol"] for s in stocks
        if s.get("close") is None or s.get("open") is None
    ]
    pct_missing = (len(missing_ohlcv) / max(len(stocks), 1)) * 100
    return {
        "check_name": "ohlcv_completeness",
        "status": "pass" if pct_missing < 30 else "warning",
        "detail": f"{len(missing_ohlcv)} stocks missing OHLCV ({pct_missing:.1f}%); threshold <30%",
        "affected_count": len(missing_ohlcv),
        "threshold": 30.0,
        "actual_value": round(pct_missing, 2),
    }


def _check_indicators_completeness(
    snapshot_id: str, stocks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    indicators = db.get_snapshot_indicators(snapshot_id)
    ind_symbols = {r["symbol"].upper() for r in indicators}
    stock_symbols = {s["symbol"].upper() for s in stocks}
    missing_count = len(stock_symbols - ind_symbols)
    pct_missing = (missing_count / max(len(stocks), 1)) * 100
    return {
        "check_name": "indicators_completeness",
        "status": "pass" if pct_missing < 30 else "warning",
        "detail": f"{missing_count} stocks missing indicator records ({pct_missing:.1f}%)",
        "affected_count": missing_count,
        "threshold": 30.0,
        "actual_value": round(pct_missing, 2),
    }


def _check_data_freshness(
    snapshot_id: str, stocks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Check that snapshot was generated within a reasonable window."""
    import pytz
    from datetime import datetime, timedelta
    snap = db.get_snapshot_by_id(snapshot_id)
    if not snap:
        return {
            "check_name": "data_freshness",
            "status": "warning",
            "detail": "Snapshot record not found",
            "affected_count": 0,
            "threshold": 24.0,
            "actual_value": None,
        }
    try:
        generated_at = datetime.fromisoformat(snap["generated_at"])
        if generated_at.tzinfo is None:
            generated_at = pytz.timezone("Asia/Kolkata").localize(generated_at)
        now = datetime.now(pytz.timezone("Asia/Kolkata"))
        hours_old = (now - generated_at).total_seconds() / 3600.0
        passed = hours_old <= 24.0
        return {
            "check_name": "data_freshness",
            "status": "pass" if passed else "warning",
            "detail": f"Snapshot is {hours_old:.1f}h old; threshold ≤24h",
            "affected_count": 0,
            "threshold": 24.0,
            "actual_value": round(hours_old, 2),
        }
    except Exception as e:
        return {
            "check_name": "data_freshness",
            "status": "warning",
            "detail": f"Could not parse generated_at: {e}",
            "affected_count": 0,
            "threshold": 24.0,
            "actual_value": None,
        }


def _check_sector_coverage(
    snapshot_id: str, stocks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    has_sector = [s for s in stocks if s.get("sector") and s["sector"] not in ("—", "", None)]
    pct = (len(has_sector) / max(len(stocks), 1)) * 100
    return {
        "check_name": "sector_coverage",
        "status": "pass" if pct >= 50 else "warning",
        "detail": f"{len(has_sector)}/{len(stocks)} stocks have sector ({pct:.1f}%); threshold ≥50%",
        "affected_count": len(stocks) - len(has_sector),
        "threshold": 50.0,
        "actual_value": round(pct, 2),
    }


def _check_portfolio_feasibility(
    snapshot_id: str, stocks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    buys = [s for s in stocks if s.get("final_rating") in ("STRONG BUY", "BUY")]
    return {
        "check_name": "portfolio_feasibility",
        "status": "pass" if buys else "warning",
        "detail": f"{len(buys)} stocks rated STRONG BUY or BUY",
        "affected_count": 0,
        "threshold": 1,
        "actual_value": float(len(buys)),
    }


def _check_changes_computed(
    snapshot_id: str, stocks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    prev = db.get_previous_official_snapshot(snapshot_id)
    if prev is None:
        return {
            "check_name": "changes_computed",
            "status": "pass",
            "detail": "No previous snapshot; changes N/A for first snapshot",
            "affected_count": 0,
            "threshold": None,
            "actual_value": None,
        }
    changes = db.get_snapshot_changes(snapshot_id)
    return {
        "check_name": "changes_computed",
        "status": "pass" if changes else "warning",
        "detail": f"{len(changes)} recommendation changes vs previous snapshot",
        "affected_count": 0,
        "threshold": None,
        "actual_value": float(len(changes)),
    }


# ── Main Validator ────────────────────────────────────────────────────────────

CRITICAL_CHECKS = {c[0] for c in CHECKS if c[1]}


def run_validation(snapshot_id: str) -> Tuple[str, float, List[Dict[str, Any]]]:
    """
    Run all 12 validation checks against a snapshot.

    Returns:
        Tuple of (final_status, quality_score_0_100, check_results)
        final_status: 'completed' | 'completed_with_warnings' | 'failed'
        quality_score: 0–100 (pass=10pts, warning=5pts, fail=0pts per check)
    """
    logger.info(f"[Validator] Running validation for snapshot {snapshot_id}")
    stocks = db.get_snapshot_stocks(snapshot_id)

    check_results = []
    critical_failed = False

    check_fns = {
        "min_coverage": _check_min_coverage,
        "no_duplicates": _check_no_duplicates,
        "valid_composite_range": _check_valid_composite_range,
        "valid_confidence_range": _check_valid_confidence_range,
        "valid_ratings": _check_valid_ratings,
        "no_missing_composite": _check_no_missing_composite,
        "ohlcv_completeness": _check_ohlcv_completeness,
        "indicators_completeness": _check_indicators_completeness,
        "data_freshness": _check_data_freshness,
        "sector_coverage": _check_sector_coverage,
        "portfolio_feasibility": _check_portfolio_feasibility,
        "changes_computed": _check_changes_computed,
    }

    for check_name, is_critical, _ in CHECKS:
        try:
            fn = check_fns.get(check_name)
            if fn is None:
                continue
            result = fn(snapshot_id, stocks)
            check_results.append(result)
            status = result["status"]
            if status == "fail" and is_critical:
                critical_failed = True
                logger.error(f"[Validator] CRITICAL FAIL — {check_name}: {result['detail']}")
            elif status == "warning":
                logger.warning(f"[Validator] WARNING — {check_name}: {result['detail']}")
            else:
                logger.info(f"[Validator] PASS — {check_name}")
        except Exception as e:
            logger.error(f"[Validator] Check '{check_name}' raised exception: {e}")
            check_results.append({
                "check_name": check_name,
                "status": "warning",
                "detail": f"Check raised exception: {e}",
                "affected_count": 0,
                "threshold": None,
                "actual_value": None,
            })

    # Determine final status
    if critical_failed:
        final_status = "failed"
    elif any(r["status"] in ("warning", "fail") for r in check_results):
        final_status = "completed_with_warnings"
    else:
        final_status = "completed"

    # Quality score: 10 pts per pass, 5 per warning, 0 per fail
    pass_count = sum(1 for r in check_results if r["status"] == "pass")
    warn_count = sum(1 for r in check_results if r["status"] == "warning")
    total_checks = len(check_results)
    quality_score = round(
        ((pass_count * 10 + warn_count * 5) / max(total_checks * 10, 1)) * 100, 1
    )

    # Persist validation results
    db.save_snapshot_validations(snapshot_id, check_results)
    logger.info(
        f"[Validator] Done: status={final_status}, score={quality_score}, "
        f"pass={pass_count}, warn={warn_count}, "
        f"fail={total_checks - pass_count - warn_count}"
    )
    return final_status, quality_score, check_results

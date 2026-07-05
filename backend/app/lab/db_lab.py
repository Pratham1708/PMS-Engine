"""
db_lab.py — CRUD layer for all Quant Research Laboratory SQLite tables.

Tables managed here (all in the shared pms_engine.db):
  - lab_experiments
  - lab_metrics
  - lab_charts
  - lab_rec_audit
  - lab_reports
  - lab_weight_snapshots

All functions use get_db_connection() from the existing db.py service.
No new database file is introduced.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import pytz

from app.services.db import get_db_connection

logger = logging.getLogger(__name__)
IST = pytz.timezone("Asia/Kolkata")


def _now_ist() -> str:
    return datetime.now(IST).strftime("%d-%b-%Y %I:%M %p IST")


# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENTS
# ─────────────────────────────────────────────────────────────────────────────

def create_experiment(
    module: str,
    name: str,
    symbol: Optional[str] = None,
    params: Optional[Dict] = None,
    seed: int = 42,
) -> str:
    """Insert a new experiment row and return its experiment_id."""
    exp_id = str(uuid.uuid4())
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO lab_experiments
                (experiment_id, lab_module, name, symbol, params_json,
                 version, status, started_at, reproducibility_seed)
            VALUES (?, ?, ?, ?, ?, 1, 'pending', ?, ?)
            """,
            (
                exp_id,
                module,
                name,
                symbol,
                json.dumps(params or {}),
                _now_ist(),
                seed,
            ),
        )
        conn.commit()
        logger.info(f"Created lab experiment {exp_id} [{module}] — {name}")
        return exp_id
    except Exception as e:
        logger.error(f"create_experiment error: {e}")
        raise
    finally:
        conn.close()


def update_experiment_status(
    exp_id: str,
    status: str,
    error_msg: Optional[str] = None,
) -> None:
    """Update experiment status. Sets completed_at when status is complete/failed."""
    conn = get_db_connection()
    try:
        completed_at = _now_ist() if status in ("complete", "failed") else None
        conn.execute(
            """
            UPDATE lab_experiments
            SET status = ?, completed_at = ?, error_msg = ?
            WHERE experiment_id = ?
            """,
            (status, completed_at, error_msg, exp_id),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"update_experiment_status error: {e}")
    finally:
        conn.close()


def get_experiment(exp_id: str) -> Optional[Dict]:
    """Return full experiment detail including metrics and charts."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM lab_experiments WHERE experiment_id = ?", (exp_id,)
        ).fetchone()
        if row is None:
            return None

        result = dict(row)
        # Parse params_json
        try:
            result["params"] = json.loads(result.get("params_json") or "{}")
        except Exception:
            result["params"] = {}

        # Attach metrics
        metrics_rows = conn.execute(
            "SELECT metric_name, metric_value, metric_str FROM lab_metrics WHERE experiment_id = ?",
            (exp_id,),
        ).fetchall()
        result["metrics"] = {}
        for m in metrics_rows:
            key = m["metric_name"]
            result["metrics"][key] = m["metric_value"] if m["metric_value"] is not None else m["metric_str"]

        # Attach charts
        chart_rows = conn.execute(
            "SELECT chart_type, chart_data_json FROM lab_charts WHERE experiment_id = ?",
            (exp_id,),
        ).fetchall()
        result["charts"] = {}
        for c in chart_rows:
            try:
                result["charts"][c["chart_type"]] = json.loads(c["chart_data_json"])
            except Exception:
                result["charts"][c["chart_type"]] = []

        return result
    except Exception as e:
        logger.error(f"get_experiment error: {e}")
        return None
    finally:
        conn.close()


def list_experiments(
    module: Optional[str] = None,
    status: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict]:
    """List experiments with optional filters. Returns newest first."""
    conn = get_db_connection()
    try:
        clauses = []
        params = []
        if module:
            clauses.append("lab_module = ?")
            params.append(module)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if symbol:
            clauses.append("UPPER(symbol) = ?")
            params.append(symbol.upper())

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        rows = conn.execute(
            f"""
            SELECT experiment_id, lab_module, name, symbol, status,
                   started_at, completed_at, error_msg, version
            FROM lab_experiments
            {where}
            """,
            params,
        ).fetchall()
        
        experiments = [dict(r) for r in rows]
        
        from datetime import datetime
        def get_date(r):
            date_str = r.get("started_at", "")
            if date_str and date_str.endswith(" IST"):
                date_str = date_str[:-4]
            try:
                return datetime.strptime(date_str, "%d-%b-%Y %I:%M %p")
            except Exception:
                return datetime.min

        experiments.sort(key=get_date, reverse=True)
        return experiments[offset : offset + limit]
    except Exception as e:
        logger.error(f"list_experiments error: {e}")
        return []
    finally:
        conn.close()


def get_experiments_summary() -> Dict:
    """Return counts by module and status for the research dashboard."""
    conn = get_db_connection()
    try:
        by_module = conn.execute(
            "SELECT lab_module, COUNT(*) as cnt FROM lab_experiments GROUP BY lab_module"
        ).fetchall()
        by_status = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM lab_experiments GROUP BY status"
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM lab_experiments").fetchone()[0]
        return {
            "total": total,
            "by_module": {r["lab_module"]: r["cnt"] for r in by_module},
            "by_status": {r["status"]: r["cnt"] for r in by_status},
        }
    except Exception as e:
        logger.error(f"get_experiments_summary error: {e}")
        return {"total": 0, "by_module": {}, "by_status": {}}
    finally:
        conn.close()


def delete_experiment(exp_id: str) -> bool:
    """Hard-delete an experiment and all its metrics/charts."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM lab_metrics WHERE experiment_id = ?", (exp_id,))
        conn.execute("DELETE FROM lab_charts WHERE experiment_id = ?", (exp_id,))
        conn.execute("DELETE FROM lab_weight_snapshots WHERE experiment_id = ?", (exp_id,))
        conn.execute("DELETE FROM lab_experiments WHERE experiment_id = ?", (exp_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"delete_experiment error: {e}")
        return False
    finally:
        conn.close()


def export_experiment_json(exp_id: str) -> Optional[Dict]:
    """Return full experiment snapshot for JSON export/download."""
    return get_experiment(exp_id)


# ─────────────────────────────────────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────────────────────────────────────

def save_metrics(exp_id: str, metrics: Dict[str, Any]) -> None:
    """Bulk-insert metrics dict into lab_metrics."""
    conn = get_db_connection()
    try:
        rows = []
        for k, v in metrics.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                rows.append((exp_id, k, float(v), None))
            else:
                rows.append((exp_id, k, None, str(v)))
        conn.executemany(
            "INSERT INTO lab_metrics (experiment_id, metric_name, metric_value, metric_str) VALUES (?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    except Exception as e:
        logger.error(f"save_metrics error: {e}")
    finally:
        conn.close()


def get_metrics(exp_id: str) -> Dict:
    """Return metrics dict for an experiment."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT metric_name, metric_value, metric_str FROM lab_metrics WHERE experiment_id = ?",
            (exp_id,),
        ).fetchall()
        result = {}
        for r in rows:
            result[r["metric_name"]] = r["metric_value"] if r["metric_value"] is not None else r["metric_str"]
        return result
    except Exception as e:
        logger.error(f"get_metrics error: {e}")
        return {}
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def save_chart(exp_id: str, chart_type: str, data: List) -> None:
    """Save chart data JSON blob for an experiment."""
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO lab_charts (experiment_id, chart_type, chart_data_json) VALUES (?, ?, ?)",
            (exp_id, chart_type, json.dumps(data)),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"save_chart error: {e}")
    finally:
        conn.close()


def get_charts(exp_id: str) -> Dict[str, List]:
    """Return all chart data for an experiment keyed by chart_type."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT chart_type, chart_data_json FROM lab_charts WHERE experiment_id = ?",
            (exp_id,),
        ).fetchall()
        result = {}
        for r in rows:
            try:
                result[r["chart_type"]] = json.loads(r["chart_data_json"])
            except Exception:
                result[r["chart_type"]] = []
        return result
    except Exception as e:
        logger.error(f"get_charts error: {e}")
        return {}
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATION AUDIT
# ─────────────────────────────────────────────────────────────────────────────

AUDIT_HORIZONS = [1, 5, 10, 20, 30, 90, 180, 365]


def insert_rec_audit_rows(
    analysis_id: str,
    symbol: str,
    rating: str,
    composite_score: float,
    analyzed_at: str,
) -> int:
    """
    Insert one audit row per horizon for a single analysis record.
    Uses INSERT OR IGNORE to be idempotent.
    Returns number of rows inserted.
    """
    conn = get_db_connection()
    inserted = 0
    try:
        for h in AUDIT_HORIZONS:
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO lab_rec_audit
                        (analysis_id, symbol, rating, composite_score,
                         analyzed_at, horizon_days)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (analysis_id, symbol.upper(), rating, composite_score, analyzed_at, h),
                )
                inserted += conn.execute("SELECT changes()").fetchone()[0]
            except Exception:
                pass
        conn.commit()
        return inserted
    except Exception as e:
        logger.error(f"insert_rec_audit_rows error: {e}")
        return 0
    finally:
        conn.close()


def get_pending_audit_rows() -> List[Dict]:
    """Return all audit rows where forward_return is NULL (not yet validated)."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, analysis_id, symbol, rating, composite_score,
                   analyzed_at, horizon_days
            FROM lab_rec_audit
            WHERE validated IS NULL
            ORDER BY analyzed_at ASC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"get_pending_audit_rows error: {e}")
        return []
    finally:
        conn.close()


def update_rec_audit_result(
    row_id: int,
    forward_return: float,
    validated: int,
) -> None:
    """Mark an audit row as validated with its computed forward return."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            UPDATE lab_rec_audit
            SET forward_return = ?, validated = ?, validated_at = ?
            WHERE id = ?
            """,
            (forward_return, validated, _now_ist(), row_id),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"update_rec_audit_result error: {e}")
    finally:
        conn.close()


def get_rec_audit_dashboard() -> Dict:
    """Return aggregated recommendation accuracy by rating × horizon."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT rating, horizon_days,
                   COUNT(*) as total,
                   SUM(CASE WHEN validated = 1 THEN 1 ELSE 0 END) as correct,
                   AVG(forward_return) as avg_return
            FROM lab_rec_audit
            WHERE validated IS NOT NULL
            GROUP BY rating, horizon_days
            """
        ).fetchall()

        dashboard: Dict = {"by_rating": {}, "total_validated": 0}
        total = 0
        for r in rows:
            rating = r["rating"]
            h = r["horizon_days"]
            accuracy = round(r["correct"] / r["total"] * 100, 1) if r["total"] > 0 else None
            if rating not in dashboard["by_rating"]:
                dashboard["by_rating"][rating] = {}
            dashboard["by_rating"][rating][str(h)] = {
                "total": r["total"],
                "correct": r["correct"],
                "accuracy_pct": accuracy,
                "avg_return_pct": round(r["avg_return"] * 100, 2) if r["avg_return"] is not None else None,
            }
            total += r["total"]
        dashboard["total_validated"] = total

        # Overall accuracy by horizon
        horizon_rows = conn.execute(
            """
            SELECT horizon_days,
                   COUNT(*) as total,
                   SUM(CASE WHEN validated = 1 THEN 1 ELSE 0 END) as correct
            FROM lab_rec_audit
            WHERE validated IS NOT NULL
            GROUP BY horizon_days
            """
        ).fetchall()
        dashboard["by_horizon"] = {}
        for r in horizon_rows:
            acc = round(r["correct"] / r["total"] * 100, 1) if r["total"] > 0 else None
            dashboard["by_horizon"][str(r["horizon_days"])] = acc

        return dashboard
    except Exception as e:
        logger.error(f"get_rec_audit_dashboard error: {e}")
        return {"by_rating": {}, "total_validated": 0, "by_horizon": {}}
    finally:
        conn.close()


def get_rec_audit_by_symbol(symbol: str) -> List[Dict]:
    """Return all audit records for a single symbol."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, analysis_id, rating, composite_score, analyzed_at,
                   horizon_days, forward_return, validated, validated_at
            FROM lab_rec_audit
            WHERE UPPER(symbol) = ?
            ORDER BY analyzed_at DESC, horizon_days ASC
            """,
            (symbol.upper(),),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"get_rec_audit_by_symbol error: {e}")
        return []
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# LAB REPORTS
# ─────────────────────────────────────────────────────────────────────────────

def save_lab_report(
    report_id: str,
    experiment_id: Optional[str],
    report_type: str,
    html_path: str,
    pdf_path: Optional[str] = None,
) -> None:
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO lab_reports
                (report_id, experiment_id, report_type, generated_at, html_path, pdf_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (report_id, experiment_id, report_type, _now_ist(), html_path, pdf_path),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"save_lab_report error: {e}")
    finally:
        conn.close()


def list_lab_reports() -> List[Dict]:
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM lab_reports"
        ).fetchall()
        reports = [dict(r) for r in rows]
        
        from datetime import datetime
        def get_date(r):
            date_str = r.get("generated_at", "")
            if date_str and date_str.endswith(" IST"):
                date_str = date_str[:-4]
            try:
                return datetime.strptime(date_str, "%d-%b-%Y %I:%M %p")
            except Exception:
                return datetime.min

        reports.sort(key=get_date, reverse=True)
        return reports
    except Exception as e:
        logger.error(f"list_lab_reports error: {e}")
        return []
    finally:
        conn.close()


def get_lab_report(report_id: str) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM lab_reports WHERE report_id = ?", (report_id,)
        ).fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_lab_report error: {e}")
        return None
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# WEIGHT SNAPSHOTS
# ─────────────────────────────────────────────────────────────────────────────

def save_weight_snapshot(
    exp_id: str,
    weights: Dict[str, float],
    target_metric: str,
    metric_value: float,
) -> None:
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO lab_weight_snapshots
                (experiment_id, w_technical, w_ml, w_gru, w_reliability,
                 target_metric, metric_value, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                exp_id,
                weights.get("TechnicalScore", 0),
                weights.get("MLScore", 0),
                weights.get("GRUScore", 0),
                weights.get("ReliabilityScore", 0),
                target_metric,
                metric_value,
                _now_ist(),
            ),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"save_weight_snapshot error: {e}")
    finally:
        conn.close()


def list_weight_snapshots(exp_id: str) -> List[Dict]:
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT w_technical, w_ml, w_gru, w_reliability,
                   target_metric, metric_value, recorded_at
            FROM lab_weight_snapshots
            WHERE experiment_id = ?
            ORDER BY metric_value DESC
            """,
            (exp_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"list_weight_snapshots error: {e}")
        return []
    finally:
        conn.close()

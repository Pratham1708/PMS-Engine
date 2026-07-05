"""
drift_monitor.py — Score & Model Drift Monitoring Engine.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from app.services.db import get_db_connection

logger = logging.getLogger(__name__)

def check_score_drift(
    threshold: float = 0.20 # mean shift threshold in standard deviations
) -> Dict:
    """
    Perform a score drift audit by comparing recent 30-day score averages in
    analysis_history against the baseline historical averages.
    Logs drift alerts into lab_drift_alerts.
    """
    conn = get_db_connection()
    try:
        # Load scores
        rows = conn.execute(
            "SELECT composite_score, confidence, analyzed_at FROM analysis_history"
        ).fetchall()
    except Exception as e:
        logger.error(f"Error querying analysis history: {e}")
        return {"alerts": [], "drift_detected": False}
    finally:
        conn.close()
        
    if not rows:
        return {"alerts": [], "drift_detected": False, "note": "Insufficient historical data"}
        
    df = pd.DataFrame(rows, columns=["composite_score", "confidence", "analyzed_at"])
    df["analyzed_at"] = pd.to_datetime(df["analyzed_at"], errors="coerce", format="mixed")
    df = df.dropna().sort_values("analyzed_at")
    
    if len(df) < 20:
        return {"alerts": [], "drift_detected": False, "note": "Insufficient historical data"}
        
    # Split: Baseline (older data) vs Recent (last 30 days)
    cutoff = datetime.now() - pd.Timedelta(days=30)
    baseline_df = df[df["analyzed_at"] < cutoff]
    recent_df = df[df["analyzed_at"] >= cutoff]
    
    # Fallback if recent is empty
    if recent_df.empty or baseline_df.empty:
        # Split half-half
        mid = len(df) // 2
        baseline_df = df.iloc[:mid]
        recent_df = df.iloc[mid:]
        
    alerts = []
    
    # Check Composite Score Drift
    b_mean = baseline_df["composite_score"].mean()
    b_std = baseline_df["composite_score"].std()
    r_mean = recent_df["composite_score"].mean()
    
    std_shift_comp = abs(r_mean - b_mean) / (b_std if b_std > 0 else 1.0)
    if std_shift_comp > threshold:
        msg = f"Composite Score V2 mean shifted by {std_shift_comp:.2f} standard deviations (baseline: {b_mean:.2f}, recent: {r_mean:.2f})"
        alerts.append({
            "type": "composite",
            "name": "composite_score_drift",
            "threshold": threshold,
            "val": std_shift_comp,
            "message": msg
        })
        _log_drift_alert("composite", "composite_score_drift", threshold, std_shift_comp, msg)
        
    # Check Confidence Score Drift
    b_conf = baseline_df["confidence"].mean()
    b_conf_std = baseline_df["confidence"].std()
    r_conf = recent_df["confidence"].mean()
    
    std_shift_conf = abs(r_conf - b_conf) / (b_conf_std if b_conf_std > 0 else 1.0)
    if std_shift_conf > threshold:
        msg = f"Confidence Score mean shifted by {std_shift_conf:.2f} standard deviations (baseline: {b_conf:.2f}, recent: {r_conf:.2f})"
        alerts.append({
            "type": "confidence",
            "name": "confidence_score_drift",
            "threshold": threshold,
            "val": std_shift_conf,
            "message": msg
        })
        _log_drift_alert("confidence", "confidence_score_drift", threshold, std_shift_conf, msg)
        
    return {
        "drift_detected": len(alerts) > 0,
        "alerts": alerts,
        "metrics": {
            "composite": {
                "baseline_mean": round(float(b_mean), 2),
                "recent_mean": round(float(r_mean), 2),
                "deviation_std": round(float(std_shift_comp), 3)
            },
            "confidence": {
                "baseline_mean": round(float(b_conf), 2),
                "recent_mean": round(float(r_conf), 2),
                "deviation_std": round(float(std_shift_conf), 3)
            }
        }
    }

def _log_drift_alert(alert_type: str, metric_name: str, threshold: float, current_val: float, message: str):
    """Insert drift alert into SQLite DB."""
    conn = get_db_connection()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            """
            INSERT INTO lab_drift_alerts (alert_type, metric_name, threshold, current_value, message, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (alert_type, metric_name, threshold, current_val, message, now_str)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Error logging drift alert: {e}")
    finally:
        conn.close()

def get_drift_alerts(limit: int = 20) -> List[Dict]:
    """Retrieve logged drift alerts from SQLite."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT id, alert_type, metric_name, threshold, current_value, message, recorded_at FROM lab_drift_alerts ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error reading drift alerts: {e}")
        return []
    finally:
        conn.close()

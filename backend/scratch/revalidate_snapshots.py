"""
Recompute and update the status for all existing snapshots using the validator.
This fixes existing snapshots that were incorrectly marked as 'completed_with_warnings'
purely due to skipped pipeline stages (not actual data quality failures).
"""
from app.services import db
from app.services.snapshot_validator import run_validation

conn = db.get_db_connection()
try:
    rows = conn.execute("SELECT snapshot_id, snapshot_date, status FROM snapshots ORDER BY snapshot_date").fetchall()
    print(f"Found {len(rows)} snapshots to revalidate\n")
    for row in rows:
        snap_id = row['snapshot_id']
        old_status = row['status']
        
        if old_status == 'failed' and not db.get_snapshot_stocks(snap_id):
            print(f"[SKIP] {row['snapshot_date']} ({snap_id[:8]}...) — status=failed, no stocks to validate")
            continue
        
        try:
            new_status, score, checks = run_validation(snap_id)
            passed = sum(1 for c in checks if c['status'] == 'pass')
            failed = sum(1 for c in checks if c['status'] == 'fail')
            
            conn.execute(
                "UPDATE snapshots SET status = ?, validation_score = ?, validation_passed = ? WHERE snapshot_id = ?",
                (new_status, score, 1 if new_status in ('completed', 'completed_with_warnings') else 0, snap_id)
            )
            conn.commit()
            
            changed = "  *** CHANGED ***" if new_status != old_status else ""
            print(f"[{row['snapshot_date']}] {snap_id[:8]}...  {old_status!r} -> {new_status!r}  score={score}  pass={passed} fail={failed}{changed}")
        except Exception as e:
            print(f"[ERROR] {row['snapshot_date']} ({snap_id[:8]}...): {e}")

finally:
    conn.close()

print("\nDone.")

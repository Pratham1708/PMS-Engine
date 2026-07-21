"""
Script to re-process existing snapshots through the pipeline logic to calculate dynamic scores, ratings, and changes.
"""
from app.services import db
from app.services.snapshot_pipeline import run_pipeline

conn = db.get_db_connection()
snaps = conn.execute("SELECT snapshot_date FROM snapshots ORDER BY snapshot_date ASC").fetchall()
dates = [s["snapshot_date"] for s in snaps]
conn.close()

print(f"Re-running pipeline for {len(dates)} dates: {dates}")

for d in dates:
    print(f"\n==========================================")
    print(f"Re-processing snapshot for date: {d}")
    print(f"==========================================")
    try:
        snap_id, status = run_pipeline(snapshot_date=d, is_official=True)
        print(f"RESULT: snapshot_id={snap_id}, status={status}")
    except Exception as e:
        print(f"ERROR: {e}")

print("\nAll snapshots re-processed!")

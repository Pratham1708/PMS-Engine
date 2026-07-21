"""
Cleanup script: remove duplicate validation rows from snapshot_validation.
For each snapshot, keeps only the latest row per check_name (highest id).
This fixes the accumulation caused by the non-idempotent INSERT before the fix.
"""
from app.services import db

conn = db.get_db_connection()
try:
    # Find and count duplicates before cleanup
    dup_rows = conn.execute("""
        SELECT snapshot_id, check_name, COUNT(*) as cnt
        FROM snapshot_validation
        GROUP BY snapshot_id, check_name
        HAVING cnt > 1
    """).fetchall()
    
    print(f"Found {len(dup_rows)} (snapshot_id, check_name) pairs with duplicates")
    for r in dup_rows:
        print(f"  snapshot_id={r['snapshot_id'][:8]}..., check_name={r['check_name']}, count={r['cnt']}")
    
    if dup_rows:
        # Keep only the row with the MAX id for each (snapshot_id, check_name)
        conn.execute("""
            DELETE FROM snapshot_validation
            WHERE id NOT IN (
                SELECT MAX(id)
                FROM snapshot_validation
                GROUP BY snapshot_id, check_name
            )
        """)
        conn.commit()
        deleted = sum(r['cnt'] - 1 for r in dup_rows)
        print(f"\nDeleted {deleted} duplicate validation rows. DB is now clean.")
    else:
        print("No duplicates found - DB is already clean.")
finally:
    conn.close()

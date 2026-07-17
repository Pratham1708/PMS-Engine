import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.config import settings
from app.services import db

def main():
    print(f"DATABASE_URL from settings: '{settings.database_url}'")
    print(f"IS_POSTGRES from db service: {db.IS_POSTGRES}")
    
    conn = db.get_db_connection()
    try:
        rows = conn.execute("SELECT snapshot_id, snapshot_date, is_official, status, stocks_processed FROM snapshots ORDER BY snapshot_date DESC").fetchall()
        print("\nAll snapshots in active DB:")
        for r in rows:
            print(f" - Date: {r['snapshot_date']}, ID: {r['snapshot_id']}, Official: {r['is_official']}, Status: {r['status']}, Stocks: {r['stocks_processed']}")
            
        # Check if there are any records in snapshot_stock for these snapshots
        for r in rows[:2]:
            sid = r['snapshot_id']
            cnt = conn.execute("SELECT count(*) as cnt FROM snapshot_stock WHERE snapshot_id = ?", (sid,)).fetchone()
            print(f"   * snapshot_stock count for {r['snapshot_date']}: {cnt['cnt'] if cnt else 0}")
            cnt_score = conn.execute("SELECT count(*) as cnt FROM snapshot_score WHERE snapshot_id = ?", (sid,)).fetchone()
            print(f"   * snapshot_score count for {r['snapshot_date']}: {cnt_score['cnt'] if cnt_score else 0}")
            
    except Exception as e:
        print(f"Error querying active DB: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.services import db

def main():
    dates = db.list_snapshot_dates(official_only=False)
    print(f"Total snapshots found: {len(dates)}")
    for d in dates:
        print(f"ID: {d['snapshot_id']}, Date: {d['snapshot_date']}, Status: {d['status']}, Official: {d['is_official']}, Processed: {d['stocks_processed']}")

if __name__ == "__main__":
    main()

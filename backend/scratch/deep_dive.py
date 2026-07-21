"""
Deep dive: check why scores are identical between snapshots and trace the root cause.
"""
from app.services import db
import json

conn = db.get_db_connection()

# Get the two snapshots
snaps = conn.execute("SELECT snapshot_id, snapshot_date FROM snapshots WHERE status!='failed' ORDER BY snapshot_date DESC LIMIT 3").fetchall()
print("Available snapshots:")
for s in snaps:
    print(f"  {s['snapshot_date']}: {s['snapshot_id'][:8]}")

sid1 = snaps[1]['snapshot_id']  # older
sid2 = snaps[0]['snapshot_id']  # newer
date1 = snaps[1]['snapshot_date']
date2 = snaps[0]['snapshot_date']
print(f"\nComparing {date1} vs {date2}\n")

# Check if scores are actually different
stocks1 = {r['symbol']: dict(r) for r in conn.execute(
    "SELECT symbol, composite_score, technical_score, final_rating, close FROM snapshot_stock WHERE snapshot_id=?", (sid1,)
).fetchall()}
stocks2 = {r['symbol']: dict(r) for r in conn.execute(
    "SELECT symbol, composite_score, technical_score, final_rating, close FROM snapshot_stock WHERE snapshot_id=?", (sid2,)
).fetchall()}

print(f"Stocks in snap1: {len(stocks1)}, snap2: {len(stocks2)}")
common = set(stocks1.keys()) & set(stocks2.keys())

identical_scores = 0
different_scores = 0
for sym in list(common)[:10]:
    s1 = stocks1[sym]
    s2 = stocks2[sym]
    same = (s1['composite_score'] == s2['composite_score'] and s1['close'] == s2['close'])
    if same:
        identical_scores += 1
        print(f"SAME  [{sym}] close: {s1['close']} vs {s2['close']}, composite: {s1['composite_score']} vs {s2['composite_score']}, rating: {s1['final_rating']} vs {s2['final_rating']}")
    else:
        different_scores += 1
        print(f"DIFF  [{sym}] close: {s1['close']} vs {s2['close']}, composite: {s1['composite_score']} vs {s2['composite_score']}")

print(f"\nOf first 10 common stocks: {identical_scores} identical, {different_scores} different")

# Check snapshot_stage execution log  
print("\n=== Pipeline stages for latest snapshot ===")
stages = conn.execute(
    "SELECT stage_name, stage_status, started_at, ended_at, error_message FROM snapshot_stage WHERE snapshot_id=? ORDER BY started_at",
    (sid2,)
).fetchall()
for st in stages:
    print(f"  [{st['stage_status']:20}] {st['stage_name']}")
    if st['error_message']:
        print(f"    ERROR: {st['error_message'][:150]}")

conn.close()

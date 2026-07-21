"""
Diagnostic: check what data exists in the DB for each snapshot and what nulls exist.
"""
from app.services import db

conn = db.get_db_connection()

# Get all snapshots
snaps = conn.execute("SELECT snapshot_id, snapshot_date, status, stocks_processed FROM snapshots ORDER BY snapshot_date DESC").fetchall()
print(f"=== Snapshots ({len(snaps)}) ===")
for s in snaps:
    sid = s['snapshot_id']
    
    stock_cnt = conn.execute("SELECT COUNT(*) FROM snapshot_stock WHERE snapshot_id=?", (sid,)).fetchone()[0]
    ind_cnt = conn.execute("SELECT COUNT(*) FROM snapshot_indicator WHERE snapshot_id=?", (sid,)).fetchone()[0]
    score_cnt = conn.execute("SELECT COUNT(*) FROM snapshot_score WHERE snapshot_id=?", (sid,)).fetchone()[0]
    sector_cnt = conn.execute("SELECT COUNT(*) FROM snapshot_sector WHERE snapshot_id=?", (sid,)).fetchone()[0]
    market_cnt = conn.execute("SELECT COUNT(*) FROM snapshot_market WHERE snapshot_id=?", (sid,)).fetchone()[0]
    watchlist_cnt = conn.execute("SELECT COUNT(*) FROM snapshot_watchlist WHERE snapshot_id=?", (sid,)).fetchone()[0]
    change_cnt = conn.execute("SELECT COUNT(*) FROM snapshot_change WHERE snapshot_id=?", (sid,)).fetchone()[0]
    
    print(f"\n[{s['snapshot_date']}] {sid[:8]}... status={s['status']} stocks_processed={s['stocks_processed']}")
    print(f"  stock={stock_cnt} indicator={ind_cnt} score={score_cnt} sector={sector_cnt} market={market_cnt} watchlist={watchlist_cnt} change={change_cnt}")

# Check null columns in snapshot_stock for the latest snapshot
print("\n\n=== Null analysis in snapshot_stock (latest snapshot) ===")
latest = snaps[0]
sid = latest['snapshot_id']
sample_stock = conn.execute("SELECT * FROM snapshot_stock WHERE snapshot_id=? LIMIT 1", (sid,)).fetchone()
if sample_stock:
    null_cols = [k for k, v in dict(sample_stock).items() if v is None]
    non_null_cols = [k for k, v in dict(sample_stock).items() if v is not None]
    print(f"NON-NULL cols: {non_null_cols}")
    print(f"NULL cols: {null_cols}")
else:
    print("No stock records found!")

# Check snapshot_change
print("\n=== snapshot_change sample ===")
changes = conn.execute("SELECT * FROM snapshot_change WHERE snapshot_id=? LIMIT 3", (sid,)).fetchall()
if changes:
    for ch in changes:
        print(dict(ch))
else:
    print("No change records!")

# Check snapshot_sector sample
print("\n=== snapshot_sector sample ===")
sectors = conn.execute("SELECT * FROM snapshot_sector WHERE snapshot_id=? LIMIT 3", (sid,)).fetchall()
if sectors:
    for sc in sectors:
        print(dict(sc))
else:
    print("No sector records!")

# Check snapshot_market
print("\n=== snapshot_market sample ===")
market = conn.execute("SELECT * FROM snapshot_market WHERE snapshot_id=? LIMIT 1", (sid,)).fetchone()
if market:
    print(dict(market))
else:
    print("No market record!")

conn.close()

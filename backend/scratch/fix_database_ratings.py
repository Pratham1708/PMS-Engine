import sys
sys.path.insert(0, '.')
from app.services import db
from app.data.loader import data_loader

df = data_loader.get_df()
csv_map = {row['Symbol'].upper(): row for _, row in df.iterrows()}

conn = db.get_db_connection()
snaps = conn.execute("SELECT snapshot_id, snapshot_date FROM snapshots").fetchall()

print(f"Updating {len(snaps)} snapshots with quantitative model ratings & composite scores...")

for s in snaps:
    sid = s['snapshot_id']
    sdate = s['snapshot_date']
    
    stocks = conn.execute("SELECT symbol FROM snapshot_stock WHERE snapshot_id=?", (sid,)).fetchall()
    
    updated_cnt = 0
    strong_buy_cnt = 0
    buy_cnt = 0
    hold_cnt = 0
    sell_cnt = 0
    strong_sell_cnt = 0
    
    for st in stocks:
        sym = st['symbol']
        row = csv_map.get(sym.upper())
        if row is not None:
            composite = float(row['CompositeScoreV2'])
            tech = float(row['TechnicalScore'])
            rating = str(row['FinalRating'])
            
            conn.execute("""
                UPDATE snapshot_stock 
                SET composite_score = ?, technical_score = ?, final_rating = ?, portfolio_eligible = ?
                WHERE snapshot_id = ? AND symbol = ?
            """, (composite, tech, rating, 1 if rating in ('STRONG BUY', 'BUY') else 0, sid, sym))
            
            conn.execute("""
                UPDATE score_snapshot
                SET composite_score = ?, technical_score = ?, recommendation = ?
                WHERE snapshot_id = ? AND symbol = ?
            """, (composite, tech, rating, sid, sym))
            
            updated_cnt += 1
            if rating == 'STRONG BUY': strong_buy_cnt += 1
            elif rating == 'BUY': buy_cnt += 1
            elif rating == 'HOLD': hold_cnt += 1
            elif rating == 'SELL': sell_cnt += 1
            elif rating == 'STRONG SELL': strong_sell_cnt += 1
            
    # Also update snapshot_market table rating counts for this snapshot
    conn.execute("""
        UPDATE snapshot_market
        SET strong_buy_count = ?, buy_count = ?, hold_count = ?, sell_count = ?, strong_sell_count = ?
        WHERE snapshot_id = ?
    """, (strong_buy_cnt, buy_cnt, hold_cnt, sell_cnt, strong_sell_cnt, sid))

conn.commit()
conn.close()

print(f"Successfully updated database! Sample breakdown for snapshot: {strong_buy_cnt} STRONG BUY, {buy_cnt} BUY, {hold_cnt} HOLD, {sell_cnt} SELL, {strong_sell_cnt} STRONG SELL.")

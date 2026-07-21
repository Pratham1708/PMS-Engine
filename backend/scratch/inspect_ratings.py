import sys
sys.path.insert(0, '.')
from app.services import db

snap = db.get_latest_snapshot()
sid = snap['snapshot_id']
stocks = db.get_snapshot_stocks(sid)

print(f"Snapshot ID: {sid}, Date: {snap['snapshot_date']}, Total Stocks: {len(stocks)}")

ratings = {}
for s in stocks:
    r = s.get('final_rating')
    ratings[r] = ratings.get(r, 0) + 1

print("\n=== Current Ratings Breakdown ===")
for r, count in ratings.items():
    print(f"  {r}: {count}")

print("\n=== Top 20 Stocks Sorted by Composite Score ===")
sorted_stocks = sorted(stocks, key=lambda x: x.get('composite_score', 0) or 0, reverse=True)
for s in sorted_stocks[:20]:
    print(f"Symbol: {s['symbol']:<15} | Composite: {s.get('composite_score'):>6.2f} | Tech: {s.get('technical_score'):>6.2f} | ML: {s.get('ml_score'):>6.2f} | GRU: {s.get('gru_score'):>6.2f} | Rel: {s.get('reliability_score'):>6.2f} | Rating: {s.get('final_rating')}")

print("\n=== ADANIENT.NS Details ===")
adani = next((s for s in stocks if "ADANIENT" in s['symbol'].upper()), None)
if adani:
    print(f"Symbol: {adani['symbol']}")
    print(f"  Composite: {adani.get('composite_score')}")
    print(f"  Technical: {adani.get('technical_score')}")
    print(f"  ML: {adani.get('ml_score')}")
    print(f"  GRU: {adani.get('gru_score')}")
    print(f"  Reliability: {adani.get('reliability_score')}")
    print(f"  Rating: {adani.get('final_rating')}")
else:
    print("ADANIENT.NS not found in latest snapshot stocks!")

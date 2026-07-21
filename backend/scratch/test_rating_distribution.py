import sys
sys.path.insert(0, '.')
from app.services import db
from app.data.loader import data_loader
import pandas as pd

df_csv = data_loader.get_df()

snap = db.get_latest_snapshot()
stocks = db.get_snapshot_stocks(snap['snapshot_id'])
df_snap = pd.DataFrame(stocks)

print("=== CSV Data Loader (Original Model) ===")
print("Ratings:", df_csv['FinalRating'].value_counts().to_dict())
print("Top 5 stocks in CSV:")
for idx, r in df_csv.sort_values('CompositeScoreV2', ascending=False).head(5).iterrows():
    print(f"  {r['Symbol']:<15} | Composite: {r['CompositeScoreV2']:>6.2f} | Rating: {r['FinalRating']}")

print("\n=== Current Snapshot in DB ===")
print("Ratings:", df_snap['final_rating'].value_counts().to_dict())
print("Top 5 stocks in current DB snapshot:")
for idx, r in df_snap.sort_values('composite_score', ascending=False).head(5).iterrows():
    print(f"  {r['symbol']:<15} | Composite: {r['composite_score']:>6.2f} | Rating: {r['final_rating']}")

print("\n=== ADANIENT.NS in CSV vs DB ===")
csv_adani = df_csv[df_csv['Symbol'].str.upper() == 'ADANIENT.NS'].iloc[0] if not df_csv[df_csv['Symbol'].str.upper() == 'ADANIENT.NS'].empty else None
db_adani = df_snap[df_snap['symbol'].str.upper() == 'ADANIENT.NS'].iloc[0] if not df_snap[df_snap['symbol'].str.upper() == 'ADANIENT.NS'].empty else None

if csv_adani is not None:
    print(f"CSV ADANIENT: Composite={csv_adani['CompositeScoreV2']}, Rating={csv_adani['FinalRating']}, Tech={csv_adani['TechnicalScore']}")
if db_adani is not None:
    print(f"DB  ADANIENT: Composite={db_adani['composite_score']}, Rating={db_adani['final_rating']}, Tech={db_adani['technical_score']}")

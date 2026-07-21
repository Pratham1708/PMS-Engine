from app.services import db
conn = db.get_db_connection()
row = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='snapshot_validation'").fetchone()
print(row[0])

from app.services import db
conn = db.get_db_connection()
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print('All tables:', [t['name'] for t in tables])
conn.close()

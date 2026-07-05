import sqlite3
import pprint
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "pms_engine.db"))
print("DB Path:", DB_PATH)
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
try:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lab_experiments ORDER BY started_at DESC LIMIT 5")
    rows = cursor.fetchall()
    print("Latest 5 experiments:")
    for r in rows:
        pprint.pprint(dict(r))
except Exception as e:
    print("Error:", e)
finally:
    conn.close()

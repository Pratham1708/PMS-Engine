import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "pms_engine.db"))
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT rating FROM lab_rec_audit")
print("Distinct ratings in lab_rec_audit:", cursor.fetchall())
cursor.execute("SELECT COUNT(*) FROM lab_rec_audit WHERE validated IS NOT NULL")
print("Validated count:", cursor.fetchone()[0])
cursor.execute("SELECT COUNT(*) FROM lab_rec_audit")
print("Total audit count:", cursor.fetchone()[0])
conn.close()

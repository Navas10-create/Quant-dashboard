import sqlite3, os

db_dir = 'db'  # relative to project root
db_path = os.path.join(db_dir, 'ohlc_data.db')  # name it as you like

os.makedirs(db_dir, exist_ok=True)
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS ohlc_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL
)
""")
conn.commit()
conn.close()

print("Created OHLC DB at", db_path)

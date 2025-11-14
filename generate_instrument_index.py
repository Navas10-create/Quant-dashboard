import sqlite3, json, os

# --- Paths ---
db_path = os.path.join("db", "master_contract.db")
config_dir = os.path.join("config")
os.makedirs(config_dir, exist_ok=True)
json_path = os.path.join(config_dir, "instrument_index.json")

# --- Connect to DB ---
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# --- Fetch symbols and names ---
try:
    cur.execute("SELECT DISTINCT name, symbol FROM master_contract WHERE name IS NOT NULL AND symbol IS NOT NULL LIMIT 50000;")
except Exception:
    cur.execute("SELECT DISTINCT instrument_name AS name, fyers_symbol AS symbol FROM instruments WHERE instrument_name IS NOT NULL AND fyers_symbol IS NOT NULL LIMIT 50000;")

rows = cur.fetchall()
conn.close()

# --- Write JSON ---
data = [{"name": r[0], "symbol": r[1]} for r in rows]
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"✅ Exported {len(data)} symbols to {json_path}")

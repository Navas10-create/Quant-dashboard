# charting/scripts/daily_updater.py
import os, requests, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "static", "data")
os.makedirs(OUT_DIR, exist_ok=True)

OPENALGO_HOST = os.getenv("OPENALGO_HOST","http://localhost:5000")
OPENALGO_API_KEY = os.getenv("OPENALGO_API_KEY","")

def fetch_history(symbol, interval="1", limit=2000):
    url = f"{OPENALGO_HOST.rstrip('/')}/api/v1/history"
    resp = requests.get(url, headers={"X-API-KEY": OPENALGO_API_KEY}, params={"symbol":symbol,"interval":interval,"limit":limit}, timeout=10)
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    import sys
    if len(sys.argv)<2:
        print("Usage: daily_updater.py SYMBOL [interval]")
        sys.exit(1)
    sym = sys.argv[1]
    interval = sys.argv[2] if len(sys.argv)>2 else "1"
    try:
        payload = fetch_history(sym, interval)
        out_path = os.path.join(OUT_DIR, f"{sym}_{interval}.json")
        with open(out_path, "w") as f:
            json.dump(payload, f)
        print("Wrote", out_path)
    except Exception as e:
        print("failed:", e)

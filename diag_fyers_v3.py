# diag_fyers_v3.py
import os
import json
import time
import requests
from dotenv import load_dotenv
load_dotenv()

print("\n=== FYERS API DIAGNOSTIC SUITE ===")

TOKEN = os.getenv("FYERS_ACCESS_TOKEN")
if not TOKEN or ":" not in TOKEN:
    print("❌ ERROR: FYERS_ACCESS_TOKEN missing or invalid.")
    exit()

client_id, jwt_token = TOKEN.split(":", 1)

HEADERS = {
    "Authorization": f"{client_id}:{jwt_token}",
    "Content-Type": "application/json"
}

def test_endpoint(name, url, payload):
    print(f"\n--- TEST: {name} ---")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload)}\n")

    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        print(f"Status: {r.status_code}")

        if r.status_code == 200:
            print("RAW:", r.text[:400], "...\n")
        else:
            print("RAW ERROR:", r.text[:400], "...\n")

    except Exception as e:
        print("❌ Exception:", str(e))


# -----------------------------------------
# TEST 1: Profile API (simple ping test)
# -----------------------------------------
test_endpoint("PROFILE", "https://api.fyers.in/api/v3/profile", {})

# -----------------------------------------
# TEST 2: Quotes Snapshot
# -----------------------------------------
test_endpoint(
    "QUOTES",
    "https://api.fyers.in/api/v3/quotes",
    {"symbols": ["NSE:SBIN-EQ"]}
)

# -----------------------------------------
# TEST 3: Depth Snapshot
# -----------------------------------------
test_endpoint(
    "DEPTH",
    "https://api.fyers.in/api/v3/depth",
    {"symbol": "NSE:SBIN-EQ"}
)

# -----------------------------------------
# TEST 4: Historical Candle Data (REAL endpoint)
# -----------------------------------------
now = int(time.time())
test_endpoint(
    "HISTORY",
    "https://api.fyers.in/api/v3/history",
    {
        "symbol": "NSE:SBIN-EQ",
        "resolution": "5",
        "date_format": 0,
        "range_from": now - (60 * 60 * 5),
        "range_to": now,
        "cont_flag": "1"
    }
)

print("\n=== END OF DIAGNOSTICS ===")

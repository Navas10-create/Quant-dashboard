# scripts/test_fyers_history.py
import os, requests, time, json, sys

# configure
FYERS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN")  # clientid:jwt
if not FYERS_TOKEN:
    print("ERROR: FYERS_ACCESS_TOKEN not in env"); sys.exit(1)
client_id, jwt = (FYERS_TOKEN.split(':',1) + [None])[:2]
if not jwt:
    print("ERROR: FYERS_ACCESS_TOKEN must contain ':' and JWT part"); sys.exit(1)

# Pick a common symbol
TEST_SYMBOL = "NSE:SBIN-EQ"
RESOLUTION = "5"  # minutes
limit = 10

# Endpoint choices (try recommended data-rest cluster)
ENDPOINTS = [
    "https://api.fyers.in/data-rest/v2/history/",
    "https://api-t1.fyers.in/data-rest/v2/history/",
    "https://api.fyers.in/api/v3/quotes/history",   # fallback
]

end = int(time.time())
start = end - (int(RESOLUTION) * 60 * limit)

for url in ENDPOINTS:
    try:
        headers = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}
        payload = {
            "symbol": TEST_SYMBOL,
            "resolution": RESOLUTION,
            "date_format": 0,
            "range_from": start,
            "range_to": end,
            "cont_flag": "1"
        }
        print("Calling:", url)
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        print("HTTP", r.status_code)
        text = r.text[:1200]
        print("RAW:", text)
        try:
            j = r.json()
            print("JSON keys:", list(j.keys())[:10])
            print(json.dumps(j, indent=2)[:1600])
        except Exception as e:
            print("Not JSON:", e)
        # break on 200 OK
        if r.status_code == 200:
            break
    except Exception as e:
        print("ERR", e)

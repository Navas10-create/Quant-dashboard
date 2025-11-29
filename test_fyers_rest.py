# test_fyers_rest.py
from dotenv import load_dotenv
load_dotenv()

import os, json, requests, sys, time

URL = "https://api.fyers.in/data-rest/v2/history/"

token = os.getenv("FYERS_ACCESS_TOKEN")
if not token:
    print("ERROR: FYERS_ACCESS_TOKEN not set in environment")
    sys.exit(2)

# Token format is <client_id>:<jwt>
if ':' not in token:
    print("ERROR: Token format invalid")
    print("Value:", token)
    sys.exit(2)

client_id, jwt = token.split(":", 1)

AUTH_HEADER = f"Bearer {jwt}"

TEST_SYMBOL = "FOREX:USDINR"

RESOLUTION = "5"

end_time = int(time.time())
start_time = end_time - (10 * 5 * 60)

headers = {
    "Authorization": AUTH_HEADER,
    "Content-Type": "application/json"
}

payload = {
    "symbol": TEST_SYMBOL,
    "resolution": RESOLUTION,
    "date_format": "0",
    "range_from": start_time,
    "range_to": end_time,
    "cont_flag": "1"
}

print("Calling Fyers v3 history endpoint for:", TEST_SYMBOL)
print("Payload:", json.dumps(payload))

r = requests.post(URL, json=payload, headers=headers, timeout=15)
print("Status:", r.status_code)

try:
    data = r.json()
    print("JSON keys:", list(data.keys()))
    if "candles" in data:
        print("candles sample:", data["candles"][:3])
    else:
        print("FULL RESPONSE:", json.dumps(data, indent=2))
except:
    print("RAW TEXT:", r.text)

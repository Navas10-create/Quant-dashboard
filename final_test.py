from dotenv import load_dotenv
load_dotenv()

import os, json, requests, sys, time

URL = "https://api-t1.fyers.in/data-rest/v2/history/"

token = os.getenv("FYERS_ACCESS_TOKEN")
client_id, jwt = token.split(":", 1)

headers = {
    "Authorization": f"Bearer {jwt}",
    "Content-Type": "application/json"
}

TEST_SYMBOL = " NSE:SBIN-EQ."
end_time = int(time.time())
start_time = end_time - (10 * 5 * 60)

payload = {
    "symbol": TEST_SYMBOL,
    "resolution": "5",
    "date_format": "0",
    "range_from": start_time,
    "range_to": end_time,
    "cont_flag": "1"
}

print("Calling:", URL)
print("Payload:", payload)

r = requests.post(URL, json=payload, headers=headers)
print("Status:", r.status_code)
print("Response:", r.text[:500])

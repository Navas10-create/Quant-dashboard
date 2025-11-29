from dotenv import load_dotenv
load_dotenv()

import os, requests

token = os.getenv("FYERS_ACCESS_TOKEN")
client_id, jwt = token.split(":", 1)

headers = {
    "Authorization": f"Bearer {jwt}",
    "Content-Type": "application/json"
}

url = "https://api.fyers.in/api/v3/profile"
response = requests.get(url, headers=headers)

print("Status:", response.status_code)
print("Body:", response.text[:500])

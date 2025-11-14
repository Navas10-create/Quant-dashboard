import os
import re
import json
import time
import requests
import webbrowser
import hashlib

from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv, set_key

# ============================================================
#  FYERS TOKEN AUTO GENERATOR (CLEAN VERSION - API v3)
# ============================================================

# --- Load environment variables ---
BASE_DIR = os.path.dirname(__file__)
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

FYERS_APP_ID = os.getenv("FYERS_CLIENT_ID") or os.getenv("BROKER_API_KEY")
FYERS_SECRET_ID = os.getenv("FYERS_SECRET_ID") or os.getenv("BROKER_API_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI") or "http://127.0.0.1:5000/fyers/callback"

AUTH_URL = (
    f"https://api-t1.fyers.in/api/v3/generate-authcode"
    f"?client_id={FYERS_APP_ID}&redirect_uri={REDIRECT_URI}"
    f"&response_type=code&state=openalgo"
)

TOKEN_URL = "https://api-t1.fyers.in/api/v3/validate-authcode"

# Storage for the captured authorization code
auth_code_holder = {"code": None}


# ============================================================
#  HTTP HANDLER TO CAPTURE AUTH CODE FROM REDIRECT
# ============================================================

class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if "code=" in self.path:
            # Extract authorization code from redirect URL
            code = re.search(r"auth_code=([\w\-_.]+)", self.path)

            if code:
                auth_code_holder["code"] = code.group(1)
                print(f"\nAuthorization Code Captured:\n{auth_code_holder['code']}\n")

                # Respond to browser
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                message = "<h2>Authorization successful.</h2><p>You may close this window.</p>"
                self.wfile.write(message.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


# ============================================================
#  STEP 1: OPEN LOGIN PAGE AND CAPTURE AUTH CODE
# ============================================================

def get_auth_code():
    print("\nOpening Fyers login page...")
    print("If it does not open automatically, visit the URL below manually:\n")
    print(AUTH_URL + "\n")

    # Open Fyers login page
    webbrowser.open(AUTH_URL)

    # Start a small local HTTP server to catch redirect
    server = HTTPServer(("127.0.0.1", 5000), AuthHandler)
    print("Waiting for authorization (log in to Fyers and approve)...")
    server.handle_request()  # waits for a single request
    server.server_close()

    if not auth_code_holder["code"]:
        raise Exception("Failed to capture authorization code. Try again.")
    return auth_code_holder["code"]


# ============================================================
#  STEP 2: EXCHANGE AUTH CODE FOR ACCESS TOKEN
# ============================================================

# ============================================================
#  STEP 2: EXCHANGE AUTH CODE FOR ACCESS TOKEN (Fyers API v3)
# ============================================================

def exchange_token(auth_code):
    """Exchange authorization code for a live access token."""
    import hashlib

    # Fyers requires SHA256 hash of (App ID + Secret ID)
    app_id_hash = hashlib.sha256(f"{FYERS_APP_ID}:{FYERS_SECRET_ID}".encode()).hexdigest()


    payload = {
        "grant_type": "authorization_code",
        "app_id": FYERS_APP_ID,
        "appIdHash": app_id_hash,
        "secret_key": FYERS_SECRET_ID,
        "redirect_uri": REDIRECT_URI,
        "code": auth_code
    }

    headers = {"Content-Type": "application/json"}

    print("\nRequesting Access Token...")
    try:
        resp = requests.post("https://api-t1.fyers.in/api/v3/validate-authcode",
                             headers=headers, json=payload, timeout=10)
        data = resp.json()
        print("Response:", json.dumps(data, indent=2))
        if data.get("s") == "ok" and "access_token" in data:
            print("\nAccess Token Obtained Successfully!\n")
            return data["access_token"]
        else:
            raise Exception(data.get("message", "Unknown error"))
    except Exception as e:
        raise Exception(f"Token exchange failed: {e}")


# ============================================================
#  STEP 3: UPDATE .ENV FILE WITH NEW TOKEN
# ============================================================


def update_env_file(token):
    # Ensure the token is APPID:JWT format
    app_id = os.getenv("BROKER_API_KEY") or os.getenv("FYERS_CLIENT_ID")
    if app_id and not token.startswith(f"{app_id}:"):
        token = f"{app_id}:{token}"

    # Write token into .env without quotes
    try:
        set_key(ENV_PATH, "FYERS_ACCESS_TOKEN", token)
        print("FYERS_ACCESS_TOKEN updated in .env (no quotes).")
    except Exception as e:
        print(" Failed to update .env:", e)


# ============================================================
#  MAIN SCRIPT EXECUTION
# ============================================================

def main():
    print("===============================================")
    print(" FYERS TOKEN AUTO GENERATOR (API v3 Compatible) ")
    print("===============================================\n")

    print(f"App ID      : {FYERS_APP_ID}")
    print(f"Redirect URI: {REDIRECT_URI}")
    print(f"Secret ID   : {FYERS_SECRET_ID[:6]}... (hidden)\n")

    try:
        auth_code = get_auth_code()
        token = exchange_token(auth_code)
        update_env_file(token)
        print("Access token generation complete. You may now start OpenAlgo.")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        time.sleep(1)


if __name__ == "__main__":
    main()

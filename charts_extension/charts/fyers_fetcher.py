import os
import json
import time
import threading
import requests
import logging

# Set up a basic logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ADD THIS AT THE TOP (after other imports):

try:
    from fyers_apiv3 import fyersModel
except ImportError:
    logger.warning("fyers_apiv3 not installed")
    fyersModel = None

try:
    import requests
except ImportError:
    raise ImportError("requests library required: pip install requests")

from datetime import datetime, timedelta


def get_fyers_client(client_id, access_token):
    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="")
    profile = fyers.get_profile()
    if "s" in profile and profile["s"] == "ok":
        print(f"[✅] Connected as {profile['data']['name']}")
        return fyers
    else:
        print("[❌] Invalid or expired token. Regenerate the access token.")
        return None
# ============================================================
# === ENVIRONMENT CONFIGURATION ===
# ============================================================

# Read environment variables (supports both FYERS_* and BROKER_* naming)
FYERS_CLIENT_ID = (
    os.getenv("FYERS_CLIENT_ID")
    or os.getenv("BROKER_API_KEY")
    or ""
)

FYERS_ACCESS_TOKEN = (
    os.getenv("FYERS_ACCESS_TOKEN")
    or os.getenv("BROKER_API_KEY")
    or ""
)

# Fyers REST endpoints
FYERS_DATA_URL = os.getenv("FYERS_DATA_URL", "https://api.fyers.in/data-rest/v2/history/")

# Configuration settings from your .env file
CACHE_TTL = int(os.getenv("CHART_CACHE_TTL", os.getenv("FYERS_CACHE_TTL", "60")))
POLL_INTERVAL = int(os.getenv("CHART_POLL_INTERVAL", "10"))
MAX_DAYS = int(os.getenv("FYERS_RANGE_DAYS", "5"))

# Authorization header for Fyers API requests
HEADERS = {
    "Authorization": f"Bearer {FYERS_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

# Local in-memory cache
_cache = {}
_lock = threading.Lock()


# ============================================================
# === CORE FETCH FUNCTION ===
# ============================================================

def fetch_ohlc(symbol, interval="5minute", range_days=None):
    """
    Fetch OHLC (Open, High, Low, Close) data from Fyers REST API.

    Args:
        symbol (str): Fyers symbol, e.g., "NSE:NIFTY50-INDEX"
        interval (str): timeframe like "1minute", "5minute", "1hour", "1day"
        range_days (int): number of days of data to pull (default = MAX_DAYS)

    Returns:
        list of dict: [{time, open, high, low, close, volume}, ...]
    """

    # Handle missing or invalid tokens
    if not FYERS_ACCESS_TOKEN or "FAKE" in FYERS_ACCESS_TOKEN:
        raise ValueError("Fyers access token missing or invalid in environment (.env).")

    range_days = range_days or MAX_DAYS
    to_date = datetime.now()
    from_date = to_date - timedelta(days=range_days)

    params = {
        "symbol": symbol,
        "resolution": interval,
        "date_format": "1",
        "range_from": from_date.strftime("%Y-%m-%d"),
        "range_to": to_date.strftime("%Y-%m-%d"),
        "cont_flag": "1",
    }

    print(f"[INFO] Fetching OHLC: {symbol}, interval={interval}, days={range_days}")
    print(f"[DEBUG] Params: {params}")

    try:
        resp = requests.get(FYERS_DATA_URL, headers=HEADERS, params=params, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Fyers API request failed: {e}")

    data = resp.json()

    # Validate response
    if not data or data.get("s") != "ok":
        raise Exception(f"Fyers API error: {data}")

    candles = data.get("candles", [])
    if not candles:
        raise Exception(f"No OHLC data returned for {symbol}.")

    # Convert Fyers candles into frontend-friendly format
    formatted = [
    {
        "time": int(c),
        "open": float(c),
        "high": float(c),
        "low": float(c),
        "close": float(c),
        "volume": float(c),
    }
    for c in candles
]


    return formatted


# ============================================================
# === CACHE WRAPPER (ANTI-RATE LIMIT) ===
# ============================================================

def cached_fetch(symbol, interval="5minute", range_days=None):
    """
    Cached version of fetch_ohlc() to reduce redundant Fyers API calls.
    Respects CHART_CACHE_TTL from .env.
    """
    range_days = range_days or MAX_DAYS
    key = f"{symbol}_{interval}_{range_days}"
    now = time.time()

    with _lock:
        # If data exists and still valid
        if key in _cache and now - _cache[key]["time"] < CACHE_TTL:
            print(f"[CACHE] Returning cached data for {symbol} ({interval})")
            return _cache[key]["data"]

        # Fetch new data
        print(f"[CACHE] Fetching fresh data for {symbol} ({interval})")
        data = fetch_ohlc(symbol, interval, range_days)
        _cache[key] = {"data": data, "time": now}
        return data


# ============================================================
# === SAFE REQUEST RETRY HANDLER (for internal use) ===
# ============================================================

def _request_with_retries(url, params, headers, retries=3, backoff=0.75):
    """
    Low-level helper that retries failed requests with exponential backoff.
    """
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=8)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(backoff * (2 ** i))


# ============================================================
# === OPTIONAL MOCK FALLBACK (OFFLINE TESTING) ===
# ============================================================

def mock_fetch(symbol="NSE:NIFTY50-INDEX", interval="5minute", points=100):
    """
    Generate random mock OHLC data for offline testing.
    """
    import random
    base_price = 20000
    candles = []
    ts = int(time.time()) - (points * 300)

    for _ in range(points):
        open_p = base_price + random.uniform(-50, 50)
        close_p = open_p + random.uniform(-20, 20)
        high_p = max(open_p, close_p) + random.uniform(0, 20)
        low_p = min(open_p, close_p) - random.uniform(0, 20)
        volume = random.uniform(1000, 5000)
        candles.append({
            "time": ts,
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": round(volume, 2),
        })
        ts += 300  # increment by 5 minutes

    print("[MOCK] Returning simulated data (offline mode)")
    return candles


# ============================================================
# === MAIN TEST BLOCK (run standalone) ===
# ============================================================

if __name__ == "__main__":
    symbol = "NSE:NIFTY50-INDEX"
    try:
        data = cached_fetch(symbol, "5minute")
        print(f"✅ Retrieved {len(data)} candles for {symbol}")
    except Exception as e:
        print(f"⚠️ {e}")
        print("Using mock data instead...")
        data = mock_fetch(symbol)
        print(f"Generated {len(data)} mock candles.")
